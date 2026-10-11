from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del MCP Server. Mismo patrón que los 5 backends de
    Nexus (pydantic-settings, `.env` en la raíz del propio módulo — ver
    p. ej. backend/app/core/config.py)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Backends que este MCP Server consume. El JWT lo emite únicamente
    # Casos (ver auth.py) — los 5 backends comparten el mismo JWT_SECRET
    # (confirmado en la auditoría de arquitectura MCP), así que ese mismo
    # token sirve para hablar con Timeline e Informes sin volver a
    # autenticarse por separado en cada uno.
    CASOS_BASE_URL: str = "http://localhost:8000"
    TIMELINE_BASE_URL: str = "http://localhost:8002"
    INFORMES_BASE_URL: str = "http://localhost:8003"
    TRACKING_BASE_URL: str = "http://localhost:8001"
    OSINT_BASE_URL: str = "http://localhost:8124"

    # Usuario de servicio contra el que este proceso se autentica una vez
    # al arrancar (ver app/core/auth.py). NO es la cuenta de un analista
    # humano — ver .env.example.
    MCP_SERVICE_EMAIL: str = "change_me"
    MCP_SERVICE_PASSWORD: str = "change_me"

    # Alternativa al usuario de servicio: un JWT ya emitido por Casos. Si
    # viene relleno, el proceso NO inicia sesión nunca y actúa con la
    # identidad de ese token. Es como lanza este servidor el asistente de
    # Informes (sharingan/app/modules/chat/fuente_mcp.py): un proceso por
    # pregunta, con el token del analista que la hace, de modo que el
    # asistente no puede leer nada que ese analista no pueda leer. Si el
    # token caduca, el 401 sube tal cual: no hay credenciales con las que
    # renovarlo, y no debe haberlas.
    MCP_ACCESS_TOKEN: str = ""

    # Fase 2I: directorios locales desde los que `analizar_log` puede leer
    # un fichero, separados por coma (rutas absolutas). VACÍO por defecto
    # a propósito: sin configurar explícitamente al menos uno, la tool
    # rechaza cualquier ruta — ver app/main.py::_validar_ruta_permitida y
    # el README. Nunca se acepta una ruta fuera de esta lista, ni siquiera
    # implícitamente vía symlink (se resuelve con Path.resolve() antes de
    # comprobarla).
    MCP_ALLOWED_FILE_DIRS: str = ""


settings = Settings()
