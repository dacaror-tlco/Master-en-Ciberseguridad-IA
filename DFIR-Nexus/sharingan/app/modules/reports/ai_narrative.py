"""
Capa de IA: hallazgos y conclusiones del informe pericial.

Mismo principio que el resto de Nexus (ver ai_service.py de scam-shield):
la cronología ya viene resuelta de forma determinista por el Módulo 4
(timeline_events, ordenados por `orden`). El LLM no decide hechos ni
severidades — solo redacta, en base a esos eventos ya correlacionados,
los hallazgos y las conclusiones que se incluyen en el PDF final.

A diferencia de scam-shield (donde la narrativa IA es un extra opcional),
aquí es la razón de ser del módulo: si no hay ANTHROPIC_API_KEY
configurada, se lanza un error explícito en vez de degradar en silencio.

Trazabilidad (requisito pericial, no capricho técnico):

* Los eventos se numeran [E1], [E2]... en el prompt y se le exige al
  modelo que cada afirmación cite el evento del que procede. Después se
  valida por código que no ha citado ningún índice inexistente: es la
  comprobación de alucinación más barata disponible y no necesita red.
* `PROMPT_VERSION`, el modelo y el nivel de esfuerzo se devuelven junto al
  texto para poder estamparlos en el PDF. Un informe pericial tiene que
  poder declarar con qué se generó.
* Y además se devuelve el prompt **literal** que se envió, que es lo que
  permite comprobar esa declaración. Declarar «versión de instrucciones
  2026-08-15.1» obliga a creerse que esa versión decía lo que dice hoy el
  código; el texto guardado no hay que creérselo. Ahí va también la
  cronología concreta que se le pasó al modelo, que es el resto de la
  entrada y cambia en cada informe.
* No se fija `temperature`: Claude Opus 5 rechaza ese parámetro (HTTP 400).
  La reproducibilidad exacta no es alcanzable con un LLM, así que se
  gestiona declarándolo en el informe, no fingiéndola.
"""
import json
import re
from dataclasses import dataclass

import anthropic
from anthropic import Anthropic

from app.core.config import settings
from app.modules.shared.models import Case, TimelineEvent

MODEL = "claude-opus-5"
EFFORT = "medium"
PROMPT_VERSION = "2026-08-15.1"

# El pensamiento del modelo también consume `max_tokens`, así que se deja
# margen amplio: un caso con 30+ eventos truncaba las conclusiones a mitad
# de frase con el límite anterior de 1024.
_MAX_TOKENS = 8000

_SYSTEM_PROMPT = (
    "Eres un perito informático redactando dos secciones de un informe pericial forense: "
    "HALLAZGOS y CONCLUSIONES. Te paso el caso y su cronología de eventos, ya correlacionados "
    "y ordenados por otro módulo del sistema, numerados [E1], [E2], etc.\n\n"
    "HALLAZGOS: expón de forma técnica y objetiva qué ocurrió, siguiendo la cronología. "
    "Cada afirmación debe ir seguida de la referencia del evento del que procede, con el "
    "formato [E1] o [E1][E3] si procede de varios. No afirmes nada que no puedas referenciar.\n\n"
    "CONCLUSIONES: valoración pericial de lo anterior — alcance del incidente, vector de "
    "entrada si se deduce de los hechos, y limitaciones del análisis. Distingue lo acreditado "
    "de lo meramente indiciario.\n\n"
    "Escribe en español, en tono formal y objetivo, en párrafos de texto plano sin markdown "
    "ni encabezados. No inventes ningún hecho, dato, fecha ni evento que no esté en la "
    "información proporcionada: si algo no consta, dilo explícitamente."
)

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "hallazgos": {"type": "string"},
        "conclusiones": {"type": "string"},
    },
    "required": ["hallazgos", "conclusiones"],
    "additionalProperties": False,
}

_CITA = re.compile(r"\[E(\d+)\]")


