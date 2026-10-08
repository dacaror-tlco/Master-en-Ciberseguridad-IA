---
tags:
- Inteligencia artificial
---

# IA Practica 1 Grafos Subagentes Infraestructura

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**IA: Presentación de la Práctica 1**

Instructor: Carlos Gómez Pintado · 30/07/2026

*Bloque de Inteligencia Artificial — Grafos de conocimiento, subagentes, machine learning e infraestructura*

# **1. Cómo leer estos apuntes**

| **ℹ Cómo leer estos apuntes**  Estos apuntes recogen **lo que se explicó en clase** y añaden, marcadas aparte, las **correcciones y ampliaciones** necesarias. La sesión tuvo una primera parte muy larga de charla informal ajena a la materia: se ha eliminado por completo y solo se conserva el contenido técnico impartido por Carlos Gómez. |
| --- |

Cada corrección indica **qué se dijo**, **qué conviene precisar** y **por qué**. El objetivo no es contradecir al instructor —cuya intuición de fondo es correcta en casi todos los puntos— sino evitar que una imprecisión terminológica se arrastre al examen o a la práctica de verano.

| **⚠ Número de sesión pendiente de confirmar**  La transcripción no asigna número de sesión. El documento se titula por su tema. **Verifica el número de sesión en el campus antes de archivarlo.** |
| --- |

# **2. Objetivos de aprendizaje**

- Consolidar la diferencia entre **grafo relacional de notas**, **grafo con ontología** y **red neuronal**, y saber cuándo usar cada uno.
- Entender por qué un **índice de conocimiento** (bóveda de Obsidian) reduce el consumo de **tokens** de un agente frente a leer el proyecto entero.
- Conocer el patrón de **arquitectura de subagentes** para investigación: buscadores en paralelo, agente de poda (*jardinero*) y agente conector.
- Aplicar el **enrutado de modelos** (*model routing*): reservar los modelos caros para tareas complejas y usar el modelo barato para búsqueda masiva.
- Distinguir con rigor **qué es machine learning y qué no lo es**, a partir de la demostración de Tetris con tres algoritmos.
- Comprender el flujo **desarrollo → GitHub → servidor de producción** y la autenticación por **claves SSH** (pública/privada).
- Conocer los **requisitos obligatorios de la Práctica 1** y la organización en grupos.

# **3. Resumen inicial**

La sesión encadena tres bloques. Primero, un **repaso de estructuras de conocimiento**: Obsidian como índice relacional, Neo4j como grafo con ontología y el machine learning como algoritmos que sí aprenden. Segundo, una **demostración práctica**: un panel web de Tetris con tres algoritmos (Q-learning, heurística y neuroevolución) que el propio instructor advierte que es **una simulación, no un entrenamiento real**, y la construcción en directo de una bóveda de conocimiento sobre ajedrez mediante diez subagentes en paralelo.

Tercero, la parte de **infraestructura y organización**: Git y GitHub, el flujo hasta un servidor de producción, la generación y uso de **claves SSH**, el proveedor Hetzner y, finalmente, el **enunciado y los requisitos de la Práctica 1** con la formación de grupos. El hilo conductor de toda la clase es uno solo: **optimizar el consumo de tokens estructurando bien la información**.

# **4. Conceptos y terminología**

## **4.1. Repaso: las tres estructuras (tal como se presentaron)**

Carlos abrió la clase repasando el esquema de la sesión anterior. Esta es la síntesis de lo dicho, en pizarra:

| **Estructura** | **Herramienta** | **Qué es, según la clase** |
| --- | --- | --- |
| Grafo direccional / relacional | Obsidian Graph | Un **índice**. Aunque lo parezca, *no es una red neuronal*. |
| Red vectorial con ontología | Neo4j | Nodos y relaciones donde la arista **describe la relación** (p. ej. *el coche tiene color rojo*: la ontología es *tiene color*). |
| Machine learning | Algoritmos | Algoritmos que **utilizan redes neuronales para aprender**. |

| **✓ Punto bien fijado en clase**  El instructor fue **explícito y correcto** en el punto más importante: *«Obsidian no es una red neuronal, aunque lo parezca: es un índice»* y *«esto no va a aprender, lo único que tienes son referencias»*. Es exactamente la distinción que se corrigió en apuntes anteriores y aquí ya aparece bien formulada desde el principio. Consolídala. |
| --- |

| **⚠ Corrección clave: un grafo con ontología no aprende solo**  **Se dijo en clase:** que *«mi grafo va a aprender cuando sea una red vectorial, una red vectorial además con ontología»*, y que Neo4j es *«donde metemos la inteligencia»*. |
| --- |

**Conviene precisar:** un grafo con ontología —por muy rico que sea— **tampoco aprende por sí solo**. Neo4j es una **base de datos de grafos**: almacena nodos y aristas tipadas y permite consultarlas (Cypher) y calcular métricas de grafo. Que soporte índices vectoriales para búsqueda por similitud **no lo convierte en un modelo que se entrene**. El aprendizaje aparece solo cuando se ejecuta un algoritmo de *machine learning* **sobre** esos datos (por ejemplo *graph machine learning* o *graph neural networks*), y eso es un paso adicional, no una propiedad de la base de datos.

**Por qué importa:** la progresión real es *fuente de datos → grafo → dataset → entrenamiento*, no *Obsidian → Neo4j → inteligencia*. Neo4j sustituye a Obsidian como almacén consultable, no como cerebro.

## **4.2. Vocabulario nuevo de la sesión**

| **Término** | **Definición** |
| --- | --- |
| **Ontología** | El **significado explícito** de la relación entre dos nodos. En lugar de un enlace vacío, la arista dice *qué* une a los nodos (*tiene color*, *es modelo de*, *protege a*). |
| **MOC** (*Map of Content*) | Nota-índice dentro de una bóveda de Obsidian que agrupa y enlaza el resto de notas de un tema. Es el punto de entrada que consulta el agente. |
| **Bóveda** (*vault*) | Carpeta de trabajo de Obsidian: un conjunto de ficheros Markdown enlazados entre sí. |
| **Subagente** | Agente lanzado por otro agente para una subtarea acotada. Se pueden ejecutar varios **en paralelo**. |
| **Agente de poda** (*jardinero*) | Subagente cuya única función es detectar información duplicada entre los resultados de los buscadores y consolidarla en un solo nodo. |
| **Agente conector** | Subagente que lee los nodos ya podados y **crea las relaciones** entre ellos. |
| **Skill** | Fichero de instrucciones persistente que fija el comportamiento y las pautas que un agente debe seguir, sin releer toda la fuente cada vez. |
| **Tasa de mutación** | En neuroevolución, magnitud de la variación aleatoria que se aplica a los valores entre generaciones (*«si trabajamos con un 1, probamos 1,2 · 1,08 · 1,25…»*). |
| **Población** | Número de redes que compiten simultáneamente en una generación de neuroevolución. |
| **Heurística** | Regla o función de evaluación que escoge la opción **potencialmente mejor en cada momento**, sin garantizar el óptimo global. |
| **Clave pública / privada** | Par criptográfico. La **pública** se sube al servidor; la **privada** se queda en tu máquina y es la que te autentica. |
| **Servidor de pre / de producción** | *Pre* (o desarrollo) es tu propio equipo; *producción* es el servidor con IP pública donde se publica la aplicación. |

# **5. Explicación intuitiva: la biblioteca de Alejandría**

La analogía central de la clase, y la que mejor resume el porqué de todo lo demás. Imagina que tienes todos los pergaminos de la biblioteca de Alejandría **amontonados en una única caja gigante** y te piden uno concreto. Tienes que:

1. Abrir cada pergamino.
2. Leerlo entero.
3. Compararlo con lo que buscas.
4. Descartarlo y pasar al siguiente.

En términos de un agente de IA, eso son **cuatro operaciones que consumen tokens** por cada documento: búsqueda, listado, lectura y comparación. Si en cambio la biblioteca está **ordenada en estanterías con un índice**, vas directo a la sección, consultas el índice y sacas el documento: **una o dos operaciones en lugar de cuatro**.

La versión moderna que usó Carlos: el cartel **«usted está aquí»** de un centro comercial. En vez de recorrer el edificio entero buscando la salida, miras el plano y sabes por dónde ir.

| **✓ Por qué esto importa en un proyecto real**  Traducción al proyecto real: una aplicación de millones de líneas de código con un bug. Sin índice, el agente lee y entiende todo el código para localizar el problema. Con una bóveda de Obsidian donde **cada fichero de código es un nodo** y hay un MOC que los relaciona, el agente lee el índice, salta al nodo del problema y lo arregla. *«Estamos hiperoptimizando el uso de tokens»*. |
| --- |

