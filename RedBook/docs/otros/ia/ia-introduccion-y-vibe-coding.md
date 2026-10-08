---
tags:
- Inteligencia artificial
---

# IA Introduccion y Vibe Coding

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**IA: Introducción y Vibe Coding**

Instructor: Carlos Gómez Pintado · 15/07/2026

*Bloque de IA aplicada · Fundamentos, agentes, Claude Code y grafos de conocimiento*

| **ℹ Cómo leer estos apuntes**  Estos apuntes recogen fielmente lo explicado en clase y añaden correcciones y ampliaciones cuando la terminología del aula difiere de la terminología técnica estándar. Cada aportación externa va marcada como Ampliación técnica, Simplificación didáctica o Nota. El enfoque de la sesión fue muy conversacional y comercial; aquí se ha extraído la sustancia técnica y se ha eliminado el ruido. |
| --- |

# **1. Objetivos de la sesión**

- Entender los **conceptos base de IA** que se manejan al construir con LLMs: modelo, agente, herramienta, contexto y tokens.
- Conocer el flujo de trabajo del **vibe coding**: idea → debate con el LLM → prompt → diseño → programación asistida → pruebas.
- Introducir **Claude Code**, sus modos de permisos y la selección de modelo para controlar coste (tokens).
- Diferenciar un **grafo de conocimiento** (Obsidian / Neo4j, ontologías) de una **red neuronal** real, y saber cuándo usar cada uno.
- Repasar la base de **redes neuronales** (pesos, entrenamiento, embeddings, sesgos) tal como surgió en el debate de clase, con las correcciones oportunas.

# **2. Conceptos clave de IA**

La primera parte de la clase fijó el vocabulario mínimo. Estas distinciones son las que tu guía de IA marca como **obligatorias**, así que conviene tenerlas muy claras de cara al examen.

## **2.1 Modelo, aplicación, herramienta y agente**

Son cuatro cosas distintas y en clase se usaron a veces como sinónimos. La distinción correcta:

| **Término** | **Qué es** | **Ejemplo de la clase** |
| --- | --- | --- |
| Modelo (LLM) | La red neuronal entrenada que predice el siguiente token. No actúa por sí sola. | Claude Opus, Sonnet, Haiku, Fable |
| Aplicación | La interfaz o producto que envuelve al modelo. | El chat de Claude, la app de escritorio |
| Herramienta (tool) | Función externa que el modelo puede invocar (buscar web, ejecutar código, navegar). | Playwright, búsqueda en Internet |
| Agente | Modelo + herramientas + un objetivo (goal), que actúa en bucle sin intervención constante. | El subagente diseñador, el agente prompter |
| **⚠ Error conceptual a evitar**  La confusión clásica (y que tu guía pide corregir): un chatbot no es lo mismo que un agente. Un chatbot responde; un agente persigue una meta usando herramientas y decidiendo pasos. Del mismo modo, la herramienta no es el modelo: Claude es el modelo; Playwright o la búsqueda web son herramientas que el modelo llama. |

## **2.2 Tokens y ventana de contexto**

Un **token** es la unidad mínima en la que el modelo trocea el texto (aproximadamente fragmentos de palabra). El modelo **factura y razona por tokens**: todo lo que entra y sale consume tokens.

La **ventana de contexto** es la cantidad máxima de tokens que el modelo puede tener "a la vista" en una conversación. En clase se explicó bien un punto esencial:

| **ℹ Ampliación técnica: contexto ≠ memoria**  La ventana de contexto NO es memoria permanente. Cuando se llena, el modelo pierde lo que ya no cabe. Por eso, si quieres que el conocimiento del proyecto persista entre sesiones o entre cuentas distintas, hay que sacarlo del contexto y guardarlo en ficheros (por ejemplo CLAUDE.md, notas .md u Obsidian). |
| --- |

Corolario práctico visto en clase: **cuanta más información del proyecto tengas documentada en local**, menos tokens gasta el modelo en volver a analizar de qué va el proyecto cada vez.

## **2.3 Por qué el mismo modelo da respuestas distintas a cada persona**

En clase se afirmó que "tu Claude no te responde igual que a mí". Conviene precisar el porqué para no quedarse con una idea mágica:

