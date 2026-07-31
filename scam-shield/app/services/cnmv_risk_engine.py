"""
Motor de scoring de riesgo para verificaciones CNMV.

La señal CNMV es simple a propósito: aparecer en el listado oficial de
advertencias de un regulador es una de las más fuertes que existen — no
es una heurística nuestra, es un organismo público diciendo explícitamente
"esta entidad no está autorizada". Por eso el score es alto directamente
con un solo match, a diferencia de otros módulos donde varias señales
débiles se van sumando.

La señal de FCA (Reino Unido) tiene dos niveles, confirmados probando
contra la API real (no contra lo que documentaba la librería de
referencia):

1. **`Unauthorised firm`** (alta): la propia búsqueda de la FCA ya
   incluye, mezcladas con el registro normal, entradas marcadas
   explícitamente como firma no autorizada/clon — con nombres tan
   directos como "Barclays Capital (clone of FCA authorised firm)". Esto
   es, en la práctica, el mismo tipo de señal que `CNMV_UNAUTHORIZED_ENTITY`:
   un regulador diciendo explícitamente "esto es una suplantación".
2. **Estado registrado mas no activo** (media): la entidad aparece en el
   registro pero con un estado que no es de autorización activa
   (caducada, retirada...) — más ambiguo que el caso anterior (podría ser
   simplemente una firma que dejó el negocio), así que severidad menor.
   **Importante — solo se dispara si NINGUNA coincidencia está activa**:
   un grupo grande con décadas de historial en el Reino Unido (fusiones,
   marcas absorbidas...) acumula de forma totalmente normal muchas
   entidades "No longer authorised" antiguas — probado con datos reales
   buscando "Santander": aparecen entidades activas (Santander UK Plc,
   Banco Santander S.A....) MEZCLADAS con antiguas absorbidas (Abbey
   Stockbrokers, Alliance & Leicester...). Si hay aunque sea una
   coincidencia con autorización activa, esa mezcla es historial
   corporativo normal, no indicio de nada — la señal solo tiene sentido
   cuando TODO lo encontrado está caducado/retirado.

Aparecer con un estado de autorización ACTIVA (`Authorised`,
`Registered`...) no dispara nada — es justo lo esperable de una firma
legítima. Y si la búsqueda encuentra TANTO una entidad activa legítima
COMO un clon (`Unauthorised firm`) — como pasa buscando "Santander", que
tiene un clon real ("santanderbank-finances.com") — la descripción de
`FCA_UNAUTHORISED_FIRM` lo deja explícito: el clon es una entidad
DISTINTA, no significa que la entidad buscada deje de ser legítima.

El registro de entidades autorizadas de la propia CNMV (comprobación en
positivo, `cnmv_registry_service.py`) es distinto de los dos anteriores
por lo que significa la AUSENCIA de resultado: aquí no hay un regulador
diciendo explícitamente "esto es fraude" (como CNMV_UNAUTHORIZED_ENTITY o
FCA_UNAUTHORISED_FIRM), solo la ausencia de una entidad con ese nombre en
el registro — un indicio razonable pero no una prueba (una entidad
extranjera legítima que opera por pasaporte comunitario sin registro
local en España tampoco aparecería). Por eso la severidad es media, y
además — a diferencia de las demás señales — solo se dispara si la
comprobación se ejecutó con éxito (`registry_matches is not None`): si
falló (red, cambio de HTML de la CNMV), no hay base para decir "no
encontrado", así que no se dispara nada.
"""
from app.schemas.cnmv import CnmvMatch, CnmvRegisteredEntity, FcaMatch
from app.schemas.domain_analysis import RiskFlag

_FCA_ACTIVE_STATUSES = {"authorised", "registered", "eea authorised", "eea registered", "psd authorised"}
_FCA_UNAUTHORISED_TYPE = "unauthorised firm"


def evaluate_cnmv_risk(
    matches: list[CnmvMatch],
    fca_matches: list[FcaMatch] | None = None,
    registry_matches: list[CnmvRegisteredEntity] | None = None,
) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    if matches:
        flags.append(RiskFlag(
            code="CNMV_UNAUTHORIZED_ENTITY",
            severity="high",
            description=(
                f"La CNMV ha publicado {len(matches)} advertencia(s) pública(s) que coinciden con esta "
                "búsqueda: la(s) entidad(es) no está(n) autorizada(s) para prestar servicios de inversión "
                "en España (\"chiringuito financiero\")"
            ),
        ))
        score += 90

    fca_matches = fca_matches or []
    active = [m for m in fca_matches if m.status.lower() in _FCA_ACTIVE_STATUSES]
    unauthorised = [m for m in fca_matches if (m.type_of_business or "").lower() == _FCA_UNAUTHORISED_TYPE]
    lapsed = [
        m for m in fca_matches
        if m not in unauthorised and m.status.lower() not in _FCA_ACTIVE_STATUSES
    ]

    if unauthorised:
        names = "; ".join(m.name for m in unauthorised[:3])
        # Si también hay una coincidencia activa, dejarlo explícito: el clon es una
        # entidad DISTINTA, no significa que la entidad buscada deje de ser legítima.
        aclaracion = (
            " — esto NO es sobre la entidad buscada (que también aparece con autorización activa más "
            "abajo), es una entidad distinta que usa un nombre parecido para hacerse pasar por ella"
        ) if active else ""
        flags.append(RiskFlag(
            code="FCA_UNAUTHORISED_FIRM",
            severity="high",
            description=(
                f"La FCA (Reino Unido) tiene registrada(s) explícitamente como firma no autorizada/clon "
                f"a: {names} — coincide con esta búsqueda, indicio directo de suplantación de identidad"
                f"{aclaracion}"
            ),
        ))
        score += 60

    if lapsed and not active:
        statuses = ", ".join(sorted({m.status for m in lapsed}))
        flags.append(RiskFlag(
            code="FCA_NOT_CURRENTLY_AUTHORISED",
            severity="medium",
            description=(
                f"Aparece en el registro de la FCA (Reino Unido) pero con un estado que no es de "
                f"autorización activa ({statuses}), y ninguna coincidencia tiene autorización activa — "
                "indicio de autorización caducada/retirada, o de una entidad que se hace pasar por una "
                "firma que sí estuvo autorizada"
            ),
        ))
        score += 30

    if registry_matches is not None and not registry_matches:
        flags.append(RiskFlag(
            code="CNMV_NOT_IN_AUTHORIZED_REGISTRY",
            severity="medium",
            description=(
                "No se ha encontrado ninguna entidad con este nombre en el registro de la CNMV de "
                "Empresas de Servicios de Inversión autorizadas — indicio de que no está autorizada a "
                "operar en España, aunque también podría tratarse de una entidad extranjera sin registro "
                "local o de un nombre que no corresponde a una entidad financiera"
            ),
        ))
        score += 25

    return flags, min(score, 100)
