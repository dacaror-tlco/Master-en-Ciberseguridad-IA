"""
Motor de scoring de riesgo para imágenes.

Deliberadamente NO incluye reconocimiento facial ni identificación de
personas — eso es un dato personal y la línea que ya trazamos con el
módulo de teléfono (ver la discusión sobre "buscar el nombre del dueño
del número" en el README). Las señales de aquí son sobre la IMAGEN como
archivo, no sobre quién aparece en ella:

- Reutilización entre casos (la señal fuerte de verdad): si la misma foto
  ya apareció en otro caso analizado en la herramienta, es un indicio
  muy directo de que es una foto reciclada por un estafador — típico en
  estafas románticas donde se usa la misma foto de perfil robada contra
  varias víctimas.
- Ausencia de EXIF: señal MUY débil por sí sola (es lo normal en casi
  cualquier foto bajada de internet o reenviada por WhatsApp), se incluye
  solo como dato informativo de baja severidad, nunca como prueba.
- Software de edición conocido en el EXIF: tampoco es sospechoso por sí
  mismo (cualquiera edita fotos), señal baja.
"""
from app.schemas.domain_analysis import RiskFlag
from app.schemas.image_analysis import ExifInfo, FacialSearchMatch, ImageMatch, ReverseImageMatch

_EDITING_SOFTWARE_KEYWORDS = ("photoshop", "gimp", "snapseed", "facetune", "lightroom", "picsart")


def evaluate_image_risk(exif: ExifInfo, matches: list[ImageMatch]) -> tuple[list[RiskFlag], int]:
    flags: list[RiskFlag] = []
    score = 0

    if matches:
        case_ids = ", ".join(f"#{m.case_id}" for m in matches)
        flags.append(RiskFlag(
            code="IMAGE_REUSED_ACROSS_CASES", severity="high",
            description=(
                f"Esta imagen (o una muy parecida) ya se analizó antes en otro caso de esta herramienta "
                f"({case_ids}) — posible foto reciclada, un patrón típico de estafas románticas o perfiles falsos"
            ),
        ))
        score += min(60 + 10 * (len(matches) - 1), 90)

    if not exif.has_exif:
        flags.append(RiskFlag(
            code="IMAGE_NO_METADATA", severity="low",
            description=(
                "La imagen no tiene metadatos EXIF — es lo normal en fotos bajadas de redes sociales o "
                "reenviadas por WhatsApp, así que por sí solo no es una señal fuerte, pero se anota igualmente"
            ),
        ))
        score += 5
    elif exif.software and any(kw in exif.software.lower() for kw in _EDITING_SOFTWARE_KEYWORDS):
        flags.append(RiskFlag(
            code="IMAGE_EDITED", severity="low",
            description=f"Los metadatos indican que la imagen se editó con {exif.software} — tampoco es sospechoso por sí mismo, cualquiera edita fotos",
        ))
        score += 10

    return flags, min(score, 100)


def evaluate_reverse_search_risk(matches: list[ReverseImageMatch]) -> tuple[list[RiskFlag], int]:
    """
    Aparecer en otras páginas no prueba robo por sí solo (puede ser un
    reposteo legítimo, una foto de stock, o la propia cuenta de la
    persona) — severidad media y se pide revisión humana explícita en la
    descripción, en vez de presentarlo como prueba automática.
    """
    if not matches:
        return [], 0

    sites = ", ".join(sorted({m.source for m in matches if m.source})[:5]) or "varias páginas externas"
    flag = RiskFlag(
        code="IMAGE_FOUND_ON_EXTERNAL_PAGES", severity="medium",
        description=(
            f"Esta imagen aparece en {len(matches)} página(s) externa(s) ({sites}) — revisa manualmente "
            "si corresponden a un perfil/nombre distinto al analizado (indicio de foto robada) o si es "
            "un reposteo/foto de stock sin relación con una estafa"
        ),
    )
    score = min(20 + 10 * len(matches), 70)
    return [flag], score


def evaluate_facial_search_risk(matches: list[FacialSearchMatch]) -> tuple[list[RiskFlag], int]:
    """
    Coincidencia facial en otras páginas: severidad alta porque, si de
    verdad corresponde a un perfil con otro nombre, es un indicio fuerte de
    identidad robada — pero PimEyes solo dice "esta cara aparece aquí", no
    "esto es un perfil distinto", así que la descripción exige
    explícitamente revisión humana antes de tratarlo como prueba.
    """
    if not matches:
        return [], 0

    flag = RiskFlag(
        code="IMAGE_FACE_FOUND_ELSEWHERE", severity="high",
        description=(
            f"Se ha encontrado esta misma cara en {len(matches)} página(s) externa(s) — revisa "
            "manualmente si corresponden a un nombre/perfil distinto al analizado (indicio de "
            "identidad robada) o si es la cuenta legítima de la misma persona (no es señal de estafa "
            "por sí sola)"
        ),
    )
    score = min(40 + 10 * len(matches), 90)
    return [flag], score
