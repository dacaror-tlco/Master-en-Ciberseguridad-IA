"""
Vocabulario de nivel de riesgo compartido por TODA la herramienta.

Los cortes (30 / 60) tienen que ser LOS MISMOS en tres sitios: el frontend
(`frontend/src/modules/osint/components/riskLevel.ts`), la monitorización
continua (`monitoring/service.py`) y el modelo de lectura para otros
módulos (`findings/`). Por eso viven en un único sitio y todos importan de
aquí — si esto cambiara, "ha cambiado de nivel de riesgo" dejaría de
significar lo mismo en cada parte.
"""

# Rango de cada bucket, para comparar si un nivel es "peor" que otro.
BUCKET_RANK = {"low": 0, "medium": 1, "high": 2}


def risk_bucket(score: int) -> str:
    """Traduce un risk_score (0-100) a low / medium / high con los mismos cortes que el frontend."""
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"