class AIConfigError(RuntimeError):
    """La narrativa IA no se puede generar por falta de configuración (p.ej. sin API key)."""


class AIUnavailableError(RuntimeError):
    """La API de Anthropic no ha podido atender la petición (red, rate limit, error 5xx)."""


class AIResponseError(RuntimeError):
    """La respuesta del modelo no es utilizable en un informe (truncada, rechazada, o cita eventos inexistentes)."""


@dataclass(frozen=True)
class Narrativa:
    """Texto redactado por la IA más los metadatos que el PDF debe declarar."""

    hallazgos: str
    conclusiones: str
    modelo: str = MODEL
    esfuerzo: str = EFFORT
    version_prompt: str = PROMPT_VERSION
    #: Transcripción literal de lo que se envió al modelo, para archivarla
    #: junto al informe. Vacía cuando la narrativa no viene de una llamada
    #: real (previsualizaciones y tests), y entonces ni se archiva ni se
    #: menciona en el apartado 8: un informe no puede declarar que conserva
    #: un registro que no tiene.
    prompt: str = ""

    @property
    def texto_plano(self) -> str:
        """Versión de una sola cadena, que es como se guarda en `reports.resumen_ia`."""
        return f"HALLAZGOS\n\n{self.hallazgos}\n\nCONCLUSIONES\n\n{self.conclusiones}"


def _transcripcion(
    prompt_usuario: str,
    modelo: str = MODEL,
    esfuerzo: str = EFFORT,
    sistema: str | None = None,
    esquema: dict | None = None,
) -> str:
    """
    Lo que se archiva: los parámetros de la llamada y los dos prompts enteros.

    Se guardan también los parámetros porque el prompt por sí solo no explica
    la salida: el mismo texto con otro `effort` o con otro esquema de salida
    no produce lo mismo. Es la única parte del informe que un tercero no
    puede reconstruir a partir del propio documento.

    Todos los parámetros llegan como argumento en vez de leerse de las
    constantes porque desde que la narrativa puede redactarla un modelo local
    ya no hay un único valor posible: cambia el modelo, y con él el prompt de
    sistema y el esquema de salida. El registro tiene que decir qué se usó de
    verdad — es justamente lo que da sentido a archivarlo. Los valores por
    defecto son los de la ruta de Anthropic.
    """
    return (
        f"modelo: {modelo}\n"
        f"esfuerzo: {esfuerzo}\n"
        f"max_tokens: {_MAX_TOKENS}\n"
        f"version_prompt: {PROMPT_VERSION}\n"
        f"esquema_de_salida: "
        f"{json.dumps(esquema if esquema is not None else _OUTPUT_SCHEMA, ensure_ascii=False)}\n"
        f"\n===== SYSTEM =====\n{sistema if sistema is not None else _SYSTEM_PROMPT}\n"
        f"\n===== USUARIO =====\n{prompt_usuario}\n"
    )


def _build_prompt(case: Case, timeline_events: list[TimelineEvent], notas: str | None) -> str:
    lines = [
        f"Caso: {case.nombre}",
        f"Estado: {case.estado.value}",
        f"Responsable: {case.responsable or 'no asignado'}",
    ]
    if case.descripcion:
        lines.append(f"Descripción: {case.descripcion}")

    lines.append("")
    lines.append("Cronología de eventos (todas las horas en UTC):")
    for indice, event in enumerate(timeline_events, start=1):
        lines.append(
            f"[E{indice}] {event.fecha_hora.isoformat()} "
            f"({event.origen_modulo}#{event.origen_id}) {event.descripcion}"
        )

    if notas:
        lines.append("")
        lines.append(f"Notas e instrucciones del perito: {notas}")

    # Recordatorio de la regla de citación, al final y no solo en el prompt de
    # sistema. No es redundancia: un modelo pequeño atiende mucho más a lo
    # último que ha leído, y la primera narrativa generada en local salió sin
    # una sola referencia pese a que el sistema la exigía. A Claude no le
    # cambia nada —ya citaba—, así que va en la ruta común.
    if timeline_events:
        lines.append("")
        lines.append(
            f"RECUERDA: en HALLAZGOS, cada afirmación termina con la referencia del "
            f"evento del que procede, entre corchetes. Solo existen [E1] a "
            f"[E{len(timeline_events)}]; no inventes ninguna otra."
        )

    return "\n".join(lines)


