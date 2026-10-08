---
tags:
- Auditoría web
---

# Fuzzing Parametros x 8

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD**

**Fuzzing de parámetros ocultos con x8 — Máquina rockstar**

Instructor: Carlos Gómez Pintado  ·  Julio 2026

*Entorno: máquina rockstar (HTB-style) · objetivo 192.168.52.139 · index.php*

# **Objetivos de la sesión**

* Entender qué es un **parámetro oculto** y por qué no aparece en el HTML ni en el código visible.

* Comprender el motor de descubrimiento de **x8** (learn → lotes → bisección) y por qué es rápido.

* Aplicar x8\_lite.py sobre index.php en POST para descubrir parámetros no documentados.

* Interpretar el baseline y la anomalía de respuesta (500 → 200\) como señal de hallazgo.

* Distinguir el fuzzing de **nombres** de parámetro del fuzzing de **valores**.

# **Conceptos clave**

## **¿Qué es un parámetro oculto?**

Un parámetro oculto es una variable de entrada (GET o POST) que el servidor **procesa internamente pero no expone** en ningún sitio: no está en el HTML, ni en los formularios, ni en los enlaces, ni en el código fuente que ve el cliente. La aplicación lo acepta y cambia su comportamiento cuando lo recibe, pero un usuario normal nunca sabría que existe.

La única forma de descubrirlos es **probar nombres a fuerza bruta** y detectar cuándo la respuesta del servidor se desvía de lo normal. Eso es el *fuzzing de parámetros*.

## **Fuzzing de nombres vs. fuzzing de valores**

Son dos cosas distintas que conviene no confundir:

* **Fuzzing de nombres** (lo de esta sesión): el diccionario contiene *nombres* de parámetro (admin, debug, backdoor...). Buscamos **cuál** acepta el servidor. Herramientas: x8, Arjun, x8\_lite.py.

* **Fuzzing de valores**: el nombre es fijo y probamos *valores* distintos (backdoor=FUZZ). Buscamos **qué valor** activa algo. Herramientas: ffuf, wfuzz, valfuzz.py.

| ℹ  Ampliación En esta sesión hicimos fuzzing de NOMBRES: descubrimos que existe el parámetro backdoor. El siguiente paso lógico es fuzzear su VALOR para ver qué hace. |
| :---- |

# **Desarrollo técnico**

## **El motor de x8 en cuatro fases**

x8\_lite.py (versión propia del script de Sh1Yo/x8) no prueba un parámetro por petición — sería lentísimo. Replica el motor de x8 en cuatro fases:

| 1\. LEARN — peticiones basura para aprender la respuesta normal (baseline) |
| :---: |

**↓**

| 2\. BATCH — meter 128 parámetros por petición, cada uno con valor único |
| :---: |

**↓**

| 3\. COMPARE — comparar contra el baseline: ¿cambia código, líneas o reflexión? |
| :---: |

**↓**

| 4\. BISECT — si el lote cambia algo, partirlo por la mitad hasta aislar el culpable |
| :---: |

## **Fase 1 — LEARN (aprender el baseline)**

El script manda 9 peticiones con parámetros aleatorios que el servidor no espera. Con eso fija cómo es una respuesta *normal*: su código de estado y qué líneas del cuerpo no cambian. En nuestra máquina el resultado fue:

| \[\*\] Baseline: code=500  lineas\_estables=1  dinamicas=0  refl\_base=0 |
| :---- |

El baseline quedó en **500 (Internal Server Error)**. Esto ya es una pista fuerte: index.php **procesa** el body POST y su código **revienta** cuando no encuentra el parámetro que busca. Una página que ignorase el input habría dado 200 siempre; ésta reacciona.

## **Fase 2+3 — BATCH y COMPARE (lotes grandes)**

El diccionario common.txt de dirb tiene **4613 palabras**. En vez de 4613 peticiones, el script las agrupa en lotes de 128 parámetros. Cada lote es UNA petición con 128 parámetros a la vez:

| POST /index.php lote0=x\&lote1=x& ... \&backdoor=x& ... \&lote127=x |
| :---- |

Cuando el lote que contiene backdoor llega al servidor, la respuesta pasa de 500 a 200\. El script sabe que *alguno* de esos 128 es el responsable, pero todavía no cuál.

## **Fase 4 — BISECT (búsqueda binaria)**

Aquí está la clave de la velocidad. El lote de 128 se parte en 64+64, se prueba cada mitad, se conserva la que sigue disparando el cambio, y se repite. En **log₂(128) ≈ 7 peticiones** se aísla el parámetro exacto:

| 128 → 64 → 32 → 16 → 8 → 4 → 2 → 1   (7 divisiones) |
| :---- |

Total del escaneo: \~37 lotes \+ unas pocas bisecciones ≈ **50-60 peticiones** en lugar de 4613\. Esa reducción es la razón de existir de x8.

## **El hallazgo**

| \[\*\] Objetivo : POST http://192.168.52.139/index.php \[\*\] Modo     : body/urlencode   params: 4613   lote\_max: 128   concurrencia: 15 \[\*\] Baseline: code=500  lineas\_estables=1  dinamicas=0  refl\_base=0 \[FOUND\] backdoor                     code=200  (code 500-\>200) \[+\] 1 parametro(s) encontrados:     backdoor |
| :---- |

Interpretación: cuando se envía POST index.php con un parámetro llamado backdoor, el servidor deja de dar error y responde **200 OK**. El código de index.php tiene una rama especial que se activa SOLO si ese parámetro existe. Eso es, literalmente, una **puerta trasera** — de ahí el nombre de la máquina (*rockstar*) y del parámetro.

