import pytest

from app.modules.tracking import service
from app.modules.tracking.schemas import SaveEventsRequest
from app.core.database import SessionLocal
from .conftest import SharedCaseRow


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def existing_case(db):
    case = SharedCaseRow(nombre="Caso de test", responsable="perito")
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


SAMPLE_LOG = (
    "2026-08-10 14:32:05 powershell.exe -EncodedCommand SQBFAFgA\n"
    "2026-08-10 14:32:11 net user hacker P@ssw0rd123! /add\n"
    "2026-08-10 14:33:00 dir C:\\Users\n"
)


def test_analyze_does_not_persist_anything(db, existing_case):
    result = service.analyze_log_content(SAMPLE_LOG, fuente_log="incidente.log")

    assert result.total_eventos == 3
    assert service.get_events_for_case(db, existing_case.id) == []  # nada guardado todavía


def test_analyze_classifies_correctly():
    result = service.analyze_log_content(SAMPLE_LOG, fuente_log="incidente.log")
    severidades = [e.severidad.value for e in result.eventos]
    assert "critica" in severidades  # powershell -EncodedCommand
    assert "alta" in severidades     # net user ... /add
    assert "baja" in severidades     # dir, no matchea ninguna regla


def test_save_events_persists_to_official_schema(db, existing_case):
    preview = service.analyze_log_content(SAMPLE_LOG, fuente_log="incidente.log")
    request = SaveEventsRequest(case_id=existing_case.id, fuente_log="incidente.log", eventos=preview.eventos)

    result = service.save_events(db, request)

    assert result.guardados == 3
    saved = service.get_events_for_case(db, existing_case.id)
    assert len(saved) == 3
    assert all(e.case_id == existing_case.id for e in saved)
    assert all(e.fuente_log == "incidente.log" for e in saved)


def test_save_events_raises_for_nonexistent_case(db):
    from app.modules.tracking.schemas import AnalyzePreviewItem
    from app.modules.tracking.models import Severidad
    from datetime import datetime, timezone

    request = SaveEventsRequest(
        case_id=99999,
        fuente_log="x.log",
        eventos=[AnalyzePreviewItem(hora=datetime.now(timezone.utc), evento="x", severidad=Severidad.BAJA)],
    )
    with pytest.raises(service.CaseNotFoundError):
        service.save_events(db, request)


def test_save_events_also_feeds_internal_chain_and_verifies_ok(db, existing_case):
    preview = service.analyze_log_content(SAMPLE_LOG, fuente_log="incidente.log")
    request = SaveEventsRequest(case_id=existing_case.id, fuente_log="incidente.log", eventos=preview.eventos)
    service.save_events(db, request)

    verification = service.verify_integrity(db, existing_case.id)
    assert verification.ok is True
    assert "3" in verification.mensaje


def test_verify_integrity_for_case_without_events(db, existing_case):
    verification = service.verify_integrity(db, existing_case.id)
    assert verification.ok is True
    assert "No hay eventos" in verification.mensaje


def test_get_events_raises_for_nonexistent_case(db):
    with pytest.raises(service.CaseNotFoundError):
        service.get_events_for_case(db, 99999)
