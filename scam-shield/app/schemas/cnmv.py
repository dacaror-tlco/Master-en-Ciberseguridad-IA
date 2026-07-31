from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.domain_analysis import RiskFlag


class CnmvCheckRequest(BaseModel):
    query: str = Field(
        ...,
        description="Nombre de la empresa, broker o dominio a comprobar contra la lista de advertencias de la CNMV",
        examples=["Aichaintrader"],
    )


class CnmvMatch(BaseModel):
    fecha: str
    companias: str
    observaciones: Optional[str] = None


class FcaMatch(BaseModel):
    """
    Resultado del registro público de la FCA (Reino Unido,
    https://register.fca.org.uk) — comprobación EN POSITIVO (¿está
    realmente registrada, y con qué estado?), no una lista negra. Útil
    para detectar "clone scams": brokers que se hacen pasar por una firma
    real autorizada en el Reino Unido, o que inventan un número de
    registro que no existe o ya no está activo.
    """
    name: str
    reference_number: str
    status: str
    # "Firm", "Unauthorised firm"... — este último es la señal fuerte de
    # verdad (clone scam), confirmado con datos reales de la API.
    type_of_business: Optional[str] = None
    url: Optional[str] = None


class CnmvRegisteredEntity(BaseModel):
    """
    Coincidencia en el registro de entidades autorizadas de la CNMV
    (Empresas de Servicios de Inversión) — comprobación EN POSITIVO,
    equivalente español de `FcaMatch`: ¿existe una entidad con ese nombre
    realmente autorizada a operar en España?
    """
    code: str
    name: str


class CnmvCheckResponse(BaseModel):
    query: str
    match_count: int
    matches: list[CnmvMatch] = []
    # Optional (no `= []`) a propósito en ambos campos siguientes: `None`
    # distingue un caso analizado ANTES de que existiera esta señal, o en
    # el que la comprobación falló esta vez, de un caso que sí se
    # comprobó correctamente y no encontró nada (lista vacía real).
    fca_matches: Optional[list[FcaMatch]] = None
    registry_matches: Optional[list[CnmvRegisteredEntity]] = None
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    analyzed_at: datetime


class CnmvCheckCaseResponse(CnmvCheckResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CnmvCheckCaseListItem(BaseModel):
    id: int
    query: str
    match_count: int
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True
