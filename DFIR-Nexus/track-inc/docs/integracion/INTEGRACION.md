# Integrar esta versión de Tracking en `development`

Comparado con `origin/development` en el commit `4cc4096` (22/09/2026). Esta
carpeta del módulo ya incorpora lo que el equipo cambió al integrarlo; lo que
queda aquí es lo que vive **fuera** de `track-inc/` y hay que llevar a mano.

## 1. Qué hay ya fusionado en `track-inc/`

| Del equipo (se conserva) | Tuyo (se añade) |
|---|---|
| Sin `cases` provisional: Tracking no define ni importa `cases` | `app/dev/casos_locales.py`: casos de prueba **solo con SQLite** (contra MySQL no existe) |
| `case_exists` con SQL directo | Consultar un caso eliminado sí, escribir no (409), como Casos; archivado tampoco admite eventos |
| `GET /cases-lookup` para el selector | …filtrando los casos eliminados |
| Middleware de errores 500 en JSON con CORS | CORS cerrado a `localhost:5173` / `127.0.0.1:5173`, gzip, 404 JSON |
| Carga del `.env` por ruta absoluta (`load_dotenv`) | Mismo `.env`, además `MYSQL_*` y TLS |
| Alembic: tabla `alembic_version_tracking`, solo `tracking_events` | Misma URL que la app, aviso del destino |
| Tests con `SharedCaseRow` | Todos los tests nuevos adaptados a ese patrón |
| `start-dev.ps1` puede usar el `.env` | …solo con `-UsarEnv`; por defecto SQLite |

El frontend (`frontend/src/modules/tracking/`) ya usa `VITE_TRACKING_API_URL`
(por defecto `http://localhost:8001`, como development) y `/cases-lookup`.

## 2. Fuera de `track-inc/`: tabla compartida

El módulo de Tracking usa ordenación, clases por columna y `layout` en la
tabla compartida. `DataTable.development.tsx` es el `DataTable` de
`frontend/src/shared/ui/DataTable/` de development con esas tres cosas
**opcionales** y su mismo estilo de código. Sin usarlas, las tablas de los
demás módulos se pintan exactamente igual.

Comprobado: frontend de development + este módulo de Tracking + esta tabla →
`tsc -b` y `vite build` sin errores. Sin ella, 21 errores de tipos.

**Es un componente compartido: coméntalo con el equipo antes de subirlo.**

## 3. Fuera de `track-inc/`: volumen para la cadena de integridad

La verificación de integridad compara `tracking_events` con la cadena local
de cada caso. En el despliegue común (`deploy/docker-compose.yml` de la
raíz), el contenedor de Tracking no tiene volumen para esa cadena: cada
redespliegue la borraría y "Verificar integridad" daría fallo en todos los
casos con eventos. Añadir al servicio `tracking`:

```yaml
  tracking:
    # ...lo que ya tiene...
    environment:
      - DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}
      - TRACKING_CHAIN_DIR=/app/.tracking_chain
    volumes:
      - tracking-chain:/app/.tracking_chain

volumes:
  tracking-chain:
```

(Si falta, la API ya no acusa de manipulación: responde que no encuentra la
cadena y sugiere revisar el volumen.)

## 4. Cosas que no bloquean, pero conviene decir al equipo

- **Imagen de Tracking:** el `Dockerfile` ya construye por defecto solo la
  API (variante `api`). No necesita `track-inc/frontend/`, así que esa
  carpeta se puede borrar como pide la auditoría sin romper el despliegue.
- **Tamaño máximo de log:** 20 MB por defecto, igual que
  `client_max_body_size` de la pasarela (`TRACKING_MAX_LOG_MB` lo cambia).
- **TLS:** ningún otro backend cifra la conexión con Aiven (credenciales y
  datos viajan en claro por Internet). Tracking sí lo hace.
- **`env.py` de development:** su comentario dice que falta el `stamp` de
  Alembic en Aiven; el 11/09 `alembic_version_tracking` ya estaba en
  `6b5d49c8a514`, así que `alembic upgrade head` al arrancar no hace nada.
- **No copiar** `frontend/.env.production` al frontend único: allí las URL
  las fija la pasarela.

## Autenticación JWT (traída de development, commit `9d625bd`)

Ya está aplicada en este módulo:

- `app/modules/auth/{security,dependencies}.py`, copia de la pieza de Casos.
- `app/main.py`: los dos routers con `dependencies=[Depends(get_current_user)]`.
- `pyjwt` en `requirements-web.txt` y `JWT_SECRET` en `.env.example`.
- Frontend: `shared/auth/` (sesión y reacción al 401) y la cabecera puesta en
  `api/httpClient.ts`.
- Tests: cliente autenticado centralizado en `tests/conftest.py` y
  `tests/test_auth_tracking.py` (16 casos).

Diferencias respecto a la versión de `development`, a tener en cuenta al
integrar:

| Aquí | En development | Por qué |
|---|---|---|
| CORS con `_origenes_cors()` (lista + `CORS_ORIGINS`), `Authorization` incluida en `allow_headers` | `allow_origins=["http://localhost:5173"]` a fuego | mismo efecto en desarrollo, configurable en despliegue |
| `ApiError(status, detail)` en el `httpClient` de Tracking | `ApiError(detail, status)` | el contrato unificado con Casos, OSINT e Informes (ver auditoría) |
| El token se añade solo en `httpRequest` | además, a mano en `analyzeLog` | aquí `analyzeLog` ya pasa por `httpRequest` |
| `TRACKING_AUTH_DESACTIVADA` para el módulo suelto | no existe | el frontend único trae login; este módulo también se arranca solo |
| Cliente de test autenticado en `conftest.py` | fixture repetida en `test_routes.py` | esta suite crea clientes en diez ficheros |

`TRACKING_AUTH_DESACTIVADA` **no debe aparecer** en el despliegue común ni en
`npm run dev:all`: sin esa variable, la autenticación es obligatoria.