# **6. Desarrollo técnico**

## **6.1. El grafo relacional como índice del proyecto**

Carlos mantiene **una bóveda de Obsidian por cada proyecto** que desarrolla. Su contenido no es el código, sino la **documentación estructurada del código**: un nodo por fichero (.js, .py, .css…), con las relaciones que indican qué fichero llama a cuál y qué método habla con qué otro.

El agente no navega el repositorio: navega el índice. Ejemplo dado en clase con el grafo de ajedrez: si la consulta es *«¿puedo hacer un rey ahogado?»*, el agente entra por el nodo **reglas**, que está relacionado con **jaque mate** y con **patrones de mate**, y de ahí baja al nodo concreto.

| **ℹ Matiz: no es inteligencia, pero sí es la herramienta correcta**  **Se dijo en clase** que este grafo *«no vale para una mierda»* si lo que se quiere es inteligencia. **Matiz:** es cierto que un grafo de notas no aprende, pero **sí es la pieza correcta** para lo que se está usando: documentación navegable y ahorro de contexto. Es la misma idea que hay detrás de **RAG** (*Retrieval-Augmented Generation*): recuperar solo el fragmento relevante y meterlo en el contexto en tiempo de inferencia. Los pesos del modelo no cambian, pero la calidad de la respuesta sí. No es un fracaso de red neuronal: es un acierto de arquitectura de contexto. |
| --- |

Carlos también fue claro sobre el límite: se puede meter un agente que recorra los nodos, correlacione y **parezca** que ha razonado, pero *«la inteligencia la pone el modelo que lee el grafo, no el grafo»*. Esa frase es técnicamente correcta y conviene memorizarla.

## **6.2. Arquitectura de subagentes para investigación**

Patrón usado en directo para construir la base de conocimiento de ajedrez. Es el mismo patrón que se aplica a un *deep research* propio:

| **1. Se lanzan de 1 a N subagentes buscadores en paralelo (en clase, 10)** |
| --- |

**↓**

| **2. Cada buscador cubre un ámbito distinto y vuelca sus notas en la bóveda** |
| --- |

**↓**

| **3. El agente de poda (jardinero) detecta duplicados y consolida nodos** |
| --- |

**↓**

| **4. El agente conector lee los nodos y crea las relaciones entre ellos** |
| --- |

**↓**

| **5. Resultado: grafo navegable listo para alimentar de contexto al agente principal** |
| --- |

| **ℹ NOTA**  Este diagrama es una **representación simplificada** del flujo descrito en clase. |
| --- |

Los diez subagentes recibieron un encargo temático distinto: normas del ajedrez, movimientos de cada pieza, notación, aperturas, táctica, estrategia, finales, estructuras de peones, planes de evaluación e historia y estilos. El resultado es una bóveda con esos MOC como puntos de entrada.

## **6.3. Enrutado de modelos: usa el modelo barato para lo simple**

Regla dada explícitamente por Carlos para el patrón anterior: para los subagentes buscadores hay que usar **el modelo más rápido y barato de la familia**, no el más capaz. Su razonamiento textual: *«no hay complejidad en la tarea; es buscar información, buscar en Google, copiar y pegar»*.

| **⚠ Corrección de nomenclatura: no existe «Haiku 5»**  **Se dijo en clase:** *«utilizar Haiku 5»*, y que usar *«un Fable 5 o un Opus 5 no tiene sentido»*. **Conviene precisar el nombre:** a fecha de consulta (30/07/2026) **no existe un modelo llamado «Haiku 5»**. El modelo vigente de la familia Haiku —la más rápida y económica— es **Claude Haiku 4.5**. El resto de la afirmación es correcta: Opus 5 y Fable 5 son los niveles de mayor capacidad y coste, y desperdiciarlos en una búsqueda web es tirar presupuesto. **El criterio de fondo es válido:** ajusta el modelo a la dificultad de la tarea. |
| --- |

| **Nivel** | **Modelo vigente (30/07/2026)** | **Cuándo usarlo según el criterio de clase** |
| --- | --- | --- |
| Rápido y económico | Claude Haiku 4.5 | Subagentes de búsqueda, lecturas simples, alto volumen |
| Equilibrado (por defecto) | Claude Sonnet 5 | Trabajo general de desarrollo y análisis |
| Alta capacidad | Claude Opus 5 | Código difícil y cadenas agénticas largas |
| Máxima capacidad | Claude Fable 5 | Solo cuando la capacidad justifica el coste y la facturación aparte |

| **⚠ Aviso temporal**  Los nombres de modelo, precios y límites de plan **cambian con frecuencia**. Esta tabla refleja la consulta del 30/07/2026 y debe contrastarse con la documentación oficial de Anthropic antes de usarse como referencia definitiva. |
| --- |

## **6.4. La demostración del Tetris: tres algoritmos comparados**

Carlos generó con Claude un panel web donde un agente aprende a jugar al Tetris, con controles de **tasa de mutación**, **población** y **velocidad de simulación**, y una gráfica de curva de aprendizaje.

| **⚠ La demo es una simulación, no un entrenamiento real**  **Advertencia dada por el propio instructor, y hay que conservarla:** *«lo que vais a ver es un cartón piedra que es totalmente fake; el resultado de esto no va a ser un algoritmo de machine learning real»*. Es una **simulación visual** en HTML del comportamiento de tres algoritmos, no un entrenamiento. Sirve para intuir cómo se conectan los nodos y cómo evoluciona una curva de aprendizaje. **No es evidencia de rendimiento de ningún algoritmo.** |
| --- |

| **Algoritmo** | **Cómo se explicó en clase** | **Resultado en la demo** |
| --- | --- | --- |
| **Q-learning** | *«Da a cada tipo de ficha un valor y ve el resultado»*. Carlos comenta que le gusta poco porque *«solo mete 2 nodos»*. | 8 líneas |
| **Heurística** | *«La mejor posibilidad en cada momento»*. Deja huecos grandes buscando completar varias líneas de golpe, porque cada línea es un +1 de recompensa. | 143 → 223 → 485 líneas |
| **Neuroevolución** | Prueba pequeñas variaciones sobre los valores (tasa de mutación) y conserva las mejores. *«Coge diferentes nodos, diferentes posiciones y va eligiendo la mejor»*. | Más de 500 líneas |

| **⚠ Corrección: heurística ≠ aleatoriedad**  **Se dijo en clase:** *«la heurística no se basa en la ciencia como tal, sino que es aleatoriedad»*. **Conviene precisar:** una heurística **no es aleatoriedad**. Es una **función de evaluación** —una regla práctica— que puntúa cada opción disponible y escoge la mejor según ese criterio. En un Tetris, esa función típicamente penaliza huecos tapados, altura de la pila y superficie irregular, y premia líneas completadas. Es determinista dado un estado. Lo que **no** garantiza es el óptimo global: por eso se llama heurística y no algoritmo exacto. El ejemplo que dio Carlos a continuación —colocar edificios en un terreno para cubrir el máximo posible— es precisamente un caso clásico de heurística, y es correcto. |
| --- |

| **⚠ Corrección: Q-learning no es una red neuronal**  **Se dijo en clase** que el Q-learning *«solo mete 2 neuronas, 2 nodos»*. **Conviene precisar:** el **Q-learning clásico no tiene neuronas en absoluto**. Es un algoritmo de **aprendizaje por refuerzo tabular**: mantiene una tabla que asocia cada par *(estado, acción)* con un valor Q, y actualiza esos valores según la recompensa obtenida. Solo cuando esa tabla se sustituye por una red neuronal se habla de **Deep Q-Network (DQN)**, que sí es una red. La intuición de clase —que es más limitado que la neuroevolución para este problema— tiene fondo (el espacio de estados del Tetris es enorme para una tabla), pero la explicación por «número de neuronas» no es la razón. |
| --- |

| **ℹ Simplificación didáctica corregida: mutación vs. peso**  **Se dijo en clase:** *«¿qué es la tasa de mutación? Es el peso que le podemos dar para ir superándolo»*. **Conviene precisar:** tasa de mutación **no** es lo mismo que peso. El **peso** es un número interno de la red que indica cuánto influye la salida de una neurona sobre la siguiente. La **tasa de mutación** es un parámetro del algoritmo evolutivo: la probabilidad o magnitud con la que esos pesos se perturban aleatoriamente al pasar de una generación a la siguiente. Más adelante Carlos lo explicó bien: *«va haciendo pequeñas variaciones sobre el valor: 1,2 · 1,08 · 1,25…»*. Esa segunda explicación es la correcta. |
| --- |