| **ℹ Corrección: el modelo es el mismo; cambia el contexto**  Un LLM es determinista salvo por dos factores: (1) la temperatura (aleatoriedad controlada en la elección del siguiente token) y (2) el contexto que recibe (tu prompt, tu historial, tus instrucciones o memoria si están activadas). No es que el modelo tenga "un cerebro tuyo" distinto del mío: es el mismo modelo, pero recibe entradas distintas. La personalización viene del contexto y de la memoria del producto, no de una red neuronal individual por usuario. |
| --- |

# **3. Vibe coding: el flujo de trabajo de la sesión**

El grueso práctico de la clase fue construir un MVP (producto mínimo viable) de una app de finanzas personales usando IA de principio a fin. El instructor insistió en una idea central: hoy lo difícil ya no es programar, sino **tener la idea, saber estructurarla y saber venderla**. El código lo genera y lo mantiene la IA.

## **3.1 El flujo completo**

| **1. Idea: debatir en voz alta con el LLM (debatir, analizar, mejorar) y sacar valor diferencial frente a la competencia** |
| --- |

**↓**

| **2. Requisitos: refinar hasta un prompt hiperdetallado con las funcionalidades del producto** |
| --- |

**↓**

| **3. Diseño: generar los frontales con una herramienta de diseño asistida (tipo Claude Design)** |
| --- |

**↓**

| **4. Programación: pasar los ficheros a Claude Code para que genere el MVP (back y front)** |
| --- |

**↓**

| **5. Pruebas: un agente lanza tests (smoke, seguridad, accesibilidad, end-to-end)** |
| --- |

**↓**

| **6. Iteración: sobre el MVP funcional, refinar y mejorar (dev → main)** |
| --- |

## **3.2 MVP "de cartón piedra"**

El instructor definió el objetivo del MVP como algo rápido y desechable: en **una tarde** hay que tener algo operable para validar si la idea funciona, no un producto de producción. La lógica: no gastar semanas en algo que quizá no tenga aceptación.

| **ℹ Debate de clase**  Punto en el que hubo debate en clase (Mariana vs. Carlos): ¿el prompt de un MVP se escribe "a lo bruto" o se refina mucho antes? La postura del instructor: para el MVP, prompt rápido; el refinado profundo (documento largo de requisitos) se reserva para cuando el MVP ya ha demostrado que vale. Ambas posturas son defendibles; no hay una única forma correcta. |
| --- |

## **3.3 Prompts: tamaño y claridad**

Consejo dado en clase sobre cómo escribir buenos prompts, formulado con humor pero con fondo correcto:

| **✓ Buena práctica: prompts claros y específicos**  Un prompt grande y autoexplicativo deja menos libertad al modelo, así que "divaga" menos y se ciñe mejor a lo que quieres. No hay que tener miedo a los prompts largos cuando la tarea es compleja. (Matiz técnico: más largo no siempre es mejor; lo que importa es que sea claro, específico y sin ambigüedad. Un prompt enorme y desordenado también confunde.) |
| --- |

Recurso avanzado mencionado: un **agente prompter** intermediario que recibe tu prompt informal, lo mejora y lo optimiza antes de pasarlo al modelo final. Así tú escribes poco y el resultado es mejor, sin gastar tokens de más en el modelo caro.

# **4. Claude Code y control de coste**

**Claude Code** es la herramienta/agente de programación de Anthropic que usa los modelos Claude desde la terminal (o desde la app/IDE). En clase se remarcó que **no es un modelo distinto**: es un agente que ejecuta a Claude sobre tu repositorio, lee ficheros, propone cambios, ejecuta comandos y corre pruebas.

## **4.1 CLAUDE.md: el "cerebro" del proyecto**

El fichero CLAUDE.md actúa como **system prompt del proyecto**: instrucciones persistentes que Claude Code lee siempre. En clase se usó para fijar reglas fijas del estilo "usa siempre este subagente", "invoca el agente prompter al comunicarte con otro agente", etc.

| **ℹ Ampliación: CLAUDE.md como instrucciones persistentes**  Jerarquía vista en clase: lo que pongas en CLAUDE.md prevalece. Si le das unos ficheros de referencia, el CLAUDE.md sigue mandando sobre cómo interpretarlos. |
| --- |

## **4.2 Modos de permisos**

