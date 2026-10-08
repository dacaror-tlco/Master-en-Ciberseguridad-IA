"""Genera la sección Metodología a partir de los apuntes ya importados en docs/.

No inventa contenido: localiza en cada apunte las secciones de metodología, fases,
flujo y checklist, las reparte por fases de una auditoría y escribe páginas que
enlazan a tus propios apuntes.

Uso:  .venv\\Scripts\\python tools\\build_methodology.py
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MET = DOCS / "metodologias"

# Fases del ciclo de una auditoría. (slug, título, objetivo en una línea, patrones)
# Un apunte se asocia a una fase si su nombre o sus encabezados casan con los patrones.
PHASES = [
    ("reconocimiento", "1 · Reconocimiento", "Reunir información del objetivo sin tocarlo (pasivo) o con contacto mínimo.",
     ["osint", "reconocimiento", "anonimato", "superficie"]),
    ("enumeracion", "2 · Enumeración", "Descubrir hosts, puertos, servicios, tecnologías, rutas y parámetros.",
     ["enumeracion", "fingerprint", "escaneo de puertos", "nmap", "fuzzing", "subdominios", "directorios"]),
    ("analisis", "3 · Análisis de vulnerabilidades", "Clasificar y priorizar hallazgos (OWASP, CWE, CVE, CVSS).",
     ["owasp", "cvss", "cwe", "cve", "clasific"]),
    ("explotacion-web", "4a · Explotación — Web", "Abusar de vulnerabilidades de aplicación web para obtener acceso.",
     ["sqli", "sql injection", "ssti", "ssrf", "lfi", "path traversal", "xxe", "file upload",
      "command injection", "burp", "cms", "wordpress", "auditoria web", "api"]),
    ("explotacion-servicios", "4b · Explotación — Servicios", "Abusar de servicios de red y software vulnerable.",
     ["servicios", "nfs", "ftp", "smb", "responder"]),
    ("post-explotacion", "5 · Post-explotación y escalada", "Consolidar el acceso y elevar privilegios.",
     ["escalada", "post-explotacion", "privilegios", "reverse shell", "estabiliz"]),
    ("informe", "6 · Informe y evidencias", "Documentar hallazgos, impacto, cadenas de ataque y remediación.",
     ["report", "informe", "evidencia", "hallazgos"]),
]

SECTION_RE = re.compile(r"(metodolog|^\W*fase\s|flujo|checklist|secuencia de trabajo|"
                        r"vectores|cadena de|cadena de ataque|cadena de la)", re.I)
HEAD_RE = re.compile(r"^(#{1,3})\s+(.*)$")


def clean_heading(s):
    return re.sub(r"^[\s*#`①-⓿\d.\-—)]+", "", s).strip(" *`—-")


def read_title(md):
    for line in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#\s+(.*)", line)
        if m:
            return clean_heading(m.group(1))
    return md.stem


def scan():
    """Devuelve lista de (relpath, titulo, [secciones_metodologia], texto_para_match)."""
    notes = []
    GENERATED = {(MET / "index.md"), (MET / "selector.md")}
    for md in sorted(DOCS.rglob("*.md")):
        if md.name == "index.md" or md in GENERATED or (MET / "fases") in md.parents:
            continue
        text = md.read_text(encoding="utf-8")
        secs = [clean_heading(m.group(2)) for line in text.splitlines()
                if (m := HEAD_RE.match(line)) and SECTION_RE.search(clean_heading(m.group(2)))]
        rel = md.relative_to(DOCS).as_posix()
        title = read_title(md)
        # Emparejar solo por ruta + título + encabezados (no por el cuerpo: da falsos positivos)
        hay = (rel + " " + title + " " + " ".join(secs)).lower()
        notes.append((rel, title, secs, hay))
    return notes


def phase_of(hay, secs):
    joined = (hay + " " + " ".join(secs)).lower()
    out = []
    for slug, _t, _g, pats in PHASES:
        if any(p in joined for p in pats):
            out.append(slug)
    return out


def rel_link(src_rel):
    # enlaces desde docs/metodologias/fases/<x>.md hacia docs/<src_rel>
    return "../../" + src_rel


def build():
    (MET / "fases").mkdir(parents=True, exist_ok=True)
    notes = scan()
    by_phase = {slug: [] for slug, *_ in PHASES}
    for rel, title, secs, hay in notes:
        for slug in phase_of(hay, secs):
            by_phase[slug].append((rel, title, secs))

    # Página por fase
    for slug, title, goal, _pats in PHASES:
        items = sorted(by_phase[slug], key=lambda x: x[1].lower())
        lines = [f"# {title}\n", f"> {goal}\n"]
        if not items:
            lines.append('!!! info "Sin apuntes todavía"\n    Aún no hay apuntes asociados a esta fase.')
        else:
            lines.append(f"Apuntes del máster que cubren esta fase ({len(items)}):\n")
            for rel, ntitle, secs in items:
                lines.append(f"## [{ntitle}]({rel_link(rel)})")
                for s in secs[:6]:
                    lines.append(f"- {s}")
                lines.append("")
        (MET / "fases" / f"{slug}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    build_index(by_phase)
    build_selector(notes)
    print(f"Metodología generada: {len(PHASES)} fases, {len(notes)} apuntes analizados.")
    return [slug for slug, *_ in PHASES], [(slug, t) for slug, t, *_ in PHASES]


def build_index(by_phase):
    lines = ["# Metodologías\n",
             "Ciclo de una auditoría organizado por fases. Cada fase enlaza a los apuntes "
             "del máster que la desarrollan. Para decidir qué aplicar ante un caso concreto, "
             "usa el [Selector de metodología](selector.md).\n",
             "```mermaid",
             "flowchart LR"]
    ids = [slug for slug, *_ in PHASES]
    labels = {slug: t.replace(" · ", ". ") for slug, t, *_ in PHASES}
    # cadena principal (4a y 4b en paralelo)
    lines.append(f'  R["{labels["reconocimiento"]}"] --> E["{labels["enumeracion"]}"]')
    lines.append(f'  E --> A["{labels["analisis"]}"]')
    lines.append(f'  A --> W["{labels["explotacion-web"]}"]')
    lines.append(f'  A --> S["{labels["explotacion-servicios"]}"]')
    lines.append(f'  W --> P["{labels["post-explotacion"]}"]')
    lines.append(f'  S --> P')
    lines.append(f'  P --> I["{labels["informe"]}"]')
    lines.append("```\n")
    lines.append('<div class="grid cards" markdown>\n')
    for slug, title, goal, _ in PHASES:
        n = len(by_phase[slug])
        lines.append(f"-   **[{title}](fases/{slug}.md)**\n\n    ---\n\n    {goal}\n\n    *{n} apuntes*\n")
    lines.append("</div>")
    (MET / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_selector(notes):
    """Tabla situación → apuntes, a partir de disparadores detectados en los apuntes."""
    TRIGGERS = [
        ("Puerto 80/443 — aplicación web", ["auditoria web", "enumeracion web", "owasp", "burp"]),
        ("Formulario / parámetro sospechoso de SQL", ["sqli", "sql injection"]),
        ("Plantillas del lado servidor (SSTI)", ["ssti"]),
        ("La app hace peticiones a URLs (SSRF)", ["ssrf"]),
        ("Lectura de ficheros / rutas (LFI / Path Traversal)", ["lfi", "path traversal", "xxe"]),
        ("Subida de archivos", ["file upload"]),
        ("CMS / WordPress detectado", ["cms", "wordpress"]),
        ("API REST", ["api"]),
        ("Necesito fuzzear rutas o parámetros", ["fuzzing"]),
        ("Puerto 21 FTP / 445 SMB / NFS", ["ftp", "smb", "nfs", "servicios"]),
        ("Relay NTLM / Responder", ["responder"]),
        ("Ya tengo shell: escalar privilegios", ["escalada", "privilegios"]),
        ("Información previa del objetivo (OSINT)", ["osint", "superficie", "anonimato"]),
        ("Clasificar y puntuar un hallazgo", ["cvss", "cwe", "cve", "owasp"]),
        ("Redactar el informe", ["report", "informe", "evidencia"]),
    ]
    def match(pats):
        res = []
        for rel, title, secs, hay in notes:
            if any(p in hay for p in pats):
                res.append((rel, title))
        return res[:6]

    lines = ["# Selector de metodología\n",
             "Localiza tu situación y salta a los apuntes del máster que explican cómo proceder.\n",
             "| Situación | Apuntes recomendados |", "|---|---|"]
    for sit, pats in TRIGGERS:
        hits = match(pats)
        cell = "<br>".join(f"[{t}](../{r})" for r, t in hits) if hits else "—"
        lines.append(f"| {sit} | {cell} |")
    (MET / "selector.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