## **6.5. Qué es y qué NO es machine learning**

La parte más valiosa de la sesión desde el punto de vista conceptual. Carlos delimitó el término con ejemplos concretos y acertó en todos ellos:

| **NO es machine learning** | **SÍ es machine learning** |
| --- | --- |
| Buscar información en Internet con subagentes | Aprender a jugar al Tetris desde cero por prueba y error |
| Mapear y relacionar esa información en un grafo | Detectar patrones en una mamografía para identificar cáncer de mama en etapa temprana |
| Generar una *skill* a partir de errores observados | Cualquier algoritmo que, partiendo de no saber hacer algo, mejora iterando sobre datos |
| Que un agente lea la documentación oficial de AWS y actúe en consecuencia | — |

| **✓ Definición útil para el examen**  Definición operativa que dio Carlos y que conviene memorizar tal cual: *«Machine learning es cuando consigues que el algoritmo aprenda a hacer algo que al principio no sabía»*. Es una definición informal pero correcta y muy útil como filtro rápido. |
| --- |

El razonamiento sobre **dónde tiene sentido meter inteligencia** también es correcto y merece retenerse:

- **¿Tiene sentido meter inteligencia en código ya escrito?** No. *«¿Que tu código aprenda de tu código? ¿A qué? ¿Cómo se llaman los métodos entre sí? Si ya lo sabes.»*
- **¿En aprender a jugar al Tetris?** Sí: hay que descubrir una estrategia que no está escrita en ninguna parte.
- **¿En detectar anomalías en imagen médica?** Sí: hay patrones que ni siquiera el humano ha formalizado.

| **ℹ Frase que resume la clase**  Síntesis del instructor: *«la inteligencia se la metemos al dato; el dato enriquece la aplicación; la aplicación tiene su código indexado en un Obsidian»*. Tres capas, tres herramientas, tres propósitos. |
| --- |

## **6.6. Debate de clase: SQL, Neo4j y Obsidian en la misma arquitectura**

Uno de los alumnos planteó su arquitectura para una herramienta de *pentesting* automatizado: **PostgreSQL** como fuente de verdad canónica donde entra la información en bruto, **Neo4j** como proyección navegable del conocimiento ya saneado, y **Obsidian** como documentación pura.

La postura de Carlos fue que ese triple almacenamiento es **redundante** —*«triple gasto de recursos»*— y propuso un reparto estricto:

| **Capa** | **Herramienta** | **Qué guarda** | **Qué NO debe guardar** |
| --- | --- | --- | --- |
| Datos de aplicación | SQL (PostgreSQL, MySQL…) | Usuarios, contraseñas, imágenes, comentarios, reseñas | Código ni conocimiento estructurado |
| Conocimiento e inteligencia | Neo4j | Entidades y relaciones con ontología; base para algoritmos de ML | Documentación del código |
| Documentación del código | Obsidian | Un nodo por fichero, relaciones entre módulos, MOC de entrada | Datos de negocio ni de usuario |

| **ℹ Debate de clase: las dos posturas**  **Presentado como debate, no como verdad cerrada.** La postura del alumno tiene una justificación legítima en ingeniería de datos: usar una base relacional como **fuente de verdad transaccional** (con integridad, transacciones y copias de seguridad) y proyectar desde ahí a un grafo derivado y reconstruible es un patrón conocido. La objeción de Carlos también es válida: si el grafo puede ser la fuente primaria, mantener dos copias del mismo conocimiento duplica el coste de sincronización. **Criterio para decidir:** ¿necesitas transacciones, integridad referencial estricta o poder reconstruir el grafo desde cero? Entonces la fuente relacional se justifica. ¿El grafo es el único consumidor y nunca se reconstruye? Entonces sobra. |
| --- |

| **⚠ El peligro real: aceptar la propuesta del modelo sin criterio**  Aviso del instructor que va más allá de la arquitectura y es el más importante de la sesión: *«si tú no tienes criterio para debatírselo, te vas a creer todo lo que te diga, y ahí es donde está el peligro real»*. Un LLM sin contexto claro **te propondrá una arquitectura plausible y bien redactada**, y la defenderá. La fluidez no es veracidad. Técnica que dio Carlos: no digas *«está mal»*; pide **las razones de por qué tiene que ser así** y luego pregunta *«¿cómo refactorizarías esto para no necesitarlo?»*. |
| --- |

## **6.7. De la bóveda a la skill: clonar un comportamiento**

Una alumna planteó un caso concreto: un chatbot que imita a una persona conocida. El diseño que se acordó en clase ilustra bien la relación entre grafo, skill y agente:

| **1. Análisis del comportamiento: tono, gestos, forma de responder, frases hechas** |
| --- |

**↓**

| **2. Bóveda de Obsidian con ese perfil como base de conocimiento** |
| --- |

**↓**

| **3. Un agente analiza la bóveda y genera skills con las pautas de comportamiento** |
| --- |

**↓**

| **4. El agente responde consultando la skill, no recorriendo toda la bóveda cada vez** |
| --- |

**↓**

| **5. Un panel de administración valida las respuestas correctas y las reutiliza** |
| --- |

La clave del diseño es el ahorro: *«¿cómo reducimos el uso de tokens? No teniendo que recorrer fuentes de información, porque la recorremos una única vez —o una vez a la semana— y generamos la skill»*. La bóveda se recorre en **diferido**; en tiempo de respuesta solo se lee la skill.

| **✓ Ampliación técnica: aquí sí hay aprendizaje**  Aquí sí apareció machine learning legítimo: si cada vez que el administrador **aprueba** una respuesta ese refuerzo se registra y se usa para ajustar futuras respuestas, se tiene un ciclo de **aprendizaje por refuerzo con validación humana** (*human in the loop*). Carlos lo describió como *«si lo ha hecho bien, le doy una galletita»*. Correcto: la recompensa es la señal de aprendizaje. |
| --- |

| **⚠ Aviso legal sobre clonado de personas reales**  Suplantar la identidad de una **persona real identificable** —voz, gestos, frases— tiene implicaciones legales serias: derechos de imagen y voz, protección de datos (RGPD) y, según el uso, suplantación. Un clon conversacional de alguien concreto **no es un ejercicio neutro**: exige consentimiento explícito o un encuadre claramente satírico y etiquetado. Si acaba en la práctica, documenta la base legal. |
| --- |

# **7. Infraestructura: Git, GitHub, claves SSH y servidor**

## **7.1. Git y GitHub**

Definición dada en clase: GitHub es *«una herramienta que utilizamos para crear repositorios de código»*, y un repositorio es *«donde guardas tus cosas»*. La analogía usada: **GitHub es una estantería**; cada balda tiene huecos y **cada libro es un proyecto**.

| **ℹ Matiz: Git no es GitHub**  **Precisión de nomenclatura:** conviene separar dos cosas que en clase se usaron casi como sinónimas. **Git** es el **sistema de control de versiones**: funciona en local, guarda el historial de cambios (*commits*) y permite ramas. **GitHub** es una **plataforma de alojamiento** de repositorios Git en la nube, con interfaz web, permisos y colaboración. Puedes usar Git sin GitHub. Lo que exige la práctica es *«utilizar GitHub con el historial»*: que se vea la **evolución en commits**, no una única subida final. Esa es la parte evaluable. |
| --- |

También se aclaró que un repositorio no guarda solo código: admite cualquier fichero, incluido el README.md con la documentación del proyecto. En clase se comentó que ese README lo genera automáticamente el agente.

## **7.2. Flujo de desarrollo hasta producción**

| **1. Servidor de pre / desarrollo: tu ordenador, con el IDE (Cursor, Visual Studio, IntelliJ…)** |
| --- |

**↓**

| **2. Se sube el código a GitHub, el contenedor de proyectos** |
| --- |

**↓**

| **3. Se despliega desde GitHub al servidor de producción, que tiene IP pública** |
| --- |

**↓**

| **4. Se publica el puerto y la aplicación queda accesible como página web** |
| --- |

| **ℹ NOTA**  Diagrama simplificado del flujo descrito en clase. En entornos reales suele haber además una fase de **integración continua** (pruebas automáticas antes del despliegue) que no se trató en esta sesión. |
| --- |

## **7.3. Claves SSH: generación y uso**

La parte técnica más aprovechable de la clase para el bloque de ciberseguridad. El procedimiento tal como se hizo en directo, desde PowerShell en Windows:

