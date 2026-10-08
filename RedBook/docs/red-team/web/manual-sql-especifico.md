---
tags:
- Auditoría web
date: '2026-09-09'
author: Carlos Gómez
---

# Manual SQL especifico

<p class="note-meta">2026-09-09 · Carlos Gómez</p>

**SQL**

**Manual específico de SQL para la sesión 09/09/2026**

MySQL aplicado a consultas, comprensión de SQLi y práctica académica

Profesor de la sesión: Carlos Gómez

Documento complementario a los apuntes del Máster de Ciberseguridad Ofensiva

Base: contenido de clase + ampliación técnica contrastada

▰  
▰  
▰

# 1. Objetivo y alcance

Este manual consolida las consultas SQL vistas en clase y las amplía para convertirlas en una referencia de estudio. La sesión trabajó sobre MySQL, mientras que el manual de Jorge Sánchez consultado está orientado principalmente a Oracle SQL. Por eso se separa la sintaxis común del SQL estándar de las instrucciones específicas de MySQL.

|  |
| --- |
| **INFO — Regla de lectura:** Todo lo marcado como “Clase” procede de la transcripción. Las secciones “Ampliación técnica” incorporan sintaxis y conceptos no demostrados de forma completa durante la sesión, contrastados con el manual de Jorge Sánchez y documentación oficial de MySQL. |

# 2. SQL, SGBD y dialectos

- SQL es un lenguaje declarativo: se expresa qué resultado se desea obtener y el SGBD decide cómo ejecutarlo.
- SQL tiene un estándar, pero Oracle, MySQL, PostgreSQL, SQL Server y otros SGBD añaden diferencias de sintaxis y comportamiento.
- En esta sesión el servidor de base de datos desplegado fue MySQL y el puerto trabajado fue TCP/3306.
- El manual de Jorge Sánchez resulta útil para fundamentos de SELECT, alias, JOIN, agrupaciones y subconsultas, pero sus ejemplos están orientados a Oracle.

| **Familia** | **Finalidad** | **Ejemplos** |
| --- | --- | --- |
| DQL | Consulta de datos | SELECT |
| DML | Modifica filas | INSERT, UPDATE, DELETE, MERGE |
| DDL | Define estructura | CREATE, ALTER, DROP, TRUNCATE |
| DCL | Permisos | GRANT, REVOKE |
| Control de transacciones | Confirma o revierte cambios | COMMIT, ROLLBACK |

# 3. Modelo mental de una base de datos relacional

|  |
| --- |
| Servidor MySQL  ↓ Bases de datos / schemas  ↓ Tablas  ↓ Columnas + filas  ↓ Relaciones mediante claves |

En clase se usó una base de datos de un taller mecánico con varias tablas, entre ellas empleados y clientes. La jerarquía anterior ayuda a entender qué enumeramos cuando hacemos SHOW DATABASES, SHOW TABLES o consultas SELECT.

# 4. Consultas de descubrimiento vistas en clase (MySQL)

**Clase — listar bases de datos visibles para el usuario actual**

|  |
| --- |
| SHOW DATABASES; |

En la sesión aparecieron INFORMATION\_SCHEMA, PERFORMANCE\_SCHEMA y la base de datos del taller. Es importante no asumir que esas bases internas serán idénticas en todos los despliegues ni que el usuario tendrá privilegios para ver todas.

**Clase — seleccionar la base de datos de trabajo**

|  |
| --- |
| USE taller\_mecanico; |

**Clase — listar tablas de la base de datos seleccionada**

|  |
| --- |
| SHOW TABLES; |

|  |
| --- |
| **INFO — Ampliación técnica:** En MySQL, INFORMATION\_SCHEMA permite consultar metadatos mediante SELECT. SHOW DATABASES y SHOW TABLES son cómodos en trabajo interactivo, pero en SQLi suele ser más útil consultar INFORMATION\_SCHEMA cuando el contexto lo permite. |

**Ampliación técnica — metadatos mediante INFORMATION\_SCHEMA**

