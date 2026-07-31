"""
Servicio de análisis de imagen.

Dos piezas, ambas 100% offline (solo Pillow, sin llamadas a red ni APIs):

1. EXIF: metadatos que la cámara/app graba dentro del archivo (modelo de
   cámara, software de edición, fecha, GPS si lo hay). Las fotos robadas
   de redes sociales o bancos de imágenes casi siempre llegan sin EXIF
   (las plataformas lo eliminan al subirlas) — la ausencia de EXIF NO es
   en sí misma sospechosa (es lo normal para casi cualquier foto de
   internet), pero es un dato más a considerar junto con el resto.

2. Hash perceptual ("huella visual"): a diferencia de un hash criptográfico
   (que cambia por completo si se modifica un solo píxel), un hash
   perceptual sigue siendo parecido aunque la imagen se recorte,
   recomprima o le cambien el tamaño. Esto permite detectar la MISMA foto
   reciclada entre distintos casos analizados en la herramienta —
   señal muy fuerte en estafas románticas (la misma foto de perfil
   robada usada contra varias víctimas).

No hacemos reconocimiento facial ni identificación de personas: ver la
nota en image_risk_engine.py y en el README sobre por qué.
"""
from io import BytesIO

from PIL import ExifTags, Image

from app.schemas.image_analysis import ExifInfo

_HASH_SIZE = 8  # hash de 64 bits (8x8), suficiente para detectar duplicados/recortes


def _convert_gps_to_decimal(gps_coord, gps_ref) -> float | None:
    try:
        degrees, minutes, seconds = gps_coord
        decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
        if gps_ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def extract_exif(image: Image.Image) -> ExifInfo:
    raw_exif = image.getexif()
    if not raw_exif:
        return ExifInfo(has_exif=False)

    tagged = {ExifTags.TAGS.get(k, k): v for k, v in raw_exif.items()}

    gps_lat = gps_lon = None
    gps_info = raw_exif.get_ifd(ExifTags.IFD.GPSInfo) if hasattr(raw_exif, "get_ifd") else None
    if gps_info:
        gps_tagged = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_info.items()}
        if "GPSLatitude" in gps_tagged and "GPSLongitude" in gps_tagged:
            gps_lat = _convert_gps_to_decimal(gps_tagged.get("GPSLatitude"), gps_tagged.get("GPSLatitudeRef"))
            gps_lon = _convert_gps_to_decimal(gps_tagged.get("GPSLongitude"), gps_tagged.get("GPSLongitudeRef"))

    return ExifInfo(
        has_exif=True,
        camera_make=tagged.get("Make"),
        camera_model=tagged.get("Model"),
        software=tagged.get("Software"),
        date_taken=tagged.get("DateTime") or tagged.get("DateTimeOriginal"),
        gps_latitude=gps_lat,
        gps_longitude=gps_lon,
    )


def compute_perceptual_hash(image: Image.Image) -> str:
    """
    Average hash (aHash): reduce la imagen a una cuadrícula pequeña en
    escala de grises, y cada píxel se convierte en un bit (1 si es más
    claro que la media, 0 si no). El resultado es un hash que apenas
    cambia si la imagen se recorta o recomprime ligeramente — justo lo
    que hace falta para detectar la misma foto reutilizada, aunque no sea
    un archivo idéntico byte a byte.
    """
    small = image.convert("L").resize((_HASH_SIZE, _HASH_SIZE), Image.LANCZOS)
    pixels = list(small.getdata())
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p > avg else "0" for p in pixels)
    return format(int(bits, 2), f"0{_HASH_SIZE * _HASH_SIZE // 4}x")


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Nº de bits distintos entre dos hashes — 0 = idénticos, cuanto más alto, más distintas."""
    return bin(int(hash_a, 16) ^ int(hash_b, 16)).count("1")


def similarity_percent(hash_a: str, hash_b: str) -> int:
    total_bits = _HASH_SIZE * _HASH_SIZE
    distance = hamming_distance(hash_a, hash_b)
    return round((1 - distance / total_bits) * 100)


def analyze_image(raw_bytes: bytes) -> tuple[str, ExifInfo]:
    try:
        image = Image.open(BytesIO(raw_bytes))
        image.load()
    except Exception as exc:
        raise ValueError(f"El archivo no parece ser una imagen válida: {exc}")

    phash = compute_perceptual_hash(image)
    exif = extract_exif(image)
    return phash, exif
