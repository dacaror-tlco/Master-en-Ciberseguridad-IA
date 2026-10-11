"""
De dónde salen los indicadores del Anexo B, y qué declara el informe en cada
caso.

Esto no es una hipótesis: el 2026-09-02 se comprobó contra la base de datos
compartida del equipo que **`osint_results` no existe**. Y no existe con
consecuencias: `repository` la consultaba sin condiciones al componer todo
informe, así que en cuanto el Módulo 1 creara un caso y el Módulo 4 le pusiera
cronología, *toda* generación habría devuelto un 500. Ni siquiera excluir el
Anexo B con las opciones de alcance lo evitaba, porque la consulta ocurre antes
de aplicar el filtro.

Los tres estados que el informe tiene que saber distinguir están en `osint.py`.
El que más importa aquí es el tercero: un anexo vacío que dice «no constan
consultas OSINT» cuando lo que pasa es que nadie ha creado la tabla afirma algo
falso sobre la investigación.
"""
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.modules.reports import repository
from app.modules.reports.document import construir_documento
from app.modules.reports.json_builder import construir_json
from app.modules.reports.opciones import Anexo, OpcionesInforme
from app.modules.reports.osint import FuenteOsint
from app.modules.shared.models import (
    Case,
    EstadoCaso,
    OsintFinding,
    OsintResult,
    TimelineEvent,
)
from tests.conftest import NARRATIVA_FALSA


