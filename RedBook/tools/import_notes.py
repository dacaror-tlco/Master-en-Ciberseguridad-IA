"""Importa apuntes (.docx / .md) a docs/ y regenera el menú de mkdocs.yml.

Uso:  .venv\\Scripts\\python tools\\import_notes.py <carpeta_con_apuntes>

Clasifica cada archivo por palabras clave de su nombre (ver RULES),
convierte .docx a Markdown (imágenes incluidas) y genera:
  - una página por apunte en docs/<sección>/<subsección>/
  - índices de cada sección y el índice cronológico del máster
  - el bloque `nav:` de mkdocs.yml
"""
import re
import sys
import shutil
import unicodedata
from pathlib import Path

import mammoth
import yaml
from markdownify import markdownify

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MKDOCS = ROOT / "mkdocs.yml"

# (sección, subsección, título subsección, palabras clave) — gana la primera que encaje
RULES = [
    ("otros", "ia", "Inteligencia artificial", ["apuntes_ia", "ia hibrida", "vibecoding"]),
    ("blue-team", "analisis-trafico", "Análisis de tráfico", ["wireshark"]),
    ("metodologias", "estandares", "Estándares y clasificación", ["cvss", "cwe"]),
    ("otros", "informes", "Informes", ["report"]),
    ("red-team", "osint", "OSINT e ingeniería social", ["osint", "anonimato", "ingenieria"]),
    ("otros", "fundamentos", "Fundamentos", ["fundamentoslinux", "bash", "consolas", "introredes", "redestypos", "vbox"]),
    ("red-team", "maquinas", "Máquinas y prácticas", [
        "htb", "vaccine", "nibbles", "magic", "curling", "goodgames", "devel", "mrrobot",
        "reactor", "facultad", "rockstar", "robots", "casapaco", "nike", "webos", "academy", "oopsie",
    ]),
    ("red-team", "web", "Auditoría web", [
        "owasp", "sql", "ssti", "ssrf", "xxe", "lfi", "portswigger", "fuzz", "enumeracionweb",
        "cms", "wordpress", "burp", "file_upload", "bounty", "auditoriaweb",
    ]),
    ("red-team", "explotacion", "Explotación y escalada", ["explotacion", "escalada"]),
    ("red-team", "repasos", "Repasos", ["repaso"]),
]
DEFAULT = ("otros", "general", "General")

SECTIONS = {
    "metodologias": "Metodologías",
    "red-team": "Red Team",
    "blue-team": "Blue Team",
    "otros": "Otros conocimientos",
}

AUTHORS = ["Carlos Castillo", "Carlos Gómez Pintado", "Carlos Gómez", "Carlos Gomez Pintado",
           "Carlos Gomez", "Yuba González Parrilla", "Yuba"]


FIXES = {
    "Word Press": "WordPress", "Port Swigger": "PortSwigger", "Good Games": "GoodGames",
    "Mr Robot": "Mr. Robot", "Casa Paco": "CasaPaco", "Starting Point": "Starting Point",
}


def first_heading(body):
    m = re.search(r"^#{1,3}\s+(.+)$", body, flags=re.M)
    return m.group(1).strip("*_ ") if m else None


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return s


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")


def find_date(name):
    for pat, order in [
        (r"(\d{4})-(\d{2})-(\d{2})", "ymd"),
        (r"(\d{2})-(\d{2})-(\d{4})", "dmy"),
        (r"(?<!\d)(\d{2})(\d{2})(20\d{2})(?!\d)", "dmy"),
    ]:
        m = re.search(pat, name)
        if m:
            a, b, c = m.groups()
            y, mo, d = (a, b, c) if order == "ymd" else (c, b, a)
            return f"{y}-{mo}-{d}", m.group(0)
    return None, None


