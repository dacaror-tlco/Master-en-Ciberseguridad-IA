"""
Configuración central de la aplicación.
Usa variables de entorno (ver .env.example) para no hardcodear claves de API.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ScamShield"
    environment: str = "development"

    # APIs externas (fase 2 en adelante, dejamos ya el hueco preparado)
    virustotal_api_key: str = ""
    abuseipdb_api_key: str = ""
    etherscan_api_key: str = ""
    # TronGrid (red Tron/TRC20): a diferencia de Etherscan, funciona sin key
    # (con límites de rate más bajos); esta key es opcional, solo sube el límite.
    tron_api_key: str = ""
    anthropic_api_key: str = ""
    openspam_api_key: str = ""
    serpapi_api_key: str = ""
    pimeyes_api_key: str = ""
    ipqualityscore_api_key: str = ""

    # FCA Register (Reino Unido): comprobación en positivo (¿está realmente
    # registrada?) que complementa el listado de advertencias de la CNMV.
    # Requiere las dos variables (la API exige ambos headers a la vez).
    fca_api_email: str = ""
    fca_api_key: str = ""

    # Twilio Lookup: única integración de PAGO de la herramienta (sin tier
    # gratuito, ~0,005 $/consulta). Inactiva por defecto — solo se activa si
    # se configuran ambas variables. Ver README ("Carrier en tiempo real —
    # Twilio Lookup") para el aviso de coste, incluido su uso repetido desde
    # la monitorización continua.
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""

    # URL pública donde esté desplegada esta instancia (ej.
    # https://miapp.example.com, sin barra final). Solo hace falta para la
    # búsqueda inversa de imagen (SerpApi/Google): esos servicios exigen una
    # URL pública de la imagen, no aceptan subida directa de bytes, así que
    # sin esto la búsqueda inversa vía SerpApi no puede completarse (la
    # herramienta degrada con gracia a los enlaces manuales). En local sin
    # desplegar, se puede usar un túnel tipo ngrok para probarlo.
    public_base_url: str = ""

    # Base de datos (la conectamos en el siguiente paso, de momento no se usa)
    database_url: str = "sqlite:///./scamshield.db"

    # Monitorización continua: re-chequea periódicamente los sujetos ya
    # analizados (mismo pipeline que el análisis manual) y genera una
    # alerta si el riesgo sube. Corre dentro del propio proceso (sin
    # Celery/Redis todavía, ver "Próximos pasos" en el README).
    monitoring_enabled: bool = True
    monitoring_default_interval_hours: int = 24  # cada cuánto se re-chequea un sujeto nuevo por defecto
    monitoring_scheduler_interval_minutes: int = 60  # cada cuánto el scheduler mira qué sujetos ya tocan
    monitoring_score_change_threshold: int = 15  # subida de score (sin cambiar de nivel) que ya dispara alerta

    class Config:
        env_file = ".env"


settings = Settings()
