"""
core/parser.py — Parser del XML de salida de nmap.
Extrae hosts, puertos, servicios, detección de SO y resultados de scripts NSE.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class NmapHost:
    ip: str
    hostnames: list[str] = field(default_factory=list)
    state: str = "unknown"
    mac: str = ""
    mac_vendor: str = ""

    # Puertos: lista de dicts con portid, protocol, state, service, version, extrainfo, scripts
    ports: list[dict] = field(default_factory=list)

    # Detección de SO
    os_name: str = ""
    os_matches: list[dict] = field(default_factory=list)   # {name, accuracy, cpe}

    # Scripts a nivel de host
    host_scripts: list[dict] = field(default_factory=list)  # {id, output}

    # Traceroute
    traceroute: list[dict] = field(default_factory=list)    # {ttl, ip, rtt}


class NmapParser:
    """Parsea el XML generado por nmap -oX y devuelve lista de NmapHost."""

    def parse(self, xml_content: str) -> list[NmapHost]:
        if not xml_content.strip():
            return []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            return []

        hosts = []
        for host_el in root.findall("host"):
            h = self._parse_host(host_el)
            hosts.append(h)
        return hosts

    # ── Host ──────────────────────────────────────────────────────────────────

    def _parse_host(self, el: ET.Element) -> NmapHost:
        host = NmapHost(ip=self._get_ip(el))
        host.state = self._get_state(el)
        host.hostnames = self._get_hostnames(el)
        host.mac, host.mac_vendor = self._get_mac(el)
        host.ports = self._get_ports(el)
        host.os_name, host.os_matches = self._get_os(el)
        host.host_scripts = self._get_host_scripts(el)
        host.traceroute = self._get_traceroute(el)
        return host

    def _get_ip(self, el: ET.Element) -> str:
        for addr in el.findall("address"):
            if addr.get("addrtype") in ("ipv4", "ipv6"):
                return addr.get("addr", "")
        return ""

    def _get_state(self, el: ET.Element) -> str:
        status = el.find("status")
        return status.get("state", "unknown") if status is not None else "unknown"

    def _get_hostnames(self, el: ET.Element) -> list[str]:
        names = []
        hn_el = el.find("hostnames")
        if hn_el is not None:
            for hn in hn_el.findall("hostname"):
                name = hn.get("name", "")
                if name:
                    names.append(name)
        return names

    def _get_mac(self, el: ET.Element) -> tuple[str, str]:
        for addr in el.findall("address"):
            if addr.get("addrtype") == "mac":
                return addr.get("addr", ""), addr.get("vendor", "")
        return "", ""

    # ── Puertos ───────────────────────────────────────────────────────────────

    def _get_ports(self, el: ET.Element) -> list[dict]:
        ports = []
        ports_el = el.find("ports")
        if ports_el is None:
            return ports

        for port_el in ports_el.findall("port"):
            p: dict = {
                "portid":    port_el.get("portid", ""),
                "protocol":  port_el.get("protocol", ""),
                "state":     "",
                "service":   "",
                "product":   "",
                "version":   "",
                "extrainfo": "",
                "cpe":       "",
                "scripts":   [],
            }

            state_el = port_el.find("state")
            if state_el is not None:
                p["state"] = state_el.get("state", "")
                p["reason"] = state_el.get("reason", "")

            svc_el = port_el.find("service")
            if svc_el is not None:
                p["service"]   = svc_el.get("name", "")
                p["product"]   = svc_el.get("product", "")
                p["version"]   = self._build_version_string(svc_el)
                p["extrainfo"] = svc_el.get("extrainfo", "")
                cpe_el = svc_el.find("cpe")
                if cpe_el is not None:
                    p["cpe"] = cpe_el.text or ""

            p["scripts"] = self._get_scripts(port_el)
            ports.append(p)

        return ports

    def _build_version_string(self, svc_el: ET.Element) -> str:
        parts = [
            svc_el.get("product", ""),
            svc_el.get("version", ""),
            svc_el.get("extrainfo", ""),
        ]
        return " ".join(p for p in parts if p).strip()

    # ── Scripts ───────────────────────────────────────────────────────────────

    def _get_scripts(self, el: ET.Element) -> list[dict]:
        scripts = []
        for s in el.findall("script"):
            scripts.append({
                "id":     s.get("id", ""),
                "output": s.get("output", "").strip(),
            })
        return scripts

    def _get_host_scripts(self, el: ET.Element) -> list[dict]:
        hs_el = el.find("hostscript")
        if hs_el is None:
            return []
        return self._get_scripts(hs_el)

    # ── OS ────────────────────────────────────────────────────────────────────

    def _get_os(self, el: ET.Element) -> tuple[str, list[dict]]:
        os_el = el.find("os")
        if os_el is None:
            return "", []

        matches = []
        best_name = ""
        for m in os_el.findall("osmatch"):
            name = m.get("name", "")
            accuracy = m.get("accuracy", "0")
            cpes = [c.text or "" for c in m.findall(".//cpe")]
            matches.append({
                "name": name,
                "accuracy": accuracy,
                "cpe": ", ".join(cpes),
            })
            if not best_name:
                best_name = name

        matches.sort(key=lambda x: int(x.get("accuracy", 0)), reverse=True)
        return best_name, matches

    # ── Traceroute ────────────────────────────────────────────────────────────

    def _get_traceroute(self, el: ET.Element) -> list[dict]:
        tr_el = el.find("trace")
        if tr_el is None:
            return []
        hops = []
        for hop in tr_el.findall("hop"):
            hops.append({
                "ttl": hop.get("ttl", ""),
                "ip":  hop.get("ipaddr", ""),
                "rtt": hop.get("rtt", ""),
            })
        return hops
