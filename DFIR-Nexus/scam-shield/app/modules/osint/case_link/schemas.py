from pydantic import BaseModel


class VinculacionUpdateRequest(BaseModel):
    """`case_id=None` desvincula. Cualquier otro valor vincula/cambia."""

    case_id: int | None = None


class VinculacionUpdateResponse(BaseModel):
    case_type: str
    id: int
    case_id: int | None

    #: False si case_id ya era el mismo (no-op): no se ha tocado nada, ni
    #: siquiera se ha intentado avisar a la auditoría.
    cambiado: bool

    #: None si cambiado=False (no aplica). Si cambiado=True: si la llamada
    #: a case_audit_log (Casos) tuvo éxito. El cambio de vinculación en SÍ
    #: ya está persistido en OSINT independientemente de este valor — ver
    #: case_link/audit_client.py.
    auditoria_registrada: bool | None = None
    auditoria_error: str | None = None
