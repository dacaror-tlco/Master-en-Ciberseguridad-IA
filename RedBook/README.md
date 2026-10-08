# RedBook

Base de conocimiento del máster, generada con [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

## Estructura

```
mkdocs.yml          # configuración y menú (nav, generado)
docs/
  index.md          # portada / lanzadera (manual)
  guia-maquina.md   # "¿por dónde tiro?" — guía operativa por puerto/servicio (manual)
  metodologias/     # metodología por fases + selector (generado)
  red-team/
    walkthroughs/   # máquinas resueltas (web/windows/linux) — manual
  blue-team/
  otros/
  chuletas/         # referencias rápidas por técnica — manual
  herramientas/     # catálogo de herramientas (generado)
  master/           # índice por módulos
  tags.md           # índice automático de etiquetas
```

Menú principal: **Inicio · Guía de máquina · Metodología · Walkthroughs · Chuletas ·
Herramientas · Apuntes**.

Se editan a mano: `index.md`, `guia-maquina.md`, `walkthroughs/`, `chuletas/`.
Se regeneran con los scripts de `tools/`: `metodologias/`, `herramientas/` y el `nav`.

Para añadir contenido: crea un `.md` en la carpeta que toque y añádelo a `nav` en `mkdocs.yml`.
Las etiquetas se ponen al principio del archivo:

```markdown
---
tags:
  - modulo-1
---
# Título
```

## Importar apuntes (.docx / .md)

```
.venv\Scripts\python tools\import_notes.py <carpeta_con_apuntes>
```

Convierte los `.docx` a Markdown (con imágenes), los clasifica por palabras clave del
nombre de archivo (`RULES` en `tools/import_notes.py`) y regenera índices y el `nav` de `mkdocs.yml`.

## Regenerar secciones automáticas

```
.venv\Scripts\python tools\build_methodology.py   # Metodología por fases + selector
.venv\Scripts\python tools\build_tools.py          # Catálogo de herramientas
```

Ambos leen los apuntes de `docs/` y actualizan sus secciones y los enlaces "aparece en".
El catálogo de herramientas se edita en la lista `TOOLS` de `tools/build_tools.py`.

## Ver en local (Windows)

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\mkdocs serve
```

Abre http://127.0.0.1:8000 (se recarga sola al guardar).

## Desplegar en la Raspberry Pi (Docker, arm64)

```
docker compose up -d --build
```

Queda en `http://<ip-de-la-raspberry>:8080`. Tras añadir contenido, repite el mismo comando.

### Sin Docker

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs build
```

Sirve la carpeta `site/` con nginx, o con `python3 -m http.server 8080 -d site`.