def _sesion_con(tablas_fuera: set[str]):
    """
    Una base en la que faltan a propósito las tablas indicadas.

    Es la única forma de reproducir lo que hay en la base compartida: allí las
    tablas las crean otros módulos, y el que debía crear `osint_results` no lo
    ha hecho. Crear todo el esquema y luego borrar una tabla daría lo mismo,
    pero así queda explícito en cada test qué se está simulando.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[t for t in Base.metadata.sorted_tables if t.name not in tablas_fuera],
    )
    return sessionmaker(bind=engine)()


def _caso_con_cronologia(sesion):
    caso = Case(
        nombre="Fraude por suplantación de proveedor",
        estado=EstadoCaso.EN_PROGRESO,
        fecha_creacion=datetime(2026, 9, 1, 9, 0),
        descripcion="Transferencia desviada tras correo suplantado",
        responsable="Ana Pérez",
    )
    sesion.add(caso)
    sesion.flush()
    sesion.add(
        TimelineEvent(
            id=1,
            case_id=caso.id,
            fecha_hora=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            descripcion="Tracking: acceso desde IP no habitual",
            origen_modulo="tracking",
            origen_id=1,
            orden=1,
        )
    )
    sesion.commit()
    return caso


def _texto_del_informe(sesion, caso, opciones=None):
    registro = repository.get_registro_osint(sesion, caso.id)
    doc = construir_documento(
        case=caso,
        timeline_events=repository.get_timeline_events(sesion, caso.id),
        narrativa=NARRATIVA_FALSA,
        generado_por="Ana Pérez",
        version=1,
        generado_el=datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        evidences=repository.get_evidences(sesion, caso.id),
        osint_results=registro.indicadores,
        fuente_osint=registro.fuente,
        tracking_events=repository.get_tracking_events(sesion, caso.id),
        opciones=opciones,
    )
    return json.dumps(json.loads(construir_json(doc)), ensure_ascii=False)


# --- Qué fuente se elige --------------------------------------------------


def test_con_osint_results_se_usa_la_tabla_oficial():
    sesion = _sesion_con(set())
    caso = _caso_con_cronologia(sesion)
    sesion.add(
        OsintResult(
            case_id=caso.id,
            tipo_indicador="dominio",
            valor="proveedor-falso.example",
            reputacion="malicioso",
            pais="RU",
            detecciones=7,
            fuente="VirusTotal",
            fecha_consulta=datetime(2026, 9, 1, 11, 0),
        )
    )
    sesion.commit()

    registro = repository.get_registro_osint(sesion, caso.id)
    assert registro.fuente is FuenteOsint.RESULTS
    assert [i.valor for i in registro.indicadores] == ["proveedor-falso.example"]
    sesion.close()


def test_sin_osint_results_se_cae_a_osint_findings():
    """La capa de lectura que el Módulo 2 publicó el 02/09."""
    sesion = _sesion_con({"osint_results"})
    caso = _caso_con_cronologia(sesion)
    sesion.add(
        OsintFinding(
            case_id=caso.id,
            case_type="ip",
            source_table="ip_cases",
            source_id=3,
            subject_type="ip_address",
            subject_value="45.83.122.14",
            risk_score=72,
            risk_level="high",
            headline="IP 45.83.122.14 — RIESGO ALTO (72)",
            flag_count=4,
            top_flags=["abuseipdb", "tor_exit"],
            details={"asn": "AS12345"},
            analyzed_at=datetime(2026, 9, 2, 8, 36, 55),
        )
    )
    sesion.commit()

    registro = repository.get_registro_osint(sesion, caso.id)
    assert registro.fuente is FuenteOsint.FINDINGS

    indicador = registro.indicadores[0]
    assert indicador.valor == "45.83.122.14"
    assert indicador.tipo_indicador == "ip_address"
    # `risk_level` no es una reputación: se imprime con su puntuación al lado
    # para que se vea que es el juicio del Módulo 2 y no el de una fuente.
    assert indicador.reputacion == "high (72)"
    assert indicador.detecciones == 4          # <- flag_count
    assert indicador.fuente == "scam-shield/ip"
    assert indicador.pais is None              # osint_findings no lo publica
    sesion.close()


def test_sin_ninguna_de_las_dos_tablas_no_se_cae():
    """El fallo que se descubrió en la base compartida: antes, esto era un 500."""
    sesion = _sesion_con({"osint_results", "osint_findings"})
    caso = _caso_con_cronologia(sesion)

    registro = repository.get_registro_osint(sesion, caso.id)
    assert registro.fuente is FuenteOsint.NO_DISPONIBLE
    assert registro.indicadores == []
    sesion.close()


def test_findings_de_otro_caso_no_entran():
    sesion = _sesion_con({"osint_results"})
    caso = _caso_con_cronologia(sesion)
    for case_id in (caso.id + 99, None):  # otro caso, y el `case_id` NULL de hoy
        sesion.add(
            OsintFinding(
                case_id=case_id,
                case_type="domain",
                source_table="osint_domain_cases",
                source_id=1,
                subject_type="domain",
                subject_value="ajeno.example",
                risk_score=10,
                risk_level="low",
                headline="—",
                flag_count=0,
                top_flags=[],
                details={},
                analyzed_at=datetime(2026, 9, 2, 8, 0),
            )
        )
    sesion.commit()

    registro = repository.get_registro_osint(sesion, caso.id)
    assert registro.fuente is FuenteOsint.FINDINGS
    assert registro.indicadores == []
    sesion.close()


# --- Qué declara el informe -----------------------------------------------


def test_el_informe_no_dice_que_no_constan_consultas_si_no_puede_saberlo():
    """
    El corazón del asunto. Sin registro OSINT accesible, el anexo **no** puede
    afirmar que no hubo consultas: solo que no ha podido consultarlas.
    """
    sesion = _sesion_con({"osint_results", "osint_findings"})
    caso = _caso_con_cronologia(sesion)

    texto = _texto_del_informe(sesion, caso)

    assert "no está disponible en el sistema" in texto
    assert "No debe interpretarse como que no se realizaron consultas" in texto
    assert "No constan consultas OSINT registradas para este caso" not in texto
    sesion.close()


def test_con_la_tabla_oficial_vacia_si_dice_que_no_constan():
    """Aquí sí lo sabe: la tabla existe y no tiene filas para el caso."""
    sesion = _sesion_con(set())
    caso = _caso_con_cronologia(sesion)

    texto = _texto_del_informe(sesion, caso)

    assert "No constan consultas OSINT registradas para este caso" in texto
    assert "no está disponible en el sistema" not in texto
    sesion.close()


def test_el_anexo_declara_cuando_lee_la_capa_del_modulo_2():
    """
    Si los indicadores no vienen del registro que el modelo de datos prevé, el
    informe lo dice, y explica qué significan las columnas que no son
    equivalentes. Quien lo lea no puede acabar creyendo que «high (72)» es el
    veredicto de VirusTotal.
    """
    sesion = _sesion_con({"osint_results"})
    caso = _caso_con_cronologia(sesion)
    sesion.add(
        OsintFinding(
            case_id=caso.id,
            case_type="ip",
            source_table="ip_cases",
            source_id=3,
            subject_type="ip_address",
            subject_value="45.83.122.14",
            risk_score=72,
            risk_level="high",
            headline="—",
            flag_count=4,
            top_flags=[],
            details={},
            analyzed_at=datetime(2026, 9, 2, 8, 36, 55),
        )
    )
    sesion.commit()

    texto = _texto_del_informe(sesion, caso)

    assert "45.83.122.14" in texto
    assert "osint_findings" in texto
    assert "no está implantado" in texto
    assert "no consta el país asociado" in texto
    sesion.close()


def test_sin_tabla_y_con_el_anexo_excluido_tampoco_se_cae():
    """
    La consulta ocurre antes de aplicar el alcance, así que excluir el Anexo B
    nunca fue una vía de escape al 500. Comprobado que ahora ninguna de las dos
    cosas rompe, y que el anexo excluido sigue sin dejar rastro.
    """
    sesion = _sesion_con({"osint_results", "osint_findings"})
    caso = _caso_con_cronologia(sesion)

    texto = _texto_del_informe(
        sesion,
        caso,
        OpcionesInforme(anexos=frozenset({Anexo.EVIDENCIAS, Anexo.TRACKING})),
    )

    assert "no está disponible en el sistema" not in texto
    assert "Indicadores consultados en fuentes abiertas" in texto  # solo en el alcance
    sesion.close()