| ssh-keygen -t rsa -b 4096 |
| --- |

- **Comando:** ssh-keygen, la herramienta estándar de generación de pares de claves de OpenSSH.
- **Opciones:** -t rsa fija el tipo de clave; -b 4096 la longitud en bits. En clase no se detallaron los parámetros: se buscó el comando y se aceptaron las preguntas con *enter*.
- **Comentario opcional:** el campo de correo (-C) no es necesario, como se indicó en clase.
- **Passphrase:** las preguntas siguientes piden una frase de paso. Se puede dejar vacía, pero **añade seguridad**: cifra la clave privada en disco.
- **Resultado esperado:** dos ficheros en la carpeta oculta .ssh del perfil de usuario.

| **Fichero** | **Qué es** | **Dónde va** | **¿Se puede filtrar?** |
| --- | --- | --- | --- |
| id\_rsa | Clave **privada** | Se queda **solo** en tu equipo | **No.** Compromete el acceso |
| id\_rsa.pub | Clave **pública** | Se **sube al servidor** | Sí, es pública por diseño |

| **⚠ Corrección hecha en clase: qué clave se sube**  **Momento de la clase que conviene registrar:** al preguntar cuál de las dos claves se sube al servidor, la respuesta inicial fue *«la privada»*, y se corrigió acto seguido: *«nuestra clave pública, que da igual que se filtre, es la que subimos al servidor, y nos autenticamos con la privada»*. **La versión correcta es la segunda.** Regla mnemotécnica: *la pública viaja, la privada se queda*. El fichero de clave privada empieza por una cabecera que dice literalmente PRIVATE KEY; si estás a punto de pegar eso en un panel web, párate. |
| --- |

Conexión al servidor una vez subida la clave pública:

| ssh root@IP\_DEL\_SERVIDOR -i C:/Users/usuario/.ssh/id\_rsa |
| --- |

- **Comando:** ssh, cliente de conexión remota.
- **`root@IP`:** usuario y host destino.
- **`-i`:** ruta al fichero de **clave privada** con el que autenticarse.
- **Resultado esperado:** sesión abierta **sin pedir usuario ni contraseña**.

| **⚠ Corrección: los «==» son padding de Base64**  **Se dijo en clase** que los dos signos = al final de la clave pública se deben a *«lo del passphrase, que modifica y altera la composición de las letras»*. **Conviene precisar:** los = finales son el \**relleno (*padding*) de Base64, nada más. Base64 codifica en bloques de 3 bytes a 4 caracteres; cuando el último bloque no está completo se rellena con uno o dos `=`. No tiene relación con la frase de paso. Además: la* passphrase *cifra la clave privada*\*, no la pública. Que la parte inicial de dos claves distintas se parezca (ssh-rsa AAAAB3Nza…) es normal: son los mismos metadatos de cabecera codificados. |
| --- |

| **ℹ Ampliación técnica: RSA vs Ed25519**  **Ampliación técnica:** hoy el estándar recomendado ya no es RSA sino **Ed25519**, más corto, más rápido y con mejor margen de seguridad. El comando equivalente sería ssh-keygen -t ed25519, y los ficheros pasan a llamarse id\_ed25519 e id\_ed25519.pub. RSA sigue siendo válido con 4096 bits, pero si empiezas un proyecto nuevo, empieza con Ed25519. |
| --- |

| **⚠ Fase de auditoría: las claves SSH como persistencia**  **Conexión directa con el bloque de explotación**, señalada por el propio instructor: *«es muy importante que tengamos en cuenta lo que es una clave RSA, porque también es una forma de persistencia que veremos cuando entremos en explotación de máquinas»*. En una auditoría, escribir tu clave pública en el fichero authorized\_keys de un usuario comprometido da acceso persistente sin contraseña, y sobrevive a cambios de credencial. Es una técnica clásica de **post-explotación** que verás en máquinas Linux. **Solo en entornos autorizados.** |
| --- |

## **7.4. Hetzner: el servidor de producción**

Hetzner es un **proveedor de servidores en la nube**. En el panel se vieron los servidores organizados por centro de datos, cada uno con su IP, y el apartado **Security** donde se registran las claves SSH autorizadas.

Flujo completo mostrado: se pega la **clave pública** en *Security → Add SSH key*, se crea el servidor en *Servers → Add server* eligiendo tipo (*cost optimized* o *general purpose*), se **marca la clave** que podrá acceder y se le da un nombre.

| **⚠ Precios no verificados**  Sobre el precio: en clase se mencionó que la opción más barata ha subido (de unos 4,95 € a unos 7 € al mes) y que la instancia mostrada costaba unos 11 € al mes. **Los precios de los proveedores cambian constantemente**: consúltalos en la web oficial antes de presupuestar la práctica. No se ha verificado ninguna de estas cifras. |
| --- |

| **✓ No hace falta pagar servidor para la práctica**  Alternativas que Carlos dio explícitamente por válidas para la práctica, si no se quiere pagar servidor: montarlo **en local** y entregar un vídeo del funcionamiento, o exponerlo con un **túnel de Cloudflare**. *«Me da igual: un panel web.»* |
| --- |

## **7.5. Riesgo: entregar credenciales al agente**

En clase se propuso dar a Claude Code el acceso a GitHub y la clave privada junto con la IP del servidor, *«y ya puede hacer absolutamente todo»*. Funciona, pero es exactamente el punto donde conviene detenerse en un máster de ciberseguridad.

| **⚠ Mínimo privilegio también para los agentes**  **Qué implica dar a un agente tu clave privada SSH y tus credenciales de GitHub:** el agente puede **desplegar, borrar o modificar** cualquier cosa en ese servidor sin pedir permiso si está en un modo sin confirmaciones; un fichero o repositorio con instrucciones maliciosas escondidas puede desviar su comportamiento (**prompt injection**, el equivalente agéntico de una inyección clásica); y la clave privada acaba **leída dentro del contexto** del modelo y potencialmente en los registros de la sesión. **Buenas prácticas mínimas:** clave dedicada solo para ese servidor (nunca la personal), usuario sin privilegios en lugar de root, tokens de GitHub con alcance mínimo y caducidad, y revisar los cambios antes de confirmarlos. **Principio de mínimo privilegio, igual que con cualquier cuenta de servicio.** |
| --- |

# **8. Comparaciones importantes**

| **Criterio** | **Índice / grafo de notas (Obsidian)** | **Grafo con ontología (Neo4j)** | **Red neuronal entrenada** |
| --- | --- | --- | --- |
| Qué almacena | Notas Markdown enlazadas | Nodos y aristas tipadas | Pesos numéricos distribuidos |
| Cómo se construye | Se escribe o lo genera un agente | Se modela o se genera con reglas | Se entrena con datos y backpropagation |
| ¿Aprende? | No | No por sí solo | Sí |
| ¿Es inspeccionable? | Sí, se lee | Sí, se consulta | Parcialmente (interpretabilidad) |
| Coste de actualizar | Bajo: añades una nota | Bajo: añades un nodo | Alto: hay que reentrenar |
| Para qué sirve aquí | Ahorrar tokens al agente | Correlacionar y razonar por relaciones | Descubrir patrones nuevos |

| **Concepto** | **Definición correcta** | **Confusión frecuente** |
| --- | --- | --- |
| **Peso** | Cuánto influye la salida de una neurona sobre la siguiente | Confundirlo con la tasa de mutación o con un cable |
| **Tasa de mutación** | Magnitud de la variación aleatoria entre generaciones | Llamarlo peso |
| **Heurística** | Función de evaluación que escoge la mejor opción del momento | Llamarlo aleatoriedad |
| **Entrenamiento** | Ajustar pesos con un dataset; costoso y en diferido | Llamar así a crear skills o agentes |
| **Inferencia** | Usar el modelo ya entrenado para generar una respuesta | Creer que el modelo aprende al usarlo |
| **Ventana de contexto** | Tokens que el modelo tiene a la vista ahora mismo | Confundirla con memoria permanente |

# **9. Aplicación a Claude y Claude Code**

| **ℹ Niveles de información**  Distinción de niveles: lo que sigue mezcla **comportamiento observable** (lo que se vio en pantalla) con **información oficial** (nombres de modelos, verificados el 30/07/2026). Ningún detalle interno de arquitectura se afirma aquí, porque no es público. |
| --- |

## **9.1. Prácticas de trabajo mostradas en clase**