Por defecto Claude Code **pide confirmación** antes de editar ficheros o ejecutar comandos. En clase se usó continuamente --dangerously-skip-permissions ("modo YOLO") para que no preguntara nada. Aquí hay que ser muy honesto contigo, porque la clase presentó esto como algo trivial y no lo es:

| **⚠ Riesgo real de --dangerously-skip-permissions**  --dangerously-skip-permissions desactiva TODAS las confirmaciones. Según la documentación oficial de Anthropic, está pensado para entornos aislados (contenedores, VMs, dev containers), no para tu máquina principal. De hecho Claude Code se niega a arrancar en este modo como root/sudo. Sin la pausa de permiso, una instrucción maliciosa escondida en un fichero o repo puede ejecutarse de inmediato (prompt injection), y hay incidentes documentados de borrados accidentales (rm -rf). El propio equipo de Anthropic recomienda ejecutarlo "en un contenedor, no en tu máquina real". |
| --- |
| **✓ Ampliación técnica: auto mode, acceptEdits y plan**  Alternativa segura que la clase no mencionó y que sí conviene conocer: Anthropic introdujo en 2026 el auto mode (modo automático), un punto intermedio con clasificadores que aprueban lo seguro y bloquean lo peligroso, evitando la fatiga de confirmar sin renunciar a la protección. También existen acceptEdits (autoaprueba ediciones de fichero pero no comandos) y plan (planifica y tú apruebas). Para trabajar cómodo sin quitar toda la red de seguridad, estos modos son preferibles al bypass total. |

## **4.3 Selección de modelo (coste)**

Cada modelo consume distinto. En clase, un alumno gastó ~70 % de su cuota porque estaba en un modelo potente para una tarea sencilla. La regla que se dio:

| **✓ Buena práctica: enrutado de modelos (model routing)**  Usa el modelo más potente (y caro) solo para tareas complejas (planificar, investigar, refactorizar). Para tareas simples (buscar, operaciones triviales) usa el modelo más ligero. En Claude Code el comando /model permite fijarlo, e incluso pedir que seleccione automáticamente el modelo más óptimo por tarea. Jerarquía habitual de menor a mayor coste: Haiku → Sonnet → Opus → Fable. |
| --- |

Para ver consumo, en la app se usa la sección de **uso/usage**; en Claude Code el comando de uso muestra la cuota **diaria** (se recarga cada 5 horas), la **semanal** y la del modelo de gama alta. Estos números y límites cambian con frecuencia:

| **⚠ Verificación temporal**  Los planes, límites y nombres de modelos (Haiku, Sonnet, Opus, Fable) evolucionan rápido. No tomes como fijas las cifras concretas de cuota que se dijeron en clase: verifícalas en la documentación oficial de Anthropic antes de usarlas como referencia. |
| --- |

## **4.4 RTK: reducir consumo de tokens**

En clase se instaló "RTK" para gastar menos tokens. Conviene corregir dos cosas que se dijeron: no es una skill, y no reduce el gasto "de Claude" en general, sino el ruido de la salida de comandos.

| **ℹ Ampliación técnica: qué es RTK realmente**  RTK = Rust Token Killer: un proxy CLI (binario en Rust, código abierto) que intercepta comandos de shell verbosos (git status, tests, docker, grep, find...) y comprime su salida antes de que entre en el contexto del modelo. Ahorra un 60-90 % en esos comandos concretos. Se instala con un hook (PreToolUse) que reescribe las llamadas Bash de forma transparente; se le suele indicar en CLAUDE.md que lo use siempre. |
| --- |
| **⚠ Límite de RTK**  Matiz importante que la clase no mencionó: el hook de RTK SOLO intercepta llamadas por la herramienta Bash. Las herramientas nativas de Claude Code (Read, Grep, Glob) lo esquivan. Es decir, RTK ahorra mucho en sesiones con muchos comandos de terminal (builds, tests, git), pero poco en sesiones de lectura/edición de ficheros. No es un compresor global mágico. |

# **5. Herramientas y tecnologías mencionadas en la sesión**

La sesión fue de IA aplicada, así que la columna "Fase/Área" usa categorías de desarrollo asistido en lugar de fases de auditoría.

