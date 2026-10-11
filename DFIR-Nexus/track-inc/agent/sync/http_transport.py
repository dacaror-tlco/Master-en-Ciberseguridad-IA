"""
Implementación REST del transporte, contra el contrato tentativo:

    POST /api/v1/agents/{agent_id}/evidence/batch
    GET  /api/v1/agents/{agent_id}/chain/last-hash

Cuando el equipo defina la API real, lo normal es que solo haya que
ajustar rutas/payloads aquí, o añadir autenticación (API key / JWT /
mTLS) en el cliente httpx. El resto del agente no debería enterarse.
"""

from __future__ import annotations

import httpx

from agent.evidence.models import EvidenceRecord

from .transport import SyncResult


class HttpEvidenceTransport:
    def __init__(self, base_url: str, agent_id: str, api_key: str | None = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout)

    def send_batch(self, records: list[EvidenceRecord]) -> SyncResult:
        try:
            response = self._client.post(
                f"/api/v1/agents/{self.agent_id}/evidence/batch",
                json={"records": [r.model_dump(mode="json") for r in records]},
            )
            response.raise_for_status()
            data = response.json()
            return SyncResult(
                accepted_ids=data.get("accepted", []),
                rejected_ids=data.get("rejected", []),
            )
        except httpx.HTTPError as e:
            return SyncResult(error=str(e))

    def health_check(self) -> bool:
        try:
            response = self._client.get("/api/v1/health", timeout=3.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def get_last_hash(self, agent_id: str) -> str | None:
        try:
            response = self._client.get(f"/api/v1/agents/{agent_id}/chain/last-hash")
            response.raise_for_status()
            return response.json().get("hash")
        except httpx.HTTPError:
            return None

    def close(self) -> None:
        self._client.close()