|  |
| --- |
| SELECT SCHEMA\_NAME FROM INFORMATION\_SCHEMA.SCHEMATA;  SELECT TABLE\_NAME FROM INFORMATION\_SCHEMA.TABLES WHERE TABLE\_SCHEMA = DATABASE(); |

# 5. SELECT: proyección de columnas

**Clase — obtener todas las columnas**

|  |
| --- |
| SELECT \* FROM empleados; |

**Clase — obtener una sola columna**

|  |
| --- |
| SELECT nombre FROM empleados; |

**Ampliación técnica — varias columnas**

|  |
| --- |
| SELECT nombre, telefono FROM empleados; |

**Ampliación técnica — eliminar duplicados**

|  |
| --- |
| SELECT DISTINCT puesto FROM empleados; |

El asterisco es útil para reconocimiento rápido, pero en aplicaciones reales conviene seleccionar solo las columnas necesarias para reducir datos transferidos y evitar exposición accidental.

# 6. WHERE y operadores de comparación

**Clase — igualdad**

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora = 45.30; |

**Clase — comparación numérica**

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora <= 45.30; |

| **Operador** | **Significado** |
| --- | --- |
| = | igual |
| <> o != | distinto (según dialecto) |
| > | mayor que |
| < | menor que |
| >= | mayor o igual |
| <= | menor o igual |
| AND | todas las condiciones deben cumplirse |
| OR | basta una condición |
| NOT | niega una condición |

**Clase — dos condiciones encadenadas**

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora > 40  AND tarifa\_hora < 70; |

|  |
| --- |
| **ADVERTENCIA — Error corregido de clase:** Cuando se combinan condiciones con AND/OR, cada comparación debe ser una expresión completa. No basta escribir “tarifa\_hora < 70 AND > 40”; debe repetirse la columna o usarse BETWEEN. |

# 7. BETWEEN

**Clase — rango inclusivo**

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora BETWEEN 40 AND 70; |

BETWEEN incluye ambos extremos. Es equivalente, en este caso, a tarifa\_hora >= 40 AND tarifa\_hora <= 70.

# 8. ORDER BY

**Clase — ordenar de menor a mayor**

|  |
| --- |
| SELECT \* FROM empleados WHERE tarifa\_hora BETWEEN 40 AND 70 ORDER BY tarifa\_hora ASC; |

**Clase — ordenar por una columna distinta de la filtrada**

|  |
| --- |
| SELECT \* FROM empleados ORDER BY telefono ASC; |

**Ampliación técnica — ordenación por varios criterios**

|  |
| --- |
| SELECT \* FROM empleados ORDER BY tarifa\_hora DESC, nombre ASC; |

|  |
| --- |
| **ADVERTENCIA — Corrección:** ORDER BY necesita una expresión o columna por la que ordenar. ASC y DESC indican dirección; no sustituyen al nombre de columna. |

# 9. LIMIT

**Clase — devolver como máximo cinco filas**

|  |
| --- |
| SELECT \* FROM clientes LIMIT 5; |

**Ampliación técnica — paginación**

|  |
| --- |
| SELECT \* FROM clientes ORDER BY id\_cliente LIMIT 5 OFFSET 10; |

LIMIT es sintaxis habitual de MySQL. No debe extrapolarse literalmente a Oracle clásico, que históricamente ha usado mecanismos diferentes para limitar filas.

# 10. Expresiones, operaciones y alias

**Clase corregida — cálculo sin modificar los datos almacenados**

|  |
| --- |
| SELECT salario\_bruto\_anual \* 1.33 AS coste\_empresa FROM empleados; |

|  |
| --- |
| **BUENA PRÁCTICA — Detalle importante:** En SQL los decimales se escriben con punto, no con coma: 1.33, no 1,33. AS asigna un alias a la columna calculada y mejora la legibilidad del resultado. |

**Ampliación técnica — conservar columnas originales y cálculo**

|  |
| --- |
| SELECT nombre, salario\_bruto\_anual,  salario\_bruto\_anual \* 1.33 AS coste\_empresa FROM empleados; |