| **Herramienta** | **Objetivo** | **Fase / Área** | **Uso visto en clase** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Claude (chat) | Debatir idea, generar prompts, orquestar | Ideación / Desarrollo | Debatir requisitos, crear prompt para el MVP | Introducida | Modelo base; distinto de Claude Code |
| Claude Code | Programar el proyecto de forma agéntica | Programación asistida | Generar back y front del MVP en local | Introducida | Agente sobre repositorio; usa CLAUDE.md |
| Claude Design | Generar frontales/diseño de la web | Diseño | Crear landing y vistas del MVP | Mencionada | "Super Claude con skills de diseño" |
| RTK (Rust Token Killer) | Comprimir salida de comandos | Optimización de tokens | Instalado vía hook; activado en CLAUDE.md | Mencionada | Solo afecta a llamadas Bash |
| Playwright | Automatizar navegador (clics, formularios) | Automatización / Tests | Navegación web y tests end-to-end | Mencionada | Da acceso al navegador al agente |
| Neo4j | Grafo de conocimiento con ontologías | Datos / Conocimiento | Base de la "red neuronal" del proyecto felino | Mencionada | Grafo dirigido; NO es red neuronal |
| Obsidian | Notas enlazadas (índice de conocimiento) | Documentación | Guardar contexto y grafo de notas | Mencionada | Índice 2D; no aprende |
| pandas / numpy | Limpieza de datos y estadística | Preparación de datos | Limpieza de datasets, vectores por usuario | Mencionada | Aportado por Mariana |
| PyTorch | Entrenar redes neuronales | Entrenamiento | Extracción de features, entrenamiento | Mencionada | Discusión sobre biometría de menores |
| GoPhish / phishing tooling | Campañas de phishing autorizadas | Red Team (contexto) | Clonado de webs para campañas con contrato | Mencionada | Solo en entornos autorizados y con contrato |
| **ℹ NOTA**  Varias de estas herramientas solo se nombraron de pasada, sin desarrollarse en profundidad en el material. Su nivel es "Mencionada" a propósito: no asumas dominio por una sola aparición. |

# **6. Comandos y acciones vistas**

Comandos y órdenes que aparecieron en la sesión (cada uno en una sola línea). Los que van entre comillas son instrucciones en lenguaje natural al agente, no comandos de shell.

| # Lanzar Claude Code en la terminal  claude    # Modo sin confirmaciones (SOLO en entorno aislado)  claude --dangerously-skip-permissions    # Selección/gestión del modelo dentro de Claude Code  /model    # Ver consumo de tokens / cuota dentro de Claude Code  /usage |
| --- |

Instrucciones en lenguaje natural que se dieron al agente durante la clase:

| "oye, te me instalas RTK y lo activas por defecto"  "añádelo a tu CLAUDE.md para que por defecto se utilice RTK"  "créame un subagente diseñador que mantenga siempre el mismo estilo"  "créame un agente prompter que mejore mis prompts antes de pasarlos"  "haz un deep research en Internet durante los próximos 5 minutos" |
| --- |
| **ℹ Ampliación: forzar iteración**  Truco de clase ("regla del temporizador"): dar al agente un tiempo mínimo ("busca durante 5 minutos", "no pares hasta que diga la palabra X") fuerza a que itere y contraste en vez de quedarse con la primera solución. Útil, pero recuerda que un agente en bucle largo sin supervisión combinado con permisos abiertos multiplica el riesgo. |

# **7. Grafos de conocimiento vs. redes neuronales**

La parte más densa (y más confusa terminológicamente) de la clase. Aquí es donde más falta hace separar lo que se dijo de lo que es técnicamente correcto, porque **en clase se llamó "red neuronal" a cosas que no lo son**.

## **7.1 Lo que se explicó en clase**

Se contrastaron dos formas de guardar conocimiento del proyecto:

|  | **Obsidian (grafo de notas)** | **Neo4j (grafo ontológico)** |
| --- | --- | --- |
| Idea en clase | "2D / plano": índice de páginas enlazadas | "3D / neurona": nodos con relaciones con significado |
| Conexión | Un enlace (hipervínculo) sin significado explícito | Una arista con ontología: "John tiene un balón" |
| Para qué | Buscar información, navegar entre notas | Correlacionar y razonar sobre relaciones |

