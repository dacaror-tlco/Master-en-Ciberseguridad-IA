from io import BytesIO

import pytest
from PIL import Image

from app.services.image_service import (
    analyze_image,
    compute_perceptual_hash,
    hamming_distance,
    similarity_percent,
)


def _make_image_bytes(seed: int, size=(100, 100), fmt="JPEG") -> bytes:
    img = Image.new("RGB", size)
    px = img.load()
    for x in range(size[0]):
        for y in range(size[1]):
            px[x, y] = ((x + seed) % 256, (y + seed) % 256, (x * y + seed) % 256)
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_hashes_de_imagenes_identicas_son_iguales():
    data = _make_image_bytes(seed=1)
    img1 = Image.open(BytesIO(data))
    img2 = Image.open(BytesIO(data))
    assert compute_perceptual_hash(img1) == compute_perceptual_hash(img2)


def test_hash_sobrevive_a_recorte_y_reescalado():
    data = _make_image_bytes(seed=5, size=(200, 200))
    original = Image.open(BytesIO(data))
    modified = original.resize((150, 150)).crop((5, 5, 145, 145))

    h1 = compute_perceptual_hash(original)
    h2 = compute_perceptual_hash(modified)
    assert hamming_distance(h1, h2) <= 10  # mismo umbral que usa la ruta


def test_imagenes_distintas_dan_hashes_lejanos():
    data_a = _make_image_bytes(seed=1)
    data_b = _make_image_bytes(seed=250)
    h1 = compute_perceptual_hash(Image.open(BytesIO(data_a)))
    h2 = compute_perceptual_hash(Image.open(BytesIO(data_b)))
    assert hamming_distance(h1, h2) > 10


def test_similarity_percent_100_para_hashes_identicos():
    data = _make_image_bytes(seed=1)
    h = compute_perceptual_hash(Image.open(BytesIO(data)))
    assert similarity_percent(h, h) == 100


def test_analyze_image_sin_exif():
    data = _make_image_bytes(seed=1)
    phash, exif = analyze_image(data)
    assert len(phash) == 16  # 64 bits en hex
    assert exif.has_exif is False


def test_analyze_image_con_archivo_invalido_lanza_value_error():
    with pytest.raises(ValueError):
        analyze_image(b"esto no es una imagen en absoluto")