# 11. Funciones de agregación

| **Función** | **Uso** |
| --- | --- |
| COUNT(\*) | contar filas |
| SUM(columna) | sumar valores |
| AVG(columna) | media |
| MIN(columna) | mínimo |
| MAX(columna) | máximo |

**Ampliación técnica a partir de la operación comentada en clase**

|  |
| --- |
| SELECT SUM(salario\_bruto\_anual \* 1.33) AS coste\_total FROM empleados; |

**Ampliación técnica — responder realmente “cuántos”**

|  |
| --- |
| SELECT COUNT(\*) AS num\_empleados FROM empleados WHERE tarifa\_hora BETWEEN 40 AND 70; |

# 12. GROUP BY y HAVING — ampliación técnica

El manual de Jorge Sánchez desarrolla las consultas de totales y agrupaciones. GROUP BY crea grupos por valores comunes; HAVING filtra grupos después de agregar.

|  |
| --- |
| SELECT puesto, COUNT(\*) AS personas, AVG(tarifa\_hora) AS media\_tarifa FROM empleados GROUP BY puesto ORDER BY media\_tarifa DESC; |

|  |
| --- |
| SELECT puesto, COUNT(\*) AS personas FROM empleados GROUP BY puesto HAVING COUNT(\*) >= 2; |

# 13. JOIN — ampliación técnica

Al inicio de la clase se mencionaron INNER JOIN y alias, pero no se desarrollaron con un ejercicio completo. Se incluyen aquí como ampliación porque son esenciales para consultar bases relacionales y aparecen en el manual de referencia.

**INNER JOIN — solo relaciones coincidentes**

|  |
| --- |
| SELECT c.nombre, v.matricula FROM clientes AS c INNER JOIN vehiculos AS v  ON v.id\_cliente = c.id\_cliente; |

**LEFT JOIN — conserva todos los clientes aunque no tengan vehículo asociado**

|  |
| --- |
| SELECT c.nombre, v.matricula FROM clientes AS c LEFT JOIN vehiculos AS v  ON v.id\_cliente = c.id\_cliente; |

| **JOIN** | **Resultado conceptual** |
| --- | --- |
| INNER JOIN | solo filas con coincidencia en ambos lados |
| LEFT JOIN | todas las filas de la izquierda + coincidencias |
| RIGHT JOIN | todas las filas de la derecha + coincidencias |
| CROSS JOIN | producto cartesiano; usar con cuidado |

# 14. Subconsultas — ampliación técnica y corrección

Durante la explicación se intentó ilustrar una consulta anidada, pero la formulación oral quedó incompleta. Una subconsulta válida debe producir un resultado que tenga sentido para la consulta exterior y normalmente se encierra entre paréntesis.

**Ejemplo correcto — empleados por encima de la tarifa media**

|  |
| --- |
| SELECT nombre, tarifa\_hora FROM empleados WHERE tarifa\_hora > (  SELECT AVG(tarifa\_hora)  FROM empleados ); |

# 15. LIKE, IN, NULL y otras herramientas útiles — ampliación

|  |
| --- |
| SELECT \* FROM clientes WHERE nombre LIKE 'Mar%'; SELECT \* FROM empleados WHERE puesto IN ('mecanico','recepcion'); SELECT \* FROM clientes WHERE telefono IS NULL; |

LIKE usa comodines (% para cualquier secuencia y \_ para un solo carácter). NULL no se compara con =; se usa IS NULL o IS NOT NULL.

# 16. Orden lógico de una consulta SELECT

|  |
| --- |
| SELECT columnas FROM tablas JOIN ... WHERE filtro\_filas GROUP BY grupos HAVING filtro\_grupos ORDER BY orden LIMIT cantidad; |

Este orden de escritura ayuda a construir consultas legibles. El optimizador interno puede decidir un plan de ejecución diferente, por lo que una consulta corta no es automáticamente más rápida.

