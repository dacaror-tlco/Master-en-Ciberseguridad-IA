"""
Schema para la generación del informe combinado.

El usuario elige qué casos de cada módulo (dominio, email, wallet) quiere
incluir en un único PDF — normalmente porque están todos relacionados con
la misma estafa (ej: el dominio del sitio falso + el email que lo
promocionaba + la wallet a la que pedían transferir el dinero).
"""
from typing import Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    domain_case_ids: list[int] = Field(default_factory=list)
    email_case_ids: list[int] = Field(default_factory=list)
    wallet_case_ids: list[int] = Field(default_factory=list)
    typosquatting_case_ids: list[int] = Field(default_factory=list)
    phone_case_ids: list[int] = Field(default_factory=list)
    cnmv_check_case_ids: list[int] = Field(default_factory=list)
    image_case_ids: list[int] = Field(default_factory=list)
    ip_case_ids: list[int] = Field(default_factory=list)
    victim_notes: Optional[str] = Field(
        None,
        description="Espacio libre para que la víctima describa qué pasó, en sus propias palabras (se incluye tal cual en el informe).",
    )
    ai_narrative: Optional[str] = Field(
        None,
        description="Narrativa generada por /analysis/consolidated (opcional). Si se incluye, se añade como sección en la portada del informe.",
    )
