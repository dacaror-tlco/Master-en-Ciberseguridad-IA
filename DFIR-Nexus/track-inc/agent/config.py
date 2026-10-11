"""
Configuración del agente. Todo lo que hoy son parámetros sueltos
(watch_paths, agent_id, intervalos de polling, URL del servidor...) vive
aquí, cargado y validado desde un único fichero YAML.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class SyncConfig(BaseModel):
    server_url: str | None = None  # None -> no hay servidor central aún; se usa mock
    api_key: str | None = None
    interval_seconds: float = 5.0
    batch_size: int = 50
    max_retries: int = 5


class CollectorsConfig(BaseModel):
    filesystem_enabled: bool = True
    watch_paths: list[str] = Field(default_factory=lambda: ["/tmp"])

    process_enabled: bool = True
    process_poll_interval: float = 1.0

    network_enabled: bool = True
    network_poll_interval: float = 2.0
    ip_blacklist: list[str] = Field(default_factory=list)


class AgentConfig(BaseModel):
    agent_id: str
    db_path: str = "evidence.db"
    rules_path: str = "agent/classifier/rules.yaml"
    collectors: CollectorsConfig = Field(default_factory=CollectorsConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)

    @field_validator("agent_id")
    @classmethod
    def agent_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("agent_id no puede estar vacío")
        return v

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AgentConfig":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el fichero de configuración: {path}")
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate(raw)