|  |
| --- |
| **ADVERTENCIA — Corrección técnica:** En clase se asoció directamente “menos operadores” con “consulta más rápida”. La optimización real depende del plan de ejecución, índices, cardinalidad, estadísticas, joins y selectividad; no puede concluirse solo por la longitud textual. |

# 17. Conexión con SQL Injection

El objetivo de aprender SQL en este bloque es poder inferir qué consulta puede estar construyendo una aplicación y entender cómo una entrada no validada puede alterar su estructura. En clase se representó de forma conceptual una consulta PHP que incorpora un parámetro GET en una sentencia SELECT.

**Modelo conceptual**

|  |
| --- |
| SELECT \* FROM alguna\_tabla WHERE algun\_campo = '<entrada\_usuario>'; |

|  |
| --- |
| **BUENA PRÁCTICA — Defensa:** En aplicaciones reales deben utilizarse consultas parametrizadas/prepared statements y cuentas de base de datos con mínimo privilegio. La concatenación directa de entrada del usuario en SQL es una causa clásica de SQL Injection. |

# 18. Chuleta rápida de consultas de la sesión

| **Objetivo** | **Consulta** |
| --- | --- |
| Listar bases | SHOW DATABASES; |
| Elegir base | USE taller\_mecanico; |
| Listar tablas | SHOW TABLES; |
| Todo de una tabla | SELECT \* FROM empleados; |
| Una columna | SELECT nombre FROM empleados; |
| Filtrar | SELECT \* FROM empleados WHERE tarifa\_hora <= 45.30; |
| Dos filtros | SELECT \* FROM empleados WHERE tarifa\_hora > 40 AND tarifa\_hora < 70; |
| Rango | SELECT \* FROM empleados WHERE tarifa\_hora BETWEEN 40 AND 70; |
| Ordenar | SELECT \* FROM empleados ORDER BY tarifa\_hora ASC; |
| Limitar | SELECT \* FROM clientes LIMIT 5; |
| Cálculo + alias | SELECT salario\_bruto\_anual \* 1.33 AS coste\_empresa FROM empleados; |

# 19. Banco de ejercicios

1. Lista todas las bases de datos disponibles y selecciona la del taller.
2. Lista las tablas de la base seleccionada.
3. Muestra todas las columnas de empleados.
4. Muestra únicamente nombre y teléfono de empleados.
5. Obtén empleados con tarifa\_hora igual a 45.30.
6. Obtén empleados con tarifa\_hora menor o igual a 45.30.
7. Obtén empleados entre 40 y 70 usando AND.
8. Repite el ejercicio anterior usando BETWEEN.
9. Ordena esos empleados por tarifa\_hora ascendente.
10. Ordénalos por tarifa\_hora descendente y nombre ascendente.
11. Muestra los cinco primeros clientes.
12. Muestra cinco clientes a partir del undécimo resultado.
13. Calcula el coste\_empresa como salario\_bruto\_anual \* 1.33 y usa un alias.
14. Calcula el coste total de toda la plantilla.
15. Cuenta cuántos empleados tienen tarifa\_hora entre 40 y 70.
16. Calcula tarifa media, mínima y máxima.
17. Agrupa por puesto y cuenta empleados por puesto.
18. Filtra los grupos para mostrar solo puestos con al menos dos personas.
19. Busca clientes cuyo nombre empiece por M.
20. Busca clientes cuyo teléfono sea NULL.
21. Haz un INNER JOIN entre clientes y vehículos mediante su clave relacionada.
22. Haz un LEFT JOIN para conservar clientes sin vehículo.
23. Obtén empleados con tarifa superior a la media mediante subconsulta.
24. Muestra puestos distintos sin duplicados.
25. Explica por qué una consulta con menos texto no tiene por qué ejecutarse más rápido.

# 20. Soluciones orientativas

**1.** SHOW DATABASES; / USE taller\_mecanico;

**2.** SHOW TABLES;

**3.** SELECT \* FROM empleados;

**4.** SELECT nombre, telefono FROM empleados;

**5.** SELECT \* FROM empleados WHERE tarifa\_hora = 45.30;

**6.** SELECT \* FROM empleados WHERE tarifa\_hora <= 45.30;