El concepto de **ontología** que se usó es correcto y útil: en lugar de una conexión vacía, la arista lleva el **sentido** de la relación ("juega con", "se come", "es igual que"). Eso permite inferir: si *balón de fútbol es redondo* y *balón de fútbol es igual que balón de baloncesto*, entonces *balón de baloncesto es redondo*.

## **7.2 La corrección necesaria**

| **⚠ Corrección clave: grafo ≠ red neuronal**  Un grafo de conocimiento (knowledge graph) NO es una red neuronal. Son dos cosas distintas:• Grafo de conocimiento (Neo4j, ontologías): nodos y aristas con significado explícito, definidos por reglas y relaciones. Razona por lógica simbólica y consultas. No "aprende" pesos ni usa gradiente.• Red neuronal: capas de neuronas conectadas por pesos numéricos que se ajustan durante el entrenamiento (backpropagation, descenso del gradiente) a partir de un dataset. El "conocimiento" está distribuido en esos pesos, no en aristas con texto.Decirle a Claude que conecte nodos con ontologías construye un grafo de conocimiento excelente, pero eso NO es "entrenar una red neuronal". |
| --- |
| **⚠ Matiz: no confundir los dos paradigmas**  La "regla BDSM" y el "pesos vs. ontología" de la clase mezclan dos paradigmas. La intuición de fondo (dar contexto en lenguaje natural mejora el resultado frente a un simple peso numérico) es válida para un grafo simbólico consultado por un LLM. Pero un LLM real SÍ funciona con pesos: la contraposición "pesos malos / ontología buena" no describe cómo funciona un modelo de lenguaje por dentro. |

## **7.3 Cuándo usar cada uno (síntesis útil)**

| **Necesito...** | **Herramienta adecuada** |
| --- | --- |
| Guardar notas y navegar entre ellas | Obsidian (índice / grafo de notas) |
| Correlacionar entidades y razonar por relaciones | Grafo de conocimiento (Neo4j + ontologías) |
| Aprender patrones a partir de muchos datos etiquetados | Red neuronal real (PyTorch, entrenamiento) |
| Generar texto / código a partir de instrucciones | LLM (Claude) — ya viene preentrenado |

# **8. Redes neuronales: la base (con correcciones)**

En el debate final surgieron muchos términos de redes neuronales (vectores, embeddings, pesos, sesgos, datasets). Se recogen aquí ordenados y corregidos, porque son fundamentos que tu guía de IA pide dominar.

## **8.1 La neurona artificial**

| **1. Entradas (los datos que recibe la neurona)** |
| --- |

**↓**

| **2. Multiplicación por pesos (cuánto influye cada entrada)** |
| --- |

**↓**

| **3. Suma ponderada de todas las entradas** |
| --- |

**↓**

| **4. Se suma el sesgo (bias)** |
| --- |

**↓**

| **5. Función de activación (introduce no linealidad)** |
| --- |

**↓**

| **6. Salida (que pasa a la siguiente capa)** |
| --- |
| **ℹ Corrección: qué es un peso**  El peso NO es un cable físico ni una conexión "real": es un número que indica cuánta influencia tiene la salida de una neurona sobre la siguiente. Durante el entrenamiento el sistema ajusta esos números para reducir el error. Y una neurona artificial NO es una reproducción de una neurona biológica: es una analogía útil con límites. |

## **8.2 Entrenamiento vs. inferencia**

| **Entrenamiento** | **Inferencia** |
| --- | --- |
| Se ajustan los pesos con un dataset | Los pesos ya están fijos |
| Usa backpropagation y descenso del gradiente | Solo se calcula la salida (forward) |
| Es caro y lento; lo hacen grandes empresas | Es lo que ocurre cada vez que usas el modelo |
| Ejemplo: entrenar una red de reconocimiento | Ejemplo: pedirle algo a Claude |
| **ℹ Ampliación: crear agentes ≠ entrenar un modelo**  Punto de la clase muy relevante: para casi todo lo que construyó Carlos NO se entrena ninguna red. Se usa un LLM ya preentrenado (Claude) y se le especializa con instrucciones, skills y agentes. Entrenar una red neuronal desde cero con un dataset (lo que hace Mariana con PyTorch para los niños neurodivergentes) es un caso distinto y mucho más costoso, reservado a cuando realmente necesitas aprendizaje a partir de tus propios datos. |

