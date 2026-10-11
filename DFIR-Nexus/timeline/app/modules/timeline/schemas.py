from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    fecha_hora: datetime
    descripcion: str
    origen_modulo: str
    origen_id: int
    orden: int
