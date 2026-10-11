import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.reports import ai_narrative, document, repository
from app.modules.reports.formats import FORMATO_PRINCIPAL, FORMATOS, FormatoInforme
from app.modules.reports.models import Report
from app.modules.reports.opciones import OpcionesInforme

#: Colisiones consecutivas de número de versión antes de rendirse. Tres es de
#: sobra: cada intento lee el máximo ya confirmado, así que solo puede fallar
#: si otra generación del mismo caso confirma justo en medio.
_REINTENTOS_DE_VERSION = 3


class CaseNotFoundError(LookupError):
    pass


class EmptyTimelineError(ValueError):
    pass


class EmptySelectionError(ValueError):
    """
    El caso tiene cronología, pero las opciones elegidas la dejan vacía.

    Se distingue de `EmptyTimelineError` a propósito: allí falta el Módulo 4 y
    no hay nada que el perito pueda hacer; aquí el arreglo está en su propia
    petición, y el mensaje dice cuál.
    """


class VersionConflictError(RuntimeError):
    """Varias generaciones simultáneas del mismo caso se pisaron la versión."""


class ReportFileMissingError(LookupError):
    """La fila existe en `reports` pero el fichero ya no está en disco."""


class ReportTamperedError(RuntimeError):
    """El fichero en disco no es el que se emitió: su huella no coincide."""


class PromptNotStoredError(LookupError):
    """El informe es anterior a que se archivase el prompt enviado a la IA."""


#: Clave con la que la transcripción del prompt figura en `reports.huellas`.
#: No es un `FormatoInforme`: no es una copia del informe, es el registro de
#: cómo se redactó.
CLAVE_PROMPT = "prompt"


def generate_report(
    db: Session,
    case_id: int,
    generado_por: str,
    notas: str | None = None,
    opciones: OpcionesInforme | None = None,
) -> Report:
    opciones = opciones or OpcionesInforme()
    case = repository.get_case(db, case_id)
    if case is None:
        raise CaseNotFoundError(f"No existe el caso {case_id}")

    timeline_events = repository.get_timeline_events(db, case_id)
    if not timeline_events:
        raise EmptyTimelineError(
            f"El caso {case_id} todavía no tiene eventos en la línea temporal (Módulo 4)"
        )

    # El recorte se aplica aquí, antes de la IA, y no más tarde: el prompt
    # numera los eventos [E1], [E2]… y valida que la narrativa no cite
    # ninguno inexistente. Si el modelo redactase sobre la cronología entera
    # y el documento imprimiese una recortada, el informe hablaría de hechos
    # que sus propias tablas no recogen — y la comprobación de citas, que es
    # la defensa contra la alucinación, daría por buenas esas referencias.
    # De qué tabla salen los indicadores del Anexo B no lo decide este módulo:
    # depende de qué exista en la base. La procedencia viaja hasta el documento
    # porque es lo que el anexo declara (ver osint.py).
    registro_osint = repository.get_registro_osint(db, case_id)
    seleccion = opciones.aplicar(
        timeline_events,
        repository.get_evidences(db, case_id),
        registro_osint.indicadores,
        repository.get_tracking_events(db, case_id),
    )
    if not seleccion.timeline_events:
        raise EmptySelectionError(
            f"Las opciones elegidas no dejan ningún evento en la cronología del caso "
            f"{case_id}: el caso tiene {len(timeline_events)} evento(s), pero ninguno "
            f"entra en el alcance seleccionado. Amplía la franja temporal, baja la "
            f"severidad mínima o incluye más anexos."
        )

    narrativa = ai_narrative.generar_narrativa(case, seleccion.timeline_events, notas)

    # Un único sello de tiempo para el documento y para su registro en base
    # de datos: si cada uno estampa su propio `now()`, el PDF y la fila que
    # lo referencia declaran fechas distintas.
    generado_el = datetime.now(timezone.utc)
    contexto = dict(
        case=case,
        timeline_events=seleccion.timeline_events,
        narrativa=narrativa,
        generado_por=generado_por,
        generado_el=generado_el,
        evidences=seleccion.evidences,
        osint_results=seleccion.osint_results,
        fuente_osint=registro_osint.fuente,
        tracking_events=seleccion.tracking_events,
        notas=notas,
        opciones=opciones,
    )

    # El número de versión va impreso en el propio documento (código
    # INF-XXXX-vN), así que si otra generación simultánea se queda con él no
    # basta con reintentar la inserción: hay que recomponer el informe entero.
    # La llamada a la IA se queda fuera del bucle, que es lo caro y lo que no
    # depende de la versión.
    for _ in range(_REINTENTOS_DE_VERSION):
        version = repository.next_version(db, case_id)
        try:
            report = repository.reservar_report(
                db,
                case_id=case_id,
                resumen_ia=narrativa.texto_plano,
                archivo_pdf=_ruta_relativa(case_id, version, FORMATO_PRINCIPAL),
                generado_por=generado_por,
                version=version,
                fecha_generacion=generado_el,
                notas=notas,
                opciones=opciones.como_json(),
            )
        except IntegrityError:
            # Otro proceso emitió esta versión mientras tanto. Aún no se ha
            # escrito nada en disco, así que basta con volver a intentarlo.
            db.rollback()
            continue

        doc = document.construir_documento(version=version, **contexto)
        # Se componen todos los formatos elegidos antes de tocar el disco: si
        # uno falla, no queda un informe a medio emitir con unas copias sí y
        # otras no. Se recorren en el orden del Enum y no en el del conjunto
        # recibido, para que el resultado no dependa del orden de iteración de
        # un `set`.
        copias = {
            formato: FORMATOS[formato].render(doc)
            for formato in FormatoInforme
            if formato in opciones.formatos
        }

        # El apartado 8 del informe declara con qué modelo y con qué versión
        # de instrucciones se redactó. Archivar el texto literal es lo que
        # convierte esa declaración en algo comprobable: es la única entrada
        # del informe que no se puede reconstruir leyendo el propio documento.
        # Va con las copias, no en una columna: es un documento de la emisión,
        # como ellas, y se le exige la misma integridad.
        ficheros: dict[str, tuple[Path, bytes]] = {
            formato.value: (_ruta_absoluta(report.archivo_pdf, formato), contenido)
            for formato, contenido in copias.items()
        }
        if narrativa.prompt:
            ficheros[CLAVE_PROMPT] = (
                _ruta_prompt(report.archivo_pdf),
                narrativa.prompt.encode("utf-8"),
            )

        # La huella se calcula sobre los bytes que se acaban de componer, no
        # releyendo el fichero: es la huella de *lo que se emitió*. Releerlo
        # daría por buena cualquier alteración ocurrida entre escribir y
        # verificar, que es justo el hueco que esto viene a cerrar.
        report.huellas = {
            clave: _huella(contenido) for clave, (_, contenido) in ficheros.items()
        }

        try:
            for ruta, contenido in ficheros.values():
                ruta.parent.mkdir(parents=True, exist_ok=True)
                ruta.write_bytes(contenido)
        except OSError:
            # Sin documentos no hay informe: una fila que declara un informe
            # emitido cuyo documento no existe es peor que no tener la fila.
            db.rollback()
            raise

        db.commit()
        db.refresh(report)
        return report

    raise VersionConflictError(
        f"No se ha podido asignar un número de versión al informe del caso {case_id}: "
        f"otras generaciones se adelantaron {_REINTENTOS_DE_VERSION} veces seguidas. "
        f"Vuelve a intentarlo."
    )


