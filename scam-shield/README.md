# ScamShield

Herramienta de recolección de evidencias y análisis de riesgo de estafas
online (dominios, emails y wallets cripto), pensada como base para un
informe que se pueda adjuntar a una denuncia ante las autoridades.

Estado actual: 10 módulos de análisis + persistencia + informe PDF + capa
de IA + frontend + monitorización continua con alertas. Pendiente: cola
de tareas con Celery/Redis y autenticación (ver checklist al final).

## Cómo ejecutarlo (macOS / Linux)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

## Cómo ejecutarlo (Windows / PowerShell)

Usa **PowerShell** (no cmd), viene instalado por defecto en Windows.

1. Comprueba que tienes Python instalado:
   ```powershell
   python --version
   ```
   Si da error, instala Python desde [python.org/downloads](https://python.org/downloads)
   marcando la casilla **"Add python.exe to PATH"** durante la instalación.

2. Entra en la carpeta del proyecto (puedes arrastrarla desde el explorador
   de Windows a la ventana de PowerShell después de escribir `cd `):
   ```powershell
   cd ruta\a\scam-shield
   ```

3. Crea el entorno virtual:
   ```powershell
   python -m venv venv
   ```

4. Actívalo:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   Si sale un error de "ejecución de scripts deshabilitada", ejecútalo una
   sola vez (te pedirá confirmar, responde `S`):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   Sabrás que se activó porque aparece `(venv)` al principio de la línea.

5. Actualiza pip antes de instalar (evita errores de compilación con
   paquetes como `pydantic-core` en versiones recientes de Python):
   ```powershell
   python -m pip install --upgrade pip
   ```

6. Instala las dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

7. Arranca el servidor:
   ```powershell
   uvicorn app.main:app --reload
   ```

**Para las próximas veces** (ya con el entorno creado), solo necesitas
los pasos 2, 4 y 7:
```powershell
cd ruta\a\scam-shield
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Configurar variables de entorno (opcional, solo para wallets ETH/EVM)

El único módulo que necesita configuración adicional para funcionar por
completo es el de wallets cripto, y solo para direcciones **ETH/EVM**
(BTC y Tron funcionan sin tocar nada):

1. Crea una cuenta gratuita en https://etherscan.io/apis
2. Genera una API key
3. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env      # Windows: copy .env.example .env
   ```
4. Abre `.env` y pon la key en `ETHERSCAN_API_KEY=...`

`TRON_API_KEY` es opcional para wallets Tron/TRC20 (funcionan sin ella,
la key gratuita de https://www.trongrid.io solo sube el límite de rate).
`VIRUSTOTAL_API_KEY` y `ABUSEIPDB_API_KEY` son opcionales para el módulo
de dominio (veredicto de la comunidad + reputación de la IP resuelta) —
ver Módulo 1. La segunda también la reutiliza el Módulo 11 (IP).
`SERPAPI_API_KEY`, `PIMEYES_API_KEY` y `PUBLIC_BASE_URL` son opcionales
para el módulo de imagen (búsqueda inversa y facial) — ver Módulo 7.
`IPQUALITYSCORE_API_KEY`, `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN` son
opcionales para el módulo de teléfono (Twilio es de pago) — ver Módulo 5.
`FCA_API_EMAIL` y `FCA_API_KEY` son opcionales para el módulo CNMV
(comprobación en positivo contra el registro FCA) — ver Módulo 6.

## Despliegue en producción (Docker / Portainer)

Para uso propio en local (los pasos de arriba) no hace falta nada de esto.
Esta sección es para cuando quieras publicar la herramienta en un servidor
propio (por ejemplo una Raspberry Pi u otro host con Docker) detrás de un
reverse proxy y control de acceso.

**Qué cambia respecto a correrlo en local:**
- `app/main.py` monta el frontend estático (`StaticFiles` sobre
  `frontend/`) al final de la app, después de todas las rutas de la API —
  así el mismo backend sirve también el panel, sin CORS ni un segundo
  servidor.
- `frontend/index.html` autodetecta el backend: si no se abre como
  `file://` (es decir, si se sirve desde un dominio/IP), el campo
  "Backend" se autoconfigura a `location.origin` en vez del
  `127.0.0.1:8000` por defecto. No hay que tocar nada a mano al pasar de
  local a producción.

**Artefactos en `deploy/`:**
- `Dockerfile` — `python:3.12-slim`, un único worker de `uvicorn`
  (**obligatorio**: el scheduler en proceso de la monitorización continua,
  Módulo 9, no soporta varios workers — con más de uno se ejecutaría el
  re-chequeo periódico duplicado por cada worker).
- `docker-compose.yml` — expone el puerto `8088` del host (`8088:8000`),
  persiste `scamshield.db` en un volumen (`/mnt/hdd/scam-shield/data:/data`,
  ajusta la ruta a tu host) y toma cada API key como variable de entorno
  vía `${VAR}` — funciona igual con un archivo `.env` junto al compose que
  con las variables de entorno que le pases al stack (por ejemplo, el
  formulario de Portainer).
- `.env.example` — plantilla con todas las variables que acepta el
  compose (las mismas de la sección "Configurar variables de entorno" de
  arriba, más `PUBLIC_BASE_URL`). Cópiala a `deploy/.env` y rellena solo
  las que vayas a usar; nunca se commitea (cubierto por `.gitignore`).

**Desplegar con Portainer (Build method: Repository):**
1. Si el repo es privado, genera un token de acceso de GitHub de solo
   lectura (fine-grained, scope solo a este repo, permiso `Contents:
   Read-only`) — Portainer lo necesita para poder clonarlo. Si el repo es
   público, este paso no hace falta.
2. Crea el stack: Repository URL del repo, rama `main`, **Compose path
   `scam-shield/deploy/docker-compose.yml`** (el contexto de build es la
   raíz de esta carpeta, no `deploy/`, para poder copiar `app/` y
   `frontend/`), autenticación con tu usuario + el token del paso 1 (solo
   si aplica), y las variables de entorno (a mano o subiendo un `.env`,
   Portainer soporta ambas formas).
3. Deploy → comprobar `http://<host>:8088/health` desde la red local.
4. Publicarlo hacia fuera (reverse proxy con SSL — p.ej. Nginx Proxy
   Manager — y algún control de acceso delante, p.ej. Cloudflare Access)
   depende de tu propia infraestructura, no de esta herramienta.

**Instancia desplegada:** https://dfir.gondorhub.com

## Probarlo — visión general

Abre http://localhost:8000/docs — ahí tienes la documentación interactiva
(Swagger) generada automáticamente por FastAPI. Es la forma más cómoda de
probar cualquier endpoint sin necesidad de frontend.

| Módulo | Endpoint para analizar | Endpoints para consultar el histórico |
|---|---|---|
| Dominio | `POST /analysis/domain` | `GET /cases`, `GET /cases/{id}` |
| Email | `POST /analysis/email/file` (recomendado) o `POST /analysis/email` | `GET /email-cases`, `GET /email-cases/{id}` |
| Wallet cripto | `POST /analysis/wallet` | `GET /wallet-cases`, `GET /wallet-cases/{id}` |
| Typosquatting | `POST /analysis/typosquatting` | `GET /typosquatting-cases`, `GET /typosquatting-cases/{id}` |
| Teléfono | `POST /analysis/phone` | `GET /phone-cases`, `GET /phone-cases/{id}` |
| CNMV | `POST /analysis/cnmv-check` | `GET /cnmv-check-cases`, `GET /cnmv-check-cases/{id}` |
| Imagen | `POST /analysis/image` (+ opcional `POST /analysis/image/{id}/reverse-search`, `POST /analysis/image/{id}/facial-search`) | `GET /image-cases`, `GET /image-cases/{id}` |
| IP | `POST /analysis/ip` | `GET /ip-cases`, `GET /ip-cases/{id}` |
| Informe PDF | `POST /reports/generate` (combina casos de los 8 módulos) | — |
| Consolidado + IA | `POST /analysis/consolidated` (correlación + narrativa LLM) | — |
| Monitorización | `POST /monitoring/subjects/{id}/check-now` (re-chequeo manual) | `GET /monitoring/subjects`, `PATCH /monitoring/subjects/{id}`, `GET /alerts`, `POST /alerts/{id}/acknowledge` |

Si quieres empezar de cero con la base de datos, borra el archivo
`scamshield.db` y reinicia el servidor (se recrea vacío).

---

## Módulo 1 — Análisis de dominio

Consulta WHOIS, el certificado SSL, (si está configurado) VirusTotal, DNS
completo (todas las IPs, MX, SPF/DMARC, CAA), la reputación (AbuseIPDB,
opcional) de cada IP a la que resuelve el dominio, subdominios
relacionados vía Certificate Transparency (crt.sh) y el historial del
dominio en Wayback Machine — y calcula un `risk_score` con reglas
explicables. Es el módulo más completo de la herramienta: casi todas las
demás señales (email, typosquatting...) terminan apoyándose en algún
dato que produce este.

**Probarlo desde Swagger:** `POST /analysis/domain` → Try it out →
`{"domain": "google.com"}` → Execute.

**Probarlo por terminal:**

macOS / Linux:
```bash
curl -X POST http://localhost:8000/analysis/domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'
```

Windows (PowerShell — nota el `curl.exe` y las comillas escapadas con `\"`,
necesarias porque el `curl` normal de PowerShell es un alias distinto):
```powershell
curl.exe -X POST http://localhost:8000/analysis/domain -H "Content-Type: application/json" -d '{\"domain\": \"google.com\"}'
```

Prueba con un dominio recién registrado (busca ejemplos en OpenPhish o
PhishTank) para ver cómo sube el `risk_score`.

**Señales que detecta:**

| Señal | Qué significa |
|---|---|
| `DOMAIN_VERY_NEW` / `DOMAIN_RECENT` | El dominio se registró hace muy poco |
| `WHOIS_HIDDEN` | No se pudo obtener el registrador (privacidad WHOIS agresiva) |
| `NO_VALID_SSL` | No presenta certificado SSL válido |
| `CERT_JUST_ISSUED` | El certificado SSL se emitió hace muy pocos días |
| `VT_HIGH_DETECTION` / `VT_SOME_DETECTION` | Varios/algún motor de VirusTotal marca el dominio como malicioso |
| `VT_SUSPICIOUS_VOTES` | Algún motor lo marca como sospechoso (sin llegar a malicioso) |
| `IP_HIGH_ABUSE_SCORE` / `IP_MODERATE_ABUSE_SCORE` | La IP principal a la que resuelve el dominio tiene una puntuación de abuso alta/moderada en AbuseIPDB |
| `IP_TOR_EXIT_NODE` | La IP resuelta es un nodo de salida de Tor — informativo, no concluyente por sí solo |
| `ADDITIONAL_IP_HIGH_ABUSE_SCORE` / `_MODERATE_ABUSE_SCORE` / `_TOR_EXIT_NODE` | Igual que las anteriores, pero para una IP **extra** del dominio (no la principal) — la IP concreta va en la descripción de la señal |
| `DOMAIN_NO_SPF` / `DOMAIN_NO_DMARC` | El dominio recibe correo (tiene MX) pero no protege su propio nombre contra suplantación (sin SPF/DMARC en su DNS) |
| `SUBDOMAIN_BRAND_IMPERSONATION` | Certificate Transparency (crt.sh) muestra un certificado emitido para un subdominio que menciona una marca conocida sin pertenecerle (p.ej. `bbva-login.dominio-malo.xyz`) |
| `DOMAIN_NEVER_ARCHIVED` | Wayback Machine nunca ha archivado este dominio — débil por sí sola, refuerza otras señales de novedad |
| `DOMAIN_REUSED_AFTER_EXPIRY` | La primera captura en Wayback Machine es muy anterior a la fecha de registro WHOIS actual: el dominio probablemente expiró y fue vuelto a registrar para heredar su reputación/histórico ("domain drop-catching") |

### Configurar VirusTotal (opcional)

Sin esta key, el módulo funciona igual con WHOIS + SSL — VirusTotal es una
señal adicional, no un requisito.

1. Crea una cuenta gratuita en https://www.virustotal.com/gui/join-us
2. En tu perfil, copia tu API key
3. Añádela a tu `.env`: `VIRUSTOTAL_API_KEY=...`

El plan gratuito tiene un límite de 4 consultas/minuto — de sobra para
pruebas y para un volumen moderado en producción.

### Reputación de la IP resuelta — AbuseIPDB (opcional)

Además de WHOIS/SSL/VirusTotal (que miran el dominio en sí), se resuelve
el dominio a su IP (offline, `dns_service.py`) y se consulta su
reputación en [AbuseIPDB](https://www.abuseipdb.com): consenso de la
comunidad de seguridad sobre esa IP (fuerza bruta, escaneos, spam,
phishing...) — mismo principio que VirusTotal, reputación de
infraestructura, no vigilancia de personas. Esta misma señal (y el mismo
servicio, `abuseipdb_service.py` + `ip_risk_engine.py`) la reutiliza
también el **Módulo 11 — Análisis de IP**, para no duplicar los mismos
umbrales en dos sitios.

**Configurarlo (opcional):**
1. Crea una cuenta gratuita en https://www.abuseipdb.com/register
2. Añade tu API key a `.env`: `ABUSEIPDB_API_KEY=...`
3. **Reinicia el servidor**

El plan gratuito tiene un límite de 1000 consultas/día al endpoint de
comprobación. Sin esta key (o si el dominio no resuelve a ninguna IP),
`/analysis/domain` sigue funcionando igual; solo se omite esta señal y
verás el motivo en `errors`.

### DNS completo: todas las IPs, MX, SPF/DMARC, CAA

Una resolución simple solo da la primera IP. `dns_service.get_dns_records`
(vía [`dnspython`](https://www.dnspython.org/)) consulta además:

- **Todas las IPs** (registros A) — un dominio puede resolver a varias
  (balanceo, CDN, o directamente varias IPs sospechosas). Cada una recibe
  su propia reputación AbuseIPDB (tope de 5 IPs por dominio, para no
  agotar el límite gratuito); la primera sigue siendo `resolved_ip`/
  `abuseipdb` para no romper nada que ya dependiera de esos campos, el
  resto aparece en `ip_reputations`.
- **MX** — a través de qué proveedor de correo recibe email el dominio.
- **SPF/DMARC** (registros TXT del propio dominio, y de `_dmarc.<dominio>`)
  — si el dominio protege su propio nombre contra suplantación. Solo se
  evalúa como señal si el dominio tiene MX (sin MX no recibe correo, no
  necesita SPF/DMARC).
- **CAA** — qué autoridades certificadoras están autorizadas a emitir
  certificados para el dominio.

Es DNS público, sin API key ni límite de consultas.

### Subdominios relacionados — Certificate Transparency (crt.sh)

Desde 2018, toda autoridad certificadora está obligada a publicar
públicamente cada certificado que emite (Certificate Transparency).
[crt.sh](https://crt.sh) indexa ese registro y permite buscar por
dominio: `crtsh_service.get_crtsh_info` devuelve todos los subdominios
para los que se ha emitido certificado alguna vez — infraestructura
relacionada (paneles de login, entornos de prueba) que ni WHOIS ni una
resolución DNS del dominio principal revelan. Si algún subdominio
menciona una marca conocida sin pertenecerle (`bbva-verificacion.dominio-
malo.xyz`), dispara `SUBDOMAIN_BRAND_IMPERSONATION`.

Gratis, sin API key. **Aviso:** crt.sh es un servicio público conocido
por ser inestable bajo carga (falla de forma intermitente incluso para
consultas válidas) — cuando eso pasa, `crtsh` viene a `null` en la
respuesta y el motivo queda en `errors`, el resto del análisis no se ve
afectado.

### Historial — Wayback Machine

`wayback_service.get_wayback_info` consulta el
[CDX API](https://web.archive.org/cdx/search/cdx) de Internet Archive:
cuántas veces se ha archivado el dominio, desde cuándo y hasta cuándo.
Interesa por dos motivos:

1. **Cero capturas** (`DOMAIN_NEVER_ARCHIVED`): dominio nunca indexado —
   normal en uno recién creado, refuerza otras señales de novedad.
2. **Primera captura muy anterior al registro WHOIS actual**
   (`DOMAIN_REUSED_AFTER_EXPIRY`): el dominio existió antes con otro
   contenido y fue "recuperado" tras expirar (*domain drop-catching*),
   técnica habitual para heredar la reputación/backlinks de un dominio
   ajeno. Señal fuerte, no depende de ninguna opinión externa: es
   simplemente contrastar dos fechas.

Gratis, sin API key.

---

## Módulo 2 — Forense de email

Analiza un email sospechoso en varias capas: **cabeceras técnicas**
(SPF/DKIM/DMARC), **nombre visible del remitente** (¿dice ser un banco
pero no lo es?), **enlaces del cuerpo** (acortadores, suplantación de
marca, dominios recién registrados, veredicto de VirusTotal) y
**adjuntos** (extensiones ejecutables, doble extensión).

**No hace falta saber descargar el `.eml` para usarlo.** Si puedes
conseguir el código fuente original, mejor (es la única forma de
verificar SPF/DKIM/DMARC), pero si no —por ejemplo, si acabas de recibir
el intento de estafa y solo quieres pegar lo que ves en pantalla— el
mismo endpoint lo acepta igual: el análisis avisa de que no pudo verificar
la autenticación técnica (`is_raw_source: false`), pero sigue analizando
enlaces, adjuntos y el nombre del remitente sin más pasos previos.

> ⚠️ **Si usas `POST /analysis/email` (JSON) a mano en Swagger y te da un
> error `422 - Invalid control character`**, es normal: un email raw tiene
> saltos de línea reales, y JSON no permite saltos de línea literales
> dentro de una cadena sin escapar. Usa `POST /analysis/email/file` en su
> lugar — subes el archivo tal cual, sin ese problema. El endpoint JSON
> está pensado para cuando el frontend (o cualquier código) construya la
> petición ya escapada — es justo lo que hace la opción de "pegar texto"
> del panel de Email.

**Para el análisis más completo (con SPF/DKIM/DMARC), consigue el código
fuente / original** del mensaje:

- **Gmail**: abre el email → menú de 3 puntos → **"Mostrar original"** →
  cópialo entero y pégalo en el panel de Email, o botón **"Descargar
  original"** para subir el `.eml`
- **Outlook**: abre el email → Archivo → Propiedades → cuadro
  **"Encabezados de Internet"** → copia el contenido
- **Apple Mail**: Ver → Mensaje → "Código fuente" → copia el contenido

Sube el archivo en `POST /analysis/email/file` desde Swagger (botón
"Choose File" en Try it out), o pega el texto en `POST /analysis/email`.

**Señales que detecta:**

| Señal | Qué significa |
|---|---|
| `SPF_FAIL` / `SPF_MISSING` | El servidor no autoriza a ese remitente a enviar en nombre de ese dominio |
| `DKIM_FAIL` / `DKIM_MISSING` | Firma criptográfica inválida o ausente — el contenido pudo alterarse |
| `DMARC_FAIL` | No cumple la política de autenticación del dominio |
| `REPLY_TO_MISMATCH` | Las respuestas se redirigen a un dominio distinto del remitente (truco clásico) |
| `RETURN_PATH_MISMATCH` | El dominio de rebote no coincide con el remitente |
| `SUSPICIOUS_TLD` | Extensión barata típica de phishing (.xyz, .top, .tk...) |
| `SENDER_DOMAIN_VERY_NEW` / `_RECENT` | El dominio del remitente se registró hace poco (reutiliza el WHOIS del módulo 1) |
| `DISPLAY_NAME_BRAND_MISMATCH` | El nombre visible dice ser una marca conocida (banco, Correos, Amazon...) pero el dominio real no le pertenece |
| `SHORTENED_LINK` | Un enlace del cuerpo usa un acortador (bit.ly...) que oculta el destino real |
| `LINK_BRAND_IMPERSONATION` | Un enlace apunta a un dominio que imita a una marca conocida sin serlo |
| `LINK_DOMAIN_VERY_NEW` | El dominio de un enlace del cuerpo se registró hace muy poco |
| `LINK_FLAGGED_BY_VIRUSTOTAL` | VirusTotal marca el dominio de un enlace como malicioso |
| `DANGEROUS_ATTACHMENT` | Adjunto con extensión capaz de ejecutar código (.exe, .js, .docm...) |
| `DOUBLE_EXTENSION_ATTACHMENT` | Adjunto con doble extensión (ej. `factura.pdf.exe`), técnica clásica para disfrazar un ejecutable |
| `LIMITED_ANALYSIS_NO_RAW_SOURCE` | Aviso informativo: no había cabeceras técnicas que comprobar (se pegó texto visible, no el código fuente) |

El análisis de enlaces reutiliza WHOIS/VirusTotal ya usados en el módulo
de dominio, acotado a un máximo de 5 dominios distintos por email (evita
agotar el límite gratuito de VirusTotal y consultas WHOIS lentas cuando
un email trae muchos enlaces). Los dominios de infraestructura habitual
(Google, Microsoft, redes sociales, proveedores de email marketing) se
ignoran porque no aportan señal.

Si hay `ANTHROPIC_API_KEY` configurada, cada análisis incluye además
`ai_explanation`: un párrafo en lenguaje sencillo pensado para la propia
víctima, explicando el motivo del riesgo y qué evitar hacer. Es opcional
— sin la key, el resto del análisis funciona exactamente igual.

**Nota de privacidad:** no guardamos el email crudo completo en base de
datos, solo los datos extraídos (remitente, asunto, resultados de
autenticación, enlaces, adjuntos...). Los adjuntos se identifican por su
huella SHA-256 y metadatos (nombre, tamaño, extensión) — nunca se guarda
el contenido del archivo en sí. Si más adelante hace falta conservar el
original como prueba, se añadirá como campo explícito y cifrado, no en
texto plano.

---

## Módulo 3 — Trazado de wallets cripto

Analiza una dirección de wallet (**BTC**, **ETH/EVM** o **Tron/TRC20**)
consultando el blockchain público directamente — no hace falta API key
para BTC ni Tron (opcional para subir el límite de rate), sí para ETH
(ver "Configurar variables de entorno" más arriba).

**Probarlo desde Swagger:** `POST /analysis/wallet` → Try it out →
`{"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"}` → Execute (esa es la
wallet original de Satoshi, tiene histórico real para ver el análisis en
acción). El endpoint autodetecta la red por el formato de la dirección.

> ℹ️ Usamos la **API V2** de Etherscan (la V1 se cerró definitivamente en
> 2025). No hace falta hacer nada especial: tu API key gratuita de
> Etherscan vale igual para ambas versiones, la URL correcta ya está en
> el código.

### Encontrar la dirección: extractor de texto libre y ayuda de formato

Localizar a mano la dirección dentro de un mensaje de estafa es tedioso
y propenso a errores (copiar de más/de menos un carácter invalida el
análisis). Dos ayudas nuevas:

- **`POST /analysis/wallet/extract-addresses`** con `{"text": "..."}`:
  pega el chat/email/WhatsApp completo tal cual y devuelve todas las
  direcciones BTC/ETH/Tron reconocibles que contiene, listas para
  analizar con un clic desde el frontend (panel Wallet → "¿No encuentras
  la dirección?").
- **`GET /analysis/wallet/format?address=...`**: mientras escribes en el
  frontend, dice en vivo qué tipo de dirección es (p.ej. "Bitcoin —
  bech32 (SegWit nativo)"), sin necesidad de completarla ni de lanzar el
  análisis completo.

### Redes soportadas

- **BTC**: legacy (`1...`), P2SH-SegWit (`3...`), bech32/taproot (`bc1...`) — vía blockchain.info.
- **ETH/EVM**: comprueba automáticamente **Ethereum, BSC y Polygon** con la misma `ETHERSCAN_API_KEY` (API V2, parámetro `chainid`) y usa la red con más actividad — importante porque una wallet de scam puede no tener ningún movimiento en Ethereum (gas caro) pero sí cientos en BSC (gas casi gratis); antes esto se reportaba erróneamente como `WALLET_NO_HISTORY`.
- **Tron/TRC20**: vía [TronGrid](https://www.trongrid.io) (API oficial, funciona sin key). Prioriza el histórico de transferencias de **USDT-TRC20** (la moneda que de verdad piden la mayoría de estafas hoy, por sus comisiones casi nulas) sobre el TRX nativo; si no hay movimientos de USDT, cae de vuelta al histórico nativo de TRX (con la limitación de que, en ese caso, no se calculan importes ni remitentes distintos — ver campo `note` de la respuesta).

**Señales que detecta:**

| Señal | Qué significa |
|---|---|
| `WALLET_OFAC_SANCTIONED` | La dirección aparece en la lista de direcciones sancionadas de la OFAC (Tesoro de EEUU) — fuerza el score a 100, es prueba documental externa |
| `HIGH_FAN_IN` / `MODERATE_FAN_IN` | Muchas direcciones distintas han enviado fondos — típico de wallet de recogida reutilizada para varias víctimas |
| `RAPID_OUTFLOW` | Los fondos recibidos ya han salido casi en su totalidad — típico de lavado rápido |
| `WALLET_VERY_NEW` | La primera transacción fue hace muy pocos días |
| `WALLET_NO_HISTORY` | La wallet nunca se ha usado públicamente (en ninguna de las redes EVM comprobadas, para ETH) |

### Cruce contra la lista de sancionados de la OFAC

Además del histórico de transacciones, cada análisis cruza la dirección
contra el listado de direcciones cripto sancionadas por la OFAC (Tesoro
de EEUU) — mismo patrón de caché local que el listado de advertencias de
la CNMV (se refresca solo si tiene más de 24h). Fuente: espejo público
[`0xB10C/ofac-sanctioned-digital-currency-addresses`](https://github.com/0xB10C/ofac-sanctioned-digital-currency-addresses)
(regenerado cada noche desde la fuente oficial vía GitHub Actions),
cubre BTC, ETH y Tron.

> **Pendiente (no implementado):** [Chainabuse](https://chainabuse.com)
> tiene un API real de "¿esta dirección se ha reportado como scam?" —
> justo el AbuseIPDB de wallets — pero requiere solicitar acceso como
> partner "pre-vetted" (no es autoservicio como AbuseIPDB), así que no
> hay key disponible todavía. `CryptoScamDB` se descartó: su API pública
> lleva tiempo abandonada (responde `502`).

**Limitación conocida:** solo se analizan las últimas 50 transacciones
(para no sobrecargar las APIs públicas gratuitas). Si la wallet tiene más
movimiento, la fecha de "primera transacción" puede no ser exacta — el
campo `note` de la respuesta avisa cuando pasa esto.

---

## Módulo 4 — Detector de typosquatting

Dado un dominio legítimo (tu marca, o la de la empresa que investigas),
genera decenas de variantes con las técnicas más comunes de suplantación
y comprueba **de verdad** (resolución DNS real) cuáles están registradas.
A diferencia de los módulos 1-3 (dominio, email, wallet), aquí no evaluamos "¿es sospechoso este
dominio?" sino "¿cuánta suplantación activa hay alrededor de esta marca?".

Todas las variantes activas reciben además la reputación de la IP a la
que resuelven (AbuseIPDB, el mismo servicio que ya usan los módulos de
Dominio e IP) — a diferencia del análisis completo (WHOIS/SSL/VirusTotal,
caro y limitado a `max_full_analysis` variantes), la reputación de IP es
barata (consulta por IP, no por dominio) y se aplica a **todas** las
variantes activas (hasta `max_ip_checks`, con caché por IP para no
repetir consulta cuando varias variantes comparten el mismo hosting —
típico en campañas grandes). Esto es lo que evita que la mayoría de
variantes se queden sin ninguna señal ("sin analizar").

- `POST /analysis/typosquatting` — genera variantes, comprueba DNS, y
  opcionalmente analiza en profundidad las que resuelven
- `GET /typosquatting-cases`, `GET /typosquatting-cases/{id}`

**Técnicas de generación:**

| Técnica | Ejemplo (a partir de `bbva.es`) |
|---|---|
| `omission` | `bva.es` (falta una letra) |
| `duplication` | `bbbva.es` (letra repetida) |
| `transposition` | `bvba.es` (dos letras cambiadas de orden) |
| `adjacent_key` | `vbva.es` (tecla vecina en el teclado) |
| `homoglyph` | `bbv4.es` (carácter visualmente similar) |
| `hyphenation` | `bb-va.es` |
| `tld_swap` | `bbva.com`, `bbva.xyz`, `bbva.top`... |
| `phishing_keyword` | `bbva-verificacion.es`, `secure-bbva.es`... |

**Cuerpo de la petición:**
```json
{
  "domain": "bbva.es",
  "include_full_analysis": false,
  "max_variants": 200,
  "max_full_analysis": 4,
  "max_ip_checks": 50
}
```

Con `include_full_analysis: true`, las variantes que resuelven pasan
además por el mismo pipeline WHOIS/SSL/VirusTotal del módulo 1 (limitado
a `max_full_analysis` para no agotar el límite gratuito de VirusTotal).
Independientemente de ese flag, **todas** las variantes activas (hasta
`max_ip_checks` IPs únicas) reciben la reputación de su IP vía AbuseIPDB
— sin `ABUSEIPDB_API_KEY` configurada, esa señal se omite igual que en
los demás módulos, y el motivo queda en `errors`.

Cada candidato (`TyposquattingCandidate`) trae un campo `fully_analyzed`
para distinguir el origen de su `risk_score`: `true` si vino del análisis
completo (WHOIS/SSL/VirusTotal), `false` si vino solo de la reputación de
su IP.

**Señales que detecta:**

| Señal | Severidad | Qué significa |
|---|---|---|
| `TYPOSQUATTING_LOW_VOLUME` / `_MODERATE_VOLUME` / `_HIGH_VOLUME` | Baja/Media/Alta | Cuántas variantes activas se han encontrado |
| `TYPOSQUATTING_ACTIVELY_WEAPONIZED` | Alta | Alguna variante activa tiene certificado SSL recién emitido — no es solo un dominio aparcado |
| `TYPOSQUATTING_HIGH_RISK_VARIANT` | Alta | Alguna variante **analizada en profundidad** tiene su propio score alto (≥60) |
| `TYPOSQUATTING_VARIANT_ON_ABUSIVE_IP` | Media | Alguna variante activa (sin análisis completo) está alojada en una IP con mala reputación en AbuseIPDB — señal más débil que la anterior, podría ser hosting compartido |

**Rendimiento:** la comprobación DNS de las ~150-200 variantes generadas
se hace en paralelo (25 hilos simultáneos), así que tarda menos de un
segundo incluso con el límite máximo de variantes — comprobarlas una a
una habría tardado varios minutos.

**Limitación conocida:** no cubre homógrafos Unicode completos (dominios
internacionalizados con caracteres cirílicos u otros alfabetos que se ven
idénticos a los latinos). Es una técnica real pero mucho menos común
contra objetivos hispanohablantes que las técnicas ASCII de arriba —
ampliación futura clara si hace falta.

---

## Módulo 5 — Análisis de teléfono

Identifica el tipo de línea, operador y país de un número de teléfono, y
opcionalmente si otras personas ya lo han reportado como spam/fraude, si
tiene señales de fraude agregadas (IPQualityScore) y su carrier real en
tiempo real (Twilio Lookup).

La parte de tipo de línea/operador usa `phonenumbers` (el port en Python
de libphonenumber, la misma base de datos que usa Android/Chrome) —
**100% offline, sin API key ni límite de cuota**. Las tres integraciones
externas (OpenSpam, IPQualityScore, Twilio Lookup) son opcionales: sin
ellas, el resto del análisis funciona exactamente igual. Ninguna de las
tres busca "de quién es este número" (ver por qué en cada subsección) —
es la misma línea que ya trazamos con el reconocimiento facial en el
módulo de imagen.

**Probarlo desde Swagger:** `POST /analysis/phone` → Try it out →
`{"phone": "+34803123456", "default_region": "ES"}` → Execute (ese es un
número de tarificación especial español, verás cómo dispara la señal de
mayor severidad).

**Señales que detecta:**

| Señal | Severidad | Qué significa |
|---|---|---|
| `PHONE_PREMIUM_RATE` | Alta | Tarificación especial — cobra por llamada/minuto, mecanismo económico del timo de "falso premio" o llamadas perdidas ("wangiri") |
| `PHONE_VOIP` | Media | Número VoIP — se crea y desecha en segundos sin línea física ni contrato, habitual en campañas de estafa a gran escala |
| `PHONE_INVALID_FORMAT` | Media | El número no tiene un formato válido para su país — puede estar falsificado |
| `PHONE_UNKNOWN_LINE_TYPE` | Baja | Formato válido pero no se pudo determinar el tipo de línea |
| `PHONE_PAGER` | Baja | Tipo de línea muy poco común hoy en día (buscapersonas) |
| `PHONE_COMMUNITY_REPORTED_HIGH/MEDIUM/LOW` | Según nivel | Otras personas ya han reportado este número concreto como spam/fraude (ver OpenSpam abajo) |
| `PHONE_HIGH_FRAUD_SCORE` / `_MODERATE_FRAUD_SCORE` | Alta / Media | Puntuación de fraude agregada de IPQualityScore (≥85 / 60-84 sobre 100) |
| `PHONE_RECENT_ABUSE_REPORTED` | Alta | IPQualityScore registra abuso reciente asociado al número |
| `PHONE_NUMBER_LEAKED` | Baja | El número aparece en alguna brecha de datos filtrada — muy común, no concluyente por sí solo |
| `PHONE_VOIP_LIVE_MISMATCH` | Alta | Twilio Lookup dice en tiempo real que es VoIP aunque la detección offline no lo marcaba así — posible portabilidad o spoofing |

Los números `FIXED_LINE`, `MOBILE` y `TOLL_FREE` normales no disparan
ninguna señal — son los tipos de línea esperados en comunicación legítima.

**Limitación conocida:** la detección de VoIP depende de qué tan
actualizados estén los rangos numéricos en la base de datos de
libphonenumber para cada país — algunos números VoIP modernos (sobre todo
en EE. UU.) se clasifican como `FIXED_LINE_OR_MOBILE` porque la librería
no tiene ese rango marcado específicamente como VoIP. No es un fallo de
nuestro código, es una limitación de la fuente de datos — **si configuras
Twilio Lookup (más abajo), esta limitación concreta queda cubierta**,
porque esa consulta es en tiempo real contra el operador, no un rango
estático.

### Reportes comunitarios — OpenSpam (opcional)

**Por qué así, y no "buscar el nombre del dueño del número" (tipo
Truecaller):** identificar a la persona detrás de un número es un dato
personal, y las fuentes que lo permiten (bases de datos de agendas de
contacto subidas por otros usuarios, sin consentimiento del dueño del
número) son la misma técnica que se usa para acosar o localizar a
alguien. En su lugar, consultamos si **otras personas ya han reportado
ese número concreto** como spam/fraude — es un reporte de comportamiento
público, no la identidad de nadie, y sigue el mismo principio que ya
aplicamos con VirusTotal o Chainabuse: consenso de la comunidad, no
vigilancia de personas.

[OpenSpam](https://www.openspam.es) ofrece justo esto: una base de datos
colaborativa de números reportados en España (y creciendo a otros
países), con una API pública gratuita pensada explícitamente para
integraciones e investigación — piden no hacer scraping de su web, así
que usamos su API tal cual.

**Configurarlo (opcional):**

1. Crea una cuenta en https://api.openspam.es/panel y genera una API key
2. Añádela a tu `.env`: `OPENSPAM_API_KEY=...`
3. **Reinicia el servidor** — las variables de entorno solo se leen al
   arrancar `uvicorn`, así que si editas el `.env` con el servidor ya
   corriendo, no se aplica hasta que lo reinicies

Sin esta key, `/analysis/phone` sigue funcionando exactamente igual (tipo
de línea, operador, país) — solo se omite la capa de reportes
comunitarios, y verás el motivo en el campo `errors` de la respuesta.

**Nota — la estructura real de la respuesta no coincide con la
documentación oficial ni con lo que parecía a primera vista:** confirmado
con una respuesta completa real (capturada de la demo de su propia web),
los datos del número van anidados así:
```json
{
  "success": true,
  "data": {
    "encontrado": true,
    "numero": {
      "telefono": "+34600123456", "total_reportes": 81,
      "nivel_peligro": "alto", "tipo_spam": "spam", "provincia": null, "operadora": "Vodafone"
    }
  }
}
```
Es decir: **los datos están dentro de `data.numero`, no directamente en
`data`** — ni la documentación oficial ni el primer ejemplo que vimos (de
`/api/top`, que sí es plano) dejaban ver este anidamiento extra. El código
ya lo soporta correctamente, con un *fallback* a estructura plana por si
la API cambia otra vez. Si en el futuro ves `community_reports` con
`reports_count: 0` para un número que sabes que está reportado, pide una
respuesta completa real (no solo la documentación) antes de tocar nada —
es la única forma en que se detectaron estos bugs.

**Cómo probarlo con un número real reportado:** los números que aparecen
como ejemplo en el resto de este README para el módulo de teléfono
(`+34803123456`, etc.) son inventados para probar la parte offline
(tarificación especial) — no están en la base de datos real de OpenSpam.
Para probar la integración con un caso real, usa el endpoint `/api/top`
(no lo consumimos desde la app, pero puedes llamarlo tú directamente) que
devuelve el ranking de números con más reportes:
```bash
curl -H "X-API-Key: tu_api_key" "https://api.openspam.es/api/top?limit=5"
```
Coge el valor del campo `telefono` de cualquiera de esos resultados y
pruébalo en `/analysis/phone`.

**Historial de bugs corregidos durante el desarrollo** (documentado por
transparencia, y porque cada uno se detectó pidiendo evidencia real en
vez de fiarse de la documentación):
1. Se trataba "número nunca reportado" (un 200 con `encontrado: false`,
   el caso normal para la inmensa mayoría de números) como un fallo del
   servicio, escondiéndolo en `errors` — la sección desaparecía por
   completo en vez de mostrar "0 reportes".
2. Los nombres de campo de la documentación oficial (`reportes`, `tipo`)
   no coinciden con los reales (`total_reportes`, `tipo_spam`).
3. Los datos van anidados bajo `data.numero`, no directamente en `data`
   — este era el bug que quedaba tras arreglar el 1 y el 2, y el que de
   verdad explicaba por qué números con miles de reportes reales seguían
   apareciendo como "0 reportes" en la herramienta.

Los tres están corregidos y cubiertos por tests con la respuesta real
exacta (`test_respuesta_real_de_produccion_con_estructura_anidada`).

### Puntuación de fraude — IPQualityScore (opcional)

[IPQualityScore](https://www.ipqualityscore.com) es una API de validación
de teléfono pensada para prevención de fraude: puntuación agregada
(`fraud_score`, 0-100), si el número es VoIP o de prepago (típico de
números desechables usados en campañas de estafa), si se ha reportado
abuso reciente, si el número aparece filtrado en alguna brecha de datos,
y si está marcado como spammer. Mismo principio que OpenSpam: reputación
de comportamiento, no identidad.

**Importante — su API TAMBIÉN devuelve un campo `name`** con el nombre
del titular o de la empresa asociada al número (la propia documentación
de IPQualityScore lo describe como "the owner of the phone number
including first and last name or the company's name"). Es exactamente el
dato que este proyecto evita en todos sus módulos — por eso
`ipqualityscore_service.py` **nunca lee ni expone ese campo**, a
propósito, aunque la API lo incluya en su respuesta.

**Configurarlo (opcional):**
1. Crea una cuenta gratuita en https://www.ipqualityscore.com/create-account
2. Añade tu API key a `.env`: `IPQUALITYSCORE_API_KEY=...`
3. **Reinicia el servidor**

Sin esta key, `/analysis/phone` sigue funcionando igual; solo se omite
esta señal y verás el motivo en `errors`.

### Carrier en tiempo real — Twilio Lookup (opcional, de pago)

[Twilio Lookup](https://www.twilio.com/lookup) (add-on
`line_type_intelligence`) consulta al operador en tiempo real (HLR) el
carrier y tipo de línea reales — a diferencia de la detección offline
(`phonenumbers`), que solo mira un rango estático de numeración, esto sí
detecta números portados o VoIP moderno que la base de datos de
libphonenumber no tiene catalogado (ver "Limitación conocida" más
arriba).

Twilio ofrece por separado los add-ons `caller_name` (CNAM, nombre del
titular) e `identity_match` (verifica nombre, dirección, fecha de
nacimiento) — **esta herramienta nunca los pide**, solo
`line_type_intelligence`, precisamente para no cruzar la misma línea que
ya evitamos con OpenSpam/IPQualityScore.

**Es la única integración de pago de la herramienta** (sin tier
gratuito, del orden de 0,005 $ por consulta) — por eso está inactiva por
defecto y solo se activa si configuras explícitamente tus credenciales.
**Aviso de coste con la monitorización continua:** si activas Twilio Y
tienes teléfonos en monitorización continua (Módulo 9), **cada
re-chequeo periódico también consulta a Twilio** — no es solo el análisis
manual. Ten esto en cuenta antes de activarlo sobre muchos sujetos
monitorizados.

**Configurarlo (opcional, solo si contratas el servicio):**
1. Crea una cuenta en https://www.twilio.com/lookup y consigue tu
   `Account SID` y `Auth Token`
2. Añádelos a `.env`: `TWILIO_ACCOUNT_SID=...` y `TWILIO_AUTH_TOKEN=...`
3. **Reinicia el servidor**

Sin estas credenciales, `/analysis/phone` sigue funcionando igual; solo
se omite esta señal y verás el motivo en `errors`.

---

## Módulo 6 — Verificación CNMV (chiringuitos financieros)

Comprueba si una empresa, broker o web de inversión aparece en el listado
público de advertencias de la CNMV — el registro oficial de entidades que
ofrecen servicios de inversión en España **sin estar autorizadas**
("chiringuitos financieros"). Directamente relevante para estafas de
falsa inversión en cripto/forex, que son uno de los fraudes más
denunciados ahora mismo en España.

Además, opcionalmente comprueba el registro público de la FCA (Reino
Unido) — no otra lista negra, sino una **comprobación en positivo**
(¿está la entidad realmente registrada, y con qué estado?) que añade
valor real frente a mirar solo la web de la CNMV: detecta "clone scams"
que se hacen pasar por firmas realmente autorizadas en el Reino Unido, un
patrón habitual en estafas de trading/forex que también llegan a víctimas
españolas. Ver la subsección propia más abajo.

**Probarlo desde Swagger:** `POST /analysis/cnmv-check` → Try it out →
`{"query": "algún nombre real de la lista"}` → Execute.

### Cómo funciona (importante para entender el diseño)

La CNMV **no tiene API** — su listado es una tabla HTML pública de
cientos de páginas (https://www.cnmv.es/Portal/BusquedaAdvertencias.aspx).
Scrapear las ~358 páginas en cada búsqueda sería lentísimo, así que:

1. La primera búsqueda descarga las ~50 páginas más recientes (del orden
   de un año largo de advertencias) y las guarda en una caché local
   (tabla `cnmv_warnings`) — esto tarda unos segundos
2. Las búsquedas siguientes, durante 24h, se resuelven al instante contra
   esa caché local
3. Pasadas 24h, la siguiente búsqueda vuelve a refrescar la caché sola

Esto significa que la cobertura **no es el histórico completo** desde
que existe el registro (miles de entidades a lo largo de los años), sino
las advertencias más recientes — que son las más relevantes para detectar
una campaña de estafa activa ahora mismo.

**Señales que detecta:**

| Señal | Severidad | Qué significa |
|---|---|---|
| `CNMV_UNAUTHORIZED_ENTITY` | Alta (score 90) | La CNMV ha advertido públicamente sobre una entidad que coincide con la búsqueda |
| `FCA_UNAUTHORISED_FIRM` | Alta | La FCA (Reino Unido) marca explícitamente la coincidencia como firma no autorizada/clon de una firma real |
| `FCA_NOT_CURRENTLY_AUTHORISED` | Media | Todas las coincidencias en el registro de la FCA tienen un estado que no es de autorización activa (ninguna vigente) — ver subsección FCA más abajo |
| `CNMV_NOT_IN_AUTHORIZED_REGISTRY` | Media | No se ha encontrado ninguna entidad con este nombre en el registro de la CNMV de Empresas de Servicios de Inversión — ver subsección propia más abajo |

El score es alto directamente con un solo resultado — a diferencia de
otros módulos donde varias señales débiles se van sumando, aquí un
regulador público ya ha hecho el trabajo de decir explícitamente "esta
entidad no está autorizada", así que no hace falta acumular más señales.

### ⚠️ Aviso de fiabilidad — léelo antes de confiar ciegamente en este módulo

Este es el módulo con más riesgo de fragilidad de toda la herramienta,
por una razón concreta: se construyó **sin poder inspeccionar el HTML en
crudo** de la página de la CNMV (la herramienta usada para verificar la
estructura la convierte a texto/markdown, no deja ver las etiquetas
exactas). El parseo de la tabla (`cnmv_service.py`) busca de forma
defensiva la tabla cuya cabecera contiene "Fecha" y "Compañías" en vez de
depender de un id o clase CSS concretos, y si no encuentra ninguna tabla
así, **falla de forma ruidosa** (excepción clara, visible en el campo
`errors` de la respuesta) en vez de devolver silenciosamente "0
resultados" — que sería mucho peor, porque parecería que una entidad no
está advertida cuando en realidad es que no hemos podido leer la página.

**Si al usarlo ves que las búsquedas nunca encuentran nada** (ni siquiera
para nombres que sabes que están en el listado), antes de nada mira el
campo `errors` de la respuesta:
- Si menciona "No se encontró la tabla de advertencias" → la CNMV cambió
  el HTML de su web, hay que revisar `_parse_page()` en
  `cnmv_service.py` con una copia real del HTML de la página (con
  `curl https://www.cnmv.es/portal/resultadobusqueda.aspx?lang=es&tipo=1&page=0`
  o "ver código fuente" del navegador) y ajustar el parseo a la
  estructura real, exactamente como tuvimos que hacer con OpenSpam en el
  módulo de teléfono
- Si `errors` está vacío pero el `match_count` sigue en 0 → puede que la
  entidad que buscas no esté en las páginas más recientes cubiertas por
  la caché (ver limitación de cobertura arriba)

Consulta `/cnmv-warnings/cache-status` para ver cuántas advertencias hay
en caché ahora mismo y de cuándo son — útil para descartar que el
problema sea simplemente que la caché está vacía.

### Registro de entidades autorizadas — comprobación en positivo (España)

Equivalente español de la subsección de FCA (justo abajo): en vez de
consultar solo el listado de advertencias (lista negra), esta consulta el
[buscador de entidades autorizadas de la propia
CNMV](https://www.cnmv.es/portal/consultas/busquedaporentidad?tipoBusqueda=ESI&lang=es)
— ¿existe una entidad con ese nombre en el registro de Empresas de
Servicios de Inversión (ESI) autorizadas a operar en España? No hace
falta ninguna API key: es scraping público, igual que el listado de
advertencias.

**Cómo se probó (con la web real, no de memoria) antes de implementarlo:**
es un formulario ASP.NET clásico con post-back (`__VIEWSTATE`,
`__EVENTVALIDATION`) — se resuelve con un GET (para coger los tokens) +
un POST con la búsqueda, reutilizando la misma sesión (cookies), sin
necesitar JavaScript. Resultados reales obtenidos así:
- **"AICHAINTRADER"** (chiringuito real de la lista de advertencias) → 0
  resultados, correctamente no registrada
- **"Renta 4"** (empresa legítima real) → 2 resultados: RENTA 4 BANCO,
  S.A. / RENTA 4 GESTORA, S.G.I.I.C., S.A.
- **"Barclays"** → 15 entidades reales registradas en España

**Por qué la señal es media, no alta:** a diferencia de las señales de
lista negra (`CNMV_UNAUTHORIZED_ENTITY`, `FCA_UNAUTHORISED_FIRM`), aquí
no hay un regulador diciendo explícitamente "esto es fraude" — solo la
ausencia de una entidad con ese nombre en el registro. Es un indicio
razonable, no una prueba: una entidad extranjera legítima que opera en
España por pasaporte comunitario sin registro local tampoco aparecería
aquí. Por eso, además, la señal **solo se dispara si la comprobación se
ejecutó con éxito** — si falla (red, cambio de HTML de la CNMV), no hay
base para decir "no encontrada", así que no se dispara nada (solo queda
constancia en `errors`).

**Alcance actual:** solo el tipo "ESI" (`tipoBusqueda=ESI`) — la CNMV
tiene otros sub-registros (bancos, gestoras de IIC...) no cubiertos por
ahora. Mismo aviso de fragilidad que el resto del módulo: es un scraping
de un formulario que puede cambiar sin aviso; si dejara de encontrar el
`<select>` de resultados, falla de forma ruidosa (excepción visible en
`errors`) en vez de devolver "0 resultados" silenciosamente. No hace
falta configuración: sin nada que hacer, esta señal ya está activa.

### Cobertura internacional — FCA Register (Reino Unido, opcional)

**Por qué se añadió:** comparar solo contra el propio listado de la CNMV
no aportaba nada que no diera ya visitar cnmv.es directamente. El
[registro de la FCA](https://register.fca.org.uk) sí aporta algo
distinto: es una comprobación **en positivo**, no una lista negra — en
vez de "¿está en la lista de advertidos?" (que siempre va por detrás,
el regulador tarda en investigar y publicar), pregunta "¿está realmente
registrada, y con qué estado?". Un "clone scam" recién montado (broker
que se hace pasar por una firma real autorizada en el Reino Unido, o que
inventa un número de registro) normalmente no aparecerá todavía en
ninguna lista negra, pero tampoco aparece — o aparece con un estado que
no es de autorización activa — en el registro real.

**Mejor de lo esperado, confirmado con datos reales:** la documentación
del cliente de referencia (`fsrapiclient`) sugería que esta API solo
cubre el registro de firmas autorizadas, sin nada equivalente a una
"warning list". Probando contra la API real con credenciales de verdad
resultó que la propia búsqueda **ya incluye, mezcladas con el registro
normal, entradas marcadas explícitamente como firma no autorizada/clon**
(campo `Type of business or Individual: "Unauthorised firm"`), con
nombres tan directos como *"Barclays Capital (clone of FCA authorised
firm)"*. Es decir, sí hay señal de lista negra dentro de esta misma
búsqueda — de ahí las dos señales: `FCA_UNAUTHORISED_FIRM` (alta,
directa) y `FCA_NOT_CURRENTLY_AUTHORISED` (media, para el caso más
ambiguo de una firma que dejó de estar autorizada sin marcarse como
clon). **Aviso aparte:** la documentación de terceros consultada también
decía que la lista de resultados iba en la clave `"data"` — la respuesta
real la trae en `"Data"` (mayúscula); con la clave equivocada el parseo
no fallaba, simplemente devolvía siempre cero resultados en silencio.
Mismo tipo de sorpresa que ya tuvimos con OpenSpam — la lección se
repite: probar siempre contra la API real antes de dar una integración
por buena.

**Otra corrección con datos reales — bancos grandes con historial mixto:**
probando con "Santander" (banco real, no un caso inventado) salió
`risk_score: 90` a la primera versión de esta señal — no porque Santander
tenga nada raro, sino porque un grupo con décadas de historial en el
Reino Unido (fusiones, marcas absorbidas: Abbey, Alliance & Leicester...)
acumula de forma totalmente normal muchas entidades "No longer
authorised" antiguas, mezcladas con las activas (Santander UK Plc, Banco
Santander S.A....). `FCA_NOT_CURRENTLY_AUTHORISED` ahora **solo se
dispara si NINGUNA coincidencia tiene autorización activa** — si hay
aunque sea una activa, esa mezcla es historial corporativo normal, no
una señal. Además, la búsqueda de "Santander" sí encontró un clon real
("santanderbank-finances.com") — `FCA_UNAUTHORISED_FIRM` sigue
disparándose correctamente en ese caso (es un hallazgo genuino y
valioso), pero ahora la descripción aclara explícitamente que el clon es
una entidad DISTINTA, no que la entidad buscada deje de ser legítima.

**Configurarlo (opcional):**
1. Regístrate gratis en https://register.fca.org.uk/Developer/s/
2. Añade a tu `.env`: `FCA_API_EMAIL=...` y `FCA_API_KEY=...` (hacen
   falta las dos, la API exige ambos headers a la vez)
3. **Reinicia el servidor**

Sin estas credenciales, `/analysis/cnmv-check` sigue funcionando igual
(listado de la CNMV); solo se omite esta señal y verás el motivo en
`errors`.

**Fuente descartada — IOSCO I-SCAN:** se investigó también el portal
internacional de alertas de IOSCO (agrega advertencias de reguladores de
todo el mundo), pero su web devuelve 403 (bloqueo anti-bot) en cualquier
petición automatizada — no es scrapeable de forma fiable. Documentado
aquí para no reintentarlo sin motivo; si en el futuro ofrecen una API
oficial, sería la siguiente fuente natural a añadir.

---

## Módulo 7 — Análisis de imagen

Analiza una foto (típicamente una foto de perfil sospechosa en una
estafa romántica, o el "producto" en una venta falsa). El análisis
principal (EXIF + hash perceptual) sigue siendo 100% offline y sin
reconocimiento facial por defecto. Además, como acciones **separadas y
opcionales** sobre un caso ya analizado, se puede pedir una búsqueda
inversa en internet (SerpApi) o, en casos justificados y de forma muy
acotada, una búsqueda de reconocimiento facial (PimEyes) — ver más abajo.

**Probarlo desde Swagger:** `POST /analysis/image` → Try it out → sube
cualquier imagen → Execute.

### Qué hace exactamente

1. **Metadatos EXIF**: cámara, software de edición, fecha, GPS si lo hay.
   La ausencia de EXIF **no es sospechosa por sí sola** (es lo normal en
   fotos bajadas de redes sociales o reenviadas por WhatsApp, que lo
   eliminan al procesarlas) — se muestra como dato informativo de baja
   severidad, nunca como prueba.
2. **Hash perceptual ("huella visual")**: a diferencia de un hash
   criptográfico (que cambia por completo si se toca un solo píxel), este
   hash sigue siendo parecido aunque la imagen se recorte, recomprima o
   le cambien el tamaño. Cada imagen que analizas se compara contra
   **todas las que ya analizaste antes en la herramienta** — si dos casos
   distintos usan la misma foto (aunque esté recortada o reescalada), se
   detecta automáticamente. Esta es la señal fuerte de verdad: una foto
   de perfil reciclada entre varias "citas" o "vendedores" es un patrón
   clásico de estafa romántica o de perfiles falsos en marketplaces.
   Ahora bien, esto solo detecta reciclaje **dentro de esta misma
   herramienta** — si la foto nunca se subió antes aquí, hace falta
   buscarla en el resto de internet, que es justo lo que hacen los dos
   puntos siguientes.
3. **Búsqueda inversa en internet (SerpApi)** — `POST
   /analysis/image/{case_id}/reverse-search`: ¿aparece esta foto en otras
   páginas o perfiles? Acción opcional, separada del análisis principal,
   porque implica enviar la imagen a un tercero (SerpApi/Google) — a
   diferencia del resto del módulo, que es offline. Aparecer en otra
   página **no prueba robo por sí solo** (puede ser un reposteo legítimo
   o una foto de stock) — se pide revisión humana antes de tratarlo como
   prueba (`IMAGE_FOUND_ON_EXTERNAL_PAGES`).

   Limitación real de esta API, no un capricho de diseño: SerpApi/Google
   no aceptan subir los bytes de la imagen, exigen una URL pública donde
   descargarla. Para no romper la garantía de "nunca alojamos la foto en
   ningún sitio público" más de lo estrictamente necesario, la herramienta
   expone la imagen (ya en memoria, ver más abajo) en una URL propia con
   un token opaco de un solo uso y 5 minutos de vida
   (`GET /analysis/image/preview/{token}`) — se borra en cuanto SerpApi la
   descarga o al caducar, lo primero que ocurra. Esto **requiere que la
   instancia esté desplegada en una URL pública** (`PUBLIC_BASE_URL` en
   `.env`) — en local sin desplegar, o sin `SERPAPI_API_KEY`, la acción
   degrada con gracia devolviendo los mismos enlaces manuales de siempre
   (Google Images, TinEye, Yandex) para que subas la foto tú mismo.

   **Configurarlo (opcional):**
   1. Crea una cuenta en https://serpapi.com/users/sign_up y genera una API key
   2. Añádela a tu `.env`: `SERPAPI_API_KEY=...`
   3. Despliega la herramienta en una URL pública y añádela como
      `PUBLIC_BASE_URL=https://tu-dominio.example` (sin barra final) — o
      usa un túnel tipo ngrok en local mientras pruebas
   4. **Reinicia el servidor** para que se apliquen las variables nuevas
4. **Reconocimiento facial (PimEyes) — uso acotado**: ver la sección
   propia justo debajo, es lo bastante delicado como para no resumirlo
   aquí en una línea.

**Señales que detecta:**

| Señal | Severidad | Qué significa |
|---|---|---|
| `IMAGE_REUSED_ACROSS_CASES` | Alta | La misma imagen (o muy parecida) ya se analizó en otro caso de esta herramienta |
| `IMAGE_NO_METADATA` | Baja | Sin EXIF — normal en la mayoría de fotos de internet, se anota igual |
| `IMAGE_EDITED` | Baja | El EXIF indica que se editó con Photoshop/GIMP/etc. — tampoco es sospechoso por sí mismo |
| `IMAGE_FOUND_ON_EXTERNAL_PAGES` | Media | SerpApi encontró esta imagen en otras páginas — revisar si es un perfil distinto (foto robada) o un reposteo/stock legítimo |
| `IMAGE_FACE_FOUND_ELSEWHERE` | Alta | PimEyes encontró esta misma cara en otras páginas — revisar si corresponde a un nombre/perfil distinto (indicio de identidad robada) |

### Reconocimiento facial (PimEyes) — uso acotado

Durante un tiempo esta herramienta tuvo una postura simple: nada de
reconocimiento facial, punto, con el mismo argumento que "no buscamos de
quién es un teléfono" (dato biométrico, categoría especial bajo el RGPD
art. 9, riesgo de acabar siendo un Truecaller de caras alimentado por
scraping sin consentimiento). Ese riesgo de fondo sigue siendo real y no
ha desaparecido. Pero hay un caso de uso legítimo que esa postura dejaba
sin herramienta: la propia víctima de una estafa (romántica, de
identidad, de un perfil falso) necesitando probar que su foto — o la foto
que le robaron a alguien para hacerse pasar por otra persona — circula
por otros perfiles, precisamente para documentarlo en una denuncia.
Negarle esa vía a la víctima mientras el estafador usa herramientas
equivalentes sin ningún escrúpulo no es una postura neutral, es regalarle
la ventaja a quien menos la merece.

Por eso esto existe como una acción **separada, explícita y acotada**,
nunca como parte del análisis automático por defecto:

- **No se dispara nunca automáticamente.** Es una llamada aparte —
  `POST /analysis/image/{case_id}/facial-search` — sobre un caso de
  imagen ya analizado, que hay que pedir a propósito.
- **Exige confirmación explícita** (`confirmed_legal_basis=true`) de que
  existe una base legal para ese caso concreto — típicamente el art.
  9.2.f RGPD (ejercicio de reclamaciones legales: documentar una
  usurpación de identidad para una denuncia). Sin esa confirmación, la
  API devuelve 422 y no se ejecuta nada.
- **Esa confirmación queda sellada para siempre**, junto con los
  resultados obtenidos y la marca de tiempo, en la cadena de integridad
  (`integrity_service.py`, case_type `"image_facial_search"`) — no se
  puede alegar después que la búsqueda se hizo sin dejar rastro, ni
  editar nada a posteriori sin romper la cadena (`GET /integrity/verify`
  lo detectaría).
- **Los resultados nunca se presentan como prueba automática.** PimEyes
  solo dice "esta cara aparece en estas páginas", no "esto es un perfil
  distinto" — la señal `IMAGE_FACE_FOUND_ELSEWHERE` pide explícitamente
  revisión humana antes de darlo por hecho.
- **No se guarda la foto**, igual que el resto del módulo: solo se envían
  los bytes ya cacheados en memoria (ver privacidad, abajo) a PimEyes, y
  se guardan sus resultados (URLs, no imágenes).

**Esto no es asesoría legal.** El art. 9.2.f es la base más defendible
que hay para este caso de uso, pero antes de un uso real en producción
(no solo de pruebas) conviene que un DPO o abogado confirme que el caso
concreto encaja en una base legal válida y que el resto de obligaciones
del RGPD (información al interesado, minimización, etc.) están cubiertas.

**Nota técnica:** `pimeyes_service.py` es una integración de referencia,
no verificada contra el contrato real de la API de negocio de PimEyes
(su acceso requiere solicitud/aprobación previa, no es autoservicio como
SerpApi) — hay que ajustar el request/response exacto en cuanto se tenga
acceso real.

**Configurarlo (opcional):**
1. Solicita acceso a la API de negocio de PimEyes (no es autoservicio,
   requiere aprobación previa)
2. Añade la key a tu `.env`: `PIMEYES_API_KEY=...`
3. Ajusta `_PIMEYES_API_URL` y el parseo en `pimeyes_service.py` al
   contrato real que te confirme PimEyes
4. **Reinicia el servidor**

Sin esta key, `POST /analysis/image/{id}/facial-search` sigue exigiendo
la confirmación de base legal igual, pero devuelve 0 coincidencias con el
motivo en `errors` — nunca falla en bloque, igual que el resto de
integraciones opcionales de esta herramienta.

### Privacidad: no guardamos las fotos

Solo se guarda de forma permanente el hash perceptual y los metadatos
EXIF extraídos — nunca el archivo de imagen en sí, ni en la base de datos
ni en disco. Esto evita acumular una colección de fotos de gente más
tiempo del estrictamente necesario para el análisis.

Para poder ofrecer la búsqueda inversa y la facial como acciones
posteriores sin pedir que se resuba la foto, los bytes se guardan un
rato **solo en memoria del proceso** (nunca en disco/BD), con un TTL de
15 minutos tras el análisis inicial — pasado ese tiempo, esas dos
acciones devuelven 409 y piden repetir el análisis. Se purga tanto de
forma perezosa (al acceder) como periódicamente (job en
`app/core/scheduler.py`).

### Limitación conocida

El hash perceptual (average hash) es robusto a recortes y recompresión
moderados, pero no a cambios grandes (girar la imagen 90°, invertir
colores, o recortar solo una pequeña parte). Es una técnica sencilla a
propósito — hay algoritmos más sofisticados (pHash con DCT, hashes
robustos a rotación) si en el futuro hace falta más precisión, pero para
detectar "la misma foto de perfil subida sin cambios o con cambios
menores" es más que suficiente y no depende de librerías adicionales
complejas.

---

## Módulo 8 — Informe PDF combinado

Junta los casos que elijas de los módulos anteriores (dominio, email,
wallet, typosquatting, teléfono, CNMV, imagen, IP) en un único PDF
listo para adjuntar a una denuncia: portada con resumen ejecutivo, y una
sección detallada por cada caso (con su score, tabla de datos técnicos y
señales de riesgo).

- `POST /reports/generate` — genera y **descarga directamente** el PDF (no
  se guarda en base de datos, se genera al vuelo en cada petición)

**Cuerpo de la petición:**
```json
{
  "domain_case_ids": [1],
  "email_case_ids": [1],
  "wallet_case_ids": [1],
  "victim_notes": "Descripción libre de lo que pasó, en tus propias palabras (opcional)"
}
```

Los `id` son los que te devuelve cada endpoint de análisis, o los que ves
en `GET /cases`, `GET /email-cases` y `GET /wallet-cases`. Puedes incluir
solo uno de los tres tipos, o combinarlos todos si están relacionados con
la misma estafa (por ejemplo: el dominio de la web falsa + el email que la
promocionaba + la wallet a la que pedían transferir el dinero).

**Probarlo desde Swagger:** como la respuesta es un PDF (no JSON), Swagger
no lo previsualiza — al pulsar Execute te aparece un botón **"Download
file"** bajo la respuesta. Descárgalo y ábrelo con cualquier lector de PDF.

**Nota:** el informe organiza la evidencia técnica de forma clara, pero no
es un dictamen pericial ni sustituye la valoración de las autoridades —
así lo indica también el propio documento en su primera página.

---

## Módulo 9 — Análisis consolidado con IA

Combina los casos de los 4 módulos y añade dos cosas que ningún módulo
puede ver por separado:

1. **Correlación entre módulos** (reglas, no IA): si el dominio de uno de
   tus casos coincide con el remitente de un email analizado, se detecta
   automáticamente. También cruza las variantes typosquatting activas
   contra los remitentes de email: si una de esas variantes es justo la
   que usa un email sospechoso, confirma que esa variante concreta ya se
   está usando para atacar, no es solo un registro especulativo.
   automáticamente — es una señal mucho más fuerte que cualquier señal
   aislada, porque confirma que es la misma infraestructura de la estafa.
2. **Narrativa en lenguaje natural** (esto sí es IA — usa la API de
   Claude): un párrafo en español claro explicando *por qué* el caso
   parece una estafa, citando los datos concretos. Pensado para incluir
   en el informe, dirigido a alguien no técnico.

- `POST /analysis/consolidated` — devuelve el score consolidado, las
  correlaciones encontradas y la narrativa (si hay `ANTHROPIC_API_KEY`
  configurada; si no, sigue funcionando igual mostrando el porqué en
  `ai_narrative_error`)

**Diseño importante:** el LLM **nunca decide el score**. Los números
siguen saliendo siempre de las reglas deterministas de los módulos
anteriores (reproducibles, auditables, sin alucinaciones). El LLM solo
redacta la explicación a partir de los datos que ya calculamos — no se le
pide que "decida" nada, solo que lo explique. Esto es importante para la
memoria del TFM: puedes comparar explícitamente heurística pura vs
heurística + capa de IA sobre los mismos casos.

**Cuerpo de la petición:**
```json
{
  "domain_case_ids": [1],
  "email_case_ids": [1],
  "wallet_case_ids": [],
  "victim_notes": "opcional, se lo pasamos también al LLM como contexto",
  "include_ai_narrative": true
}
```

### Configurar la API de Anthropic (opcional)

1. Crea una cuenta en https://console.anthropic.com y genera una API key
2. Añádela a tu `.env`: `ANTHROPIC_API_KEY=...`

Sin esta key configurada, `/analysis/consolidated` sigue funcionando
perfectamente (correlaciones + score consolidado), solo se omite la
narrativa y verás el motivo en `ai_narrative_error`.

### Cómo cerrar el círculo con el informe PDF

`POST /reports/generate` acepta ahora un campo opcional `ai_narrative`.
El flujo completo recomendado:

1. Analiza el dominio, email, wallet y/o typosquatting por separado (módulos 1-4)
2. Llama a `POST /analysis/consolidated` con esos mismos `id` → copia el
   texto de `ai_narrative` de la respuesta
3. Pégalo en el campo `ai_narrative` de `POST /reports/generate` → el PDF
   incluirá una sección "Valoración consolidada" en la portada, antes del
   relato de la víctima

---

## Módulo 10 — Monitorización continua

Un caso analizado hoy es una foto fija: si el dominio saca certificado
SSL la semana que viene, si la wallet empieza a recibir de golpe fondos
de decenas de direcciones, o si un número empieza a acumular reportes de
spam, el caso guardado no se entera. Este módulo lo resuelve
re-analizando periódicamente cada sujeto ya analizado (dominio, wallet,
teléfono, dominio protegido frente a typosquatting, búsqueda CNMV, IP) y
generando una alerta cuando el riesgo sube de forma relevante.

### Cómo funciona (importante para entender el diseño)

- **Cada sujeto analizado se registra automáticamente** para
  monitorización la primera vez que se analiza (no hace falta darlo de
  alta a mano) — se identifica por `case_type` + un identificador
  canónico (el dominio normalizado, la dirección, el número en formato
  E.164, la búsqueda CNMV en minúsculas...).
- **Un scheduler en el mismo proceso** (APScheduler, sin Celery/Redis
  todavía — ver "Próximos pasos") revisa cada hora
  (`MONITORING_SCHEDULER_INTERVAL_MINUTES`) qué sujetos ya tocan
  re-chequeo según su intervalo individual (`MONITORING_DEFAULT_INTERVAL_HOURS`,
  24h por defecto), y para cada uno reejecuta **exactamente el mismo
  pipeline** que el análisis manual (mismo servicio, mismo motor de
  riesgo, misma persistencia).
- **Cada re-chequeo crea un caso nuevo, nunca modifica uno existente.**
  Es una decisión obligada, no estética: la cadena de custodia
  (`integrity_service.py`) hashea el contenido de cada caso tal y como
  quedó guardado — si un re-chequeo automático sobrescribiera un caso
  antiguo, la verificación de integridad lo detectaría como
  "manipulación". Por eso `MonitoredSubject` no guarda el resultado del
  análisis, solo un puntero al último caso y su score, para poder
  comparar.
- **La alerta se genera comparando el caso nuevo contra el anterior**:
  si el nivel de riesgo sube (bajo → medio → alto, mismos cortes que usa
  el frontend para el gauge) o si el score sube más de
  `MONITORING_SCORE_CHANGE_THRESHOLD` puntos (15 por defecto) sin llegar
  a cambiar de nivel, se crea una `RiskAlert`. Bajar de nivel no genera
  alerta — el objetivo es avisar de que algo empeoró, no llevar un
  registro de todas las variaciones.
- **Reanalizar algo a mano también cuenta.** La detección de alertas no
  vive solo en el scheduler: vive en el mismo punto donde se persiste
  cualquier caso (`monitoring_service.touch_subject`), así que volver a
  analizar el mismo dominio a mano desde el frontend genera la misma
  alerta si el riesgo ha subido.

**Endpoints:**

| Endpoint | Qué hace |
|---|---|
| `GET /monitoring/subjects` | Lista los sujetos monitorizados (filtrable por `case_type`), con su último score, nivel e intervalo |
| `PATCH /monitoring/subjects/{id}` | Activa/desactiva un sujeto o cambia su intervalo de re-chequeo |
| `POST /monitoring/subjects/{id}/check-now` | Fuerza un re-chequeo inmediato, sin esperar al scheduler — útil para probar o para revisar algo puntual ya |
| `GET /alerts` | Lista las alertas (`?unacknowledged_only=true` para solo las pendientes) |
| `POST /alerts/{id}/acknowledge` | Marca una alerta como leída |

**Configuración (opcional, valores por defecto ya sensatos):**

```
MONITORING_ENABLED=true
MONITORING_DEFAULT_INTERVAL_HOURS=24
MONITORING_SCHEDULER_INTERVAL_MINUTES=60
MONITORING_SCORE_CHANGE_THRESHOLD=15
```

### Limitación conocida

El scheduler corre dentro del propio proceso de `uvicorn`. Con un solo
worker (el caso normal en desarrollo y en un despliegue pequeño) esto
funciona bien y no necesita infraestructura adicional. Si en el futuro
se despliega con varios workers de `uvicorn`/`gunicorn`, cada uno
lanzaría su propio scheduler y los re-chequeos se duplicarían — ese es
el momento de pasar a Celery + Redis (ya en el checklist de "Próximos
pasos") para tener una única cola de tareas compartida entre workers.

---

## Módulo 11 — Análisis de IP

Comprueba la reputación de una dirección IP suelta — no derivada de un
dominio (eso ya lo hace el Módulo 1 automáticamente), sino como evidencia
por sí sola: la IP de una cabecera `Received` de un email, de un log de
servidor, o del panel de hosting de un sitio sospechoso.

**Probarlo desde Swagger:** `POST /analysis/ip` → Try it out →
`{"ip": "1.2.3.4"}` → Execute.

Usa el mismo servicio y motor de riesgo que el enriquecimiento de IP del
Módulo 1 (`abuseipdb_service.py` + `ip_risk_engine.py` — única fuente de
verdad para no duplicar los mismos umbrales en dos sitios), así que la
configuración (`ABUSEIPDB_API_KEY`) y las señales son exactamente las
mismas descritas en el Módulo 1. Participa también en la monitorización
continua (Módulo 10): una IP analizada se re-comprueba periódicamente por
si sube su puntuación de abuso.

**Señales que detecta:** ver la tabla del Módulo 1 (`IP_HIGH_ABUSE_SCORE`,
`IP_MODERATE_ABUSE_SCORE`, `IP_TOR_EXIT_NODE`) — son idénticas.

---

## Frontend

Panel visual de un solo archivo (`frontend/index.html`), sin build step ni
dependencias — habla directamente con el backend vía `fetch`. Cubre los
módulos de análisis, ver el histórico de casos con checkboxes de
selección, generar el informe (con o sin la valoración de IA), y una
pestaña de **Monitorización** con las alertas (con contador de pendientes
en el propio menú lateral) y el listado de sujetos monitorizados —
activar/desactivar, cambiar cada cuánto se re-chequean, o forzar un
chequeo inmediato con "Comprobar ahora".

**Cómo usarlo:**

1. Arranca el backend como siempre (`uvicorn app.main:app --reload`)
2. Abre `frontend/index.html` haciendo doble clic (se abre directamente en
   tu navegador — no hace falta servirlo desde ningún sitio)
3. En la barra lateral, campo "Backend", confirma que apunta a
   `http://127.0.0.1:8000` (es el valor por defecto)

**Flujo típico:** analiza un dominio y/o email en sus pestañas → ve a
"Casos guardados" y marca los casos que quieras incluir → en "Informe",
opcionalmente genera la valoración con IA (si no tienes
`ANTHROPIC_API_KEY` configurada, simplemente no se rellena, todo lo demás
funciona igual) → "Descargar informe PDF".

**Nota de diseño:** el medidor circular de riesgo (el "gauge") y los
colores de severidad son los mismos que usa el informe PDF — es
intencional, para que backend, frontend e informe se sientan como el
mismo producto.

---

## Tests automatizados

319 tests, ~90% de cobertura sobre `app/`. Cubren tanto los motores de
riesgo de forma aislada (lógica pura, sin red) como el flujo completo a
través de la API real (con las llamadas externas mockeadas).

### Instalación

```bash
pip install -r requirements-dev.txt
```

(`requirements-dev.txt` instala también `requirements.txt` — solo hace
falta este comando, no los dos.)

### Ejecutar los tests

```bash
pytest
```

Con reporte de cobertura:
```bash
pytest --cov=app --cov-report=term-missing
```

### Cómo están organizados

| Archivo | Qué prueba |
|---|---|
| `tests/conftest.py` | Fixtures compartidas: cliente de test con BD en memoria, datos simulados (WHOIS, SSL, emails) reutilizables. Incluye varios `autouse`: uno fuerza a vacío TODAS las API keys externas (para que una key real en tu `.env` local nunca "se cuele" en un test que no la mockea explícitamente), y otros evitan la resolución DNS real, la consulta real a crt.sh, la consulta real a Wayback Machine, el scraping real de la CNMV y la descarga real de las listas OFAC |
| `test_risk_engine.py` | Motor de riesgo de dominio: WHOIS/SSL/VirusTotal, reputación de IP (principal y adicionales), DNS (SPF/DMARC), subdominios de crt.sh y reciclaje de dominio vía Wayback (unitario, sin red) |
| `test_email_risk_engine.py` | Motor de riesgo de email: cabeceras, suplantación de nombre visible, enlaces, adjuntos y modo degradado sin raw source (unitario) |
| `test_email_service.py` | Parseo de cabeceras, extracción de enlaces/adjuntos del cuerpo y detección de si el texto es código fuente real (unitario, sin red) |
| `test_email_link_analysis.py` | Enriquecimiento de enlaces: acortadores, suplantación de marca, límite de dominios consultados (unitario, WHOIS/VirusTotal mockeados) |
| `test_wallet_risk_engine.py` | Motor de riesgo de wallet, incluida la señal OFAC (unitario) |
| `test_wallet_service.py` | Detección de chain/subtipo BTC y extractor de direcciones desde texto libre (unitario, sin red) |
| `test_typosquatting_service.py` | Generación de variantes de typosquatting (unitario, sin red) |
| `test_typosquatting_risk_engine.py` | Motor de riesgo de exposición a typosquatting (unitario) |
| `test_correlation_service.py` | Detección de coincidencias entre módulos, incluida typosquatting↔email (unitario) |
| `test_domain_analysis_api.py` | Endpoint de dominio de principio a fin (integración, WHOIS/SSL/VT/AbuseIPDB/DNS/crt.sh/Wayback mockeados) |
| `test_abuseipdb_service.py` | Cliente de AbuseIPDB (unitario, mockeado): degradación sin key, parseo, uso del header `Key` |
| `test_ip_risk_engine.py` | Motor de riesgo de IP, compartido entre dominio e IP (unitario) |
| `test_ip_analysis_api.py` | Endpoint de IP de principio a fin: caso feliz, degradación sin key, IP inválida, listado/detalle |
| `test_email_analysis_api.py` | Endpoint de email de principio a fin |
| `test_wallet_analysis_api.py` | Endpoint de wallet de principio a fin, incluidas multi-red EVM, Tron/USDT-TRC20, cruce OFAC y los endpoints de extracción/formato |
| `test_typosquatting_api.py` | Endpoint de typosquatting de principio a fin (DNS mockeado) |
| `test_phone_service.py` | Parseo de teléfono (unitario, 100% offline, sin mocks) |
| `test_phone_risk_engine.py` | Motor de riesgo de teléfono, incluidas las señales de OpenSpam, IPQualityScore y Twilio Lookup (unitario) |
| `test_phone_analysis_api.py` | Endpoint de teléfono de principio a fin, incluidas las tres integraciones externas mockeadas |
| `test_ipqualityscore_service.py` | Cliente de IPQualityScore (unitario, mockeado): degradación sin key, y regresión que confirma que el campo `name` (identidad) nunca se expone |
| `test_twilio_lookup_service.py` | Cliente de Twilio Lookup (unitario, mockeado): degradación sin credenciales, y regresión que confirma que solo se pide `line_type_intelligence` |
| `test_cnmv_service.py` | Parseo del listado HTML de la CNMV, incluido el caso de estructura inesperada (unitario) |
| `test_cnmv_risk_engine.py` | Motor de riesgo de verificación CNMV, incluidas las señales FCA y del registro de entidades (unitario) |
| `test_fca_register_service.py` | Cliente del registro FCA (unitario, mockeado): degradación sin credenciales, parseo, headers `X-Auth-*` |
| `test_cnmv_registry_service.py` | Cliente del registro de entidades de la CNMV (unitario, mockeado): búsqueda con/sin resultados, estructura inesperada, envío de tokens ASP.NET |
| `test_cnmv_api.py` | Endpoint de verificación CNMV de principio a fin, incluida la lógica de caché de 24h y la integración FCA |
| `test_image_service.py` | Hash perceptual y EXIF (unitario, 100% offline, sin mocks) |
| `test_image_risk_engine.py` | Motor de riesgo de imagen (unitario) |
| `test_image_analysis_api.py` | Endpoint de imagen de principio a fin, incluida la detección de reutilización entre casos, la búsqueda inversa (SerpApi) y la facial (PimEyes) |
| `test_image_cache.py` | Caché efímera en memoria de bytes de imagen: TTL, expiración, tokens de previsualización de un solo uso (unitario) |
| `test_serpapi_service.py` | Cliente de SerpApi (unitario, mockeado): degradación sin key/URL pública, parseo de resultados |
| `test_pimeyes_service.py` | Cliente de PimEyes (unitario, mockeado): degradación sin key, parseo de resultados |
| `test_report_and_consolidated_api.py` | Generación de PDF + análisis consolidado con IA (mockeada) |
| `test_monitoring_service.py` | Motor de monitorización (unitario): registro de sujetos, detección de subida de nivel/score, alertas |
| `test_monitoring_api.py` | Endpoints `/monitoring/*` y `/alerts/*` de principio a fin, incluido el runner que usa el scheduler (`run_due_checks`) |

### Por qué está diseñado así (útil para la memoria del TFM)

- **Nunca se llama a una API externa real en los tests.** WHOIS, SSL,
  VirusTotal, blockchain.info, Etherscan y la API de Claude están siempre
  mockeados con `unittest.mock.patch`. Esto hace que la suite sea rápida
  (toda la suite corre en menos de 1 segundo), determinista (no depende
  de que un servicio externo esté disponible en el momento de correr los
  tests) y gratuita (no consume cuota de ninguna API de pago).
- **Base de datos en memoria, aislada por test.** La fixture `client`
  sustituye la dependencia `get_db` por una sesión SQLite en memoria
  creada de cero en cada test. Nunca se toca tu `scamshield.db` real, y
  los tests no se contaminan entre sí.
- **Tests unitarios + de integración, no solo uno u otro.** Los motores de
  riesgo se prueban aislados (rápido, permite cubrir muchos casos límite)
  y también a través de la API completa (para pillar errores de "encaje"
  entre piezas que los tests unitarios no verían, como el ejemplo
  documentado de `test_raw_email_con_saltos_de_linea_reales_no_es_json_valido`,
  que deja constancia en código de un bug real que apareció durante el
  desarrollo).

---

## Estructura del proyecto

```
app/
├── main.py                          # arranque de FastAPI (lifespan: arranca/para el scheduler), registro de routers, creación de tablas
├── core/
│   ├── config.py                    # configuración (variables de entorno)
│   ├── database.py                  # conexión SQLAlchemy (SQLite ahora, PostgreSQL en producción)
│   └── scheduler.py                 # APScheduler en el mismo proceso: dispara los re-chequeos de monitorización
├── models/                          # tablas de base de datos (una por tipo de caso)
│   ├── case.py                      # casos de dominio
│   ├── email_case.py                # casos de email
│   ├── wallet_case.py               # casos de wallet
│   ├── typosquatting_case.py        # casos de typosquatting
│   ├── phone_case.py                # casos de teléfono
│   ├── cnmv_check_case.py           # casos de verificación CNMV
│   ├── cnmv_warning.py              # caché local de advertencias de la CNMV
│   ├── image_case.py                # casos de análisis de imagen
│   ├── reverse_image_search_case.py # resultados de búsqueda inversa (SerpApi) de un caso de imagen
│   ├── facial_search_case.py        # resultados de búsqueda facial (PimEyes) de un caso de imagen
│   ├── ip_case.py                   # casos de análisis de IP
│   ├── ofac_sanctioned_address.py   # caché local de direcciones sancionadas por la OFAC
│   └── monitoring.py                # MonitoredSubject + RiskAlert (monitorización continua)
├── schemas/                         # qué entra y sale de la API (Pydantic)
│   ├── domain_analysis.py           # incluye RiskFlag y AbuseIpInfo, compartidos por varios módulos
│   ├── email_analysis.py
│   ├── wallet_analysis.py
│   ├── typosquatting.py
│   ├── phone_analysis.py
│   ├── cnmv.py
│   ├── image_analysis.py
│   ├── ip_analysis.py
│   ├── report.py
│   ├── consolidated.py
│   └── monitoring.py
├── services/                        # lógica de negocio, sin saber nada de HTTP
│   ├── whois_service.py             # consulta WHOIS
│   ├── ssl_service.py               # inspección de certificados SSL
│   ├── risk_engine.py               # scoring de dominio (heurístico, delega en ip_risk_engine para la IP resuelta)
│   ├── domain_utils.py              # normalización de dominio compartida (dominio + typosquatting)
│   ├── domain_analysis_service.py   # orquesta el análisis de dominio (reutilizado por la ruta y por el scheduler)
│   ├── abuseipdb_service.py         # reputación de IP (AbuseIPDB) — compartido por dominio e IP
│   ├── ip_risk_engine.py            # scoring de IP — única fuente de verdad, compartida por dominio e IP
│   ├── ip_analysis_service.py       # orquesta el análisis de IP suelta
│   ├── email_service.py             # parseo de cabeceras/cuerpo/adjuntos de email
│   ├── email_link_analysis.py       # enriquece enlaces del cuerpo (acortadores, marca, WHOIS/VT acotado)
│   ├── brand_dictionary.py          # marcas frecuentemente suplantadas (nombre visible + enlaces)
│   ├── email_risk_engine.py         # scoring de email (cabeceras, nombre visible, enlaces, adjuntos)
│   ├── wallet_service.py            # consulta BTC (blockchain.info), ETH/EVM (Etherscan, multi-red) y Tron (TronGrid); extractor de direcciones
│   ├── wallet_risk_engine.py        # scoring de wallet
│   ├── wallet_analysis_service.py   # orquesta el análisis de wallet
│   ├── ofac_service.py              # cruce contra la lista de sancionados de la OFAC (BTC/ETH/Tron)
│   ├── typosquatting_service.py     # genera variantes de typosquatting
│   ├── dns_service.py               # resolución DNS en paralelo (pool de hilos) + registros completos de un dominio (dnspython)
│   ├── crtsh_service.py             # subdominios relacionados vía Certificate Transparency (crt.sh)
│   ├── wayback_service.py           # historial de capturas de un dominio (CDX API, Wayback Machine)
│   ├── typosquatting_risk_engine.py # scoring de exposición a typosquatting
│   ├── typosquatting_analysis_service.py  # orquesta el análisis de typosquatting
│   ├── phone_service.py             # parseo de teléfono (offline, phonenumbers)
│   ├── phone_risk_engine.py         # scoring de teléfono
│   ├── phone_analysis_service.py    # orquesta el análisis de teléfono
│   ├── openspam_service.py          # reportes comunitarios de spam (OpenSpam)
│   ├── ipqualityscore_service.py    # puntuación de fraude (VOIP/prepago/abuso/filtrado) — nunca el campo `name`
│   ├── twilio_lookup_service.py     # carrier/tipo de línea en tiempo real (line_type_intelligence) — de pago
│   ├── cnmv_service.py              # scraping del listado de advertencias CNMV + caché
│   ├── fca_register_service.py      # registro FCA (Reino Unido) — comprobación en positivo, no lista negra
│   ├── cnmv_registry_service.py     # registro de entidades autorizadas CNMV — comprobación en positivo (España)
│   ├── cnmv_risk_engine.py          # scoring de verificación CNMV (CNMV + FCA + registro de entidades)
│   ├── cnmv_analysis_service.py     # orquesta la verificación CNMV
│   ├── image_service.py             # EXIF + hash perceptual (offline, Pillow)
│   ├── image_risk_engine.py         # scoring de imagen (+ búsqueda inversa y facial)
│   ├── image_cache.py               # caché efímera en memoria de bytes de imagen + tokens de previsualización
│   ├── serpapi_service.py           # búsqueda inversa de imagen (SerpApi)
│   ├── pimeyes_service.py           # búsqueda de reconocimiento facial (PimEyes) — integración de referencia
│   ├── report_service.py            # genera el PDF combinado (reportlab)
│   ├── correlation_service.py       # detecta coincidencias entre módulos
│   ├── ai_service.py                # narrativa explicativa vía API de Claude
│   ├── virustotal_service.py        # consulta reputación en VirusTotal
│   ├── monitoring_service.py        # registro de sujetos + detección de subida de riesgo + alertas
│   └── monitoring_runner.py         # despacho por case_type: qué re-analizar y cuándo le toca a cada sujeto
└── api/routes/
    ├── analysis.py                  # POST /analysis/domain
    ├── cases.py                     # GET /cases, GET /cases/{id}
    ├── email_analysis.py            # POST /analysis/email(/file), GET /email-cases(/{id})
    ├── wallet_analysis.py           # POST /analysis/wallet, GET /wallet-cases(/{id})
    ├── typosquatting.py             # POST /analysis/typosquatting, GET /typosquatting-cases(/{id})
    ├── phone_analysis.py            # POST /analysis/phone, GET /phone-cases(/{id})
    ├── cnmv.py                      # POST /analysis/cnmv-check, GET /cnmv-check-cases(/{id}), GET /cnmv-warnings/cache-status
    ├── image_analysis.py            # POST /analysis/image, GET /image-cases(/{id}), POST .../reverse-search, POST .../facial-search, GET .../preview/{token}
    ├── ip_analysis.py                # POST /analysis/ip, GET /ip-cases(/{id})
    ├── report.py                    # POST /reports/generate
    ├── consolidated.py              # POST /analysis/consolidated
    └── monitoring.py                # GET/PATCH /monitoring/subjects(/{id}), POST .../check-now, GET /alerts, POST /alerts/{id}/acknowledge

frontend/
└── index.html                       # panel visual de un solo archivo, sin build step

tests/
├── conftest.py                      # fixtures compartidas (cliente de test, datos simulados)
├── test_risk_engine.py
├── test_abuseipdb_service.py
├── test_ip_risk_engine.py
├── test_email_risk_engine.py
├── test_email_service.py
├── test_email_link_analysis.py
├── test_wallet_risk_engine.py
├── test_wallet_service.py
├── test_typosquatting_service.py
├── test_typosquatting_risk_engine.py
├── test_phone_service.py
├── test_phone_risk_engine.py
├── test_ipqualityscore_service.py
├── test_twilio_lookup_service.py
├── test_cnmv_service.py
├── test_cnmv_risk_engine.py
├── test_fca_register_service.py
├── test_cnmv_registry_service.py
├── test_image_service.py
├── test_image_risk_engine.py
├── test_image_cache.py
├── test_serpapi_service.py
├── test_pimeyes_service.py
├── test_correlation_service.py
├── test_monitoring_service.py
├── test_domain_analysis_api.py
├── test_email_analysis_api.py
├── test_wallet_analysis_api.py
├── test_typosquatting_api.py
├── test_phone_analysis_api.py
├── test_cnmv_api.py
├── test_image_analysis_api.py
├── test_ip_analysis_api.py
├── test_monitoring_api.py
└── test_report_and_consolidated_api.py
```

## Por qué está organizado así

- **`services/` separado de `api/routes/`**: la lógica de negocio no sabe
  nada de HTTP. Esto facilita reutilizarla desde otros contextos (tests,
  scripts, un futuro worker en segundo plano) sin tocar código.
- **Un `risk_engine` por módulo, con la misma interfaz** (`RiskFlag` +
  score 0-100): en la fase de IA, un único modelo podrá combinar las
  señales de los 3 módulos en un score consolidado por caso, y también
  podrás comparar heurística vs IA sobre los mismos casos para la memoria
  del TFM.
- **Errores no tumban la respuesta** (en el módulo de dominio): si WHOIS
  falla pero SSL funciona, el endpoint responde igualmente con lo que
  consiguió y anota el error en `errors`. Las fuentes externas fallan
  constantemente (rate limits, timeouts) y el sistema tiene que ser
  resiliente a eso.

## Próximos pasos

- [x] Persistencia (SQLite ahora, PostgreSQL en producción — solo cambia `DATABASE_URL`)
- [x] Módulo de forense de email (cabeceras, enlaces del cuerpo, adjuntos, suplantación de marca; acepta código fuente o texto pegado)
- [x] Módulo de trazado de wallets cripto
- [x] Generación de informe PDF (junta los 3 tipos de caso en un documento único)
- [x] Capa de IA: correlación entre módulos + narrativa explicativa vía LLM (Claude)
- [x] Frontend (panel de un solo archivo, sin build step)
- [x] Integración con VirusTotal y AbuseIPDB (reputación de la IP resuelta) en el módulo de dominio
- [x] Detector de typosquatting (variantes de marca + correlación con email + reputación de IP AbuseIPDB para todas las variantes activas)
- [x] Análisis de teléfono (tipo de línea, operador, país + reportes comunitarios OpenSpam + puntuación de fraude IPQualityScore + carrier en tiempo real Twilio Lookup)
- [x] Verificación CNMV (chiringuitos financieros, caché local con refresco automático + comprobación en positivo contra el registro FCA del Reino Unido y el registro de entidades autorizadas de la propia CNMV)
- [x] Análisis de imagen (EXIF + hash perceptual + búsqueda inversa SerpApi + reconocimiento facial PimEyes acotado y con confirmación sellada en el ledger)
- [x] Cadena de custodia (SHA-256 encadenado + certificado en el PDF): `/integrity/verify`, `/integrity/ledger`, `/integrity/case/{tipo}/{id}`
- [x] "Dónde denunciar" en el informe PDF, según los tipos de evidencia incluidos (Policía, INCIBE, CNMV, GDT, AEPD)
- [x] Análisis de IP suelta (reputación AbuseIPDB, mismo motor que la IP resuelta del módulo de dominio)
- [x] Suite de tests automatizados (319 tests, ~90% cobertura)
- [x] Monitorización continua (re-chequeo periódico + alertas cuando sube el riesgo): `GET/PATCH /monitoring/subjects`, `GET /alerts`
- [ ] Cola de tareas con Celery + Redis (para no bloquear la petición HTTP; también sustituiría al scheduler en proceso de la monitorización si se despliega con varios workers)
- [ ] Autenticación (API keys / login) — necesaria antes de ser un SaaS real
- [ ] Notificación externa de alertas (email/webhook) — de momento las alertas de monitorización solo viven dentro de la herramienta (`GET /alerts`)
- [ ] Typosquatting + Certificate Transparency (`crt.sh`, API pública sin key): detectaría certificados SSL recién emitidos para dominios parecidos a la marca antes incluso de que resuelvan por DNS o de que el generador de variantes los contemple
- [ ] Typosquatting + comprobación de registros MX: una variante activa con servidor de correo configurado es indicio mucho más fuerte de fraude de facturas/BEC que un dominio simplemente aparcado
