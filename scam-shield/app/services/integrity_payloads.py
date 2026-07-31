"""
Construye el payload de evidencia para cada tipo de caso, en un ÚNICO
sitio compartido entre dos momentos distintos:

1. Al capturar la evidencia (justo después de guardar el caso en cada
   ruta) — se hashea este payload y se añade a la cadena.
2. Al verificar la cadena (integrity_service.verify_chain) — se vuelve a
   construir el payload a partir del caso tal y como está AHORA MISMO en
   la base de datos, se hashea otra vez, y se compara con el hash
   guardado en el eslabón.

Si estas dos construcciones no usaran exactamente la misma función,
cualquier mínima diferencia accidental (un campo en distinto orden, un
campo de más o de menos) haría saltar falsos positivos de "manipulación"
que no existen. Por eso viven aquí juntas, no repetidas en cada ruta.

Importante: los campos que se incluyen aquí son siempre los que
QUEDAN GUARDADOS en el propio caso (headers, flags, score...). Los hashes
de contenido original que NO se conservan (el email o la imagen en sí)
se guardan aparte como dato informativo (`raw_email_sha256`,
`raw_file_sha256`) pero NUNCA entran en este payload — si entraran, la
verificación fallaría siempre para esos casos, no por manipulación real,
sino porque no hay forma de reconstruir algo que nunca se guardó.

Otro caso parecido, mismo síntoma: cuando se añade una columna NUEVA a un
caso que ya existía (p.ej. `resolved_ip`/`abuseipdb` en `Case`,
`fraud_score`/`carrier_intelligence` en `PhoneCase`), los casos antiguos
ya sellados ANTES de que ese campo existiera tienen ese valor a `None` —
si el payload incluyera la clave siempre, el payload recalculado hoy
tendría una clave de más frente al que se selló en su día, y
`verify_chain` marcaría el caso como "manipulado" sin haberlo sido. Por
eso estos campos añadidos a posteriori se omiten del payload cuando valen
`None` (`_omit_none`) — un caso antiguo sin el campo genera exactamente
el mismo payload que se selló entonces, y un caso nuevo con el campo sí
lo sella.
"""
from app.models.case import Case
from app.models.cnmv_check_case import CnmvCheckCase
from app.models.email_case import EmailCase
from app.models.facial_search_case import FacialSearchCase
from app.models.image_case import ImageCase
from app.models.ip_case import IpCase
from app.models.phone_case import PhoneCase
from app.models.reverse_image_search_case import ReverseImageSearchCase
from app.models.typosquatting_case import TyposquattingCase
from app.models.wallet_case import WalletCase


def _omit_none(**fields) -> dict:
    """Solo para campos añadidos a un caso ya existente — ver nota en el docstring del módulo."""
    return {k: v for k, v in fields.items() if v is not None}


def domain_payload(case: Case) -> dict:
    return {
        "domain": case.domain, "whois": case.whois, "ssl": case.ssl, "virustotal": case.virustotal,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
        **_omit_none(
            resolved_ip=case.resolved_ip, abuseipdb=case.abuseipdb,
            dns=case.dns, ip_reputations=case.ip_reputations, crtsh=case.crtsh, wayback=case.wayback,
        ),
    }


def email_payload(case: EmailCase) -> dict:
    return {
        "from_address": case.from_address, "subject": case.subject, "headers": case.headers,
        "sender_domain_whois": case.sender_domain_whois,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
        **_omit_none(
            links=case.links, attachments=case.attachments,
            is_raw_source=case.is_raw_source, ai_explanation=case.ai_explanation,
            originating_ip_abuseipdb=case.originating_ip_abuseipdb,
        ),
    }


def wallet_payload(case: WalletCase) -> dict:
    return {
        "chain": case.chain, "address": case.address, "wallet": case.wallet,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
    }


def typosquatting_payload(case: TyposquattingCase) -> dict:
    return {
        "domain": case.domain, "candidates": case.candidates,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
    }


def phone_payload(case: PhoneCase) -> dict:
    return {
        "raw_phone": case.raw_phone, "phone": case.phone, "community_reports": case.community_reports,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
        **_omit_none(fraud_score=case.fraud_score, carrier_intelligence=case.carrier_intelligence),
    }


def cnmv_payload(case: CnmvCheckCase) -> dict:
    return {
        "query": case.query, "matches": case.matches,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
        **_omit_none(fca_matches=case.fca_matches, registry_matches=case.registry_matches),
    }


def image_payload(case: ImageCase) -> dict:
    return {
        "filename": case.filename, "perceptual_hash": case.perceptual_hash, "exif": case.exif,
        "matches": case.matches,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
    }


def reverse_image_search_payload(case: ReverseImageSearchCase) -> dict:
    return {
        "image_case_id": case.image_case_id, "source_sha256": case.source_sha256,
        "matches": case.matches,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
    }


def facial_search_payload(case: FacialSearchCase) -> dict:
    return {
        "image_case_id": case.image_case_id, "source_sha256": case.source_sha256,
        # confirmación y notas selladas junto al resto — no editables después sin romper la cadena
        "confirmed_legal_basis": case.confirmed_legal_basis, "notes": case.notes,
        "matches": case.matches,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "requested_at": case.requested_at,
    }


def ip_payload(case: IpCase) -> dict:
    return {
        "ip": case.ip, "abuseipdb": case.abuseipdb,
        "risk_flags": case.risk_flags, "risk_score": case.risk_score, "analyzed_at": case.analyzed_at,
    }


# case_type -> (modelo SQLAlchemy, función que construye el payload a partir de una instancia)
REGISTRY: dict[str, tuple[type, callable]] = {
    "domain": (Case, domain_payload),
    "email": (EmailCase, email_payload),
    "wallet": (WalletCase, wallet_payload),
    "typosquatting": (TyposquattingCase, typosquatting_payload),
    "phone": (PhoneCase, phone_payload),
    "cnmv": (CnmvCheckCase, cnmv_payload),
    "image": (ImageCase, image_payload),
    "image_reverse_search": (ReverseImageSearchCase, reverse_image_search_payload),
    "image_facial_search": (FacialSearchCase, facial_search_payload),
    "ip": (IpCase, ip_payload),
}