## **8.3 Embeddings, sesgos y limpieza de datos**

Términos que aparecieron y conviene fijar:

- **Embedding**: representación numérica (un vector) de un texto o entidad, de forma que cosas parecidas quedan cerca en el espacio vectorial. Es lo que permite "buscar por significado".
- **Dataset**: conjunto de datos (idealmente autorizados o comprados) con el que se entrena o valida un modelo. En clase se remarcó: se entrena con datasets autorizados, **nunca con los datos de tus usuarios** sin base legal.
- **Sesgo (bias) de datos**: si el dataset está desequilibrado, el modelo aprende ese desequilibrio. Ejemplo real de clase: los estudios de autismo históricamente basados en varón blanco hacen que diagnosticar a una niña sea mucho más difícil. Limpiar sesgos es parte del trabajo de datos.
- **Limpieza de datos**: con pandas/numpy se depuran y aíslan las características antes de entrenar o predecir. Sin datos limpios, la predicción no vale.

## **8.4 "La IA aprende pero no sabe cómo": matiz**

| **ℹ Simplificación didáctica corregida**  En clase se dijo que "ni el creador sabe qué pasa por detrás del aprendizaje". Es una simplificación. Es cierto que los modelos son en gran parte "cajas negras": el conocimiento está distribuido entre miles de millones de parámetros y no se lee como un programa. Pero existe un campo entero, la interpretabilidad mecanicista, dedicado precisamente a abrir esa caja. Anthropic ha publicado avances (dictionary learning, características/features, circuitos) que ya explican parte de las decisiones del modelo. No es que no se sepa NADA; es que aún no se entiende TODO. |
| --- |

# **9. Ética, legalidad y alcance**

La sesión tocó varios temas legales importantes que conviene registrar, sobre todo porque el máster es de ciberseguridad y hay líneas rojas claras.

| **⚠ Datos biométricos y menores**  Biometría de menores: se distinguió correctamente validación de edad (comprobar que se es mayor de edad sin identificar) frente a verificación/identificación (que sí identifica y trata dato biométrico). Guardar datos biométricos de menores es altamente sensible y regulado; se citó incluso una sanción. La regla segura: si no se guarda ningún dato biométrico, no se está identificando. Ante cualquier duda, consúltalo con la normativa (RGPD, ENS) y no lo trates como un detalle menor. |
| --- |
| **⚠ Phishing solo en entornos autorizados**  Clonado de webs para phishing: solo tiene sentido y solo es lícito dentro de campañas autorizadas y con contrato (Red Team / concienciación tipo ProofPoint). Fuera de un alcance autorizado, clonar un sitio para engañar a usuarios es ilegal. Estos apuntes recogen la técnica únicamente en el marco de auditoría autorizada. |
| **⚠ Privacidad y cumplimiento**  Privacidad de datos con proveedores: en clase surgió el debate de enviar datos de clientes a un proveedor estadounidense. La práctica correcta que se describió: procesar lo delicado en el backend, cifrar los datos antes de enviarlos y minimizar lo que sale. Evitar el "shadow IT" (saltarse las políticas de la empresa usando el móvil o cuentas personales) por muy tentador que parezca. |

# **10. Conexión con sesiones anteriores**

Esta sesión abre el **bloque de IA** del máster y se conecta con lo ya visto de varias formas:

- **Metodología**: el flujo idea → requisitos → construcción → pruebas es primo del flujo de auditoría (enumeración → explotación → post-explotación → informe). En ambos casos, no avanzar sin evidencia y documentar cada paso.
- **Automatización con Python**: enlaza con tus scripts previos (x8\_lite.py, valfuzz.py). Aquí pandas/numpy aparecen para datos, y Playwright para automatizar navegador, igual que antes automatizabas enumeración.
- **Phishing y Red Team**: el clonado de webs conecta con el bloque de phishing con GoPhish (Carlos Castillo) que tenías en el horizonte.
- **Documentación persistente**: la idea de CLAUDE.md / notas .md como "memoria del proyecto" es exactamente el mismo principio que tu propio pipeline de apuntes y tu proyecto RedNotes Academy.

# **11. Resumen final**