- **Subagentes en paralelo** para repartir una tarea de investigación amplia.
- **Skills** como pautas de comportamiento persistentes, generadas a partir de una base de conocimiento.
- **Enrutado de modelos** por dificultad de la tarea (ver 6.3).
- **Bóveda de documentación por proyecto** para reducir el contexto que el agente necesita cargar.
- **Debate previo con el modelo** antes de escribir el prompt definitivo, para afinar el contexto.

## **9.2. Flujo de trabajo por voz que usa el instructor**

| **1. Grabar un audio hablando en voz alta sobre la idea, divagando libremente** |
| --- |

**↓**

| **2. Transcribir el audio a texto con Whisper en local** |
| --- |

**↓**

| **3. Pasar la transcripción a Claude para que la analice** |
| --- |

**↓**

| **4. Debatir la idea con el modelo hasta llegar a una solución óptima** |
| --- |

**↓**

| **5. Recién entonces, escribir el prompt de construcción** |
| --- |

| **✓ Conexión con tu proyecto**  Este patrón es exactamente el del pipeline de RedNotes Academy: audio → Whisper → modelo → salida estructurada. Lo que aporta la clase es el **uso como herramienta de pensamiento**, no solo de documentación: hablar sin estructurar y dejar que el modelo ordene. |
| --- |

## **9.3. Afirmaciones que quedan sin verificar**

| **⚠ Cifras económicas no verificadas**  En clase se afirmó que *«una suscripción de 200 € está haciendo un trabajo de aproximadamente 8.500 € al mes»* y que el proveedor *«subvenciona 2.500 € al mes a cada desarrollador»*. **No ha sido posible verificar ninguna de estas cifras** con documentación oficial. Trátalas como **opinión del instructor sobre la sostenibilidad del modelo de negocio**, no como dato. La intuición de fondo —que los precios actuales pueden no ser estables y conviene aprender a optimizar tokens— es razonable y es, de hecho, el argumento pedagógico de toda la clase. |
| --- |

| **⚠ Corrección: macOS no es Linux**  **Corrección de un comentario lateral:** se dijo que macOS *«es Linux con una capa bonita»* y que un Mac mini lleva *«iOS»*. **Ni una cosa ni la otra.** macOS se basa en **Darwin**, con núcleo **XNU**, que combina el microkernel Mach con componentes **BSD**: es un sistema tipo Unix, pero **no es Linux** y no comparte núcleo con él. Y un Mac mini ejecuta **macOS**, no iOS (iOS es el sistema de iPhone). El buen rendimiento que se le atribuye viene sobre todo del **hardware Apple Silicon con memoria unificada**, especialmente eficaz para ejecutar modelos en local. |
| --- |

# **10. Herramientas de la sesión**

| **Herramienta** | **Objetivo** | **Fase / Área** | **Uso visto en clase** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| **Obsidian** | Índice de conocimiento en Markdown | Documentación | Bóveda de ajedrez creada por 10 subagentes; MOC de entrada | Practicado | Grafo plano: no aprende |
| **Neo4j** | Base de datos de grafos con relaciones tipadas | Datos / Conocimiento | Mencionado como paso siguiente al índice | Introducido | No entrena por sí solo |
| **Claude Code** | Agente de programación en terminal | Programación asistida | Panel de Tetris y bóveda de ajedrez generados en directo | Recurrente | Se propuso darle claves SSH: ver riesgo |
| **Subagentes** | Repartir una tarea amplia en paralelo | Agentes | 10 buscadores + jardinero + conector | Practicado | Usar el modelo barato en los buscadores |
| **Skills** | Pautas de comportamiento persistentes | Optimización de tokens | Propuestas para el chatbot de personalidad | Introducido | Se generan a partir de la bóveda |
| **Whisper (local)** | Transcripción de audio a texto | Preparación de datos | Flujo de notas de voz para debatir ideas | Introducido | Núcleo del pipeline de RedNotes |
| **Git / GitHub** | Control de versiones y alojamiento de repositorios | Desarrollo | Repositorios, README, historial de commits | Introducido | Requisito de la Práctica 1 |
| **ssh-keygen / ssh** | Par de claves y conexión remota | Post-explotación / Persistencia | Generación de par RSA y conexión al servidor | Practicada | También técnica de persistencia |
| **Hetzner** | Proveedor de servidores en la nube | Desarrollo | Alta de servidor y registro de clave pública | Introducido | Precios cambiantes: verificar |
| **Playwright** | Automatización de navegador | Automatización | Mencionado en el proyecto de un alumno | Mencionado | **No es una API**: es una herramienta |
| **PostgreSQL** | Base de datos relacional | Datos / Conocimiento | Debatido como fuente de verdad canónica | Mencionado | Ver debate de arquitectura |
| **Túnel de Cloudflare** | Exponer un servicio local a Internet | Desarrollo | Alternativa a pagar servidor | Mencionado | Opción válida para la práctica |
| **Leak Radar** | Consulta de credenciales filtradas por API | Recogida de información | Ofrecida su API a un grupo de la práctica | Mencionado | El acceso lo cede el instructor |

| **ℹ NOTA**  Varias de estas herramientas (Neo4j, Playwright, PostgreSQL, Cloudflare, Leak Radar) **solo se mencionan** en la sesión y no se desarrollan en profundidad en el material proporcionado. El nivel asignado refleja esa exposición, no dominio. |
| --- |

# **11. Comandos y acciones**

## **11.1. Comandos de shell**

| ssh-keygen -t rsa -b 4096  ssh root@IP\_DEL\_SERVIDOR -i C:/Users/usuario/.ssh/id\_rsa  git clone https://github.com/usuario/repositorio.git  git add . && git commit -m "mensaje" && git push |
| --- |

| **ℹ Ampliación: comandos de Git no vistos en pantalla**  Los dos primeros comandos se ejecutaron en clase. Los de git **no se escribieron en pantalla**: en clase se dijo que *«te descargas Git para Windows y ya automáticamente la terminal puede utilizar los comandos»*, y que el agente los ejecuta solo. Se incluyen aquí como referencia mínima de trabajo, marcados como ampliación. Verifica siempre con git --help antes de usarlos en un repositorio real. |
| --- |

## **11.2. Instrucciones en lenguaje natural al agente**

No son comandos de shell, sino peticiones al agente. Se recogen porque **el diseño de la petición es lo relevante**. Reproducidas casi literalmente:

| Quiero que me crees un portal web que sea un juego de Tetris en tiempo real,  donde podamos aplicar diferentes algoritmos de machine learning y ver como los  nodos van aprendiendo, asi como la curva de aprendizaje.    Creame un nuevo proyecto en el escritorio. Crea una carpeta y una boveda de Obsidian.  Lo primero que quiero que hagas es lanzar 10 subagentes en paralelo utilizando el  modelo mas economico para obtener toda la informacion posible acerca de las normas  del ajedrez, los posibles movimientos de cada ficha y todas las estrategias que  existen, y que creemos una red relacional de conocimiento de como jugar al ajedrez.    Ahora necesito que me crees una aplicacion de ajedrez conectada a nuestro grafo,  jugable en un 1 contra 1 contra la maquina, pudiendo seleccionar las dificultades.    Cuando termines, montame una boveda de conocimiento de Obsidian del codigo. |
| --- |

| **✓ Patrón a copiar**  Fíjate en el patrón: **primero se construye el conocimiento, después se construye la aplicación, y al final se documenta el código en su propia bóveda**. Son tres grafos distintos con tres propósitos distintos, y no se mezclan. |
| --- |

| **ℹ Cómo romper un bucle de complacencia**  Técnica para cuando el modelo se atasca defendiendo una decisión: *«¿realmente no te parece mejor [alternativa] para después poder aplicar [objetivo]?»*, o bien *«¿cómo refactorizarías esto para que no necesitara [X]?»*. Pedir la **refactorización** en vez de la corrección evita que el modelo se limite a darte la razón. |
| --- |

# **12. La Práctica 1: requisitos y organización**

## **12.1. Requisitos obligatorios**

| **⚠ Requisitos eliminatorios**  Estos cuatro puntos son **eliminatorios**. Textual del instructor: *«si no tengo uno de estos puntos, suspenso»*. |
| --- |

| **Requisito** | **Qué se pide** | **Detalle dado en clase** |
| --- | --- | --- |
| **1. Aplicación web** | Un panel web funcional | Puede estar en servidor propio, en Hetzner, en local con vídeo demostrativo o expuesto con un túnel de Cloudflare |
| **2. Base de datos** | Al menos una | Para los datos propios de la aplicación |
| **3. API o webhook** | Una API **real** | *«Que sea una API de verdad, no una llamada que devuelva un 200 OK y ya está»*. Da igual consumir o servir. Debe tener **varios endpoints** |
| **4. GitHub con historial** | Repositorio con evolución en commits | No vale una subida única al final: se evalúa el historial |

