"""Recomienda dónde denunciar según qué tipos de evidencia se han incluido."""
from pydantic import BaseModel


class ReportingChannel(BaseModel):
    name: str
    url: str
    when_to_use: str


_CHANNELS = {
    "policia": ReportingChannel(
        name="Policía Nacional (denuncia online)",
        url="https://www.policia.es/_es/colabora_denunciaonline.php",
        when_to_use="Estafa online en general, con o sin pérdida económica",
    ),
    "incibe": ReportingChannel(
        name="INCIBE (Instituto Nacional de Ciberseguridad)",
        url="https://www.incibe.es/ciudadania/tramites/reportar-un-incidente",
        when_to_use="Phishing, dominios/emails/webs fraudulentas, malware",
    ),
    "cnmv": ReportingChannel(
        name="CNMV (reclamaciones y denuncias)",
        url="https://www.cnmv.es/portal/Menu/Reclamaciones-y-Denuncias.aspx",
        when_to_use="Entidad de inversión no autorizada (\"chiringuito financiero\")",
    ),
    "gdt": ReportingChannel(
        name="Guardia Civil - GDT (Grupo de Delitos Telemáticos)",
        url="https://www.gdt.guardiacivil.es/webgdt/pinformar.php",
        when_to_use="Delitos económicos y estafas con criptomonedas",
    ),
    "aepd": ReportingChannel(
        name="AEPD (Agencia Española de Protección de Datos)",
        url="https://www.aepd.es/es/derechos-y-deberes/reclama-tus-derechos",
        when_to_use="Uso indebido de tus datos personales o tu imagen",
    ),
}

# case_type -> canales recomendados además de "policia" (siempre incluida)
_MAPPING = {
    "domain": ["incibe"],
    "email": ["incibe"],
    "typosquatting": ["incibe"],
    "wallet": ["gdt"],
    "phone": ["incibe"],
    "cnmv": ["cnmv"],
    "image": ["aepd"],
    "ip": ["incibe"],
}


def recommend_channels(case_types: set[str]) -> list[ReportingChannel]:
    keys = ["policia"]
    for ct in case_types:
        for key in _MAPPING.get(ct, []):
            if key not in keys:
                keys.append(key)
    return [_CHANNELS[k] for k in keys]