Sesión introductoria de IA aplicada centrada en el vibe coding: construir productos rápido apoyándose en LLMs y agentes. Los fundamentos que quedan: distinguir modelo / aplicación / herramienta / agente; entender tokens y que el contexto no es memoria; y saber que la personalización viene del contexto, no de un modelo por usuario.

En la práctica: Claude Code como agente de programación, con CLAUDE.md como instrucciones persistentes, modos de permisos (y sus riesgos), selección de modelo para controlar coste, y RTK para comprimir salida de comandos. La sección más delicada, la de grafos vs. redes neuronales, exige recordar que un grafo de conocimiento con ontologías no es una red neuronal, y que crear agentes con un LLM preentrenado no es entrenar un modelo.

| **✓ Idea para llevarte**  La clase fue muy inspiradora en lo comercial (MVPs rápidos, upselling, ideas de negocio), pero técnicamente mezcló conceptos. Estos apuntes conservan las ideas útiles y corrigen la terminología para que estudies sobre base sólida. |
| --- |

# **12. Checklist de repaso**

1. Sé explicar la diferencia entre modelo, aplicación, herramienta y agente con un ejemplo.
2. Entiendo qué es un token y por qué la ventana de contexto no es memoria permanente.
3. Sé por qué documentar el proyecto en local (CLAUDE.md, .md) ahorra tokens.
4. Conozco los modos de permisos de Claude Code y por qué --dangerously-skip-permissions es peligroso fuera de un entorno aislado.
5. Sé qué es auto mode y por qué suele ser preferible al bypass total.
6. Entiendo el enrutado de modelos (Haiku/Sonnet/Opus/Fable) y cuándo usar cada uno.
7. Sé qué hace RTK y su límite (solo intercepta llamadas Bash).
8. Distingo un grafo de conocimiento (ontologías, Neo4j) de una red neuronal real (pesos, entrenamiento).
9. Sé la diferencia entre entrenamiento e inferencia, y entre crear agentes y entrenar un modelo.
10. Reconozco los límites legales: biometría de menores, phishing solo autorizado, privacidad de datos.

# **13. Preguntas de repaso**

## **13.1 Preguntas cortas**

1. ¿Qué diferencia hay entre un chatbot y un agente?
2. ¿Por qué se dice que la ventana de contexto no es memoria?
3. ¿Qué es el archivo CLAUDE.md y para qué sirve?
4. ¿Qué hace exactamente RTK y qué tipo de llamadas NO intercepta?
5. ¿Por qué --dangerously-skip-permissions debe usarse solo en entornos aislados?
6. ¿En qué se diferencia un grafo de conocimiento de una red neuronal?
7. ¿Qué es un embedding?

## **13.2 Preguntas de desarrollo**

1. Explica el flujo completo de vibe coding para construir un MVP y justifica por qué el MVP debe ser "de cartón piedra".
2. Un compañero dice que ha "entrenado una red neuronal" pidiéndole a Claude que conecte nodos con ontologías. Corrige la afirmación explicando la diferencia entre grafo de conocimiento y red neuronal.
3. Compara los modos de permisos de Claude Code (default, acceptEdits, plan, auto mode, bypass) en términos de seguridad y comodidad.

## **13.3 Tipo test**

**1. La ventana de contexto de un LLM es:**

- a) Memoria permanente del modelo
- b) El máximo de tokens que puede tener a la vista en una conversación
- c) La base de datos del modelo
- d) El número de parámetros del modelo

**2. `--dangerously-skip-permissions` está pensado para usarse en:**

- a) Tu máquina principal, sin más
- b) Producción, para ir más rápido
- c) Entornos aislados (contenedores, VMs)
- d) Cualquier sitio, no tiene riesgo

**3. Un grafo de conocimiento con ontologías (Neo4j):**

- a) Es una red neuronal entrenada con gradiente
- b) Ajusta pesos numéricos con backpropagation
- c) Relaciona nodos con aristas que tienen significado, por lógica simbólica
- d) Es lo mismo que un embedding

**4. RTK reduce tokens porque:**

- a) Cambia el modelo por uno más barato
- b) Comprime la salida verbosa de comandos de shell antes de que entre al contexto
- c) Borra el historial de la conversación
- d) Entrena un modelo más pequeño

**5. En Claude Code, para tareas simples conviene usar:**