def _validar_citas(texto: str, total_eventos: int) -> None:
    """
    Rechaza el informe si las citas no sostienen lo que afirma.

    Dos comprobaciones, y la segunda se añadió al abrir la redacción a modelos
    locales. Un modelo pequeño cumple la instrucción de citar mucho peor: la
    primera narrativa generada con `qwen2.5:3b` salió técnicamente razonable y
    **sin una sola referencia**, lo que la deja fuera de lo que este módulo
    promete —que cualquier afirmación pueda contrastarse con el registro del
    que sale— y eso lo lee un juez. No era un fallo del modelo local: era que
    aquí solo se comprobaba que las citas presentes fuesen válidas, nunca que
    hubiera alguna. Con Claude no se notaba porque siempre citaba.
    """
    citas = _CITA.findall(texto)

    inexistentes = sorted({int(n) for n in citas if not 1 <= int(n) <= total_eventos})
    if inexistentes:
        raise AIResponseError(
            "La narrativa cita eventos que no existen en la cronología: "
            + ", ".join(f"[E{n}]" for n in inexistentes)
        )

    if total_eventos > 0 and not citas:
        raise AIResponseError(
            "La narrativa no cita ni un solo evento de la cronología, así que sus "
            "afirmaciones no se pueden contrastar con el registro del que proceden. "
            "El informe no se genera: un hallazgo pericial sin referencia no es "
            "verificable."
        )


#: Esquema de salida propio de la ruta local, y la razón por la que existe.
#:
#: Con el mismo esquema que usa Claude —dos cadenas de texto— el modelo local
#: escribía hallazgos correctos y **sin una sola referencia**, aunque el prompt
#: de sistema y un recordatorio al final se la exigían. Probado y medido: dos
#: intentos, cero citas.
#:
#: Pedirle a un modelo pequeño que recuerde una convención mientras redacta no
#: funciona. Lo que sí funciona es que la convención no dependa de él: aquí
#: cada hallazgo es un objeto con su afirmación y la lista de eventos que la
#: sostienen, así que el esquema **obliga** a que las referencias existan, y
#: quien escribe los corchetes `[E1]` es este código y no el modelo. De paso
#: desaparece la posibilidad de que se invente el formato de la cita.
_OUTPUT_SCHEMA_LOCAL = {
    "type": "object",
    "properties": {
        "hallazgos": {
            "type": "array",
            "minItems": 1,
            # El tope de elementos es lo que de verdad acota la longitud, y por
            # tanto el tiempo: pedir brevedad en el prompt no bastó (la primera
            # narrativa con este esquema se truncó igualmente). Ocho hallazgos
            # cubren de sobra un caso normal — la cronología del caso de prueba
            # tiene siete eventos.
            "maxItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "afirmacion": {"type": "string"},
                    "eventos": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "integer"},
                    },
                },
                "required": ["afirmacion", "eventos"],
                "additionalProperties": False,
            },
        },
        "conclusiones": {"type": "string"},
    },
    "required": ["hallazgos", "conclusiones"],
    "additionalProperties": False,
}

