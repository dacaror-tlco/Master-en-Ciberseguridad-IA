from datetime import datetime, timezone

from app.schemas.image_analysis import ExifInfo, FacialSearchMatch, ImageMatch, ReverseImageMatch
from app.services.image_risk_engine import evaluate_facial_search_risk, evaluate_image_risk, evaluate_reverse_search_risk


def test_imagen_limpia_sin_matches_da_score_bajo():
    exif = ExifInfo(has_exif=True, camera_make="Apple", camera_model="iPhone 14")
    flags, score = evaluate_image_risk(exif, [])
    assert flags == []
    assert score == 0


def test_sin_exif_dispara_flag_bajo():
    exif = ExifInfo(has_exif=False)
    flags, score = evaluate_image_risk(exif, [])
    assert "IMAGE_NO_METADATA" in [f.code for f in flags]
    assert flags[0].severity == "low"


def test_software_de_edicion_dispara_flag_bajo():
    exif = ExifInfo(has_exif=True, software="Adobe Photoshop 25.0")
    flags, score = evaluate_image_risk(exif, [])
    assert "IMAGE_EDITED" in [f.code for f in flags]


def test_una_coincidencia_dispara_flag_alto():
    exif = ExifInfo(has_exif=True)
    match = ImageMatch(case_id=1, filename="otra.jpg", similarity_percent=95, analyzed_at=datetime.now(timezone.utc))
    flags, score = evaluate_image_risk(exif, [match])
    flag = next(f for f in flags if f.code == "IMAGE_REUSED_ACROSS_CASES")
    assert flag.severity == "high"
    assert score >= 60


def test_varias_coincidencias_suben_mas_el_score():
    exif = ExifInfo(has_exif=True)
    matches = [
        ImageMatch(case_id=1, similarity_percent=95, analyzed_at=datetime.now(timezone.utc)),
        ImageMatch(case_id=2, similarity_percent=92, analyzed_at=datetime.now(timezone.utc)),
    ]
    _, score_dos = evaluate_image_risk(exif, matches)
    _, score_uno = evaluate_image_risk(exif, matches[:1])
    assert score_dos > score_uno


def test_score_nunca_supera_100():
    exif = ExifInfo(has_exif=False, software="GIMP 2.10")
    matches = [ImageMatch(case_id=i, similarity_percent=90, analyzed_at=datetime.now(timezone.utc)) for i in range(10)]
    _, score = evaluate_image_risk(exif, matches)
    assert score <= 100


def test_reverse_search_sin_matches_no_dispara_flag():
    flags, score = evaluate_reverse_search_risk([])
    assert flags == []
    assert score == 0


def test_reverse_search_con_matches_dispara_flag_medio():
    matches = [ReverseImageMatch(url="https://example.com/perfil", source="example.com")]
    flags, score = evaluate_reverse_search_risk(matches)
    assert "IMAGE_FOUND_ON_EXTERNAL_PAGES" in [f.code for f in flags]
    assert flags[0].severity == "medium"
    assert score > 0


def test_reverse_search_score_no_supera_100():
    matches = [ReverseImageMatch(url=f"https://example{i}.com") for i in range(20)]
    _, score = evaluate_reverse_search_risk(matches)
    assert score <= 100


def test_facial_search_sin_matches_no_dispara_flag():
    flags, score = evaluate_facial_search_risk([])
    assert flags == []
    assert score == 0


def test_facial_search_con_matches_dispara_flag_alto():
    matches = [FacialSearchMatch(url="https://otrared.example/perfil-falso")]
    flags, score = evaluate_facial_search_risk(matches)
    assert "IMAGE_FACE_FOUND_ELSEWHERE" in [f.code for f in flags]
    assert flags[0].severity == "high"
    assert score > 0


def test_facial_search_score_no_supera_100():
    matches = [FacialSearchMatch(url=f"https://example{i}.com") for i in range(20)]
    _, score = evaluate_facial_search_risk(matches)
    assert score <= 100
