"""
Pruebas de integración de Timeline. feature/timeline-integration no traía
ninguna — esta suite es nueva, añadida en la Fase 3 para validar
exactamente los puntos que pedía la integración: multi-fuente, ausencia
de heurística sobre osint_findings, no duplicación y persistencia real.
"""


def _seed_multi_source_case(conn):
    conn.executescript(
        """
        INSERT INTO cases (id, nombre, estado, responsable)
            VALUES (1, 'Caso multi-fuente', 'abierto', 'perito');

        INSERT INTO evidences (id, case_id, tipo, valor, fecha_subida, observaciones)
            VALUES (10, 1, 'disco', 'imagen.dd', '2026-09-01 09:00:00', NULL);

        INSERT INTO tracking_events (id, case_id, hora, evento, severidad, fuente_log, usuario_detectado)
            VALUES (20, 1, '2026-09-01 10:00:00', 'powershell -EncodedCommand ...', 'critica', 'incidente.log', 'hacker');

        INSERT INTO osint_findings (id, case_type, source_table, source_id, case_id, subject_type,
            subject_value, risk_score, risk_level, headline, flag_count, top_flags, details, analyzed_at, created_at)
            VALUES (30, 'domain', 'osint_domain_cases', 5, 1, 'domain', 'evil.example.com', 80,
            'high', 'Dominio con riesgo alto', 3, '[]', '{}', '2026-09-01 08:00:00', '2026-09-01 08:00:00');

        -- Hallazgo SIN case_id (análisis no atado a ningún expediente): no debe
        -- aparecer en la timeline del caso 1 bajo ninguna heurística de
        -- subject_value/dominio/nombre.
        INSERT INTO osint_findings (id, case_type, source_table, source_id, case_id, subject_type,
            subject_value, risk_score, risk_level, headline, flag_count, top_flags, details, analyzed_at, created_at)
            VALUES (31, 'domain', 'osint_domain_cases', 6, NULL, 'domain', 'sin-asociar.example.com', 90,
            'high', 'Sin caso asociado', 2, '[]', '{}', '2026-09-01 08:30:00', '2026-09-01 08:30:00');
        """
    )
    conn.commit()


def test_refresh_combina_las_tres_fuentes_en_orden_correcto(client, raw_conn):
    _seed_multi_source_case(raw_conn)

    r = client.post("/timeline/cases/1/refresh")
    assert r.status_code == 200
    events = r.json()

    assert len(events) == 3  # no las 4 filas de osint_findings, solo la del caso 1
    assert [e["origen_modulo"] for e in events] == ["osint", "evidence", "tracking"]  # por fecha_hora
    assert [e["orden"] for e in events] == [1, 2, 3]
    assert all(e["case_id"] == 1 for e in events)


def test_no_usa_heuristica_para_osint_findings_sin_case_id(client, raw_conn):
    _seed_multi_source_case(raw_conn)

    events = client.post("/timeline/cases/1/refresh").json()
    headlines = [e["descripcion"] for e in events]

    assert "Dominio con riesgo alto" in headlines       # case_id=1, sí entra
    assert "Sin caso asociado" not in headlines          # case_id=NULL, no entra aunque exista


def test_origen_id_apunta_al_id_real_de_la_fila_de_origen(client, raw_conn):
    _seed_multi_source_case(raw_conn)

    events = client.post("/timeline/cases/1/refresh").json()
    por_origen = {e["origen_modulo"]: e["origen_id"] for e in events}

    assert por_origen["evidence"] == 10   # evidences.id real
    assert por_origen["tracking"] == 20   # tracking_events.id real
    assert por_origen["osint"] == 30      # osint_findings.id real


def test_refresh_no_duplica_al_ejecutarse_dos_veces(client, raw_conn):
    _seed_multi_source_case(raw_conn)

    client.post("/timeline/cases/1/refresh")
    client.post("/timeline/cases/1/refresh")

    r = client.get("/timeline/cases/1")
    assert len(r.json()) == 3


