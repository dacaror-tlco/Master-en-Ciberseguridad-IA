"""Genera la sección Herramientas en docs/herramientas/.

Cada herramienta tiene una ficha (qué hace, cuándo se usa, enlace oficial) y,
automáticamente, enlaces a los apuntes del máster donde aparece. Reejecuta este
script cuando añadas apuntes para actualizar los "aparece en".

Uso:  .venv\\Scripts\\python tools\\build_tools.py
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "herramientas"

# Categorías (orden de aparición en la web)
CATS = [
    ("recon", "Reconocimiento y OSINT"),
    ("enum-red", "Enumeración de red y servicios"),
    ("enum-web", "Enumeración web y fuzzing"),
    ("proxy", "Proxys e interceptación"),
    ("explotacion", "Explotación"),
    ("credenciales", "Credenciales y hashes"),
    ("post", "Post-explotación y escalada"),
    ("shells", "Shells, acceso y transferencia"),
    ("forense", "Tráfico, forense y esteganografía"),
]

# name, categoría, detección (regex, case-insensitive), qué hace, cuándo se usa, url
TOOLS = [
    ("nmap", "enum-red", r"\bnmap\b",
     "Escáner de red: descubre hosts, puertos abiertos, servicios y versiones.",
     "Al principio de casi toda auditoría, para saber qué hay expuesto antes de atacar.",
     "https://nmap.org/"),
    ("dig", "recon", r"\bdig\b",
     "Cliente DNS para consultar registros (A, MX, TXT, NS, transferencias de zona).",
     "Reconocimiento DNS de un dominio y búsqueda de subdominios o fugas de información.",
     "https://linux.die.net/man/1/dig"),
    ("nslookup", "recon", r"nslookup",
     "Cliente DNS interactivo multiplataforma, alternativa básica a dig.",
     "Resolver nombres y comprobar registros DNS rápidamente, también en Windows.",
     "https://linux.die.net/man/1/nslookup"),
    ("theHarvester", "recon", r"theharvester|the harvester",
     "Recopila correos, subdominios, hosts y nombres a partir de fuentes públicas.",
     "Fase OSINT: dibujar la superficie expuesta de una organización sin tocarla.",
     "https://github.com/laramies/theHarvester"),
    ("Sublist3r", "recon", r"sublist3r",
     "Enumera subdominios usando buscadores y fuentes públicas.",
     "Descubrir subdominios de un objetivo en reconocimiento pasivo.",
     "https://github.com/aboul3la/Sublist3r"),
    ("Amass", "recon", r"\bamass\b",
     "Mapeo de superficie de ataque y enumeración de subdominios (OWASP).",
     "Reconocimiento de dominios amplio, combinando fuentes pasivas y activas.",
     "https://github.com/owasp-amass/amass"),
    ("exiftool", "forense", r"exiftool",
     "Lee y edita metadatos de archivos (imágenes, PDFs, documentos).",
     "OSINT sobre documentos filtrados y análisis de evidencias o retos de stego.",
     "https://exiftool.org/"),

    ("enum4linux", "enum-red", r"enum4linux",
     "Enumera información de SMB/Windows: usuarios, grupos, shares, políticas.",
     "Tras detectar SMB (445/139) para listar recursos y cuentas.",
     "https://github.com/CiscoCXSecurity/enum4linux"),
    ("smbclient", "enum-red", r"smbclient",
     "Cliente SMB para listar y acceder a recursos compartidos de red.",
     "Conectarte a shares SMB encontrados y revisar/descargar ficheros.",
     "https://www.samba.org/"),
    ("WhatWeb", "enum-web", r"whatweb",
     "Fingerprinting web: identifica tecnologías, CMS, servidores y versiones.",
     "Nada más encontrar un servicio web, para saber contra qué te enfrentas.",
     "https://github.com/urbanadventurer/WhatWeb"),
    ("Wappalyzer", "enum-web", r"wappalyzer",
     "Identifica el stack tecnológico de un sitio (CMS, frameworks, librerías).",
     "Fingerprinting rápido desde el navegador durante la enumeración web.",
     "https://www.wappalyzer.com/"),
    ("Nikto", "enum-web", r"\bnikto\b",
     "Escáner de vulnerabilidades web conocidas y ficheros/configuraciones peligrosas.",
     "Barrido inicial de un servidor web para detectar problemas evidentes.",
     "https://github.com/sullo/nikto"),

    ("ffuf", "enum-web", r"\bffuf\b",
     "Fuzzer web rápido para directorios, ficheros, parámetros y subdominios.",
     "Descubrir contenido oculto y parámetros cuando necesitas velocidad y filtros finos.",
     "https://github.com/ffuf/ffuf"),
    ("feroxbuster", "enum-web", r"feroxbuster",
     "Descubridor de contenido web recursivo y rápido.",
     "Enumeración de directorios con recursión automática sobre lo que va encontrando.",
     "https://github.com/epi052/feroxbuster"),
    ("gobuster", "enum-web", r"gobuster",
     "Fuerza bruta de directorios, DNS y vhosts.",
     "Enumeración de rutas y subdominios como alternativa sencilla a ffuf.",
     "https://github.com/OJ/gobuster"),
    ("dirsearch", "enum-web", r"dirsearch",
     "Fuerza bruta de rutas y ficheros web con diccionarios.",
     "Descubrir paneles, backups y endpoints ocultos en un sitio.",
     "https://github.com/maurosoria/dirsearch"),
    ("dirb", "enum-web", r"\bdirb\b",
     "Escáner clásico de contenido web por diccionario.",
     "Enumeración de directorios básica cuando no hay nada más a mano.",
     "https://www.kali.org/tools/dirb/"),
    ("wfuzz", "enum-web", r"\bwfuzz\b",
     "Fuzzer web para parámetros, cabeceras, formularios y rutas.",
     "Pruebas de fuzzing donde controlas con detalle el punto de inyección.",
     "https://github.com/xmendez/wfuzz"),
    ("x8", "enum-web", r"\bx8\b",
     "Descubridor de parámetros HTTP ocultos.",
     "Encontrar parámetros no documentados que amplían la superficie de ataque.",
     "https://github.com/Sh1Yo/x8"),
    ("CeWL", "enum-web", r"\bcewl\b",
     "Genera diccionarios a partir de las palabras de un sitio web.",
     "Crear wordlists a medida del objetivo para fuzzing o ataque de credenciales.",
     "https://github.com/digininja/CeWL"),
    ("SecLists", "enum-web", r"seclists",
     "Colección de diccionarios (rutas, usuarios, contraseñas, payloads).",
     "Fuente de wordlists para fuzzing, fuerza bruta y pruebas de inyección.",
     "https://github.com/danielmiessler/SecLists"),
    ("WPScan", "enum-web", r"wpscan",
     "Escáner específico de WordPress: plugins, temas, usuarios y vulnerabilidades.",
     "Cuando el fingerprinting revela un WordPress.",
     "https://wpscan.com/"),

    ("Burp Suite", "proxy", r"burp\s*suite|\bburp\b",
     "Proxy de interceptación web: inspecciona, modifica y repite peticiones (Repeater, Intruder).",
     "Trabajo manual sobre una aplicación web: probar inyecciones, lógica y autenticación.",
     "https://portswigger.net/burp"),
    ("FoxyProxy", "proxy", r"foxyproxy",
     "Extensión de navegador para cambiar de proxy con un clic.",
     "Enrutar el tráfico del navegador hacia Burp y volver a la normalidad rápido.",
     "https://addons.mozilla.org/firefox/addon/foxyproxy-standard/"),

    ("sqlmap", "explotacion", r"sqlmap",
     "Automatiza la detección y explotación de inyección SQL.",
     "Tras confirmar (o sospechar) SQLi, para extraer datos y enumerar la base de datos.",
     "https://sqlmap.org/"),
    ("Metasploit", "explotacion", r"metasploit|msfconsole|msfvenom",
     "Framework de explotación: módulos de exploits, payloads y post-explotación.",
     "Explotar servicios con exploit conocido y generar payloads (msfvenom).",
     "https://www.metasploit.com/"),
    ("searchsploit", "explotacion", r"searchsploit",
     "Buscador local de Exploit-DB desde la terminal.",
     "Buscar exploits públicos para la versión concreta de un servicio.",
     "https://gitlab.com/exploit-database/exploitdb"),
    ("Exploit-DB", "explotacion", r"exploit-?db",
     "Base de datos pública de exploits y PoCs.",
     "Consultar y descargar exploits para vulnerabilidades conocidas.",
     "https://www.exploit-db.com/"),
    ("GTFOBins", "post", r"gtfobins",
     "Catálogo de binarios Unix que pueden abusarse (sudo, SUID, capabilities) para escalar o salir de restricciones.",
     "Tras obtener acceso, para ver cómo convertir un binario permitido en escalada de privilegios.",
     "https://gtfobins.github.io/"),
    ("LOLBAS", "post", r"lolbas",
     "Equivalente de GTFOBins para binarios y scripts legítimos de Windows.",
     "Escalada y living-off-the-land en entornos Windows.",
     "https://lolbas-project.github.io/"),
    ("linPEAS", "post", r"linpeas",
     "Script que enumera el sistema Linux buscando vías de escalada de privilegios.",
     "Justo después de conseguir shell en Linux, para encontrar configuraciones débiles.",
     "https://github.com/peass-ng/PEASS-ng"),
    ("winPEAS", "post", r"winpeas",
     "Equivalente de linPEAS para enumeración de escalada en Windows.",
     "Tras obtener shell en Windows, para localizar vectores de escalada.",
     "https://github.com/peass-ng/PEASS-ng"),
    ("pspy", "post", r"\bpspy\b",
     "Observa procesos y tareas cron en Linux sin privilegios.",
     "Detectar procesos o cron ejecutados por root como vía de escalada.",
     "https://github.com/DominicBreuker/pspy"),

    ("Hydra", "credenciales", r"\bhydra\b",
     "Fuerza bruta de credenciales contra muchos protocolos (SSH, FTP, HTTP, etc.).",
     "Ataque de credenciales en línea cuando hay un servicio de login expuesto.",
     "https://github.com/vanhauser-thc/thc-hydra"),
    ("John the Ripper", "credenciales", r"\bjohn\b|john the ripper",
     "Crackeador de contraseñas y hashes offline.",
     "Romper hashes obtenidos (shadow, zip, etc.) usando diccionario o reglas.",
     "https://www.openwall.com/john/"),
    ("hashcat", "credenciales", r"hashcat",
     "Crackeador de hashes acelerado por GPU.",
     "Romper hashes offline a gran velocidad con grandes diccionarios o fuerza bruta.",
     "https://hashcat.net/hashcat/"),
    ("hashid", "credenciales", r"hashid|hash-identifier",
     "Identifica el tipo de un hash.",
     "Antes de crackear, para saber qué algoritmo y modo usar en john/hashcat.",
     "https://github.com/psypanda/hashID"),
    ("CrackMapExec / NetExec", "credenciales", r"crackmapexec|netexec|\bnxc\b",
     "Navaja suiza para redes Windows/AD: valida credenciales, enumera y ejecuta sobre SMB/WinRM.",
     "Movimiento y validación de credenciales en entornos Windows.",
     "https://github.com/Pennyw0rth/NetExec"),
    ("Impacket", "credenciales", r"impacket",
     "Colección de scripts Python para protocolos de red (SMB, Kerberos, etc.).",
     "Operaciones sobre servicios Windows: psexec, secretsdump, relays, tickets.",
     "https://github.com/fortra/impacket"),
    ("Responder", "credenciales", r"responder",
     "Envenena LLMNR/NBT-NS/mDNS para capturar hashes de autenticación en red local.",
     "Dentro de una red Windows, para capturar credenciales NTLM.",
     "https://github.com/lgandx/Responder"),

    ("evil-winrm", "shells", r"evil-?winrm",
     "Cliente WinRM pensado para pentesting en Windows.",
     "Obtener shell remota en Windows cuando tienes credenciales y WinRM (5985).",
     "https://github.com/Hackplayers/evil-winrm"),
    ("Netcat", "shells", r"\bnc\b|netcat",
     "Utilidad de red para leer/escribir por TCP/UDP; sirve de listener de shells.",
     "Recibir reverse shells y transferencias puntuales.",
     "https://linux.die.net/man/1/nc"),
    ("socat", "shells", r"\bsocat\b",
     "Relé de datos entre puntos; crea shells más estables que netcat.",
     "Shells totalmente interactivas (TTY) y túneles.",
     "http://www.dest-unreach.org/socat/"),
    ("revshells.com", "shells", r"revshells|reverse shell generator",
     "Generador web de comandos de reverse shell en muchos lenguajes.",
     "Para obtener rápido el comando de shell inversa adaptado al entorno destino.",
     "https://www.revshells.com/"),
    ("ssh", "shells", r"\bssh\b",
     "Cliente de acceso remoto seguro; también hace túneles y port-forwarding.",
     "Acceso con credenciales/clave y pivoting entre redes.",
     "https://www.openssh.com/"),
    ("curl", "shells", r"\bcurl\b",
     "Cliente HTTP de línea de comandos.",
     "Lanzar y afinar peticiones web manualmente, probar endpoints y payloads.",
     "https://curl.se/"),
    ("wget", "shells", r"\bwget\b",
     "Descargador de archivos por HTTP/FTP.",
     "Traer herramientas o ficheros al objetivo desde la terminal.",
     "https://www.gnu.org/software/wget/"),
    ("python http.server", "shells", r"http\.server",
     "Servidor HTTP improvisado de una línea.",
     "Servir archivos para transferirlos a la máquina víctima.",
     "https://docs.python.org/3/library/http.server.html"),
    ("git-dumper", "shells", r"git-?dumper",
     "Descarga un repositorio Git expuesto en un sitio web.",
     "Cuando encuentras /.git accesible, para recuperar código y secretos.",
     "https://github.com/arthaud/git-dumper"),

    ("Wireshark", "forense", r"wireshark",
     "Analizador de tráfico de red con interfaz gráfica.",
     "Inspeccionar capturas, seguir flujos y analizar protocolos (más Blue Team).",
     "https://www.wireshark.org/"),
    ("tcpdump", "forense", r"tcpdump",
     "Captura de tráfico de red por línea de comandos.",
     "Capturar paquetes en servidores sin entorno gráfico.",
     "https://www.tcpdump.org/"),
    ("steghide", "forense", r"steghide",
     "Oculta y extrae datos dentro de imágenes y audio (esteganografía).",
     "Retos de stego y análisis de ficheros con información oculta.",
     "https://steghide.sourceforge.net/"),
    ("binwalk", "forense", r"binwalk",
     "Analiza y extrae contenido incrustado en ficheros binarios.",
     "Buscar archivos o firmware escondidos dentro de otro fichero.",
     "https://github.com/ReFirmLabs/binwalk"),
]


def note_title(md):
    for line in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#\s+(.*)", line)
        if m:
            return re.sub(r"[*`]", "", m.group(1)).strip()
    return md.stem


def scan_notes():
    notes = []
    for md in sorted(DOCS.rglob("*.md")):
        if md.name == "index.md" or md.parts[md.parts.index("docs") + 1] in ("metodologias", "herramientas"):
            # metodologias/herramientas son generados; no son apuntes de origen salvo estandares
            if "estandares" not in md.as_posix():
                continue
        notes.append((md.relative_to(DOCS).as_posix(), note_title(md),
                      md.read_text(encoding="utf-8").lower()))
    return notes


def appears_in(rx, notes):
    cre = re.compile(rx, re.I)
    return [(rel, title) for rel, title, text in notes if cre.search(text)]


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    notes = scan_notes()
    cat_names = dict(CATS)
    by_cat = {slug: [] for slug, _ in CATS}
    for name, cat, rx, what, when, url in TOOLS:
        hits = appears_in(rx, notes)
        by_cat.setdefault(cat, []).append((name, what, when, url, hits))

    # Página por categoría
    for slug, title in CATS:
        items = sorted(by_cat[slug], key=lambda x: x[0].lower())
        lines = [f"# {title}\n"]
        for name, what, when, url, hits in items:
            lines.append(f"## {name}")
            lines.append(f"[:material-open-in-new: Sitio oficial]({url})\n")
            lines.append(f"**Qué hace.** {what}\n")
            lines.append(f"**Cuándo se usa.** {when}\n")
            if hits:
                refs = ", ".join(f"[{t}](../{r})" for r, t in hits[:10])
                extra = f" (+{len(hits) - 10})" if len(hits) > 10 else ""
                lines.append(f"**Aparece en.** {refs}{extra}\n")
        (OUT / f"{slug}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    # Índice general
    lines = ["# Herramientas\n",
             "Catálogo de herramientas vistas en el máster o de uso habitual, con qué hacen, "
             "cuándo se usan y los apuntes donde aparecen. Organizadas por fase de la auditoría.\n",
             '<div class="grid cards" markdown>\n']
    for slug, title in CATS:
        n = len(by_cat[slug])
        tools = ", ".join(t[0] for t in sorted(by_cat[slug], key=lambda x: x[0].lower()))
        lines.append(f"-   **[{title}]({slug}.md)**\n\n    ---\n\n    {tools}\n")
    lines.append("</div>")
    (OUT / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    total = sum(len(v) for v in by_cat.values())
    linked = sum(1 for *_ , h in [t for v in by_cat.values() for t in v] if h)
    print(f"Herramientas: {total} fichas, {linked} enlazadas a apuntes, {len(CATS)} categorías.")
    return [slug for slug, _ in CATS]


if __name__ == "__main__":
    build()
