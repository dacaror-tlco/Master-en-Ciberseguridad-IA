"""
Marcas frecuentemente suplantadas en campañas de phishing dirigidas a
víctimas en España: bancos, administraciones públicas y grandes empresas
de consumo. Se usa en dos sitios distintos del módulo de email:

1. Nombre visible del remitente (`from_display_name`): "Banco Santander"
   <alguien@gmail.com> es la técnica de suplantación más básica y más
   fácil de detectar sin ninguna llamada externa.
2. Dominio de destino de los enlaces del cuerpo: un enlace a
   "santander-verificacion-urgente.xyz" no es el dominio oficial, aunque
   lo parezca a simple vista.

Deliberadamente es una lista corta y curada (no un diccionario exhaustivo
de marcas mundiales): cuantas más marcas, más falsos positivos por
coincidencias parciales de nombre. Se amplía según lo que se vaya viendo
en casos reales.
"""

# marca -> lista de dominios oficiales (con y sin variantes .com/.es habituales)
BRANDS: dict[str, list[str]] = {
    "bbva": ["bbva.es", "bbva.com"],
    "santander": ["santander.com", "bancosantander.es"],
    "caixabank": ["caixabank.es", "lacaixa.es"],
    "sabadell": ["bancsabadell.com", "sabadell.com"],
    "bankinter": ["bankinter.com"],
    "unicaja": ["unicajabanco.es"],
    "abanca": ["abanca.com"],
    "ing": ["ing.es"],
    "correos": ["correos.es"],
    "agencia tributaria": ["agenciatributaria.gob.es", "agenciatributaria.es"],
    "hacienda": ["agenciatributaria.gob.es"],
    "seguridad social": ["seg-social.es"],
    "dgt": ["dgt.es", "sede.dgt.gob.es"],
    "policia": ["policia.es"],
    "guardia civil": ["guardiacivil.es"],
    "amazon": ["amazon.es", "amazon.com"],
    "netflix": ["netflix.com"],
    "paypal": ["paypal.com"],
    "microsoft": ["microsoft.com", "outlook.com", "live.com"],
    "apple": ["apple.com", "icloud.com"],
    "endesa": ["endesa.com"],
    "iberdrola": ["iberdrola.es"],
    "movistar": ["movistar.es"],
    "vodafone": ["vodafone.es"],
    "orange": ["orange.es"],
    "dhl": ["dhl.com"],
    "seur": ["seur.com"],
}


def domain_belongs_to_brand(domain: str, brand: str) -> bool:
    """¿Es `domain` (o un subdominio suyo) uno de los dominios oficiales de `brand`?"""
    domain = domain.lower()
    official_domains = BRANDS.get(brand, [])
    return any(domain == d or domain.endswith("." + d) for d in official_domains)


def find_mentioned_brand(text: str) -> str | None:
    """
    Busca si el texto (nombre visible del remitente, o el propio dominio)
    menciona alguna marca conocida. Devuelve la primera coincidencia, o
    None si no menciona ninguna.
    """
    text_low = text.lower()
    for brand in BRANDS:
        if brand in text_low:
            return brand
    return None


def closest_brand(domain: str) -> str | None:
    """
    ¿El nombre de este dominio (o subdominio) contiene una marca conocida,
    sin ser realmente suyo? P.ej. 'bbva-verificacion-segura.xyz' o
    'paypal-secure.otro-dominio.com' contienen 'bbva'/'paypal' pero no son
    dominios oficiales de esas marcas. Usado tanto para enlaces de email
    como para subdominios descubiertos vía Certificate Transparency.
    """
    name = domain.rsplit(".", 1)[0]
    for brand in BRANDS:
        brand_key = brand.replace(" ", "")
        if brand_key and brand_key in name.replace("-", "") and not domain_belongs_to_brand(domain, brand):
            return brand
    return None