def test_get_devuelve_lo_persistido_tras_el_refresh(client, raw_conn):
    _seed_multi_source_case(raw_conn)

    refreshed = client.post("/timeline/cases/1/refresh").json()
    fetched = client.get("/timeline/cases/1").json()

    assert len(fetched) == len(refreshed) == 3
    assert [e["descripcion"] for e in fetched] == [e["descripcion"] for e in refreshed]


def test_caso_sin_eventos_en_ninguna_fuente_devuelve_timeline_vacia(client, raw_conn):
    raw_conn.execute(
        "INSERT INTO cases (id, nombre, estado, responsable) VALUES (2, 'Caso vacío', 'abierto', 'perito')"
    )
    raw_conn.commit()

    r = client.post("/timeline/cases/2/refresh")
    assert r.status_code == 200
    assert r.json() == []

    assert client.get("/timeline/cases/2").json() == []


# --- Integración con el endurecimiento de Cases/Evidence (Módulo 1) --------
#
# Cases/Evidence añadió borrado lógico (columna `eliminado`) y un timestamp
# forense separado del administrativo (`fecha_adquisicion` vs
# `fecha_subida`). Timeline lee `evidences` con SQL directo (nunca importa
# su modelo), así que estos dos tests cruzados comprueban que ese cambio de
# esquema en otro backend se refleja correctamente aquí.


def test_evidencia_eliminada_logicamente_no_aparece_en_la_timeline(client, raw_conn):
    raw_conn.executescript(
        """
        INSERT INTO cases (id, nombre, estado, responsable)
            VALUES (3, 'Caso con evidencia eliminada', 'abierto', 'perito');

        INSERT INTO evidences (id, case_id, tipo, valor, fecha_subida, observaciones, eliminado)
            VALUES (40, 3, 'disco', 'imagen.dd', '2026-09-01 09:00:00', NULL, 0);
        INSERT INTO evidences (id, case_id, tipo, valor, fecha_subida, observaciones, eliminado)
            VALUES (41, 3, 'log', 'auth.log', '2026-09-01 09:05:00', NULL, 1);
        """
    )
    raw_conn.commit()

    events = client.post("/timeline/cases/3/refresh").json()

    assert [e["origen_id"] for e in events] == [40]


def test_evidencia_usa_fecha_de_adquisicion_cuando_existe(client, raw_conn):
    raw_conn.executescript(
        """
        INSERT INTO cases (id, nombre, estado, responsable)
            VALUES (4, 'Caso con fecha forense conocida', 'abierto', 'perito');

        INSERT INTO evidences
            (id, case_id, tipo, valor, fecha_subida, observaciones, fecha_adquisicion, eliminado)
            VALUES (50, 4, 'disco', 'imagen.dd', '2026-09-05 18:00:00', NULL,
                    '2026-08-20 07:30:00', 0);
        """
    )
    raw_conn.commit()

    events = client.post("/timeline/cases/4/refresh").json()

    assert len(events) == 1
    # La cronología usa cuándo ocurrió el hecho forense (fecha_adquisicion),
    # no cuándo se dio de alta el registro (fecha_subida, muy posterior).
    assert events[0]["fecha_hora"].startswith("2026-08-20")


# --- Regresión H-02 (auditoría Módulo 4, 2026-09-27) ------------------------


def test_refresh_devuelve_id_de_timeline_events(client, raw_conn):
    """El `id` que devuelve POST /refresh debe ser el de timeline_events,
    NO el de la fila origen. Antes del fix, `id` coincidía con el id de
    evidences / tracking_events / osint_findings, lo que provocaba
    colisiones de key en el frontend (getRowId={e => e.id})."""
    _seed_multi_source_case(raw_conn)

    refreshed = client.post("/timeline/cases/1/refresh").json()
    persisted = client.get("/timeline/cases/1").json()

    assert [e["id"] for e in refreshed] == [e["id"] for e in persisted]
    # Los ids de origen sembrados son 10, 20 y 30 — no deben aparecer
    # como ids de timeline_events.
    assert {e["id"] for e in refreshed}.isdisjoint({10, 20, 30})
