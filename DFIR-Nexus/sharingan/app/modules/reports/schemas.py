from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.reports.opciones import (
    TODOS_LOS_ANEXOS,
    TODOS_LOS_FORMATOS,
    Anexo,
    FormatoInforme,
    OpcionesInforme,
)
from app.modules.shared.models import Severidad


class OpcionesInformeIn(BaseModel):
    """
    Alcance de esta emisión, tal y como entra por la API.

    Todo es opcional y omitirlo entero equivale a lo de siempre: el caso
    completo, los tres anexos y los cuatro formatos. Se separa de
    `OpcionesInforme` (opciones.py) porque aquí se valida lo que llega de
    fuera —listas, cadenas, fechas sueltas— y allí vive la regla pericial.
    La conversión se hace en el validador para que un alcance imposible
    (ningún anexo, sin PDF, franja invertida) se rechace con 422 al validar
    el cuerpo, y no a mitad de generar el informe.
    """

    anexos: Optional[List[Anexo]] = Field(
        None,
        description=(
            "Anexos que se incluyen: «evidences» (A), «osint» (B), «tracking» (C). "
            "Al excluir uno se excluyen también las entradas de la cronología que se "
            "apoyaban en él, para que la columna «Ref.» siga resolviendo. Por defecto, "
            "los tres."
        ),
    )
    formatos: Optional[List[FormatoInforme]] = Field(
        None,
        description=(
            "Soportes en los que se emite. El PDF no se puede excluir: es el documento "
            "que se firma. Por defecto, los cuatro."
        ),
    )
    desde: Optional[datetime] = Field(
        None, description="Documenta solo los hechos posteriores a esta marca (UTC)."
    )
    hasta: Optional[datetime] = Field(
        None, description="Documenta solo los hechos anteriores a esta marca (UTC)."
    )
    severidad_minima: Optional[Severidad] = Field(
        None,
        description=(
            "Descarta los eventos de tracking por debajo de esta severidad, y las "
            "entradas de la cronología que procedan de ellos."
        ),
    )
    solo_osint_con_detecciones: bool = Field(
        False,
        description=(
            "Descarta los indicadores OSINT sin detecciones registradas, y las entradas "
            "de la cronología que procedan de ellos."
        ),
    )

    @model_validator(mode="after")
    def _validar_alcance(self) -> "OpcionesInformeIn":
        self.a_dominio()  # Lanza ValueError, que FastAPI traduce a 422.
        return self

    def a_dominio(self) -> OpcionesInforme:
        return OpcionesInforme(
            anexos=frozenset(self.anexos) if self.anexos is not None else TODOS_LOS_ANEXOS,
            formatos=(
                frozenset(self.formatos)
                if self.formatos is not None
                else TODOS_LOS_FORMATOS
            ),
            desde=self.desde,
            hasta=self.hasta,
            severidad_minima=self.severidad_minima,
            solo_osint_con_detecciones=self.solo_osint_con_detecciones,
        )


class ReportGenerateRequest(BaseModel):
    case_id: int
    generado_por: str = Field(..., max_length=100)
    notas: Optional[str] = Field(
        None,
        description="Notas adicionales del perito para orientar la redacción de las conclusiones (opcional).",
    )
    opciones: Optional[OpcionesInformeIn] = Field(
        None,
        description=(
            "Alcance de esta emisión. Omitirlo emite el informe completo, que es lo que "
            "hacía este endpoint antes de existir este campo."
        ),
    )


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    fecha_generacion: datetime
    resumen_ia: str
    archivo_pdf: str
    generado_por: str
    version: int
    notas: Optional[str] = None
    huellas: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Huella SHA-256 de cada fichero emitido: las cuatro copias del informe, por "
            "formato, y la transcripción del prompt bajo la clave «prompt». Permite "
            "comprobar que un fichero recibido es el que este informe declara. Vacío en "
            "informes emitidos antes de que se registrasen."
        ),
    )
    opciones: Optional[dict] = Field(
        None,
        description=(
            "Alcance con el que se emitió este informe. Es lo que explica que dos "
            "informes del mismo caso digan cosas distintas sin que hayan cambiado los "
            "datos. Vacío en informes emitidos antes de que se pudiera elegir, que "
            "documentaban el caso entero."
        ),
    )
