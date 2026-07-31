"""
Resolución DNS: comprobación en paralelo (para typosquatting, que lanza
cientos de variantes) y consulta completa de un único dominio (para el
análisis de dominio: todas las IPs A, MX, TXT/SPF/DMARC, CAA).

Con 100-200 variantes generadas, resolverlas una por una sería
inviablemente lento: la inmensa mayoría NO existen, y cada intento fallido
tarda hasta el timeout completo antes de darse por vencido. Usamos un pool
de hilos para lanzarlas todas a la vez — al ser operaciones de red
(esperar respuesta del DNS), los hilos son una solución simple y
suficiente aquí, sin necesitar async/await en todo el proyecto.

`check_dns_bulk`/`resolve_ip` usan `socket` (solo A, una IP) porque para
typosquatting solo importa "¿existe o no?" con la máxima velocidad posible.
`get_dns_records` usa `dnspython` porque necesita tipos de registro que
`socket` no expone (MX, TXT, CAA) y todas las IPs, no solo la primera.
"""
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

import dns.resolver

from app.schemas.domain_analysis import DnsRecords

_DEFAULT_TIMEOUT = 2.5
_DEFAULT_MAX_WORKERS = 25


def _resolve_one(domain: str, timeout: float) -> str | None:
    try:
        socket.setdefaulttimeout(timeout)
        return socket.gethostbyname(domain)
    except (socket.gaierror, socket.timeout, OSError):
        return None


def resolve_ip(domain: str, timeout: float = _DEFAULT_TIMEOUT) -> str | None:
    """Resuelve un único dominio a su IP (o None). Para una sola resolución no hace falta el pool de hilos de check_dns_bulk."""
    return _resolve_one(domain, timeout)


def check_dns_bulk(
    domains: list[str],
    timeout: float = _DEFAULT_TIMEOUT,
    max_workers: int = _DEFAULT_MAX_WORKERS,
) -> dict[str, str | None]:
    """Devuelve {dominio: ip_o_None} para cada dominio de la lista."""
    results: dict[str, str | None] = {}
    if not domains:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_domain = {executor.submit(_resolve_one, d, timeout): d for d in domains}
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            results[domain] = future.result()

    return results


def _query(resolver: dns.resolver.Resolver, name: str, rdtype: str) -> list:
    """
    Una consulta de tipo concreto (MX/TXT/CAA...) puede fallar por motivos
    perfectamente normales y no relacionados entre sí: el dominio no tiene
    ningún registro de ese tipo (NoAnswer, lo más común: la mayoría de
    dominios no tienen CAA), o no existe en absoluto (NXDOMAIN). Ninguno de
    los dos es un fallo del análisis — simplemente no hay nada que reportar
    para ese tipo — así que se trata como lista vacía, no como error.
    """
    try:
        return list(resolver.resolve(name, rdtype))
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        return []


def get_dns_records(domain: str, timeout: float = _DEFAULT_TIMEOUT) -> DnsRecords:
    """
    Consulta completa de un dominio: todas las IPs a las que resuelve (no
    solo la primera) y las cabeceras de su propia configuración de correo
    (MX, SPF, DMARC) y CAA. Un dominio que dice ser un banco pero no tiene
    SPF/DMARC configurado en su propio DNS es un dato — no necesariamente
    concluyente por sí solo (muchos sitios legítimos pequeños tampoco lo
    tienen), pero se anota igual que el resto de señales.

    A diferencia de `resolve_ip`/`check_dns_bulk`, si el dominio no
    resuelve en absoluto (NXDOMAIN) SÍ se deja subir la excepción: eso es
    justo la señal principal a nivel de dominio, quien llama debe saberlo.
    """
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout

    all_ips = sorted({rdata.address for rdata in resolver.resolve(domain, "A")})

    mx_hosts = sorted({str(rdata.exchange).rstrip(".") for rdata in _query(resolver, domain, "MX")})

    # Cada TXT puede venir partido en varios "strings" (límite de 255 bytes por string);
    # se unen antes de buscar el prefijo v=spf1/v=DMARC1.
    txt_records = ["".join(s.decode() for s in rdata.strings) for rdata in _query(resolver, domain, "TXT")]
    has_spf = any(txt.lower().startswith("v=spf1") for txt in txt_records)

    dmarc_txt = ["".join(s.decode() for s in rdata.strings) for rdata in _query(resolver, f"_dmarc.{domain}", "TXT")]
    has_dmarc = any(txt.lower().startswith("v=dmarc1") for txt in dmarc_txt)

    caa_records = [f"{rdata.flags} {rdata.tag.decode()} {rdata.value.decode()}" for rdata in _query(resolver, domain, "CAA")]

    return DnsRecords(
        all_ips=all_ips,
        mx_hosts=mx_hosts,
        txt_records=txt_records,
        has_spf=has_spf,
        has_dmarc=has_dmarc,
        caa_records=caa_records,
    )
