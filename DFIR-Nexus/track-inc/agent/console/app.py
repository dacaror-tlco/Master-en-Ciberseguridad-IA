"""
Panel de control local del agente (Módulo 3). Es una herramienta de
administración/consulta, NO el agente en sí — el agente sigue corriendo
como servicio de sistema (ver agent/service/). Esto lee y opera sobre el
mismo store SQLite y la misma configuración, para poder:

  - ver el estado (total de evidencias, pendientes de sync, por criticidad)
  - listar y filtrar evidencias
  - verificar la integridad de la cadena bajo demanda
  - forzar una sincronización manual
  - ver las reglas de clasificación activas
  - ver la configuración cargada (sin exponer secretos)

Ejecutar con:
    python -m agent.console.app --config config/agent.example.yaml

Por defecto arranca en http://127.0.0.1:5050
"""

from __future__ import annotations

import argparse
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

from agent.classifier.engine import ClassifierEngine
from agent.config import AgentConfig
from agent.evidence.chain import ChainError, verify_chain
from agent.evidence.store import EvidenceStore
from agent.sync.engine import SyncEngine
from agent.sync.http_transport import HttpEvidenceTransport
from agent.sync.mock_transport import MockEvidenceTransport

CRITICALITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def create_app(config: AgentConfig) -> Flask:
    app = Flask(__name__)
    app.secret_key = "evidence-agent-console"  # solo para flash messages locales, no auth

    def get_store() -> EvidenceStore:
        # se abre una conexión nueva por request; SQLite maneja bien
        # múltiples lectores, y así el panel nunca se queda con una
        # conexión obsoleta si el agente reescribe el fichero
        return EvidenceStore(config.db_path)

    def get_transport():
        if config.sync.server_url:
            return HttpEvidenceTransport(
                base_url=config.sync.server_url,
                agent_id=config.agent_id,
                api_key=config.sync.api_key,
            )
        return MockEvidenceTransport()

    @app.route("/")
    def dashboard():
        store = get_store()
        all_records = store.get_all()
        pending = store.get_pending(limit=10_000)

        counts_by_criticality = {c: 0 for c in CRITICALITY_ORDER}
        for r in all_records:
            counts_by_criticality[r.criticality.value] += 1

        counts_by_source = {}
        for r in all_records:
            src = r.event.source.value
            counts_by_source[src] = counts_by_source.get(src, 0) + 1

        last_hash, last_seq = store.get_last_hash_and_seq()
        store.close()

        return render_template(
            "dashboard.html",
            agent_id=config.agent_id,
            total=len(all_records),
            pending_count=len(pending),
            counts_by_criticality=counts_by_criticality,
            counts_by_source=counts_by_source,
            last_seq=last_seq,
            last_hash=last_hash,
            sync_configured=bool(config.sync.server_url),
        )

    @app.route("/verify", methods=["POST"])
    def verify():
        store = get_store()
        records = store.get_all()
        store.close()
        try:
            verify_chain(records)
            flash(f"✔ Cadena íntegra: {len(records)} evidencias verificadas correctamente.", "success")
        except ChainError as e:
            flash(f"✘ Cadena comprometida: {e}", "error")
        return redirect(url_for("dashboard"))

    @app.route("/sync", methods=["POST"])
    def sync_now():
        store = get_store()
        pending_before = len(store.get_pending(limit=10_000))
        transport = get_transport()
        engine = SyncEngine(store, transport, batch_size=config.sync.batch_size, max_retries=1)
        synced = engine.sync_once()
        store.close()

        if pending_before == 0:
            flash("No había evidencias pendientes de sincronizar.", "info")
        elif synced == pending_before:
            flash(f"✔ {synced} evidencias sincronizadas correctamente.", "success")
        else:
            flash(f"⚠ Solo se sincronizaron {synced} de {pending_before} (revisa conectividad con el servidor).", "error")
        return redirect(url_for("dashboard"))

    @app.route("/evidence")
    def evidence_list():
        criticality_filter = request.args.get("criticality", "")
        source_filter = request.args.get("source", "")
        page = max(1, int(request.args.get("page", 1)))
        page_size = 25

        store = get_store()
        all_records = store.get_all()
        store.close()

        filtered = list(reversed(all_records))  # más recientes primero
        if criticality_filter:
            filtered = [r for r in filtered if r.criticality.value == criticality_filter]
        if source_filter:
            filtered = [r for r in filtered if r.event.source.value == source_filter]

        total_filtered = len(filtered)
        start = (page - 1) * page_size
        page_records = filtered[start:start + page_size]
        has_next = start + page_size < total_filtered

        return render_template(
            "evidence.html",
            records=page_records,
            criticality_filter=criticality_filter,
            source_filter=source_filter,
            criticalities=CRITICALITY_ORDER,
            sources=["filesystem", "process", "network"],
            page=page,
            has_next=has_next,
            has_prev=page > 1,
            total_filtered=total_filtered,
        )

    @app.route("/rules")
    def rules_view():
        try:
            engine = ClassifierEngine.from_yaml(config.rules_path)
            error = None
        except Exception as e:
            engine = None
            error = str(e)
        return render_template("rules.html", engine=engine, error=error, rules_path=config.rules_path)

    @app.route("/config")
    def config_view():
        safe_config = config.model_dump()
        if safe_config.get("sync", {}).get("api_key"):
            safe_config["sync"]["api_key"] = "•" * 12 + " (oculta)"
        return render_template("config.html", config=safe_config)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Panel de control del agente (Módulo 3)")
    parser.add_argument("--config", required=True, help="Ruta al fichero de configuración YAML")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    agent_config = AgentConfig.from_yaml(args.config)
    app = create_app(agent_config)
    print(f"Panel de control disponible en http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