_SYSTEM_PROMPT_LOCAL = (
    _SYSTEM_PROMPT
    + "\n\nFORMATO DE SALIDA: devuelve `hallazgos` como una lista. Cada elemento es un "
    "hecho con dos campos: `afirmacion`, la frase en prosa SIN corchetes ni referencias, "
    "y `eventos`, los números de los eventos que la sostienen (el 1 es [E1], el 2 es "
    "[E2], etc.). Cada afirmación necesita al menos un evento; si no puedes respaldarla "
    "con ninguno, no la incluyas. `conclusiones` sigue siendo texto corrido."
    # La concisión aquí no es estilo: el modelo corre en local y sin GPU genera
    # del orden de 5 tokens por segundo, así que cada palabra de más es tiempo
    # de espera y acerca el tope de generación, que corta el informe y lo
    # invalida. Un hallazgo por hecho relevante cubre un caso normal de sobra.
    "\n\nSé conciso: un hallazgo por hecho relevante, sin repetir lo mismo con otras "
    "palabras, y unas conclusiones de un párrafo o dos. No excedas las 600 palabras "
    "en total."
)


def _componer_hallazgos(hallazgos: list[dict], total_eventos: int) -> str:
    """
    Pasa los hallazgos estructurados al texto que va al informe.

    Los corchetes los pone este código, no el modelo: es lo que garantiza que
    la notación es siempre la misma y que no aparece ninguna referencia que no
    salga de la lista de eventos.
    """
    frases: list[str] = []
    for hallazgo in hallazgos:
        afirmacion = str(hallazgo.get("afirmacion", "")).strip()
        eventos = hallazgo.get("eventos") or []
        if not afirmacion:
            continue
        if not eventos:
            raise AIResponseError(
                "La IA ha devuelto un hallazgo sin ningún evento que lo respalde: "
                f"«{afirmacion[:80]}». El informe no se genera."
            )
        fuera = [n for n in eventos if not isinstance(n, int) or not 1 <= n <= total_eventos]
        if fuera:
            raise AIResponseError(
                "La narrativa cita eventos que no existen en la cronología: "
                + ", ".join(f"[E{n}]" for n in fuera)
            )
        if not afirmacion.endswith((".", ":", ";")):
            afirmacion += "."
        marcas = "".join(f"[E{n}]" for n in dict.fromkeys(eventos))
        frases.append(f"{afirmacion} {marcas}")

    if not frases:
        raise AIResponseError("La IA no ha devuelto ningún hallazgo utilizable.")
    return " ".join(frases)


def _narrativa_local(prompt_usuario: str, total_eventos: int) -> Narrativa:
    """
    Redacta la narrativa con el modelo local (Ollama), sin API de pago.

    Las comprobaciones son **las mismas** que en la ruta de Anthropic, y eso no
    es negociable: se exige JSON con los dos apartados, se rechaza si falta
    alguno y se validan las citas [E1] contra la cronología real. Un modelo
    pequeño se equivoca más, así que si acaso importan más aquí.

    Dos diferencias que el informe declara en su apartado 8, en vez de
    disimularlas: el modelo es otro (y peor redactando), y no hay concepto de
    «esfuerzo» — se registra el tope de generación, que es el parámetro
    equivalente que sí condiciona la salida.
    """
    from app.modules.chat import llm

    modelo = f"ollama/{settings.ollama_model}"
    esfuerzo = f"num_predict={settings.ollama_narrativa_num_predict}"

    try:
        salida = llm.generar(
            _SYSTEM_PROMPT_LOCAL,
            [{"role": "user", "content": prompt_usuario}],
            esquema=_OUTPUT_SCHEMA_LOCAL,
            num_predict=settings.ollama_narrativa_num_predict,
            proveedor="ollama",
        )
    except llm.LLMConfigError as exc:
        raise AIConfigError(str(exc)) from exc
    except llm.LLMUnavailableError as exc:
        raise AIUnavailableError(str(exc)) from exc
    except llm.LLMResponseError as exc:
        raise AIResponseError(str(exc)) from exc

    # Aquí sí se descarta una narrativa truncada, al revés que en el chat: un
    # informe pericial no se firma con las conclusiones cortadas a mitad de
    # frase. Es la misma regla que ya aplicaba la ruta de Anthropic.
    if salida.truncada:
        raise AIResponseError(
            "La respuesta de la IA se ha truncado por límite de tokens; el informe no se "
            "genera para no firmar unas conclusiones incompletas."
        )

    try:
        payload = json.loads(salida.texto)
    except json.JSONDecodeError as exc:
        raise AIResponseError("La respuesta de la IA no es un JSON válido.") from exc
    if not payload.get("hallazgos") or not payload.get("conclusiones"):
        raise AIResponseError("La respuesta de la IA no incluye hallazgos y conclusiones.")

    hallazgos = _componer_hallazgos(payload["hallazgos"], total_eventos)
    # Redundante por construcción —los corchetes los ha puesto el código— y a
    # propósito: si alguien cambia el esquema o el compositor, esta línea es la
    # que impide que un informe salga sin trazabilidad.
    _validar_citas(hallazgos, total_eventos)

    return Narrativa(
        hallazgos=hallazgos,
        conclusiones=str(payload["conclusiones"]).strip(),
        modelo=modelo,
        esfuerzo=esfuerzo,
        prompt=_transcripcion(
            prompt_usuario, modelo=modelo, esfuerzo=esfuerzo, sistema=_SYSTEM_PROMPT_LOCAL,
            esquema=_OUTPUT_SCHEMA_LOCAL,
        ),
    )