- a) Siempre el modelo más potente
- b) Un modelo ligero (p. ej. Haiku/Sonnet), reservando el potente para tareas complejas
- c) Fable siempre
- d) Da igual el modelo

| **✓ Soluciones**  Soluciones tipo test: 1-b · 2-c · 3-c · 4-b · 5-b |
| --- |

# **14. Glosario**

| **Término** | **Definición breve** |
| --- | --- |
| Token | Unidad mínima en que el modelo trocea el texto; se factura y razona por tokens. |
| Ventana de contexto | Máximo de tokens que el modelo tiene a la vista; no es memoria permanente. |
| Agente | Modelo + herramientas + objetivo, que actúa en bucle con poca intervención. |
| Subagente | Agente especializado que otro agente invoca para una tarea concreta. |
| CLAUDE.md | Fichero de instrucciones persistentes del proyecto (system prompt del proyecto). |
| Auto mode | Modo de Claude Code con clasificadores que aprueban lo seguro y bloquean lo peligroso. |
| RTK | Rust Token Killer: proxy CLI que comprime la salida de comandos de shell. |
| Ontología | Traducción a lenguaje natural del sentido de una relación entre dos nodos. |
| Grafo de conocimiento | Nodos y aristas con significado explícito; razona por lógica simbólica. |
| Embedding | Vector que representa un texto/entidad; lo parecido queda cerca en el espacio. |
| Peso (weight) | Número que indica cuánto influye una neurona sobre otra; se ajusta al entrenar. |
| Sesgo de datos (bias) | Desequilibrio del dataset que el modelo aprende y reproduce. |
| Inferencia | Uso del modelo ya entrenado (pesos fijos) para producir una salida. |
| MVP | Producto mínimo viable; versión rápida para validar una idea. |

# **15. Actualización del registro (conceptos y herramientas de IA)**

Bloque copiable a tu base de conocimiento. Niveles de IA: Mencionado → Introducido → Comprendido → Practicado → Aplicado → Recurrente.

| **Concepto / Herramienta** | **Categoría** | **Nivel** |
| --- | --- | --- |
| Modelo vs aplicación vs herramienta vs agente | Fundamento | Introducido |
| Token / ventana de contexto | Fundamento | Introducido |
| Claude Code (CLAUDE.md, permisos, /model) | Agente / Herramienta | Introducido |
| Auto mode / acceptEdits / plan | Técnica de seguridad | Mencionado |
| RTK (Rust Token Killer) | Herramienta | Mencionado |
| Enrutado de modelos (model routing) | Técnica | Introducido |
| Grafo de conocimiento / ontologías (Neo4j) | Framework / Datos | Introducido |
| Obsidian (índice de conocimiento) | Herramienta | Mencionado |
| Red neuronal (pesos, backprop, gradiente) | Red neuronal | Introducido |
| Embeddings | Fundamento | Introducido |
| Sesgos y limpieza de datos (pandas/numpy) | Preparación de datos | Mencionado |
| Interpretabilidad mecanicista | Método de evaluación | Mencionado |
| Playwright (automatización de navegador) | Herramienta / Agente | Mencionado |

# **16. Fuentes técnicas consultadas**

Las correcciones y ampliaciones de estos apuntes se han contrastado con documentación oficial y fuentes técnicas (consulta: 16/07/2026). El contenido de clase es la fuente primaria; lo siguiente respalda solo las ampliaciones marcadas.

- Anthropic — *Choose a permission mode / Claude Code Docs* (modos de permisos, --dangerously-skip-permissions, restricción root/sudo). Fuente primaria.
- Anthropic — *How we built Claude Code auto mode* (auto mode como alternativa segura al bypass). Fuente primaria.
- rtk-ai/rtk (GitHub) y web oficial de RTK — qué es RTK, hook PreToolUse, límite a llamadas Bash. Fuente primaria del proyecto.
- Anthropic — investigación de interpretabilidad (dictionary learning, features, circuitos). Fuente primaria para el matiz de "caja negra".

| **⚠ AVISO**  Nota: las cifras de cuota, precios y nombres de modelos (Haiku/Sonnet/Opus/Fable) dichas en clase no se han fijado como definitivas: cambian con frecuencia y deben verificarse en la documentación oficial de Anthropic antes de usarse como referencia. |
| --- |
