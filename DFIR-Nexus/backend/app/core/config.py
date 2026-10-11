from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "nexus_user"
    MYSQL_PASSWORD: str = "change_me"
    MYSQL_DB: str = "nexus"

    # Identidad (ver propuesta de identidad y acceso): compartido, vía
    # .env, con OSINT/Tracking/Timeline/Informes en la Fase 4 — mismo
    # patrón que MYSQL_PASSWORD, cada backend lee su propia copia.
    JWT_SECRET: str = "change_me"
    JWT_EXPIRE_MINUTES: int = 120

    # Fase 4: secreto de servicio para POST /cases/{id}/auditoria/osint,
    # distinto de JWT_SECRET — autentica esa llamada servidor->servidor
    # como procedente de verdad de OSINT (ver
    # app/modules/auth/dependencies.py::resolve_osint_actor). Compartido
    # únicamente con scam-shield/.env, nunca con el frontend.
    OSINT_AUDIT_SERVICE_TOKEN: str = "change_me"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )


settings = Settings()
