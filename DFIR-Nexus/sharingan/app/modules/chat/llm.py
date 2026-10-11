"""
De quién sale la respuesta del asistente.

Dos proveedores, y el que manda es la API:

* **`anthropic`** (por defecto) — el mismo cliente que ya usa la generación de
  informes. Es lo que usa el equipo y lo que corre en el despliegue.
* **`ollama`** — modelo ejecutándose en la propia máquina, sin API de pago y
  sin que el expediente salga del equipo.

El defecto fue el local mientras se construía el módulo, y el argumento para
ello sigue en pie: el contexto que se le pasa al modelo lleva evidencias,
rutas, usuarios y direcciones IP de una investigación real, así que mandarlo a
un tercero es una decisión de tratamiento de datos, no un ajuste. Lo que
cambió es el otro lado de la balanza: medido en el portátil del equipo, la
vía local responde a ~3,5 tokens/s, o sea del orden de **cinco minutos por
pregunta sobre un caso**. Un asistente que tarda cinco minutos no se consulta,
y el módulo entero dejaba de tener sentido.

Así que el defecto es `anthropic`, con la consecuencia dicha en voz alta en la
configuración (ver `core/config.py::chat_provider`), y la vía local se
mantiene entera, probada y a una variable de distancia: es la salida para un
caso cuyo material no pueda salir de la máquina, o para quien tenga GPU.

Se habla con Ollama por HTTP con la biblioteca estándar, sin cliente propio:
son dos llamadas a un JSON local y añadir una dependencia para eso no se
sostiene.

Nota de rendimiento, porque condiciona el diseño más que ninguna otra cosa:
en una máquina sin GPU dedicada, un modelo de 3B responde en decenas de
segundos, no en dos. Por eso el asistente **no** es un bucle de agente que
encadena llamadas al modelo: el servidor reúne el contexto de una vez, de
forma determinista, y el modelo habla una sola vez. Ver `context.py`.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass

from app.core.config import settings


class LLMConfigError(RuntimeError):
    """El proveedor no está utilizable por configuración (modelo ausente, sin API key…)."""


class LLMUnavailableError(RuntimeError):
    """El proveedor no ha podido atender la petición (no arrancado, red, timeout)."""


class LLMResponseError(RuntimeError):
    """La respuesta no es utilizable (vacía o truncada)."""


@dataclass(frozen=True)
class Salida:
    texto: str
    modelo: str
    #: `True` si el modelo se quedó sin presupuesto de tokens a mitad de frase.
    truncada: bool = False


def _ollama(
    sistema: str,
    mensajes: list[dict],
    esquema: dict | None = None,
    num_predict: int | None = None,
) -> Salida:
    peticion_json: dict = {
        "model": settings.ollama_model,
        "messages": [{"role": "system", "content": sistema}, *mensajes],
        "stream": False,
        # Ver `ollama_keep_alive`: con el valor por defecto de Ollama (5 min),
        # el rato que se tarda en leer una respuesta basta para que descargue
        # el modelo, y la pregunta siguiente vuelve a pagar la carga.
        "keep_alive": settings.ollama_keep_alive,
    }
    if esquema is not None:
        # Ollama acepta un JSON Schema en `format` y restringe la generación a
        # él. No es un ruego en el prompt: el propio muestreo queda acotado, y
        # por eso funciona con modelos pequeños que ignorarían un «responde en
        # JSON» escrito en el sistema.
        peticion_json["format"] = esquema

    cuerpo = json.dumps(
        {
            **peticion_json,
            "options": {
                # Ventana de contexto: el expediente de un caso con cronología
                # ocupa varios miles de tokens y con la ventana por defecto se
                # truncaría por delante — es decir, se perderían justo las
                # instrucciones del prompt de sistema, que es lo que sostiene
                # las reglas de citación y de alcance.
                "num_ctx": settings.ollama_num_ctx,
                # Tope de generación: ver `ollama_num_predict` en config.py.
                # Sin él, una pregunta abierta sobre un caso se va de varios
                # minutos en una máquina sin GPU. El informe pericial pide su
                # propio tope, más alto, porque son dos apartados enteros.
                "num_predict": num_predict or settings.ollama_num_predict,
                # Temperatura baja, no cero: se busca que se ciña a los datos.
                "temperature": 0.2,
            },
        }
    ).encode("utf-8")

    peticion = urllib.request.Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/chat",
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(peticion, timeout=settings.chat_timeout_seconds) as resp:
            datos = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")[:500]
        if exc.code == 404:
            raise LLMConfigError(
                f"Ollama no tiene el modelo «{settings.ollama_model}». "
                f"Descárgalo con: ollama pull {settings.ollama_model}"
            ) from exc
        raise LLMUnavailableError(f"Ollama devolvió {exc.code}: {detalle}") from exc
    except urllib.error.URLError as exc:
        raise LLMUnavailableError(
            f"No se pudo contactar con Ollama en {settings.ollama_base_url}. "
            f"¿Está arrancado? ({exc.reason})"
        ) from exc
    except TimeoutError as exc:
        raise LLMUnavailableError(
            f"Ollama no respondió en {settings.chat_timeout_seconds} s. En una máquina "
            "sin GPU esto es normal con preguntas largas: prueba con una más acotada "
            "o sube CHAT_TIMEOUT_SECONDS."
        ) from exc

    texto = (datos.get("message") or {}).get("content", "").strip()
    if not texto:
        raise LLMResponseError("El modelo local no ha devuelto ninguna respuesta.")

    # Una respuesta cortada por el tope de generación se sirve igualmente, con
    # el corte declarado. Descartarla sería peor: son minutos de cómputo y lo
    # que llegó suele responder a la pregunta — lo único inaceptable es que el
    # perito no sepa que está leyendo un texto incompleto.
    truncada = datos.get("done_reason") == "length"

    return Salida(texto=texto, modelo=f"ollama/{settings.ollama_model}", truncada=truncada)


def _anthropic(sistema: str, mensajes: list[dict], esquema: dict | None = None) -> Salida:
    # Import local, no arriba: así el módulo sigue cargando con
    # CHAT_PROVIDER=ollama aunque el paquete `anthropic` no esté instalado
    # (una instalación pensada para no depender de ninguna API de pago).
    import anthropic
    from anthropic import Anthropic

    if not settings.anthropic_api_key:
        raise LLMConfigError(
            "CHAT_PROVIDER=anthropic pero ANTHROPIC_API_KEY no está configurada."
        )

    salida_config: dict = {"effort": "low"}
    if esquema is not None:
        salida_config["format"] = {"type": "json_schema", "schema": esquema}

    client = Anthropic(api_key=settings.anthropic_api_key)
    try:
        message = client.messages.create(
            model=settings.anthropic_chat_model,
            max_tokens=4000,
            system=sistema,
            output_config=salida_config,
            messages=mensajes,
        )
    except anthropic.APIStatusError as exc:
        raise LLMUnavailableError(f"La API de Anthropic devolvió un error: {exc}") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMUnavailableError(f"No se pudo contactar con Anthropic: {exc}") from exc

    _comprobar_rechazo(message)

    texto = _texto_de(message)
    if not texto:
        raise LLMResponseError("El modelo no ha devuelto ninguna respuesta.")

    return Salida(
        texto=texto,
        modelo=f"anthropic/{settings.anthropic_chat_model}",
        truncada=message.stop_reason == "max_tokens",
    )


def _texto_de(message) -> str:
    return "".join(b.text for b in message.content if getattr(b, "type", None) == "text").strip()


def _comprobar_rechazo(message) -> None:
    """
    Traduce un rechazo por políticas a un error con causa, en vez de dejarlo
    aparecer como «no ha devuelto ninguna respuesta».

    Merece código propio precisamente en esta aplicación: al asistente se le
    pregunta por intrusiones, malware, credenciales comprometidas y direcciones
    de atacantes. Es material que un clasificador de seguridad puede leer como
    una petición ofensiva, así que el rechazo no es un caso exótico aquí — y sin
    distinguirlo, un perito vería el mismo mensaje de error que ante un fallo de
    red y no sabría que basta reformular la pregunta.

    La respuesta llega con HTTP 200 y `stop_reason == "refusal"`, así que hay
    que comprobarlo antes de leer el contenido.
    """
    if getattr(message, "stop_reason", None) != "refusal":
        return
    detalles = getattr(message, "stop_details", None)
    categoria = getattr(detalles, "category", None)
    raise LLMResponseError(
        "El modelo ha declinado responder a esta pregunta"
        + (f" (categoría «{categoria}»)" if categoria else "")
        + ". No es un fallo del sistema: el contenido de la pregunta o del "
        "expediente ha activado un clasificador de seguridad. Reformular la "
        "pregunta en términos de análisis forense suele bastar."
    )


def _anthropic_stream(sistema: str, mensajes: list[dict]) -> Iterator[tuple[str, str | Salida]]:
    """
    La respuesta de Anthropic según se escribe. Ver `generar_en_trozos`.

    Se usa el gestor de contexto `messages.stream()` del SDK y su
    `get_final_message()` en vez de reconstruir el mensaje sumando deltas a
    mano: es el propio SDK el que garantiza que lo que se acumula coincide con
    lo que acabó enviando el servidor, incluidos `stop_reason` y el uso.
    """
    import anthropic
    from anthropic import Anthropic

    if not settings.anthropic_api_key:
        raise LLMConfigError(
            "CHAT_PROVIDER=anthropic pero ANTHROPIC_API_KEY no está configurada."
        )

    client = Anthropic(api_key=settings.anthropic_api_key)
    try:
        with client.messages.stream(
            model=settings.anthropic_chat_model,
            max_tokens=4000,
            system=sistema,
            output_config={"effort": "low"},
            messages=mensajes,
        ) as flujo:
            for texto in flujo.text_stream:
                yield ("trozo", texto)
            message = flujo.get_final_message()
    except anthropic.APIStatusError as exc:
        raise LLMUnavailableError(f"La API de Anthropic devolvió un error: {exc}") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMUnavailableError(f"No se pudo contactar con Anthropic: {exc}") from exc

    _comprobar_rechazo(message)

    texto = _texto_de(message)
    if not texto:
        raise LLMResponseError("El modelo no ha devuelto ninguna respuesta.")

    yield (
        "salida",
        Salida(
            texto=texto,
            modelo=f"anthropic/{settings.anthropic_chat_model}",
            truncada=message.stop_reason == "max_tokens",
        ),
    )


def generar_en_trozos(
    sistema: str,
    mensajes: list[dict],
    num_predict: int | None = None,
    proveedor: str | None = None,
) -> Iterator[tuple[str, str | Salida]]:
    """
    La respuesta del modelo según se escribe, con **los dos proveedores**.

    Emite `("trozo", texto)` por cada fragmento y termina con
    `("salida", Salida)`, que trae el texto completo y los metadatos
    (`modelo`, `truncada`). Ese último elemento es el bueno: el llamador debe
    componer la respuesta con él y no con la suma de los trozos.

    La forma es la misma para Ollama y para Anthropic a propósito, para que
    `service.py` no tenga una rama por proveedor. Al principio solo streameaba
    Ollama —era donde urgía, con respuestas de minutos— y con Anthropic se
    devolvía la respuesta de una pieza; eso dejaba la pantalla en blanco los
    segundos que tarda la API, y además obligaba a `service.py` a rearmar el
    contexto del caso dos veces por pregunta (una para preparar el prompt y otra
    dentro de la llamada no incremental). Con los dos proveedores aquí, ni una
    cosa ni la otra.
    """
    elegido = (proveedor or settings.chat_provider).strip().lower()
    if elegido == "anthropic":
        yield from _anthropic_stream(sistema, mensajes)
        return
    if elegido != "ollama":
        raise LLMConfigError(
            f"Proveedor de IA «{elegido}» no válido. Usa «ollama» o «anthropic»."
        )
    yield from _ollama_stream(sistema, mensajes, num_predict=num_predict)


def _ollama_stream(
    sistema: str,
    mensajes: list[dict],
    num_predict: int | None = None,
) -> Iterator[tuple[str, str | Salida]]:
    """
    El modelo local, a trozos.

    El streaming no acelera nada —el modelo genera a los mismos tokens por
    segundo—, pero cambia por completo la espera: en una pregunta sobre un caso
    medida en 284 s, el primer texto aparece a los ~10 s en vez de dejar la
    pantalla en blanco cuatro minutos y medio. Es la diferencia entre «tarda» y
    «se ha colgado», y es lo único que se puede hacer sin GPU.
    """
    cuerpo = json.dumps(
        {
            "model": settings.ollama_model,
            "messages": [{"role": "system", "content": sistema}, *mensajes],
            "stream": True,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "num_ctx": settings.ollama_num_ctx,
                "num_predict": num_predict or settings.ollama_num_predict,
                "temperature": 0.2,
            },
        }
    ).encode("utf-8")

    peticion = urllib.request.Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/chat",
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        respuesta = urllib.request.urlopen(peticion, timeout=settings.chat_timeout_seconds)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise LLMConfigError(
                f"Ollama no tiene el modelo «{settings.ollama_model}». "
                f"Descárgalo con: ollama pull {settings.ollama_model}"
            ) from exc
        raise LLMUnavailableError(f"Ollama devolvió {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise LLMUnavailableError(
            f"No se pudo contactar con Ollama en {settings.ollama_base_url}. "
            f"¿Está arrancado? ({exc.reason})"
        ) from exc

    partes: list[str] = []
    #: Por qué paró de generar, según lo declara Ollama en su última línea.
    motivo = None

    with respuesta:
        for linea in respuesta:
            if not linea.strip():
                continue
            try:
                dato = json.loads(linea.decode("utf-8"))
            except json.JSONDecodeError:
                # Ollama emite un JSON por línea; una línea suelta ilegible no
                # justifica tirar una respuesta que lleva minutos generándose.
                continue
            trozo = (dato.get("message") or {}).get("content", "")
            if trozo:
                partes.append(trozo)
                yield ("trozo", trozo)
            if dato.get("done"):
                motivo = dato.get("done_reason")
                break

    texto = "".join(partes).strip()
    if not texto:
        raise LLMResponseError("El modelo local no ha devuelto ninguna respuesta.")

    # `done_reason` viene en la última línea del flujo, que es esta función la
    # que la ve. Antes esto se deducía en service.py contando trozos contra
    # `num_predict` —un trozo, un token— porque quien leía el flujo no
    # devolvía el motivo. Leerlo es lo correcto: el recuento de trozos falla en
    # cuanto un trozo trae más de un token, y una narrativa truncada que se
    # cuela como completa acaba en un informe firmado a medias.
    yield (
        "salida",
        Salida(
            texto=texto,
            modelo=f"ollama/{settings.ollama_model}",
            truncada=motivo == "length",
        ),
    )


def generar(
    sistema: str,
    mensajes: list[dict],
    esquema: dict | None = None,
    num_predict: int | None = None,
    proveedor: str | None = None,
) -> Salida:
    """
    Una única llamada al modelo. `mensajes` va en formato OpenAI/Ollama.

    `esquema` (un JSON Schema) obliga a que la salida sea un objeto con esa
    forma: lo usa la narrativa del informe, que necesita hallazgos y
    conclusiones por separado. `proveedor` permite que el informe y el chat
    usen modelos distintos — redactar un informe pericial y responder una
    pregunta no tienen por qué correr el mismo riesgo.
    """
    elegido = (proveedor or settings.chat_provider).strip().lower()
    if elegido == "ollama":
        return _ollama(sistema, mensajes, esquema=esquema, num_predict=num_predict)
    if elegido == "anthropic":
        return _anthropic(sistema, mensajes, esquema=esquema)
    raise LLMConfigError(
        f"Proveedor de IA «{elegido}» no válido. Usa «ollama» o «anthropic»."
    )