| **⚠ Cómo se va a corregir la API**  Aviso explícito sobre la API: *«si yo te capturo el tráfico de tu aplicación —que lo voy a hacer— quiero encontrar una API, y le voy a pasar una herramienta mía que mapea APIs para encontrar todos los endpoints»*. La corrección de la práctica incluye **análisis del tráfico**. Diséñala pensando en eso. |
| --- |

| **⚠ Playwright ≠ API**  **Playwright no cuenta como API.** Se preguntó expresamente y la respuesta fue clara: Playwright es una herramienta de automatización (*«un MCP tool»*, *«un montón de clics que hace solo»*), no una interfaz programática de tu aplicación. |
| --- |

## **12.2. Organización, grupos y plazos**

| **Aspecto** | **Detalle** |
| --- | --- |
| **Tamaño de grupo** | De 1 a 5 personas. Se aceptó explícitamente algún grupo de 6 |
| **Comunicación de grupos** | Antes del **viernes** de esa misma semana, por WhatsApp o LinkedIn |
| **Capitán** | Un capitán por grupo. Se crea un grupo de WhatsApp *«Práctica 1 capitanes»* solo con el profesor y los capitanes |
| **Formato del mensaje** | Cada capitán publica: nombre del grupo + lista de participantes |
| **Entrega** | **Finales de septiembre**. Todo agosto disponible para trabajar |
| **Dónde se entrega** | Classroom. El enunciado se publicará también ahí, avisando por el chat |
| **Qué incluye la entrega** | Reporte con portada, además de la aplicación |
| **Apoyo durante agosto** | El instructor ofrece conexiones puntuales por Discord para repasar redes neuronales, bases de datos, despliegue, GitHub o DevOps |

| **ℹ NOTA**  El plazo se amplió de principios a **finales de septiembre** tras la intervención de Carlos Castillo. La consecuencia práctica que señaló el propio instructor: *«tenéis el doble de tiempo; podéis hacer algo el doble de bueno, o dejarlo para las dos últimas semanas»*. |
| --- |

## **12.3. Ideas de proyecto propuestas**

El tema es libre —*«si me queréis montar una aplicación de gimnasio con inteligencia artificial, adelante»*— siempre que cumpla los cuatro requisitos. Las ideas sugeridas, orientadas a que sirvan de portfolio:

- **Detector de ofertas de empleo**: analiza ofertas de LinkedIn y otras plataformas, las compara con tu currículum, da un porcentaje de encaje y aplica automáticamente a partir de un umbral (60–70 %).
- **Herramienta de pentesting automatizado** (la que ya está desarrollando un compañero).
- **Análisis de librerías de terceros** (cadena de suministro).
- **OSINT y vigilancia digital**.
- **Superficie de exposición**: se ofreció ceder la API de **Leak Radar** a **un solo grupo**.
- **Herramienta de normativa y cumplimiento**.
- **Detección de cáncer de mama en etapa temprana** con machine learning. Proyecto más complejo, en conversación con un hospital de Madrid, con dataset de mamografías etiquetadas ya disponible.

# **13. Ética, legalidad y limitaciones**

| **⚠ Matiz legal importante sobre el scraping**  **Sobre el scraping de ofertas de empleo.** En clase se afirmó que *«no es ilegal scrapear ofertas: si es para uso comercial las páginas no aceptan bots, pero si es para uso propio puedes utilizarlo»*. **Conviene matizar:** la distinción uso propio / uso comercial **no es una exención legal general**. |
| --- |

- **Condiciones de servicio del sitio.** LinkedIn prohíbe expresamente el scraping en sus términos, con independencia del uso. Incumplirlas es un incumplimiento contractual —no necesariamente un delito— pero tiene consecuencias: bloqueo y acciones civiles.
- **Datos personales.** Una oferta con nombre de reclutador o datos de contacto es dato personal: entra en el RGPD, con sus obligaciones de base jurídica y minimización. El uso doméstico tiene una excepción en el RGPD, pero es estrecha y no cubre un proyecto que se publica.
- **Acceso no autorizado.** Saltarse medidas técnicas de protección (captchas, autenticación, límites de tasa) puede cruzar a terreno penal según la jurisdicción.
- **Alternativa limpia para la práctica:** usar **APIs oficiales** donde existan, o *datasets* públicos de ofertas. Si scrapeas, hazlo sobre fuentes que lo permitan y documenta la base legal en el reporte.

| **⚠ Datos de salud**  **Proyecto médico.** El proyecto de detección de cáncer de mama solo es viable con datos **debidamente anonimizados** y con la autorización de la institución sanitaria. Los datos de salud son **categoría especial** del RGPD: requieren base jurídica reforzada y normalmente dictamen de un comité de ética. Un modelo de cribado médico, además, **nunca sustituye el diagnóstico**: asiste al profesional. |
| --- |

| **⚠ Alcance autorizado**  **Alcance de todo lo anterior:** laboratorios controlados, máquinas propias, CTF, plataformas educativas y auditorías expresamente autorizadas. La cesión de la API de Leak Radar por parte del instructor **no amplía el alcance**: sigue limitada al ejercicio académico. |
| --- |

# **14. Conexión con sesiones anteriores**

| **Sesión anterior** | **Qué se retoma aquí** |
| --- | --- |
| **IA: Introducción y Vibe Coding** (15/07/2026) | Modelo vs. herramienta vs. agente; tokens y ventana de contexto; subagentes y skills; enrutado de modelos. Aquí se aplican en un caso completo |
| **IA: Redes Neuronales, Grafos y ML** (23/07/2026) | La distinción grafo / red neuronal, que en esta sesión el instructor ya formula correctamente desde el principio. El *agente de poda* (jardinero) reaparece con nombre propio |
| **Bloque de auditoría web** (Carlos Castillo) | Las claves SSH como técnica de **persistencia** en post-explotación; la captura de tráfico con Burp para localizar endpoints de API, que es literalmente cómo se corregirá la práctica |
| **Fuzzing y enumeración web** | Mapear los endpoints de una API es el mismo problema que descubrir rutas con ffuf o x8. Diseña tu API sabiendo que alguien la va a enumerar |
| **RedNotes Academy** (proyecto propio) | El flujo audio → Whisper → modelo → salida estructurada es el mismo. Lo nuevo es usarlo como herramienta de pensamiento, y la idea de mantener una bóveda de documentación del backend Laravel |

| **✓ CORRECTO**  **Puente metodológico:** el flujo *construir conocimiento → construir la aplicación → documentar el código* es primo hermano del flujo de auditoría *planificación → recogida de información → análisis de vulnerabilidades → pruebas de explotación controladas*. En ambos casos la regla es la misma: **no avanzar sin una base de evidencia o de contexto sólida**, y documentar cada paso para no tener que rehacerlo. |
| --- |

# **15. Resumen final**

La sesión tiene un único hilo conductor: **la información bien estructurada ahorra tokens y mejora resultados**. Todo lo demás son aplicaciones de esa idea. Una bóveda de Obsidian bien indexada evita que el agente lea millones de líneas para arreglar un bug. Una skill evita recorrer la base de conocimiento en cada respuesta. Un subagente barato evita gastar un modelo caro en copiar y pegar de Google.

Conceptualmente, lo importante es tener clara la frontera: **un grafo no aprende**, por muchas ontologías que tenga. Aprende un algoritmo de machine learning entrenado sobre datos, y solo tiene sentido meterlo donde hay un patrón que descubrir —jugar al Tetris, leer una mamografía— no donde la respuesta ya está escrita, como en tu propio código.

En lo práctico, la clase deja cuatro requisitos cerrados para la Práctica 1 —aplicación web, base de datos, API real y GitHub con historial—, entrega a finales de septiembre y organización por capitanes. Y deja un aviso que vale más que cualquier requisito: **si no tienes criterio para debatir con el modelo, te creerás todo lo que te diga**.

# **16. Checklist de repaso**

1. Sé explicar por qué un grafo de notas **no aprende** y qué se necesita para que algo aprenda de verdad.
2. Sé explicar la analogía de la biblioteca de Alejandría y traducirla a consumo de tokens.
3. Sé describir el patrón buscadores → jardinero → conector y para qué sirve cada agente.
4. Sé justificar por qué se usa el modelo más barato en los subagentes de búsqueda.
5. Distingo heurística, Q-learning y neuroevolución, y sé qué caracteriza a cada una.
6. Sé diferenciar peso, tasa de mutación y población.
7. Sé qué clave SSH se sube al servidor y cuál se queda en mi máquina, y por qué.
8. Sé generar un par de claves y conectarme a un servidor con -i.
9. Entiendo por qué las claves SSH son también una técnica de persistencia en post-explotación.
10. Conozco los cuatro requisitos eliminatorios de la Práctica 1 y sé que la API se auditará capturando tráfico.
11. Tengo grupo, capitán designado y comunicado al profesor.