def _huella(contenido: bytes) -> str:
    """SHA-256 en hexadecimal de una copia del informe."""
    return hashlib.sha256(contenido).hexdigest()


def _huella_del_fichero(ruta: Path) -> str:
    """Igual que `_huella`, leyendo por bloques para no cargar el PDF entero."""
    digest = hashlib.sha256()
    with ruta.open("rb") as fichero:
        for bloque in iter(lambda: fichero.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _ruta_relativa(case_id: int, version: int, formato: FormatoInforme) -> str:
    """Ruta que se guarda en base de datos, relativa al almacén de informes."""
    return f"case_{case_id}/report_v{version}.{formato.value}"


def _ruta_prompt(archivo_pdf: str) -> Path:
    """Transcripción del prompt, junto a las copias del informe que explicó."""
    return _ruta_absoluta(archivo_pdf, FORMATO_PRINCIPAL).with_suffix(".prompt.txt")


def _ruta_absoluta(archivo_pdf: str, formato: FormatoInforme) -> Path:
    """
    Resuelve la ruta guardada contra el almacén configurado.

    Acepta también rutas absolutas: los informes emitidos antes de que esto
    se guardase en relativo las tienen, y siguen siendo válidas mientras el
    fichero exista donde decía.
    """
    guardada = Path(archivo_pdf)
    if not guardada.is_absolute():
        guardada = Path(settings.reports_storage_dir).resolve() / guardada
    return guardada.with_suffix(f".{formato.value}")


def get_report_file(
    db: Session,
    report_id: int,
    formato: FormatoInforme = FORMATO_PRINCIPAL,
) -> tuple[Report, Path]:
    """
    Devuelve el informe y la ruta del fichero pedido, comprobando que sigue ahí.

    La columna oficial del modelo de datos solo guarda la ruta del PDF; las
    demás copias son ese mismo fichero con otra extensión, emitidas en la
    misma llamada. Se derivan en vez de almacenarse para no añadir columnas
    que la especificación del proyecto no contempla.
    """
    report = repository.get_report(db, report_id)
    if report is None:
        raise LookupError(f"No existe el informe {report_id}")

    ruta = _ruta_absoluta(report.archivo_pdf, formato)
    if not ruta.is_file():
        raise ReportFileMissingError(_por_que_no_esta(report, formato))

    _verificar_huella(report, ruta, formato.value, f"La copia en {formato.value}")

    return report, ruta


def _por_que_no_esta(report: Report, formato: FormatoInforme) -> str:
    """
    Por qué falta esta copia. Son tres motivos distintos y el arreglo de cada
    uno también, así que decir solo «no está disponible» obliga a quien lo
    recibe a adivinar cuál le ha tocado.

    En ninguno de los tres se compone la copia ahora: se leería la base de
    datos tal y como esté hoy y el resultado no coincidiría con el documento
    firmado en su día, bajo el mismo código de informe.
    """
    comun = (
        f"El informe {report.id} está registrado pero su copia en {formato.value} no está "
        f"en el almacenamiento."
    )
    if report.opciones is None:
        return (
            f"{comun} Se emitió antes de que el módulo generase varios formatos, así que "
            f"solo tiene PDF. Si necesitas este formato, genera una versión nueva."
        )
    if formato.value not in (report.opciones.get("formatos") or []):
        emitidos = ", ".join(report.opciones.get("formatos") or []) or "ninguno"
        return (
            f"{comun} No se pidió al emitirlo: esta versión se emitió en {emitidos}. Si "
            f"necesitas este formato, genera una versión nueva del informe."
        )
    # Se pidió, se emitió y ya no está: el fichero ha desaparecido del almacén
    # después de emitirse. Eso no es una opción del perito, es un problema del
    # almacenamiento, y conviene que se lea como tal.
    return (
        f"{comun} Sí se emitió en este formato, de modo que el fichero ha desaparecido "
        f"del almacén después de emitirse. Revisa el almacenamiento antes de dar el "
        f"informe por perdido."
    )


def get_report_prompt(db: Session, report_id: int) -> tuple[Report, Path]:
    """
    Transcripción de lo que se envió a la IA para redactar este informe.

    Se sirve por separado y no como un formato más: no es una copia del
    informe, es el registro de cómo se redactó. Se verifica igual que ellas.
    """
    report = repository.get_report(db, report_id)
    if report is None:
        raise LookupError(f"No existe el informe {report_id}")

    ruta = _ruta_prompt(report.archivo_pdf)
    if not ruta.is_file():
        raise PromptNotStoredError(
            f"El informe {report_id} no conserva las instrucciones enviadas a la IA: se "
            f"emitió antes de que se archivasen. No se reconstruyen ahora, porque el prompt "
            f"que produciría el código de hoy no tiene por qué ser el que se usó entonces, "
            f"y presentarlo como tal sería falsear el registro."
        )

    _verificar_huella(report, ruta, CLAVE_PROMPT, "La transcripción del prompt")

    return report, ruta


def _verificar_huella(report: Report, ruta: Path, clave: str, que_es: str) -> None:
    """
    Que el fichero exista no dice que sea el que se emitió.

    Se comprueba antes de servirlo porque un informe pericial alterado hace
    más daño entregado que no entregado: quien lo recibe no tiene forma de
    saberlo. Los informes anteriores a la columna `huellas` no la tienen y se
    sirven sin verificar.
    """
    esperada = (report.huellas or {}).get(clave)
    if esperada is not None and _huella_del_fichero(ruta) != esperada:
        raise ReportTamperedError(
            f"{que_es} del informe {report.id} no coincide con la huella registrada al "
            f"emitirlo: el fichero almacenado no es el que este informe declara. No se "
            f"sirve. Hay que revisar el almacenamiento y, si el original no puede "
            f"recuperarse, emitir una versión nueva del informe: reemitir esta misma "
            f"versión produciría otro documento bajo el mismo código."
        )


def huella_registrada(report: Report, formato: FormatoInforme | str) -> str | None:
    """
    Huella declarada para esa copia, o `None` si el informe es anterior a que
    se registrasen. Se publica al descargar para que el destinatario pueda
    contrastar el fichero por su cuenta (`sha256sum`) sin fiarse de que la
    API haya hecho la comprobación.
    """
    clave = formato.value if isinstance(formato, FormatoInforme) else formato
    return (report.huellas or {}).get(clave)