| ✓  Por qué se detectó El motivo del hallazgo fue el cambio de código 500 \-\> 200. El script compara cada respuesta contra el baseline por tres criterios: código de estado, líneas del cuerpo que aparecen/desaparecen, y reflexiones del valor enviado. Aquí saltó el primero. |
| :---- |

# **Comandos importantes**

Comando ejecutado en la sesión (fuzzing de nombres sobre POST):

| python3 x8\_lite.py \-u http://192.168.52.139/index.php \-X POST \-w /usr/share/wordlists/dirb/common.txt \-m 128 \-c 15 |
| :---- |

Siguiente paso — fuzzing del VALOR de backdoor para ver qué acepta (con valfuzz.py):

| python3 valfuzz.py \-u http://192.168.52.139/index.php \-X POST \-d "backdoor=FUZZ" \-w /usr/share/wordlists/rockyou.txt \--match-keyword "uid=" |
| :---- |

Comprobación manual rápida con curl:

| curl \-X POST http://192.168.52.139/index.php \-d "backdoor=test" |
| :---- |

# **Herramientas utilizadas en la sesión**

| Herramienta | Objetivo | Fase de auditoría | Comando o uso visto | Nivel | Notas |
| :---- | :---- | :---- | :---- | :---- | :---- |
| x8 / x8\_lite.py | Descubrir parámetros ocultos | Enumeración web | python3 x8\_lite.py \-u URL \-X POST \-w lista | Practicada | Motor learn+lotes+bisección |
| valfuzz.py | Fuzzear el valor de un parámetro fijo | Enumeración / explotación | valfuzz.py \-d "backdoor=FUZZ" | Introducida | Estilo ffuf, marcador FUZZ |
| dirb (wordlist common.txt) | Diccionario de nombres | Enumeración web | /usr/share/wordlists/dirb/common.txt | Recurrente | 4613 entradas |
| curl | Petición manual de comprobación | Verificación | curl \-X POST URL \-d k=v | Recurrente | Confirma el hallazgo |

# **Riesgos, errores comunes y buenas prácticas**

| ⚠  Error visto en clase El error argument \-m/--max: invalid int value: 'c' aparece cuando se pegan los flags (\-mc 15 o \-m c). Cada flag lleva su valor separado: \-m 128 \-c 15. \-m siempre va seguido de un número. |
| :---- |
| **⚠  AVISO** Las rutas /usr/share/wordlists/... son de Linux (Kali/Parrot). En Windows NO existen: hay que descargar la wordlist y apuntar a su ruta real. Lanza el ataque desde la VM que esté en la misma red que el objetivo. |
| **✓  CORRECTO** Un baseline de 500 no es un fallo del escaneo: es información. Indica que la app procesa el input y falla sin el parámetro correcto. Es una señal fuerte de que hay algo que descubrir. |
| **⚠  RIESGO** Fuzzing solo contra objetivos autorizados (laboratorios, HTB, máquinas propias). Lanzar 50-60 peticiones con 128 parámetros cada una puede alterar o saturar un servicio real. |

# **Conexión con sesiones anteriores**

El fuzzing de parámetros se sitúa en la **fase de enumeración web**, la misma en la que ya usábamos Gobuster, ffuf o Feroxbuster. La diferencia de enfoque:

* **Feroxbuster / Gobuster** descubren *rutas y directorios* ocultos (/admin, /backup).

* **x8** descubre *parámetros* ocultos dentro de una ruta que ya conoces (index.php?backdoor=).

Son complementarios: primero encuentras los endpoints, luego fuzzeas los parámetros que cada endpoint acepta en secreto. El paso siguiente natural (fuzzear el valor con valfuzz.py, estilo ffuf/wfuzz) enlaza con el uso de Burp Intruder que ya vimos: misma idea de sustituir un valor por cada palabra de un diccionario.

# **Resumen final**

Se aplicó x8\_lite.py sobre index.php (POST) de la máquina *rockstar*. El script aprendió que la respuesta normal es un error 500, agrupó las 4613 palabras del diccionario en lotes de 128 parámetros, y detectó que el lote que contenía backdoor cambiaba la respuesta a 200\. Mediante bisección aisló ese parámetro en pocas peticiones. El resultado es el descubrimiento de un **parámetro oculto tipo puerta trasera**: index.php acepta backdoor y cambia su comportamiento al recibirlo. El siguiente objetivo es averiguar qué VALOR de backdoor desbloquea la funcionalidad (probablemente ejecución de comandos), lo que ya es fuzzing de valores.

# **Checklist de repaso**

1. Sé explicar qué es un parámetro oculto y por qué no se ve en el HTML.

2. Distingo fuzzing de nombres (x8) de fuzzing de valores (ffuf/valfuzz).

3. Entiendo las 4 fases de x8: learn, lotes, compare, bisect.

4. Sé por qué la bisección hace el escaneo rápido (log₂ en vez de lineal).

5. Interpreto el baseline y reconozco un cambio de código (500→200) como hallazgo.

6. Sé lanzar x8\_lite.py en POST con los flags \-m y \-c separados.

7. Tengo claro el siguiente paso: fuzzear el valor de backdoor.

# **Actualización del registro de herramientas**

Cambios respecto al registro acumulado tras esta sesión:

| Herramienta | Nivel |
| :---- | :---- |
| x8 / x8\_lite.py | Practicada (antes: Mencionada) |
| valfuzz.py | Introducida (nueva) |