# **17. Preguntas de repaso**

## **17.1. Preguntas cortas**

1. ¿Qué es una ontología en el contexto de un grafo de conocimiento?
2. ¿Por qué una bóveda de Obsidian reduce el consumo de tokens de un agente?
3. ¿Cuál es la función del *agente jardinero* en el patrón de subagentes?
4. ¿Cuál de las dos claves SSH se sube al servidor y por qué da igual que se filtre?
5. ¿Qué significan los = al final de una clave pública SSH?
6. ¿Qué diferencia hay entre Git y GitHub?
7. Da un ejemplo de tarea donde SÍ tiene sentido aplicar machine learning y otro donde NO.
8. ¿Por qué Playwright no cuenta como API en la Práctica 1?

## **17.2. Preguntas de desarrollo**

1. Explica la progresión *fuente de datos → grafo → dataset → entrenamiento* y por qué Neo4j no es el punto donde aparece la inteligencia.
2. Diseña la arquitectura de datos de una herramienta de pentesting automatizado justificando qué guardas en SQL, qué en un grafo y qué en documentación. Presenta las dos posturas del debate de clase.
3. Un compañero te dice que ha *«entrenado una IA»* creando una skill a partir de una bóveda de Obsidian. Explica por qué la afirmación es imprecisa y qué ha hecho realmente.
4. Relaciona el uso de claves SSH en despliegue con su uso como mecanismo de persistencia en una auditoría autorizada.

## **17.3. Tipo test**

1. La tasa de mutación en neuroevolución es: **(a)** el peso de una neurona · **(b)** la magnitud de la variación aleatoria aplicada entre generaciones · **(c)** el número de redes en competición · **(d)** la tasa de aciertos del modelo.
2. El Q-learning clásico: **(a)** es una red neuronal de dos capas · **(b)** es un algoritmo de refuerzo basado en una tabla de valores estado-acción · **(c)** requiere obligatoriamente GPU · **(d)** es lo mismo que la neuroevolución.
3. Una heurística: **(a)** es aleatoriedad pura · **(b)** garantiza siempre el óptimo global · **(c)** es una función de evaluación que escoge la mejor opción del momento · **(d)** solo se usa en juegos.
4. Los == al final de una clave pública SSH indican: **(a)** que tiene passphrase · **(b)** relleno de codificación Base64 · **(c)** que la clave es RSA · **(d)** el final del fichero.
5. Para diez subagentes que buscan información en Google, lo razonable es usar: **(a)** el modelo más capaz disponible · **(b)** el modelo más rápido y económico · **(c)** un modelo distinto por subagente · **(d)** siempre el modelo por defecto.
6. Un grafo con ontología en Neo4j: **(a)** aprende ajustando pesos · **(b)** es una red neuronal en 3D · **(c)** almacena relaciones con significado explícito pero no aprende por sí solo · **(d)** sustituye al entrenamiento.
7. El requisito de GitHub en la Práctica 1 se cumple con: **(a)** una única subida al final · **(b)** un repositorio con historial de commits · **(c)** un ZIP en Classroom · **(d)** un enlace a Google Drive.
8. macOS: **(a)** es una distribución de Linux · **(b)** se basa en Darwin, con núcleo XNU (Mach + BSD) · **(c)** es iOS con ventanas · **(d)** comparte núcleo con Ubuntu.

## **17.4. Ejercicios prácticos**

1. Genera un par de claves Ed25519, súbelo a una máquina de laboratorio propia y conéctate sin contraseña. Documenta qué fichero fue a cada sitio.
2. Crea una bóveda de Obsidian con la documentación de uno de tus scripts (x8\_lite.py o similar): un nodo por función y un MOC de entrada. Estima cuánto contexto le ahorras al agente.
3. Diseña sobre papel la API de tu proyecto de práctica: lista los endpoints, sus métodos y qué devuelve cada uno. Comprueba que resistiría un mapeo con captura de tráfico.

## **17.5. Tarjetas de memoria**

| **Pregunta** | **Respuesta** |
| --- | --- |
| ¿Qué es un MOC? | Nota-índice de una bóveda de Obsidian que agrupa y enlaza el resto de notas de un tema |
| ¿Obsidian aprende? | No. Es un índice de referencias; el conocimiento no se ajusta con el uso |
| ¿Neo4j aprende? | No por sí solo. Almacena relaciones tipadas; el aprendizaje exige un algoritmo de ML sobre esos datos |
| ¿Qué es una ontología? | El significado explícito de la relación entre dos nodos |
| ¿Qué hace el agente jardinero? | Poda duplicados y consolida nodos repetidos |
| ¿Qué hace el agente conector? | Lee los nodos y crea las relaciones entre ellos |
| ¿Qué es la población en neuroevolución? | El número de redes que compiten en una misma generación |
| ¿Qué es la tasa de mutación? | La magnitud de la variación aleatoria aplicada entre generaciones |
| ¿Qué es un peso? | Número que indica cuánto influye la salida de una neurona sobre la siguiente |
| ¿Qué caracteriza a una heurística? | Escoger la mejor opción del momento según una función de evaluación, sin garantizar el óptimo |
| ¿Qué es machine learning en una frase? | Que un algoritmo aprenda a hacer algo que al principio no sabía |
| ¿Qué clave se sube al servidor? | La **pública**. La privada se queda en tu equipo |
| ¿Para qué sirve -i en ssh? | Indicar la ruta de la clave privada con la que autenticarse |
| ¿Qué son los == de una clave pública? | Relleno (padding) de Base64 |
| ¿SSH como persistencia? | Escribir tu clave pública en authorized\_keys da acceso sin contraseña y sobrevive al cambio de credenciales |
| ¿Git vs GitHub? | Git es el sistema de control de versiones; GitHub es la plataforma que aloja repositorios Git |
| ¿Requisitos de la Práctica 1? | Aplicación web + base de datos + API real + GitHub con historial |
| ¿Playwright es una API? | No: es una herramienta de automatización de navegador |
| ¿Qué modelo para subagentes de búsqueda? | El más rápido y económico de la familia; la tarea no tiene complejidad |
| ¿Cuál es el peligro real de la IA según la clase? | Aceptar sin criterio una propuesta bien redactada del modelo |

| **✓ Soluciones**  **Soluciones del tipo test (17.3):** 1-b · 2-b · 3-c · 4-b · 5-b · 6-c · 7-b · 8-b. |
| --- |

# **18. Glosario**

| **Término** | **Definición breve** |
| --- | --- |
| **Agente** | Modelo + herramientas + objetivo, que actúa en bucle decidiendo pasos |
| **Backpropagation** | Algoritmo que propaga el error hacia atrás para ajustar los pesos durante el entrenamiento |
| **Base64** | Codificación de datos binarios en caracteres imprimibles; usa = como relleno final |
| **Bóveda** (*vault*) | Carpeta de trabajo de Obsidian con ficheros Markdown enlazados |
| **Endpoint** | Ruta concreta de una API que responde a una petición |
| **Heurística** | Función de evaluación que escoge la mejor opción disponible en cada momento |
| **Inferencia** | Uso del modelo ya entrenado para generar una respuesta; no modifica sus pesos |
| **MOC** (*Map of Content*) | Nota-índice que organiza y enlaza el resto de notas de un tema |
| **Neuroevolución** | Optimización de redes mediante algoritmos evolutivos: mutación, selección y generaciones |
| **Ontología** | Significado explícito de la relación entre dos nodos de un grafo |
| **Prompt injection** | Instrucción maliciosa escondida en contenido que el agente lee, capaz de desviar su comportamiento |
| **Q-learning** | Algoritmo de aprendizaje por refuerzo basado en una tabla de valores estado-acción |
| **RAG** | *Retrieval-Augmented Generation*: recuperar contexto relevante e inyectarlo en tiempo de inferencia |
| **Skill** | Fichero de instrucciones persistente que fija pautas de comportamiento de un agente |
| **Subagente** | Agente lanzado por otro para una subtarea acotada; puede ejecutarse en paralelo |
| **Tasa de mutación** | Magnitud de la variación aleatoria aplicada a los valores entre generaciones |
| **Token** | Unidad mínima en que el modelo trocea el texto; unidad de coste y de contexto |
| **Ventana de contexto** | Cantidad máxima de tokens que el modelo tiene a la vista en una conversación |
| **XNU** | Núcleo de macOS: combina el microkernel Mach con componentes BSD. No es Linux |

