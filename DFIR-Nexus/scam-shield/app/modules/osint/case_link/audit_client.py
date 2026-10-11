"""
Llamada HTTP a Casos para dejar constancia en `case_audit_log` de un
cambio de vinculación. Es la única excepción de todo el proyecto a
"ningún backend llama a otro backend" (ver docs/CONTRATOS.md): esa tabla
la posee y la escribe en exclusiva Casos, así que no hay otra vía
consistente con la arquitectura (nunca importar su código, nunca escribir
su tabla directamente) para que OSINT deje constancia ahí.

Auxiliar, igual que findings/service.py::record_finding: si esta llamada
falla, el cambio de vinculación en OSINT YA está persistido y no se
deshace por esto — pero, a diferencia de record_finding, el fallo no se
oculta: se registra en logs (aquí) y se devuelve al llamador (ver
case_link/routes.py), que lo expone en la respuesta HTTP en vez de
tragárselo en silencio.
"""
import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT_SEGUNDOS = 5


def registrar_cambio_en_auditoria(
    *,
    case_id: int,
    case_type: str,
    source_id: int,
    subject_value: str | None,
    case_anterior: int | None,
    case_nuevo: int | None,
    authorization_header: str | None = None,
) -> tuple[bool, str | None]:
    """
    Devuelve (ok, error). `error` es None si ok=True.

    Fase 4 — dos cabeceras, dos propósitos distintos (ver propuesta de
    identidad y acceso, mecanismo OSINT->Cases):

    - `X-Service-Token`: autentica esta llamada como procedente de este
      backend, no de un cliente cualquiera con un JWT de usuario válido.
      Obligatoria: sin ella, Casos rechaza la llamada entera.
    - `Authorization`: el MISMO JWT que llegó en la petición original del
      usuario que disparó este cambio (ver case_link/routes.py, que lo
      lee de la petición entrante y lo reenvía tal cual). Opcional: si
      falta o Casos no puede validarlo, sigue aceptando la llamada
      igualmente (por el X-Service-Token) y registra el `actor` como
      "osint" en vez de con el nombre real del usuario.
    """
    url = f"{settings.cases_api_base_url}/cases/{case_id}/auditoria/osint"
    payload = {
        "case_type": case_type,
        "source_id": source_id,
        "subject_value": subject_value,
        "case_anterior": case_anterior,
        "case_nuevo": case_nuevo,
    }
    headers = {"X-Service-Token": settings.osint_audit_service_token}
    if authorization_header:
        headers["Authorization"] = authorization_header
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT_SEGUNDOS)
        resp.raise_for_status()
        return True, None
    except Exception as exc:  # noqa: BLE001 - cualquier fallo de red/HTTP se reporta igual, sin tumbar la operación principal
        logger.exception(
            "No se pudo registrar en case_audit_log el cambio de vinculación de %s#%s (caso destino %s)",
            case_type,
            source_id,
            case_id,
        )
        return False, str(exc)
