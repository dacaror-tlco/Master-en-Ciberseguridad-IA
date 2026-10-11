"""
De dónde saca el asistente su conocimiento de NEXUS.

«Que se haga experto en los módulos» se resuelve con la documentación que el
proyecto ya escribe y mantiene —`docs/CONTRATOS.md`,
`docs/INTEGRACION_Y_DESPLIEGUE.md`, `CLAUDE.md` y los README de cada
módulo—, no con un entrenamiento ni con una base de conocimiento aparte. Es
la fuente correcta por dos motivos: es la que el equipo actualiza cuando algo
cambia, y es verificable (el asistente puede decir de qué documento y de qué
apartado sale lo que afirma).

**Por qué no hay embeddings, ni vectores, ni Neo4j, ni Obsidian.** El corpus
son unas pocas decenas de apartados de markdown, no un millón de documentos.
Con ese tamaño, una búsqueda por solapamiento de términos con peso IDF acierta
tanto como un índice vectorial y no añade ni un servicio, ni una dependencia,
ni un proceso de reindexado que se quede desincronizado. Un grafo tipo Neo4j
sí tendría sentido para correlacionar entidades *entre casos* —una IP que
aparece en dos investigaciones—, pero eso es exactamente lo contrario del
aislamiento por caso que exige `context.py`, así que sería una decisión de
producto (y de equipo), no un detalle de implementación del chat.

El índice se construye una vez, al primer uso, y se cachea en memoria: el
proceso de uvicorn recarga con `--reload` cuando cambian los `.md` del propio
backend, y para el resto basta reiniciar.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

#: Raíz del repositorio, vista desde este fichero
#: (sharingan/app/modules/chat/conocimiento.py -> cuatro niveles arriba).
_RAIZ = Path(__file__).resolve().parents[4]

#: Documentos que se indexan, en orden de autoridad. Los que no existan se
#: ignoran en silencio: este backend tiene que poder arrancar solo, fuera del
#: monorepo de integración, y entonces sencillamente sabe menos.
_DOCUMENTOS: tuple[tuple[str, str], ...] = (
    ("docs/CONTRATOS.md", "Contrato de datos entre módulos"),
    ("docs/INTEGRACION_Y_DESPLIEGUE.md", "Integración y despliegue"),
    ("CLAUDE.md", "Especificación del proyecto"),
    ("README.md", "README del proyecto"),
    ("sharingan/README.md", "Módulo 5 — Informes"),
    ("backend/README.md", "Módulo 1 — Casos"),
    ("scam-shield/README.md", "Módulo 2 — OSINT y Fraude"),
    ("track-inc/README.md", "Módulo 3 — Tracking"),
    ("timeline/README.md", "Módulo 4 — Timeline"),
)

#: Tope de caracteres del bloque de documentación que entra en el prompt. Un
#: modelo local de 3B con 8k de ventana no tiene sitio para más sin desplazar
#: el expediente del caso, que siempre tiene prioridad.
LIMITE_CARACTERES = 3500

#: Los hechos estructurales de NEXUS, escritos a mano y presentes en **todas**
#: las peticiones, no recuperados.
#:
#: Existe porque la recuperación falló justo aquí en la primera prueba real: a
#: la pregunta «qué módulos tiene NEXUS», el modelo local devolvió cinco
#: módulos inventados —«Integración y Despliegue», «Redes y Seguridad»— que
#: eran, literalmente, los títulos de los documentos que se le habían pasado
#: como contexto. Un modelo pequeño no distingue de forma fiable «esto es un
#: apartado del manual» de «esto es un elemento del sistema».
#:
#: La lección no es que la recuperación sobre `docs/` no sirva —sirve, y bien,
#: para explicar cómo funciona algo—, sino que los pocos hechos que el
#: asistente no puede permitirse equivocar no deben depender de que una
#: búsqueda acierte. Son unas pocas líneas y caben siempre.
FICHA_NEXUS = """=== QUÉ ES NEXUS (datos fijos, no los contradigas) ===
NEXUS es una plataforma de asistencia a peritos informáticos y analistas
forenses. Tiene exactamente CINCO módulos, y son estos y no otros:
1. Gestión de Casos — crea y gestiona casos periciales y sus evidencias.
   Tablas: cases, evidences.