# **19. Actualización del registro de IA**

Escala de niveles: **Mencionado** → **Introducido** → **Comprendido** → **Practicado** → **Aplicado** → **Recurrente**.

| **Concepto / Herramienta** | **Categoría** | **Nivel** |
| --- | --- | --- |
| Grafo de conocimiento vs. red neuronal | Fundamento | **Comprendido** (reforzado) |
| Ontología en grafos | Datos / Conocimiento | **Comprendido** (antes Introducido) |
| MOC (índice de bóveda) | Datos / Conocimiento | Introducido |
| Arquitectura de subagentes en paralelo | Agente | **Practicado** (antes Introducido) |
| Agente de poda (jardinero) | Agente | **Comprendido** (antes Mencionado) |
| Agente conector de relaciones | Agente | Introducido |
| Enrutado de modelos por dificultad | Técnica | **Practicado** (antes Comprendido) |
| Skills como pautas persistentes | Agente / Técnica | **Comprendido** (antes Introducido) |
| Optimización de tokens por indexación | Optimización de tokens | **Comprendido** |
| Q-learning | Técnica de entrenamiento | Introducido |
| Heurística como función de evaluación | Fundamento | Introducido |
| Neuroevolución (mutación, población) | Técnica de entrenamiento | Introducido |
| Curva de aprendizaje | Método de evaluación | Mencionado |
| Aprendizaje por refuerzo con validación humana | Técnica de entrenamiento | Introducido |
| Obsidian (bóveda por proyecto) | Herramienta | **Practicado** |
| Neo4j | Framework / Datos | Introducido |
| Whisper local (audio a texto) | Herramienta | Introducido |
| Claude Code con subagentes | Agente / Herramienta | **Recurrente** |
| Modelos vigentes: Haiku 4.5 / Sonnet 5 / Opus 5 / Fable 5 | Modelo | Introducido |
| Prompt injection en agentes con credenciales | Técnica de seguridad | Introducido |

## **19.1. Actualización del registro de herramientas de ciberseguridad**

| **Herramienta** | **Fase de auditoría** | **Nivel** |
| --- | --- | --- |
| ssh-keygen / ssh (claves RSA y Ed25519) | Post-explotación / Persistencia | **Practicada** |
| Git / GitHub | No aplica (desarrollo) | Introducida |
| Hetzner (servidor de producción) | No aplica (infraestructura) | Introducida |
| Túnel de Cloudflare | No aplica (infraestructura) | Mencionada |
| Leak Radar (API de filtraciones) | Recogida de información | Mencionada |
| Playwright | No aplica (automatización) | Mencionada |

# **20. Fuentes consultadas**

El contenido de clase es la **fuente primaria**. Lo siguiente respalda únicamente las ampliaciones y correcciones marcadas en el documento. **Fecha de consulta: 30/07/2026.**

| **Fuente** | **Tipo** | **Qué respalda** |
| --- | --- | --- |
| Transcripción de la sesión del 30/07/2026 (Carlos Gómez Pintado) | Primaria | Todo el contenido de clase |
| Búsqueda web sobre la línea de modelos vigente de Anthropic, consultada el 30/07/2026 | Secundaria | Corrección del nombre «Haiku 5» y tabla de niveles de modelo de la sección 6.3 |
| Conocimiento técnico general: criptografía de clave pública, Base64, aprendizaje por refuerzo y arquitectura de sistemas tipo Unix | Explicación propia | Correcciones de las secciones 6.4, 7.3 y 9.3 |
| Apuntes previos del bloque de IA (15/07/2026 y 23/07/2026) | Primaria | Conexión con sesiones anteriores y niveles de partida del registro |

| **⚠ Aviso de verificación**  Las correcciones sobre modelos de Anthropic se han contrastado con búsqueda web el **30/07/2026**, pero los nombres, precios y límites cambian con frecuencia. **Contrasta con la documentación oficial de Anthropic antes de utilizar estas cifras como referencia definitiva.** Tampoco ha sido posible verificar las cifras económicas sobre suscripciones citadas en clase. |
| --- |

# **21. Actualización de memoria del proyecto**

| **Campo** | **Valor** | **Certeza** |
| --- | --- | --- |
| Título de la sesión | Presentación de la Práctica 1 (bloque de IA) | Alta |
| Instructor | Carlos Gómez Pintado | Alta (indicado por Chema) |
| Fecha de clase | 30/07/2026 | Alta (indicada por Chema) |
| Número de sesión | No consta en el material | Pendiente |
| Tema principal | Grafos de conocimiento, subagentes, machine learning, infraestructura y enunciado de la Práctica 1 | Alta |
| Conceptos nuevos de IA | MOC · agente jardinero · agente conector · Q-learning · heurística · neuroevolución · tasa de mutación · población | Alta |
| Herramientas nuevas | Hetzner · Leak Radar · túnel de Cloudflare · PostgreSQL (mencionado) | Alta |
| Comandos nuevos | ssh-keygen -t rsa -b 4096 · ssh root@IP -i ruta\_clave | Alta |
| Técnicas de post-explotación | Claves SSH como mecanismo de persistencia (anunciado, se verá en explotación de máquinas) | Media |
| Correcciones aplicadas | Grafo con ontología no aprende · heurística ≠ aleatoriedad · Q-learning no es red neuronal · mutación ≠ peso · «Haiku 5» no existe (es Haiku 4.5) · == es padding Base64 · macOS no es Linux · matiz legal sobre scraping | Alta |
| Artefactos de transcripción corregidos | «colearning» → Q-learning · «Neo 4G» → Neo4j · «Claudia/cloud» → Claude · «PlayRite» → Playwright · «Hetznet/Hebsner» → Hetzner · «IQ 5» → modelo Haiku · «ILA/IEA» → IA · «ahoristica» → heurística · «Ridmey» → README | Alta |
| Temas pendientes | Comparación en profundidad de algoritmos de ML (*«cada uno es una clase nueva»*) · aplicación de ajedrez con red vectorial y ML · explotación web y de máquinas avanzada a la vuelta de vacaciones | Alta |
| Entregable pendiente | Práctica 1: aplicación web + base de datos + API real + GitHub con historial. Entrega a finales de septiembre en Classroom | Alta |
| Acción inmediata | Cerrar grupo, designar capitán y comunicarlo antes del viernes | Alta |
| Conexión con RedNotes Academy | Patrón audio → Whisper → modelo aplicable al pipeline; idea de mantener bóveda de documentación del backend Laravel | Media |

## **21.1. Bloque para memoria acumulativa**

| SESION: Presentacion de la Practica 1 (bloque IA) - Carlos Gomez Pintado - 30/07/2026  TEMAS: grafo de notas como indice (Obsidian, MOC) | Neo4j y ontologias | subagentes  en paralelo (buscadores + jardinero + conector) | enrutado de modelos | demo Tetris  con Q-learning, heuristica y neuroevolucion (simulacion, no entrenamiento real) |  que es y que no es machine learning | debate SQL vs Neo4j vs Obsidian | de la boveda  a la skill | Git/GitHub | claves SSH publica-privada | Hetzner | enunciado Practica 1  HERRAMIENTAS NUEVAS: Hetzner, Leak Radar, tunel de Cloudflare, PostgreSQL (mencionado)  COMANDOS: ssh-keygen -t rsa -b 4096 ; ssh root@IP -i ruta\_clave\_privada  PERSISTENCIA: clave publica en authorized\_keys (anunciado para el bloque de explotacion)  CORRECCIONES: grafo con ontologia no aprende ; heuristica no es aleatoriedad ; Q-learning  no es red neuronal ; tasa de mutacion no es un peso ; no existe Haiku 5 (es Haiku 4.5) ;  los == son padding Base64 ; macOS no es Linux ; matiz legal sobre scraping de ofertas  PRACTICA 1: app web + base de datos + API real con varios endpoints + GitHub con historial.  Grupos de 1 a 5 (se acepta 6), un capitan por grupo, grupo de WhatsApp de capitanes.  Entrega a finales de septiembre en Classroom. La API se corregira capturando trafico.  PENDIENTE: comparativa profunda de algoritmos de ML ; aplicacion de ajedrez con red  vectorial y ML ; explotacion web y de maquinas avanzada tras las vacaciones |
| --- |
