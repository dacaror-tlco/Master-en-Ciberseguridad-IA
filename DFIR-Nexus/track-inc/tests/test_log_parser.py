from app.modules.tracking.log_parser import parse_log_text


def test_parses_iso_style_timestamp():
    text = "2026-08-10 14:32:05 powershell.exe -Command Get-Process"
    events = parse_log_text(text, fuente_log="test.log")

    assert len(events) == 1
    assert events[0].timestamp.year == 2026
    assert events[0].timestamp.hour == 14
    assert events[0].payload["command"] == "powershell.exe -Command Get-Process"
    assert events[0].payload["timestamp_inferred"] is False


def test_parses_dd_mm_yyyy_timestamp():
    text = "10/08/2026 14:32:05 net user hacker /add"
    events = parse_log_text(text, fuente_log="test.log")

    assert len(events) == 1
    assert events[0].timestamp.day == 10
    assert events[0].timestamp.month == 8


def test_line_without_timestamp_is_not_discarded():
    text = "net localgroup administrators hacker /add"
    events = parse_log_text(text, fuente_log="test.log")

    assert len(events) == 1
    assert events[0].payload["timestamp_inferred"] is True
    assert events[0].payload["command"] == "net localgroup administrators hacker /add"


def test_preserves_relative_order_for_lines_without_timestamp():
    text = "comando uno\ncomando dos\ncomando tres"
    events = parse_log_text(text, fuente_log="test.log")

    assert len(events) == 3
    assert events[0].timestamp < events[1].timestamp < events[2].timestamp


def test_empty_lines_are_ignored():
    text = "2026-08-10 14:32:05 comando uno\n\n\n2026-08-10 14:32:06 comando dos"
    events = parse_log_text(text, fuente_log="test.log")
    assert len(events) == 2


def test_extracts_user_when_present():
    text = "2026-08-10 14:32:05 login user:jsmith source=10.0.0.5"
    events = parse_log_text(text, fuente_log="test.log")
    assert events[0].payload["user"] == "jsmith"


def test_no_user_found_returns_none():
    text = "2026-08-10 14:32:05 powershell.exe -Command Get-Process"
    events = parse_log_text(text, fuente_log="test.log")
    assert events[0].payload["user"] is None


def test_all_events_have_log_source():
    from agent.evidence.models import EventSource
    text = "2026-08-10 14:32:05 comando"
    events = parse_log_text(text, fuente_log="test.log")
    assert events[0].source == EventSource.LOG


def test_indented_lines_are_captured_as_command_output():
    text = (
        "2026-08-14 03:11:19  whoami\n"
        "    CORP\\svc_backup\n"
        "2026-08-14 03:11:35  hostname\n"
        "    SRV-FILE01\n"
    )
    events = parse_log_text(text, fuente_log="test.log")

    assert len(events) == 2, "las lineas indentadas no deben crear eventos propios"
    assert events[0].payload["command"] == "whoami"
    assert events[0].payload["output"] == "CORP\\svc_backup"
    assert events[1].payload["output"] == "SRV-FILE01"


def test_multiline_output_is_joined():
    text = (
        "2026-08-14 03:12:04  net user\n"
        "    Administrador  Invitado\n"
        "    svc_backup     soporte_it\n"
    )
    events = parse_log_text(text, fuente_log="test.log")

    assert len(events) == 1
    assert events[0].payload["output"] == "Administrador  Invitado\nsvc_backup     soporte_it"


def test_command_without_output_has_none():
    text = "2026-08-14 03:19:05  vssadmin delete shadows /all /quiet"
    events = parse_log_text(text, fuente_log="test.log")

    assert events[0].payload["output"] is None


def test_unindented_line_without_timestamp_is_still_its_own_event():
    """No debe confundirse con salida: sin sangria sigue siendo un evento,
    que es el comportamiento tolerante que ya existia."""
    text = (
        "2026-08-14 03:11:19  whoami\n"
        "comando suelto sin marca temporal\n"
    )
    events = parse_log_text(text, fuente_log="test.log")

    assert len(events) == 2
    assert events[0].payload["output"] is None
    assert events[1].payload["command"] == "comando suelto sin marca temporal"
    assert events[1].payload["timestamp_inferred"] is True


def test_line_without_timestamp_inherits_previous_time_not_now():
    """Antes recibia la hora del analisis y asi se guardaba: en Timeline el
    comando aparecia como ocurrido el dia en que se subio el log."""
    text = (
        "2026-08-14 03:11:19  whoami\n"
        "net user x /add\n"
        "2026-08-14 03:11:25  hostname\n"
    )
    events = parse_log_text(text, fuente_log="test.log")

    assert events[1].timestamp == events[0].timestamp
    assert events[1].payload["timestamp_inferred"] is True
    assert events[2].payload["timestamp_inferred"] is False


def test_leading_lines_without_timestamp_take_the_first_known_time():
    text = "cd C:\\Temp\n2026-08-14 03:11:19  whoami\n"
    events = parse_log_text(text, fuente_log="test.log")

    assert events[0].timestamp == events[1].timestamp
    assert events[0].payload["timestamp_inferred"] is True
