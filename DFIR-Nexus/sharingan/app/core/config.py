from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DFIR Nexus - Informes"
    database_url: str = "mysql+pymysql://usuario:contraseña@localhost:3306/nexus_informes"
    anthropic_api_key: str = ""
    reports_storage_dir: str = "./storage/reports"
    #: Orígenes permitidos por CORS, separados por comas. Por defecto,
    #: el único origen desde el que corre el frontend en desarrollo (Fase
    #: final, hardening — antes era "*"); se puede sobreescribir por
    #: CORS_ORIGINS si hiciera falta. En producción no protege nada
    #: adicional ni hace falta tocarlo: el navegador solo habla con el
    #: origen del gateway (ver deploy/gateway/nginx.conf), nunca
    #: directamente con este backend. Los endpoints sí exigen JWT desde
    #: la Fase 4 (ver app/modules/auth/) — CORS nunca fue la única
    #: defensa, solo la primera capa frente al navegador.
    cors_origins: str = "http://localhost:5173"

    # Identidad (Fase 4): mismo JWT_SECRET que emite el backend de Casos —
    # este backend solo lo usa para VERIFICAR los JWT que le llegan, nunca
    # emite ninguno.
    jwt_secret: str = "change_me"

    # --- Asistente conversacional (app/modules/chat) ---------------------
    #: Quién responde en el chat: «anthropic» (por defecto) u «ollama»
    #: (modelo local). Ver app/modules/chat/llm.py.
    #:
    #: El defecto fue «ollama» mientras se construía el módulo, con el
    #: argumento de que el expediente de una investigación real no debe salir
    #: de la máquina sin una decisión explícita. El argumento sigue siendo
    #: cierto, pero **la vía local no resultó utilizable**: sin GPU, una
    #: pregunta sobre un caso tarda del orden de cinco minutos (~3,5 tokens/s
    #: medidos), y un asistente al que hay que esperar cinco minutos no se
    #: usa. El equipo trabaja con la API de Anthropic, así que eso es lo que
    #: dice el defecto en vez de dejar que se descubra por un 502 contra un
    #: localhost:11434 que no existe.
    #:
    #: Lo que eso implica, dicho claro porque es una decisión de tratamiento
    #: de datos y no un detalle técnico: con este proveedor, el expediente que
    #: entra en el prompt —evidencias, usuarios, IPs, rutas— se envía a un
    #: tercero. La vía local se mantiene entera y probada
    #: (tests/test_narrativa_local.py) para quien tenga hardware o un caso que
    #: no pueda salir de la máquina: se cambia esta variable y nada más.
    chat_provider: str = "anthropic"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b-instruct"
    #: Ventana de contexto del modelo local. Si se queda corta, Ollama
    #: descarta el principio del prompt — que es donde van las reglas de
    #: citación y de alcance, justo lo que no puede perderse.
    ollama_num_ctx: int = 8192
    #: Cuántos tokens como máximo genera el modelo. Es el parámetro que más
    #: manda en el peor caso del tiempo de respuesta: medido en esta máquina,
    #: la generación va a 3,5 tokens/s, así que 800 tokens son 230 s solo de
    #: escribir. Con 500 el techo baja a ~145 s, y sigue sobrando: la
    #: respuesta real a una pregunta sobre un caso ocupó 210 tokens.
    ollama_num_predict: int = 500
    #: Un modelo local sin GPU tarda minutos por respuesta larga; el timeout
    #: por defecto de HTTP se queda muy corto.
    chat_timeout_seconds: int = 600
    #: Cuánto mantiene Ollama el modelo cargado en memoria tras responder.
    #: Con el valor por defecto (5 min) una pausa para leer la respuesta ya
    #: basta para que se descargue, y la siguiente pregunta paga otra vez la
    #: carga de 2,4 GB. Media hora cubre una sesión de trabajo entera.
    ollama_keep_alive: str = "30m"
    #: Solo se usa con chat_provider=anthropic.
    anthropic_chat_model: str = "claude-opus-5"
    #: De dónde lee el asistente el expediente: «mcp» (por defecto), a través
    #: del servidor MCP de Nexus y con el JWT de quien pregunta, o «sql»,
    #: directamente de la base como antes. En los dos casos el modelo no tiene
    #: herramientas y el `case_id` lo fija el código. Ver chat/fuente_mcp.py.
    chat_contexto: str = "mcp"
    #: Carpeta del servidor MCP (`mcp-server/` en la raíz del repo), relativa
    #: al directorio desde el que se lanza este backend.
    chat_mcp_dir: str = "../mcp-server"
    #: Intérprete con el que se lanza el MCP. Vacío: el mismo que corre este
    #: backend, que entonces necesita también las dependencias del MCP.
    chat_mcp_python: str = ""
    #: Quién redacta los hallazgos y las conclusiones del **informe pericial**:
    #: «anthropic» (por defecto) u «ollama» (modelo local).
    #:
    #: Se decide aparte del chat a propósito. El chat es apoyo al perito y una
    #: respuesta floja se descarta releyéndola; el informe se firma y se
    #: entrega, así que cambiar quién lo redacta es una decisión de más peso y
    #: no debe heredarse de haber configurado el chat. Sea cual sea, el
    #: apartado 8 del informe declara el modelo concreto que lo redactó.
    narrativa_provider: str = "anthropic"
    #: Tope de generación de la narrativa con modelo local. Son dos apartados
    #: enteros, más largos que una respuesta de chat: con el tope del chat
    #: saldrían cortados, y un informe no se firma a medias.
    #:
    #: Medido en una máquina sin GPU (~5 tokens/s): con 2500 se pasaba de los
    #: 600 s de timeout y no salía informe; con 1200 la narrativa se truncaba
    #: a mitad y se rechazaba. 1800 cabe en el timeout y deja margen — pero lo
    #: que de verdad acota la longitud es `maxItems` en el esquema de salida
    #: (ver `_OUTPUT_SCHEMA_LOCAL`), no este número. Con GPU se puede subir.
    ollama_narrativa_num_predict: int = 1800

    @property
    def cors_origins_list(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


settings = Settings()