def make_title(stem):
    date, raw = find_date(stem)
    t = stem.replace(".md", "")
    if raw:
        t = t.replace(raw, " ")
    author = next((a for a in AUTHORS if norm(a) in norm(t.replace("_", " "))), None)
    for a in AUTHORS:
        t = re.sub(re.escape(a), " ", t, flags=re.I)
        t = re.sub(re.escape(a).replace(r"\ ", "_"), " ", t, flags=re.I)
    t = re.sub(r"^(Apuntes|Portada)[ _]", "", t, flags=re.I)
    t = t.replace("_", " ")
    t = re.sub(r"\b[vV]\d{3}\b", " ", t)
    t = re.sub(r"(?<=[a-záéíóúñ])(?=[A-Z])", " ", t)  # CamelCase -> palabras
    t = re.sub(r"(?<=[a-z])(?=\d)", " ", t)
    for a, b in FIXES.items():
        t = t.replace(a, b)
    t = re.sub(r"\s*[-—]\s*(?=[-—]|$)", " ", t)
    t = re.sub(r"^[\s\-—]+|[\s\-—]+$", "", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t, date, author


def classify(stem):
    n = norm(stem).replace(" ", "")
    n_sp = norm(stem)
    for sec, sub, sub_title, keys in RULES:
        if any(k.replace(" ", "") in n or k in n_sp for k in keys):
            return sec, sub, sub_title
    return DEFAULT


def convert_docx(path, img_dir, img_rel):
    counter = {"n": 0}

    def save_image(image):
        counter["n"] += 1
        ext = (image.content_type or "image/png").split("/")[-1].replace("jpeg", "jpg")
        name = f"img{counter['n']:03d}.{ext}"
        img_dir.mkdir(parents=True, exist_ok=True)
        with image.open() as src, open(img_dir / name, "wb") as dst:
            shutil.copyfileobj(src, dst)
        return {"src": f"{img_rel}/{name}"}

    with open(path, "rb") as f:
        html = mammoth.convert_to_html(f, convert_image=mammoth.images.img_element(save_image)).value
    text = markdownify(html, heading_style="ATX", bullets="-")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def collect(src):
    files = {}
    for p in sorted(src.rglob("*")):
        if p.suffix.lower() not in (".docx", ".md"):
            continue
        stem = re.sub(r"\.md$", "", p.stem)
        # si hay versión .md y .docx del mismo apunte, gana la .md
        if stem in files and files[stem].suffix.lower() == ".md":
            continue
        files[stem] = p
    return files


def main(src):
    src = Path(src)
    notes, used, titles = [], set(), set()
    for stem, path in collect(src).items():
        title, date, author = make_title(stem)
        sec, sub, sub_title = classify(stem)
        slug_base = slugify(title) or slugify(stem)
        slug = slug_base if slug_base not in used else f"{slug_base}-{date or len(used)}"
        used.add(slug)
        out_dir = DOCS / sec / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".docx":
            body = convert_docx(path, DOCS / "assets" / "img" / slug, f"../../assets/img/{slug}")
        else:
            body = path.read_text(encoding="utf-8")
        if not title:
            title = f"Sesión {date}" if date else (first_heading(body) or stem)
        if title in titles and date:
            title = f"{title} ({date})"
        titles.add(title)
        body = re.sub(r"\A---\n.*?\n---\n", "", body, flags=re.S)  # quita frontmatter previo

        meta = {"tags": [sub_title]}
        if date:
            meta["date"] = date
        if author:
            meta["author"] = author
        info = " · ".join(x for x in [date, author] if x)
        page = "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n"
        page += f"# {title}\n\n"
        if info:
            page += f'<p class="note-meta">{info}</p>\n\n'
        page += body + "\n"
        (out_dir / f"{slug}.md").write_text(page, encoding="utf-8")
        notes.append(dict(title=title, date=date, author=author, sec=sec, sub=sub,
                          sub_title=sub_title, rel=f"{sec}/{sub}/{slug}.md", src=path.name))
        print(f"[{sec}/{sub}] {title}")

    write_indexes(notes)
    write_nav(notes)
    print(f"\n{len(notes)} apuntes importados.")


def note_sort(n):
    return (n["date"] or "9999", n["title"])


def write_indexes(notes):
    groups = {}
    for n in notes:
        groups.setdefault((n["sec"], n["sub"], n["sub_title"]), []).append(n)

    for (sec, sub, sub_title), items in groups.items():
        lines = [f"# {sub_title}\n", "| Fecha | Apunte | Autor |", "|---|---|---|"]
        for n in sorted(items, key=note_sort):
            file = Path(n["rel"]).name
            lines.append(f"| {n['date'] or '—'} | [{n['title']}]({file}) | {n['author'] or '—'} |")
        (DOCS / sec / sub / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for sec, sec_title in SECTIONS.items():
        subs = sorted({(s, t) for (se, s, t) in groups if se == sec}, key=lambda x: x[1])
        idx = DOCS / sec / "index.md"
        if sec == "metodologias":
            continue  # índice escrito a mano
        lines = [f"# {sec_title}\n", '<div class="grid cards" markdown>\n']
        for sub, title in subs:
            count = len(groups[(sec, sub, title)])
            lines.append(f"-   **[{title}]({sub}/index.md)**\n\n    ---\n\n    {count} apuntes\n")
        lines.append("</div>")
        if not subs:
            lines = [f"# {sec_title}\n", '!!! info "Pendiente"\n    Aún no hay apuntes en esta sección.']
        idx.write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = ["# Apuntes del máster (cronológico)\n", "| Fecha | Apunte | Sección | Autor |", "|---|---|---|---|"]
    for n in sorted(notes, key=note_sort):
        lines.append(f"| {n['date'] or '—'} | [{n['title']}](../{n['rel']}) | {n['sub_title']} | {n['author'] or '—'} |")
    (DOCS / "master" / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def herramientas_nav():
    hdir = DOCS / "herramientas"
    cats = ["recon", "enum-red", "enum-web", "proxy", "explotacion",
            "credenciales", "post", "shells", "forense"]
    pages = ["herramientas/index.md"] + [f"herramientas/{c}.md" for c in cats
                                         if (hdir / f"{c}.md").exists()]
    if not hdir.exists():
        return {"Herramientas": "herramientas/index.md"}
    return {"Herramientas": pages}


def write_nav(notes):
    def sub_nav(sec):
        out = []
        subs = sorted({(n["sub"], n["sub_title"]) for n in notes
                       if n["sec"] == sec and n["sub"] not in ("fases", "walkthroughs")},
                      key=lambda x: x[1])
        for sub, title in subs:
            pages = [f"{sec}/{sub}/index.md"] + [
                {n["title"]: n["rel"]} for n in sorted(notes, key=note_sort) if n["sec"] == sec and n["sub"] == sub
            ]
            out.append({title: pages})
        return out

    fases = [{"Metodología por fases": "metodologias/index.md"},
             {"Selector de metodología": "metodologias/selector.md"}]
    fases_dir = DOCS / "metodologias" / "fases"
    # Las páginas de fases, si existen, en el orden del ciclo de auditoría
    fase_pages = []
    for slug in ["reconocimiento", "enumeracion", "analisis", "explotacion-web",
                 "explotacion-servicios", "post-explotacion", "informe"]:
        if (fases_dir / f"{slug}.md").exists():
            fase_pages.append(f"metodologias/fases/{slug}.md")
    if fase_pages:
        fases.append({"Fases": fase_pages})

    # Walkthroughs (sección propia, viven en red-team/walkthroughs)
    wdir = DOCS / "red-team" / "walkthroughs"
    walkthroughs_nav = None
    if wdir.exists():
        wpages = ["red-team/walkthroughs/index.md"] + [
            f"red-team/walkthroughs/{s}.md" for s in ("web", "windows", "linux")
            if (wdir / f"{s}.md").exists()]
        walkthroughs_nav = {"Walkthroughs": wpages}

    # Chuletas (sección propia)
    chuletas_dir = DOCS / "chuletas"
    chuletas_nav = None
    if chuletas_dir.exists():
        orden = ["reconocimiento-enumeracion", "explotacion", "sqli-union", "ssti", "ssrf",
                 "path-traversal", "osint-estego", "escalada", "forense", "fundamentos"]
        pags = ["chuletas/index.md"] + [f"chuletas/{s}.md" for s in orden
                                        if (chuletas_dir / f"{s}.md").exists()]
        chuletas_nav = {"Chuletas": pags}

    # Apuntes: agrupa las áreas y el máster para despejar el menú principal
    red_sub = [x for x in sub_nav("red-team") if "walkthroughs" not in str(x)]
    apuntes = [
        {"Red Team": ["red-team/index.md"] + red_sub},
        {"Blue Team": ["blue-team/index.md"] + sub_nav("blue-team")},
        {"Otros": ["otros/index.md"] + sub_nav("otros")},
        {"Módulos del máster": "master/index.md"},
    ]

    guia = "guia-maquina.md" if (DOCS / "guia-maquina.md").exists() else None

    nav = [{"Inicio": "index.md"}]
    if guia:
        nav.append({"Guía de máquina": guia})
    nav.append({"Metodología": fases + sub_nav("metodologias")})
    if walkthroughs_nav:
        nav.append(walkthroughs_nav)
    if chuletas_nav:
        nav.append(chuletas_nav)
    nav.append(herramientas_nav())
    nav.append({"Apuntes": apuntes})
    nav.append({"Etiquetas": "tags.md"})
    cfg = MKDOCS.read_text(encoding="utf-8")
    head = cfg.split("\nnav:", 1)[0].rstrip() + "\n\n"
    MKDOCS.write_text(head + yaml.safe_dump({"nav": nav}, allow_unicode=True, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