def generar_narrativa(
    case: Case,
    timeline_events: list[TimelineEvent],
    notas: str | None = None,
) -> Narrativa:
    prompt_usuario = _build_prompt(case, timeline_events, notas)

    if settings.narrativa_provider.strip().lower() == "ollama":
        return _narrativa_local(prompt_usuario, len(timeline_events))

    if not settings.anthropic_api_key:
        raise AIConfigError(
            "ANTHROPIC_API_KEY no está configurada: el Módulo 5 necesita una IA para "
            "redactar los hallazgos y las conclusiones del informe. Alternativa sin API "
            "de pago: pon NARRATIVA_PROVIDER=ollama en el .env y arranca Ollama con el "
            f"modelo «{settings.ollama_model}» — la redacción sale peor, pero el informe "
            "declara qué modelo la escribió y las comprobaciones de citas son las mismas."
        )

    client = Anthropic(api_key=settings.anthropic_api_key)
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            output_config={
                "effort": EFFORT,
                "format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA},
            },
            messages=[{"role": "user", "content": prompt_usuario}],
        )
    except anthropic.APIStatusError as exc:
        raise AIUnavailableError(f"La API de Anthropic devolvió un error: {exc}") from exc
    except anthropic.APIConnectionError as exc:
        raise AIUnavailableError(f"No se pudo contactar con la API de Anthropic: {exc}") from exc

    # Un informe pericial no puede firmarse con unas conclusiones cortadas a
    # mitad de frase, ni con una respuesta que el modelo ha declinado emitir.
    if message.stop_reason == "max_tokens":
        raise AIResponseError(
            "La respuesta de la IA se ha truncado por límite de tokens; el informe no se "
            "genera para no firmar unas conclusiones incompletas."
        )
    if message.stop_reason == "refusal":
        raise AIResponseError("La IA ha declinado redactar el informe para este caso.")

    payload = _parsear_respuesta(message)
    _validar_citas(payload["hallazgos"], len(timeline_events))

    return Narrativa(
        hallazgos=payload["hallazgos"].strip(),
        conclusiones=payload["conclusiones"].strip(),
        prompt=_transcripcion(prompt_usuario),
    )


def _parsear_respuesta(message) -> dict:
    texto = "".join(block.text for block in message.content if block.type == "text")
    try:
        payload = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise AIResponseError("La respuesta de la IA no es un JSON válido.") from exc

    if not payload.get("hallazgos") or not payload.get("conclusiones"):
        raise AIResponseError("La respuesta de la IA no incluye hallazgos y conclusiones.")
    return payload