2. OSINT y Fraude — analiza indicadores en fuentes abiertas (dominios, IPs,
   correos, wallets, teléfonos). Tabla: osint_findings.
3. Tracking Post-Incidente — analiza logs y detecta actividad sospechosa.
   Tabla: tracking_events.
4. Línea Temporal — correlaciona lo anterior en una cronología del caso.
   Tabla: timeline_events.
5. Generador de Informes — redacta el informe pericial (norma UNE 197010) con
   ayuda de IA. Tabla: reports. Este asistente vive en este módulo.
Todo se relaciona por `case_id`. Cada módulo es un backend independiente, con
su propio proceso y puerto; comparten una única base de datos MySQL.
La identidad NO es un sexto módulo: es una capa transversal. El backend de
Casos es la autoridad —posee la tabla `users` y es el único que emite JWT—, y
los otros cuatro solo verifican el token con el mismo secreto compartido.
Todos los endpoints de los cinco módulos exigen JWT, incluida esta
conversación. Hay dos roles, `analyst` y `admin`; el segundo solo hace falta
para gestionar usuarios, no para leer un caso.
"""

#: Palabras que aparecen en casi todo y no discriminan nada.
_VACIAS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "del", "un", "una", "que",
    "se", "por", "con", "para", "es", "al", "lo", "como", "más", "o", "su",
    "sus", "no", "sin", "sobre", "este", "esta", "estos", "estas", "cada",
    "qué", "cuál", "cuáles", "cómo", "dónde", "cuando", "hay", "ser", "está",
}

_PALABRA = re.compile(r"[a-záéíóúüñ0-9_]+", re.IGNORECASE)


@dataclass(frozen=True)
class Fragmento:
    documento: str
    apartado: str
    texto: str
    #: Frecuencia de cada término, para puntuar sin recorrer el texto otra vez.
    terminos: frozenset[str]


def _tokenizar(texto: str) -> list[str]:
    return [
        p.lower()
        for p in _PALABRA.findall(texto.lower())
        if len(p) > 2 and p.lower() not in _VACIAS
    ]


def _trocear(contenido: str, documento: str) -> list[Fragmento]:
    """Parte un markdown por encabezados. Un apartado = un fragmento."""
    fragmentos: list[Fragmento] = []
    apartado = "(inicio)"
    buffer: list[str] = []

    def cerrar() -> None:
        texto = "\n".join(buffer).strip()
        if len(texto) < 40:
            return
        # Los apartados enormes se parten: si no, uno solo se come todo el
        # presupuesto de caracteres del prompt.
        for i in range(0, len(texto), 1400):
            trozo = texto[i : i + 1400]
            fragmentos.append(
                Fragmento(
                    documento=documento,
                    apartado=apartado,
                    texto=trozo,
                    terminos=frozenset(_tokenizar(f"{apartado} {trozo}")),
                )
            )

    for linea in contenido.splitlines():
        if linea.startswith("#"):
            cerrar()
            buffer = []
            apartado = linea.lstrip("#").strip() or "(sin título)"
        else:
            buffer.append(linea)
    cerrar()

    return fragmentos


@lru_cache(maxsize=1)
def _indice() -> tuple[list[Fragmento], dict[str, float]]:
    """Fragmentos de todos los documentos disponibles y su peso IDF."""
    fragmentos: list[Fragmento] = []
    for ruta_rel, titulo in _DOCUMENTOS:
        ruta = _RAIZ / ruta_rel
        try:
            contenido = ruta.read_text(encoding="utf-8")
        except OSError:
            continue
        fragmentos.extend(_trocear(contenido, titulo))

    total = len(fragmentos) or 1
    apariciones: dict[str, int] = {}
    for f in fragmentos:
        for termino in f.terminos:
            apariciones[termino] = apariciones.get(termino, 0) + 1

    idf = {t: math.log(total / n) for t, n in apariciones.items()}
    return fragmentos, idf


#: Fracción de la «masa» de la pregunta (la suma de IDF de sus términos) que un
#: apartado tiene que cubrir para entrar en el prompt.
#:
#: Calibrado midiendo, no a ojo. La puntuación absoluta no separa nada: a la
#: pregunta «¿qué módulos tiene NEXUS?» el mejor apartado puntuaba 8,76 y era
#: basura («Despliegue en producción (Docker/Portainer)»), mientras que a «¿qué
#: puertos usa cada backend?» el apartado correcto puntuaba 6,17. Lo que sí
#: separa es la **cobertura relativa**: cuánto de lo que se pregunta cubre
#: realmente ese apartado. Medido sobre cinco preguntas, las útiles caían en
#: 0,60-0,73 y las ruidosas en 0,51-0,58.
_COBERTURA_MINIMA = 0.60


def buscar(consulta: str, tope: int = 2) -> list[Fragmento]:
    """
    Los apartados de documentación que de verdad responden a la pregunta.

    Deliberadamente tacaño, y no por ahorrar tokens. Un modelo local pequeño no
    sabe descartar contexto que no viene a cuento: en la primera prueba real,
    con cuatro apartados vagamente relacionados delante, se inventó los cinco
    módulos de NEXUS copiando los títulos de esos apartados; con la misma
    pregunta y sin ellos, los enumeró correctamente. Para este modelo,
    documentación de más es peor que documentación de menos.
    """
    fragmentos, idf = _indice()
    if not fragmentos:
        return []

    terminos = set(_tokenizar(consulta))
    if not terminos:
        return []

    masa = sum(idf.get(t, 0.0) for t in terminos)
    if masa <= 0:
        return []

    puntuados = []
    for f in fragmentos:
        comunes = terminos & f.terminos
        # Con un solo término en común basta una palabra rara para colar un
        # apartado ajeno, así que se exigen dos.
        if len(comunes) < 2:
            continue
        cobertura = sum(idf.get(t, 0.0) for t in comunes) / masa
        if cobertura < _COBERTURA_MINIMA:
            continue
        puntuados.append((cobertura, f))

    puntuados.sort(key=lambda par: par[0], reverse=True)
    return [f for _, f in puntuados[:tope]]


def a_texto(fragmentos: list[Fragmento]) -> str:
    """
    El bloque de conocimiento tal cual viaja en el prompt.

    La ficha va siempre; los fragmentos recuperados, si los hay, van detrás y
    se presentan explícitamente como *extractos de manuales* con su documento y
    su apartado. Ese encuadre no es decorativo: sin él, un modelo pequeño toma
    el título del apartado por el nombre de una cosa del sistema.
    """
    if not fragmentos:
        return ""

    lineas = [
        "=== EXTRACTOS DE LA DOCUMENTACIÓN ===",
        "Fragmentos de los manuales del proyecto, seleccionados por su parecido "
        "con la pregunta. Los títulos que verás («Integración y despliegue», "
        "«Contrato de datos entre módulos»…) son nombres de APARTADOS DE "
        "DOCUMENTOS, nunca módulos ni componentes de NEXUS. Pueden no venir a "
        "cuento: si no responden a lo que se pregunta, ignóralos.",
    ]
    usados = 0
    for f in fragmentos:
        bloque = f"\n--- Documento «{f.documento}», apartado «{f.apartado}» ---\n{f.texto}"
        if usados + len(bloque) > LIMITE_CARACTERES:
            break
        lineas.append(bloque)
        usados += len(bloque)
    return "\n".join(lineas)