**7.** SELECT \* FROM empleados WHERE tarifa\_hora >= 40 AND tarifa\_hora <= 70;

**8.** SELECT \* FROM empleados WHERE tarifa\_hora BETWEEN 40 AND 70;

**9.** ... ORDER BY tarifa\_hora ASC;

**10.** ... ORDER BY tarifa\_hora DESC, nombre ASC;

**11.** SELECT \* FROM clientes LIMIT 5;

**12.** SELECT \* FROM clientes LIMIT 5 OFFSET 10;

**13.** SELECT salario\_bruto\_anual \* 1.33 AS coste\_empresa FROM empleados;

**14.** SELECT SUM(salario\_bruto\_anual \* 1.33) AS coste\_total FROM empleados;

**15.** SELECT COUNT(\*) AS cantidad FROM empleados WHERE tarifa\_hora BETWEEN 40 AND 70;

**16.** SELECT AVG(tarifa\_hora), MIN(tarifa\_hora), MAX(tarifa\_hora) FROM empleados;

**17.** SELECT puesto, COUNT(\*) FROM empleados GROUP BY puesto;

**18.** SELECT puesto, COUNT(\*) FROM empleados GROUP BY puesto HAVING COUNT(\*) >= 2;

**19.** SELECT \* FROM clientes WHERE nombre LIKE 'M%';

**20.** SELECT \* FROM clientes WHERE telefono IS NULL;

**21.** La condición ON debe usar las claves reales del esquema. No se inventan nombres si el script no está disponible.

**22.** LEFT JOIN conserva todas las filas de la tabla izquierda aunque no exista coincidencia.

**23.** SELECT nombre, tarifa\_hora FROM empleados WHERE tarifa\_hora > (SELECT AVG(tarifa\_hora) FROM empleados);

**24.** SELECT DISTINCT puesto FROM empleados;

**25.** El rendimiento depende del plan de ejecución, índices, estadísticas, cardinalidad y selectividad.

# 21. Errores frecuentes detectados en la sesión

| **Error** | **Forma correcta / interpretación** |
| --- | --- |
| ORDER BY ASC | ORDER BY columna ASC |
| columna < 70 AND > 40 | columna < 70 AND columna > 40, o BETWEEN |
| 1,33 | 1.33 en un literal decimal SQL |
| Asumir que SELECT \* es siempre ideal | Útil para explorar; en producción seleccionar solo lo necesario |
| Creer que consulta más corta = más rápida | Revisar plan de ejecución e índices |
| Usar sintaxis Oracle como si fuera idéntica a MySQL | Confirmar dialecto del SGBD |

# 22. Fuentes consultadas

- **Jorge Sánchez — Introducción al lenguaje SQL:** [abrir fuente](https://jorgesanchez.net/manuales/sql/intro-sql-sql2016.html) — Manual orientado a Oracle SQL; usado como ampliación conceptual.
- **Jorge Sánchez — Consultas simples con SELECT:** [abrir fuente](https://jorgesanchez.net/manuales/sql/select-basico-sql2016.html)
- **Jorge Sánchez — JOIN:** [abrir fuente](https://jorgesanchez.net/manuales/sql/select-join-sql2016.html)
- **Jorge Sánchez — Agrupaciones y totales:** [abrir fuente](https://jorgesanchez.net/manuales/sql/select-totales-sql2016.html)
- **Jorge Sánchez — Subconsultas:** [abrir fuente](https://jorgesanchez.net/manuales/sql/select-subconsultas-sql2016.html)
- **MySQL 8.4 — SELECT:** [abrir fuente](https://dev.mysql.com/doc/refman/8.4/en/select.html) — Referencia oficial de la sintaxis usada en el laboratorio.
- **MySQL 8.4 — SHOW DATABASES:** [abrir fuente](https://dev.mysql.com/doc/refman/8.4/en/show-databases.html)
- **MySQL 8.4 — SHOW TABLES:** [abrir fuente](https://dev.mysql.com/doc/refman/8.4/en/show-tables.html)
