---
tags:
- Inteligencia artificial
---

# IA De los cimientos a la cima

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**IA: De los cimientos a la cima**

Instructor: Carlos Gómez Pintado · 24/07/2026

*Bloque de IA · Del chat de navegador a Claude Code y la arquitectura de agentes*

# **1. Cómo leer estos apuntes**

| **ℹ Cómo usar este documento**  Estos apuntes recogen lo explicado en clase y añaden **correcciones marcadas** donde la terminología o el concepto necesitaban precisión. La clase se planteó explícitamente como una vuelta a los cimientos: el instructor cambió el título previsto ('algoritmos de machine learning') al detectar, por feedback de los alumnos, que se habían dado por supuestas las bases de la IA.Código de colores: los avisos **rojos** son correcciones importantes que conviene no arrastrar al examen; los **azules** son matices, ampliaciones o simplificaciones didácticas; los **naranjas** son límites y riesgos; los **verdes** son soluciones y confirmaciones. |
| --- |

# **2. Objetivos de aprendizaje**

- Definir qué es una IA, un LLM, un modelo, un token, el contexto y un prompt, con su base técnica y no solo su definición de uso.
- Entender cómo un modelo de lenguaje predice el siguiente token y por qué el contexto determina la calidad de la respuesta.
- Distinguir los tres niveles de uso: IA de navegador, aplicación de escritorio e IA especializada (Claude Code).
- Comprender por qué un agente con acceso a herramientas del sistema supera a un chat de navegador en tareas complejas.
- Diseñar una arquitectura de agentes (orquestador, prompter, selector de modelo, agentes especializados) y saber dónde vive cada instrucción.
- Aplicar el criterio de enrutado de modelos: elegir el modelo más óptimo por tarea, no el más potente por defecto.

# **3. Resumen inicial**

La sesión recorre la escalera completa del uso de IA. Empieza en el chat de navegador, con ejemplos cotidianos (dieta, rutina de gimnasio, consultas de historia) y una práctica en directo: generar un script de PowerShell que resuelva el Buscaminas. Esa práctica falla repetidamente y sirve de argumento: el navegador no tiene entorno de pruebas ni acceso al sistema, así que no puede verificar lo que produce.

La segunda mitad introduce los fundamentos reales —qué es un token, cómo se predice el siguiente, por qué el contexto cuesta dinero— y termina en Claude Code, donde el mismo ejercicio se resuelve solo porque el agente puede inspeccionar el equipo, ejecutar, comprobar el resultado e iterar. Cierra con la arquitectura de agentes del instructor y el reparto de instrucciones entre CLAUDE.md global y el del proyecto.

# **4. Conceptos y terminología**

## **4.1. Qué es (y qué no es) una inteligencia artificial**

En clase se pidió una definición a un alumno, que respondió *"una herramienta con un sistema de machine learning que va aprendiendo de lo que le metas"*. El instructor la reformuló así: una IA es **una herramienta de toma de decisiones**; funciona como un buscador mucho más rápido que intenta (1) usar el contexto y (2) deducir lo que el usuario espera recibir, y devuelve el resultado que cree más cercano a esa expectativa.

La frase que resume la postura de la clase: **la IA no genera, sino que busca, conecta, une y expone**. Es una simplificación útil para desmitificar, pero conviene precisarla.

| **⚠ Corrección clave: un LLM no busca, predice**  En clase se dijo que "la IA no genera; busca, conecta y expone" y que es "un Google más rápido". La intuición que hay detrás es correcta —el modelo no inventa de la nada, reorganiza patrones aprendidos— pero la formulación literal induce a error en dos puntos.**Primero: no hay búsqueda.** Un modelo de lenguaje no consulta una base de datos ni Internet cuando responde. Genera prediciendo el siguiente token a partir de sus **pesos**, que son los números ajustados durante el entrenamiento. Solo consulta fuentes externas si se le da explícitamente una **herramienta** de búsqueda web o de lectura de ficheros.**Segundo: sí genera.** Produce secuencias que no existen literalmente en ningún sitio de su entrenamiento. Lo que no hace es *razonar desde cero*: compone a partir de patrones estadísticos aprendidos. Por eso la salida puede ser fluida y a la vez falsa (alucinación). |
| --- |

## **4.2. LLM, modelo, contexto, token y prompt**

Las definiciones que se manejaron en clase, ordenadas y precisadas:

| **Término** | **Lo dicho en clase** | **Precisión** |
| --- | --- | --- |
| **LLM** (*large language model*, modelo de lenguaje grande) | "Guarda un historial del chat y lo consulta" | El LLM es el modelo en sí: una red neuronal entrenada para predecir texto. El historial no está *dentro* del modelo; se le vuelve a enviar en cada turno como contexto. |
| **Modelo** | Resultado de distintos tipos de entrenamiento; por eso hay Haiku, Sonnet, Opus, Fable | Correcto. Cada modelo difiere en datos, tamaño, entrenamiento y objetivo de diseño. |
| **Contexto** (*context window*, ventana de contexto) | Todo lo hablado en la conversación; a más contexto, mejor resultado | Correcto de fondo. Es el máximo de tokens que el modelo tiene a la vista, incluida su propia respuesta. |
| **Token** | "Fragmentos de palabras con los que deduce la siguiente" | Correcto y bien explicado: ni letra ni palabra, sino unidad subléxica. |
| **Prompt** | El texto que enviamos a la IA para que procese | Correcto. |
| **Agente** | Programa con instrucciones previas, habilidades y capacidad de comunicarse con otros agentes | Correcto. La clave que lo separa del chatbot es que persigue un objetivo usando herramientas en bucle. |

## **4.3. Distinciones que hay que tener claras**

| **Distinción** | **En qué se diferencian** |
| --- | --- |
| IA · Machine learning · Deep learning | La IA es el campo general. El **machine learning** es el subconjunto que aprende de datos en lugar de seguir reglas escritas. El **deep learning** es el subconjunto del ML que usa redes neuronales de muchas capas. Los LLM son deep learning. |
| Modelo · Aplicación · Herramienta · Agente | El **modelo** es la red entrenada. La **aplicación** es el producto que lo envuelve (claude.ai, ChatGPT). La **herramienta** es algo que el modelo invoca (búsqueda, terminal, navegador). El **agente** usa modelo y herramientas para perseguir un objetivo en bucle. |
| Entrenamiento · Inferencia | **Entrenar** ajusta los pesos con un dataset; es caro y se hace una vez. **Inferencia** es cada consulta que hacemos al modelo ya entrenado; los pesos no cambian. Todo lo que hicimos en clase es inferencia. |
| Ventana de contexto · Memoria permanente | El contexto se pierde al cerrar o llenarse la conversación. La persistencia real llega al sacarlo a ficheros (CLAUDE.md, notas .md) o mediante una función de memoria del producto. |
| Chatbot · Agente | El chatbot responde. El agente decide pasos, ejecuta acciones, observa el resultado e itera hasta cumplir el objetivo. |
| Conocimiento aprendido · Búsqueda en Internet | Lo aprendido está en los pesos y tiene fecha de corte. La búsqueda es una herramienta externa que inyecta información fresca en el contexto. |

# **5. Explicación intuitiva**

La analogía central de la clase para justificar el salto a Claude Code: el instructor comparó dar clase **con pizarra y sin ella**. Sin pizarra puede explicar, pero peor: menos ejemplos, menos claridad. Con la habilidad de dibujar, escribir y usar color, transmite mucho mejor lo mismo.

Trasladado a la IA: el chat de navegador es la clase sin pizarra —solo texto entra, solo texto sale—. Claude Code le da periféricos: terminal, ficheros, navegador, capacidad de ejecutar y comprobar. El modelo es el mismo; lo que cambia es el **arsenal de herramientas** a su alcance.

| **ℹ Nota sobre las analogías de clase**  El instructor usó una segunda comparación para la misma idea, ilustrando que más herramientas equivalen a más poder ofensivo. La idea de fondo —la capacidad de un sistema depende de las herramientas que le demos, no solo de su inteligencia— es válida y es la que conviene retener. |
| --- |

# **6. Desarrollo técnico**

## **6.1. Cómo se predice el siguiente token**

Esta fue la explicación mejor construida de la sesión. Partiendo de la frase *el gato es negro*, el instructor mostró que el modelo no lee palabras completas, sino fragmentos, y que va reduciendo posibilidades por contexto gramatical:

| el gato es negro -> [el] [gat] [o] [es] [neg] [ro] |
| --- |

El razonamiento por pasos tal y como se expuso en clase:

1. Lee el: es un determinante artículo. Tras un artículo viene casi siempre un sustantivo.
2. Deduce que el siguiente hueco es un sustantivo y lee gat: las posibilidades caen de miles a unas pocas (gato, gata, gatos...).
3. Lee el siguiente fragmento y resuelve gato. Tras artículo + sustantivo, espera un verbo.
4. Lee es: efectivamente un verbo. Tras "el gato es" espera un adjetivo.
5. Lee neg: candidatos como negro, negativo, negado. Por contexto, negro es el más probable.

| **ℹ Simplificación didáctica corregida**  Esta descripción es una **simplificación didáctica** muy buena para entender la idea, pero no es literalmente el mecanismo interno.El modelo no aplica reglas gramaticales explícitas ('tras un artículo va un sustantivo') ni mantiene una lista de candidatos que va tachando. Lo que hace es calcular, en una sola pasada, una **distribución de probabilidad sobre todo su vocabulario** para la siguiente posición, y elegir de ahí. Que el resultado respete la gramática es una consecuencia de haber visto muchísimo texto bien formado, no de tener las reglas programadas.La conclusión práctica de la clase sí es correcta: el modelo elige el siguiente token basándose en todo lo anterior, y por eso el contexto manda. |
| --- |
| **ℹ Ampliación técnica: temperatura y aleatoriedad**  La **temperatura** no se mencionó en clase, pero explica algo que sí se comentó: por qué el modelo no siempre responde igual. Tras calcular las probabilidades, la temperatura regula cuánta aleatoriedad se admite al elegir. Temperatura baja = respuestas más deterministas; alta = más variadas, pero más propensas a divagar. No es un dial de 'creatividad' ni de 'inteligencia'.Esto también matiza el ejemplo del número aleatorio de la clase: si se pide un número del 1 al 100, el modelo tiende a repetir los mismos (37, 42, 73). No es que 'no sepa' elegir al azar: reproduce el sesgo de los números que más aparecen en el texto humano. |

## **6.2. Por qué el contexto cuesta dinero**

El instructor encadenó la explicación de tokens con la de coste, y el razonamiento es correcto: con cada prompt nuevo el modelo tiene que procesar todo el contexto acumulado para deducir lo que viene. Más contexto significa más cómputo, más tiempo de respuesta y más tokens facturados.

De ahí la regla que se repitió varias veces: **elegir el modelo más óptimo para cada tarea, no el más potente por defecto**. La imagen que usó: encender una bombilla con un reactor nuclear. Funciona, pero es un desperdicio y puede traer efectos inesperados.

| **⚠ Matiz: más potente no es siempre mejor**  Esta es la idea de **enrutado de modelos** (*model routing*) y es una de las más rentables de la sesión. El tamaño no garantiza calidad: influyen los datos, el entrenamiento, el alineamiento y, sobre todo, la adecuación a la tarea. Para clasificar, extraer datos o resumir texto corto, un modelo pequeño suele ser mejor opción por coste y latencia. |
| --- |

Sobre DeepSeek, la clase afirmó que su irrupción se debió a lograr un cómputo de tokens entre 20 y 30 veces menor que el de la competencia por cómo entrenaron la red.

| **⚠ Dato pendiente de verificar**  El fondo es correcto —DeepSeek destacó por eficiencia de entrenamiento e inferencia, y eso abarató el coste por token— pero **la cifra concreta citada en clase no ha podido verificarse** con documentación oficial. Trátala como orden de magnitud aproximado y no como dato de examen. Las comparativas de coste entre proveedores cambian con cada versión. |
| --- |

## **6.3. Los tres niveles de uso de la IA**

El eje vertebrador de la sesión. Los tres escalones, con lo que cada uno aporta y lo que le falta:

| **Nivel** | **Qué es** | **Qué puede hacer** | **Su límite** |
| --- | --- | --- | --- |
| **IA de navegador** | El chat web (claude.ai, ChatGPT). Es lo que usa la inmensa mayoría de la gente | Responder, sintetizar, redactar, generar scripts sueltos, leer imágenes | No ejecuta ni comprueba lo que produce. Sin acceso al sistema ni a ficheros. Contexto más limitado |
| **Aplicación de escritorio** | El cliente instalado; en clase se asocia al trabajo con ficheros y programas locales | Trabajar con ficheros y aplicaciones del equipo | Intermedio: más capacidad que el navegador, menos control que la terminal |
| **IA especializada (Claude Code)** | Interfaz de terminal con acceso a las herramientas del equipo | Crear proyectos completos, ejecutar, probar, corregirse e iterar hasta que funcione | Requiere criterio de arquitectura y control de permisos |
| **⚠ Cifras ilustrativas, no datos**  La afirmación de clase de que "el 95% de la gente usa la IA como psicólogo, el 4% como agenda y el 1% hace cosas útiles" es una **figura retórica del instructor**, no un dato de ninguna encuesta. Se recoge porque ilustra su argumento —casi nadie explota el potencial real— pero no debe citarse como estadística. |

## **6.4. La práctica del Buscaminas: por qué falló en el navegador**

El ejercicio en directo fue pedir un script .ps1 que abriera un Buscaminas, permitiera elegir dificultad con un deslizador y se resolviera solo a la vista. Se hizo con dos alumnos y dos proveedores distintos. La cadena de problemas fue instructiva:

- **Error de ejecución**: el script no se lanzaba por la política de ejecución de PowerShell (*Execution Policy*), no por un fallo del código.
- **Fallos lógicos**: el resolutor pinchaba sobre una mina porque no se puede resolver un Buscaminas de un solo clic; requiere deducción encadenada.
- **Iteración manual**: cada error había que copiarlo o fotografiarlo y devolvérselo al chat para que regenerase. Se resolvió con capturas, que el modelo leyó y analizó.
- **Simulación en vez de uso**: los scripts *programaban* un Buscaminas simulado; nunca abrieron el juego real, porque el navegador no puede comprobar si existe en el sistema.

El diagnóstico del instructor: el navegador **no tiene entorno de pruebas**, así que entrega código sin haberlo ejecutado nunca. La verificación recae entera en el usuario.

| **✓ La idea clave de la práctica**  Este es el argumento técnico de la sesión y conviene retenerlo por encima de la anécdota: la diferencia entre el chat y el agente no es que uno sea 'más listo'. Es que **el agente puede cerrar el bucle**: ejecuta, observa el error real, corrige y vuelve a probar. Sin ese bucle, el modelo solo puede predecir código plausible. |
| --- |

## **6.5. El mismo ejercicio en Claude Code**

Repetido en la terminal, el comportamiento fue distinto desde el primer paso. Ante "abre el Buscaminas y echa una partida", el agente:

1. Lanzó un comando de PowerShell para comprobar si el juego estaba instalado.
2. Detectó que no lo estaba y, de paso, identificó el sistema operativo del equipo.
3. Propuso vías de instalación (Microsoft Store, GitHub, instalador) y las intentó.
4. Al no convencer el resultado, programó un Buscaminas desde cero: eligió Python por su cuenta y escribió 629 líneas en 4 minutos y 43 segundos, con menús, personalización y controles de límites.

El instructor subrayó dos detalles: el agente usó recursos que a un humano no se le habrían ocurrido (consultar la Store, verificar el identificador del producto) y **no paró hasta que funcionó**, porque tenía manera de comprobarlo.

Después se pidió un **agente** resolutor en lugar de un script, y en una segunda pestaña un panel web que recogiera los resultados de las partidas en JSON. Alcanzó en torno a un 33% de aciertos en nivel experto, resolviendo por reglas del juego.

| **ℹ Script vs agente**  El cambio de palabra de la clase —de "script" a "agente"— es una distinción real y vale la pena fijarla. Un **script** es una secuencia fija de instrucciones: hace siempre lo mismo. Un **agente** recibe un objetivo, decide qué pasos dar, usa herramientas, observa el resultado y ajusta. El script del navegador simulaba un tablero; el agente juega, falla y puede medirse. |
| --- |

## **6.6. Dónde viven las instrucciones: CLAUDE.md**

La parte más aprovechable de la sesión para el proyecto propio. El instructor describió CLAUDE.md como "el cerebro": el fichero que se consulta antes de actuar y donde se ponen las instrucciones que deben cumplirse siempre. Mostró el suyo, que obliga a pasar toda petición por un agente *prompter* antes de invocar a ningún otro, y a elegir el modelo menos costoso capaz de hacer bien el trabajo.

Sobre el conflicto entre el CLAUDE.md global y el del proyecto, formuló la regla como **"excepción, no norma"**: el global es la norma, el del proyecto es la excepción, y prevalece la excepción.

| **✓ Confirmado y ampliado: jerarquía de CLAUDE.md**  **La regla del instructor es correcta** y coincide con la documentación oficial: lo más específico prevalece sobre lo más general, así que las instrucciones del proyecto ganan a las personales globales.Conviene añadir el mecanismo, que la clase no detalló: los ficheros **no se sobrescriben, se concatenan** en el contexto, ordenados de lo más general a lo más específico. Como lo que se lee al final pesa más, el resultado práctico es el que describió el instructor.El orden documentado, de menor a mayor especificidad, es: política gestionada por la organización, instrucciones de usuario (~/.claude/CLAUDE.md), instrucciones de proyecto (./CLAUDE.md o ./.claude/CLAUDE.md) e instrucciones locales del proyecto (./CLAUDE.local.md).Matiz importante: CLAUDE.md es **contexto, no configuración obligatoria**. Orienta el comportamiento, pero no lo garantiza. Para bloquear una acción pase lo que pase hacen falta hooks o ajustes de permisos. |
| --- |

Comandos útiles mencionados o relacionados con lo visto:

| /memory # abre y edita los ficheros de instrucciones  /context # muestra qué ficheros se han cargado realmente en la sesión  /init # genera un CLAUDE.md inicial analizando el proyecto |
| --- |

## **6.7. Skills: cómo se hace el trabajo**

La distinción que trazó el instructor: el **agente** define quién hace el trabajo (personalidad, objetivo, límites, herramientas permitidas); la **skill** define **cómo** se hace. Su ejemplo fue una skill de humanización de texto que prohíbe explícitamente guiones largos, emojis, cajas de aviso decorativas, exclamaciones de más, mayúsculas enfáticas y negritas sin motivo, y que fija un tono claro, directo y en segunda persona.

El detalle de arquitectura que hizo notar: como su agente *prompter* consume esa skill y es quien habla después con el resto de agentes, el estilo **se hereda** hacia todos los agentes de la cadena sin repetirlo en cada uno.

## **6.8. Tools: limitar lo que un agente puede tocar**

En la definición de cada agente se especifica qué herramientas puede usar. La pregunta que planteó en clase: ¿tiene sentido que un agente de diseño de interfaces pueda acceder al correo y enviar emails? No. Y su regla de trabajo fue: se dan las herramientas concretas necesarias y, si el agente necesita otra, que la pida y se autorice.

| **⚠ Seguridad de agentes: privilegio mínimo y prompt injection**  Este es el puente más directo con el bloque de ciberseguridad del máster, y el propio instructor lo señaló al mencionar **zero trust**. Una arquitectura de agentes es una superficie de ataque: si un agente con acceso a shell, ficheros y red lee contenido no confiable (un repositorio, un fichero descargado, una página web), ese contenido puede contener instrucciones dirigidas al modelo. Es **prompt injection**, y es el equivalente de las inyecciones clásicas que ya se han visto en web.Mínimo de privilegio aplicado a agentes: solo las herramientas necesarias, revisión de lo que el agente lee, y desconfianza ante todo contenido externo. |
| --- |

Durante la clase, un alumno preguntó cómo evitar tener que aprobar cada acción, y se le indicó el flag que desactiva las confirmaciones. Es una respuesta correcta a la pregunta literal, pero necesita contexto de seguridad.

| **⚠ Corrección de seguridad importante: saltarse los permisos**  El flag --dangerously-skip-permissions (equivalente a --permission-mode bypassPermissions) **desactiva todas las pausas de aprobación**. La documentación oficial es explícita: no ofrece ninguna protección frente a prompt injection ni frente a acciones no deseadas.Riesgos reales: borrado o corrupción irreversible de ficheros, ejecución de comandos dañinos, acceso a credenciales (.env, claves SSH, tokens) y exfiltración de datos si una instrucción maliciosa llega al agente.**Está pensado para entornos desechables y aislados** —contenedor o máquina virtual, sin credenciales de producción—, nunca para el portátil de trabajo. De hecho, no puede usarse con privilegios de root/sudo por seguridad.Alternativas intermedias para la fatiga de aprobaciones: el **modo automático** (aprobaciones delegadas a clasificadores de seguridad), **acceptEdits** (autoaprueba ediciones de ficheros pero mantiene la puerta en los comandos de shell), permisos con lista de herramientas permitidas, y el **modo plan** para explorar sin tocar nada. Y en cualquier caso: commit antes de empezar una sesión larga. |
| --- |

## **6.9. Grafos, nodos y aprendizaje: lo que se estaba montando en paralelo**

Durante toda la clase, varios alumnos tenían en marcha grafos en Obsidian generados con IA (nodos por características de coches, correlacionados entre sí desde un CSV o SQLite). El propio instructor aclaró al enseñar el suyo: *"esto no es una red neuronal, esto es una red relacional"*.

| **⚠ Corrección clave: grafo de conocimiento ≠ red neuronal**  La aclaración del instructor es exacta y merece quedar fijada, porque es una confusión frecuente.Un **grafo de conocimiento** tiene nodos y aristas con significado explícito y legible ('este coche es de esta marca'), y se consulta por lógica y búsquedas. Una **red neuronal** tiene capas de unidades conectadas por **pesos numéricos** ajustados durante el entrenamiento mediante *backpropagation* y descenso del gradiente; ahí el conocimiento está distribuido en números, no en aristas con texto.Pedirle a un modelo que construya nodos y ontologías produce un grafo excelente, pero **no es entrenar una red neuronal**. Son herramientas distintas para problemas distintos, y la sesión que viene —donde se prevé meter machine learning al agente de ajedrez— es el momento de tener clara la diferencia. |
| --- |

Sobre el machine learning, la clase lo definió como "un algoritmo con el que una IA aprende basándose en prueba y error", con recompensa cuando acierta y castigo cuando falla, y lo llamó *A/B testing*.

| **⚠ Corrección clave: aprendizaje por refuerzo ≠ A/B testing**  La descripción corresponde al **aprendizaje por refuerzo** (*reinforcement learning*): un agente actúa, recibe una señal de recompensa y ajusta su comportamiento para maximizarla. Es exactamente lo que haría falta para el agente de ajedrez que se propuso.El nombre usado en clase, **A/B testing**, designa otra cosa: comparar dos variantes de algo (una web, un mensaje) entre usuarios reales para ver cuál rinde mejor. No es una técnica de entrenamiento de modelos.Y el machine learning es más amplio que el refuerzo: incluye **aprendizaje supervisado** (datos etiquetados) y **no supervisado** (encontrar estructura sin etiquetas), que son los más habituales. |
| --- |

También se comentó que los modelos antiguos daban respuestas complacientes —si el usuario decía "esto no es así", el modelo se disculpaba y cambiaba— y que en los nuevos se ha corregido. En la demo en directo, sin embargo, el modelo sí cambió su valoración de un texto cuando el instructor afirmó haberlo escrito a mano.

| **⚠ Matiz: la adulación está mitigada, no eliminada**  El fenómeno es real y tiene nombre: **adulación** o *sycophancy*, la tendencia a priorizar la conformidad del usuario sobre la exactitud. Se origina en el entrenamiento con retroalimentación humana, donde las respuestas que agradan tienden a puntuar mejor.Dos matices sobre lo dicho en clase. **No está eliminado**, como demostró la propia demo: está mitigado, no resuelto. Y en el caso concreto del ejemplo, cambiar de opinión al recibir información nueva ('lo escribí yo a mano') es en parte razonable: el problema aparece cuando el modelo cede ante la simple insistencia sin datos nuevos.Consecuencia práctica: no uses la conformidad del modelo como confirmación de que tienes razón. |
| --- |

# **7. Funcionamiento paso a paso**

**Cómo genera texto un modelo de lenguaje.** Representación simplificada del recorrido desde el texto de entrada hasta la respuesta:

| **1. Texto de entrada (prompt + contexto)** |
| --- |

**↓**

| **2. Tokenización: el texto se parte en fragmentos** |
| --- |

**↓**

| **3. Embeddings: cada token pasa a vector numérico** |
| --- |

**↓**

| **4. Capas Transformer: se relacionan todos los tokens entre sí** |
| --- |

**↓**

| **5. Probabilidades sobre el vocabulario completo** |
| --- |

**↓**

| **6. Selección del siguiente token (según temperatura)** |
| --- |

**↓**

| **7. Se repite el ciclo hasta completar la respuesta** |
| --- |
| **ℹ NOTA**  Estos diagramas son representaciones simplificadas: omiten detalles del funcionamiento real. |

**Flujo de un agente con herramientas.** Es lo que se vio en directo con Claude Code y el Buscaminas:

| **1. Objetivo del usuario ('abre el Buscaminas y juega')** |
| --- |

**↓**

| **2. El agente lee su contexto e instrucciones (CLAUDE.md)** |
| --- |

**↓**

| **3. Selecciona la herramienta adecuada (terminal, ficheros, web)** |
| --- |

**↓**

| **4. Ejecuta la acción según los permisos concedidos** |
| --- |

**↓**

| **5. Observa el resultado real (funciona / error concreto)** |
| --- |

**↓**

| **6. Itera corrigiendo, o entrega si el objetivo se cumple** |
| --- |

**↓**

| **7. El usuario revisa y valida** |
| --- |

**Arquitectura de agentes del instructor.** El flujo que definió en su CLAUDE.md para cualquier petición:

| **1. El usuario lanza una petición (prompt)** |
| --- |

**↓**

| **2. El orquestador la recibe (conoce todo el proyecto)** |
| --- |

**↓**

| **3. Agente prompter: reescribe y optimiza el prompt** |
| --- |

**↓**

| **4. Selector de modelo: elige el más óptimo por coste/capacidad** |
| --- |

**↓**

| **5. Agente destino especializado (diseño, código, investigación)** |
| --- |

**↓**

| **6. El orquestador registra lo hecho en un .md de respaldo** |
| --- |

El fichero de respaldo cumple una función concreta que el instructor destacó: si algo se rompe, cualquier agente puede leer ese .md, seguir los pasos dados y reconstruir el proyecto.

# **8. Ejemplos prácticos de la sesión**

## **8.1. Usos cotidianos en el navegador**

- **Dieta semanal**: se pidió a dos proveedores el mismo prompt con altura, peso y objetivo, pidiendo macros, lista de la compra y cantidades. Los resultados fueron parecidos en calorías pero divergían en el reparto de macros y en el detalle.
- **Rutina de gimnasio**: tabla de ejercicios para tres días y hora y media por sesión. Resultados casi idénticos entre modelos.
- **Consulta histórica**: comparación entre preguntar el descubrimiento de América a un buscador (dos clics y leer) o al chat (respuesta directa y ampliable a un PDF extenso).

El punto del instructor con estos ejemplos: son peticiones **sin contexto real**. El modelo no sabe nada relevante del usuario más allá de dos cifras, así que responde de forma genérica.

| **✓ Buena práctica: preferir el 'no lo sé' al dato inventado**  Al pedir el precio de la compra, un proveedor reconoció no poder navegar por la web del supermercado y el otro entregó una estimación. El instructor lo valoró como un avance: **admitir que no se tiene el dato** en lugar de inventarlo con aplomo, que es lo que ocurría antes.Es el hábito correcto que conviene interiorizar: si un modelo da cifras concretas de precios, fechas o referencias sin haber consultado una fuente, esas cifras hay que verificarlas. |
| --- |

## **8.2. La técnica de prompting que se enseñó**

Antes de pedir el script del Buscaminas, el instructor construyó el prompt de forma deliberada y luego pidió al modelo que participara en definirlo. La instrucción añadida fue, en esencia:

| Hazme tantas preguntas como consideres necesarias para definir correctamente los requisitos,  propon mejoras para crear algo mejor que lo que te propongo,  y el resultado de esta conversacion debe ser el script funcional. |
| --- |

El modelo respondió con preguntas de diseño concretas: niveles de dificultad fijos en lugar de deslizador continuo, modo de partida (autoresolución, mixto o paso a paso), nivel de análisis del resolutor y versión de PowerShell de destino.

El instructor destacó además que en su prompt **no dijo nunca explícitamente** que el script fuera para resolver el Buscaminas: lo mencionó solo al final, y el modelo dedujo la intención por contexto. También recomendó escribir en mayúsculas lo imprescindible y, cuando uno no domina la tecnología, conversar primero con el modelo para que aconseje formatos y enfoque antes de pedir el resultado.

| **ℹ Sobre la técnica de prompting**  La técnica —pedir preguntas y mejoras antes del entregable— es de las más útiles de la sesión y está bien fundamentada: reduce la ambigüedad, que es la principal causa de que el resultado no se parezca a lo que uno quería.Dos matices. Escribir en mayúsculas puede dar énfasis, pero es menos fiable que **estructurar** el prompt (secciones, requisitos numerados, criterios de aceptación). Y sobre la deducción por contexto: que el modelo acertara la intención es una comodidad, no una garantía. En un requisito crítico, la ambigüedad es un riesgo, no una virtud. |
| --- |

# **9. Comparaciones importantes**

## **9.1. Chat de navegador frente a Claude Code**

| **Aspecto** | **IA de navegador** | **Claude Code (terminal)** |
| --- | --- | --- |
| Entrada y salida | Texto e imágenes | Texto más acceso real al sistema |
| Ejecución | No ejecuta lo que produce | Ejecuta, comprueba y corrige |
| Ciclo de error | Manual: el usuario copia el fallo y lo devuelve | Automático: detecta el error e itera |
| Alcance | Un fichero o fragmento suelto | Proyectos completos con varios ficheros relacionados |
| Contexto | Más limitado; sesión compartida en servidor | Mayor, gestionado en el propio equipo |
| Paralelismo | Una conversación cada vez | Varias pestañas y proyectos a la vez |
| Instrucciones persistentes | Por conversación | CLAUDE.md, skills, subagentes |
| Riesgo | Bajo: no toca el sistema | Requiere control de permisos y herramientas |

## **9.2. Contextos entre pestañas**

Un punto que el instructor remarcó en directo: dos sesiones abiertas **no comparten contexto**. Cuando pidió en una pestaña un panel para los resultados del agente de la otra, lo que ocurrió no fue comunicación entre pestañas: el agente **buscó en el disco** la carpeta del proyecto y leyó sus ficheros.

| **✓ Confirmado: el disco es la memoria compartida**  La observación es correcta y es una de las más prácticas de la sesión. Cada sesión tiene su propia ventana de contexto, aislada. Lo que sí se comparte es **el sistema de ficheros**: por eso funciona sacar el estado a ficheros .md o JSON.Es la misma razón por la que existe CLAUDE.md: lo que quieres que sobreviva a la sesión no puede vivir en la conversación, tiene que estar en disco. |
| --- |

# **10. Aplicación a Claude y Claude Code**

La clase citó los modelos Fable, Opus, Sonnet y Haiku, y explicó que unos se entrenan con más parámetros o para tareas distintas. Esa parte es correcta. Los datos concretos, contrastados con la documentación oficial en la fecha de consulta:

| **Modelo** | **Perfil** | **Contexto** | **Precio (entrada / salida por millón de tokens)** |
| --- | --- | --- | --- |
| Claude Fable 5 | Máxima capacidad, agentes de larga duración | 1M tokens | 10 $ / 50 $ |
| Claude Opus 4.8 | Programación agéntica compleja y trabajo empresarial | 1M tokens | 5 $ / 25 $ |
| Claude Sonnet 5 | Equilibrio entre velocidad e inteligencia | 1M tokens | 3 $ / 15 $ |
| Claude Haiku 4.5 | El más rápido, capacidad cercana a frontera | 200k tokens | 1 $ / 5 $ |
| **✓ Datos verificados**  *Información confirmada por Anthropic* — documentación oficial de modelos, consultada el 24/07/2026.Observa que la diferencia de precio entre el modelo más caro y el más económico es de **diez veces en entrada**. Esto respalda con números exactos el argumento del instructor sobre el enrutado de modelos: usar el modelo más caro para una tarea trivial multiplica el coste sin mejorar el resultado.Nota: los planes, límites, precios y nombres de modelos evolucionan con frecuencia. Verifica las cifras en la documentación oficial antes de usarlas como referencia definitiva. |
| **⚠ No verificable: cómo se entrena cada modelo**  La afirmación de clase de que "Fable se ha basado en toda la información que Opus ha recolectado" describe un encadenamiento entre modelos que **no está documentado públicamente**. Los detalles de los datos y el proceso de entrenamiento de cada modelo no son públicos.*Detalle interno no publicado*: no debe afirmarse como hecho. Lo que sí es público y suficiente para el examen: los modelos difieren en capacidad, coste, latencia y ventana de contexto, y se eligen según la tarea. |

Sobre la afirmación de que el chat de navegador es "un mini Docker que se instala en el servidor y luego desaparece":

| **⚠ Matiz sobre la infraestructura**  La intuición de fondo es razonable —hay ejecución aislada y efímera del lado del servidor— pero **la arquitectura concreta de la infraestructura de Anthropic no es información pública**.*Detalle interno no publicado.* Lo que sí es observable y basta para entender la diferencia: en el navegador el modelo no tiene acceso a tu sistema de ficheros ni a tus programas, mientras que en la terminal sí, con los permisos que le concedas. |
| --- |

# **11. Herramientas de la sesión**

| **Herramienta** | **Objetivo** | **Fase / Área** | **Uso visto en clase** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| Claude Code | Agente de terminal con acceso al sistema | Agentes | Buscaminas resuelto de principio a fin, agentes y panel web | Practicado | Eje de la sesión y del bloque |
| Chat de navegador (claude.ai / ChatGPT) | Consulta y generación de texto y código | Inferencia | Dieta, rutina, historia, script .ps1 | Recurrente | Sin ejecución ni verificación |
| CLAUDE.md | Instrucciones persistentes por usuario y proyecto | Documentación | Reglas de flujo y de elección de modelo | Introducido | Jerarquía: lo específico prevalece |
| Skills | Definir *cómo* se ejecuta una tarea | Agentes | Skill de humanización de texto | Introducido | Se heredan a través del prompter |
| Subagentes | Delegar subtareas a agentes especializados | Agentes | Orquestador, prompter, selector, diseño | Introducido | Cada uno con sus tools |
| PowerShell | Intérprete y automatización en Windows | Automatización | Ejecución de los scripts .ps1 | Practicado | *Execution Policy* bloqueó la primera ejecución |
| Obsidian | Notas enlazadas y visualización de grafos | Datos / Conocimiento | Grafos de nodos generados con IA | Mencionado | Red **relacional**, no neuronal |
| Webhook de escucha | Recibir datos por HTTP POST | Desarrollo | Recepción del inventario del equipo en JSON | Practicado | Base del panel de inventario mostrado |
| Enrutado de modelos | Elegir el modelo óptimo por tarea | Optimización de tokens | Regla fijada en el CLAUDE.md del instructor | Introducido | Hasta 10x de diferencia de coste |
| **ℹ Herramientas solo mencionadas**  Se mencionaron de pasada, sin desarrollo en el material: Gemini, Copilot, Perplexity, Lovable, Emergent, DeepSeek, Cloudflare Tunnel, Hetzner, SQLite, Neo4j y Python. Y como regla global del CLAUDE.md del instructor, una librería de ahorro de tokens.Sobre esta última: verifica siempre **qué intercepta realmente** una herramienta de ahorro de tokens antes de darla por buena. Las que comprimen salida de terminal no actúan sobre las herramientas nativas de lectura del agente, así que el ahorro depende mucho del tipo de sesión. Desconfía de cualquier porcentaje presentado como universal. |

# **12. Comandos y acciones**

**Instalación de Claude Code en Windows**, tal y como se mostró en clase (PowerShell como administrador). Verifica siempre el comando actual en la documentación oficial antes de ejecutarlo:

| irm https://claude.ai/install.ps1 | iex |
| --- |
| **⚠ Verifica el comando de instalación**  El instructor mostró el proceso desde la web de descarga y mencionó el patrón irm ... | iex. **La URL exacta no se leyó con claridad en la transcripción**, así que aquí figura la forma general.Descarga el instalador siempre desde la página oficial y nunca ejecutes un comando de este tipo copiado de una transcripción o de un tercero: irm | iex descarga y ejecuta código directamente. |

**PowerShell: desbloquear la ejecución de scripts.** Fue el primer error del ejercicio. Para permitirlo solo en la sesión actual, sin cambiar la configuración del equipo:

| Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass  .\script.ps1 |
| --- |

**Instrucciones en lenguaje natural al agente** (no son comandos de shell; son prompts):

| Abre el Buscaminas y echa una partida  Programame uno con la interfaz antigua exacta y el funcionamiento exacto  Quiero un agente capaz de resolver un Buscaminas y ver como juega en tiempo real  Genera un panel web donde ver los resultados de las ejecuciones del agente |
| --- |

# **13. Ética, seguridad y limitaciones**

| **⚠ Uso de credenciales ajenas**  La sesión mostró en directo el uso de una cuenta ajena ("esta cuenta está sin tocar... solo le falta saber que la estoy utilizando yo"). Se recoge aquí únicamente para dejar clara la norma: usar credenciales de otra persona sin su autorización expresa vulnera los términos de servicio de cualquier proveedor y, según el contexto, puede tener consecuencias legales y disciplinarias.En un máster de ciberseguridad la exigencia es mayor, no menor: la autorización explícita es el límite que separa la práctica profesional del incidente. |
| --- |
| **⚠ Límites operativos**  Otros límites que conviene tener presentes al aplicar lo visto:**Datos en el prompt.** Todo lo que se pega en un chat sale del equipo. Antes de subir logs, inventarios de máquinas, configuraciones o listados de clientes, comprueba qué política aplica. El script del inventario mostrado en clase recoge nombre de equipo, usuario, dominio, IPs y sistema operativo: es información sensible en un contexto empresarial.**Verificación obligatoria.** La fluidez no implica veracidad. Cifras, referencias, comandos y configuraciones de seguridad se verifican antes de usarse.**Superficie de ataque.** El propio instructor lo señaló: si se multiplican las aplicaciones generadas con IA, se multiplican las vulnerables. Ese es el argumento de empleabilidad de la sesión, pero también una responsabilidad: lo que generes con IA y pongas en producción es tuyo, incluidos sus fallos. |

# **14. Conexión con otras sesiones**

- **Con la sesión anterior de IA**: se retoman los grafos, las ontologías y el machine learning, ahora con la base conceptual que faltaba (token, contexto, modelo, agente). La corrección grafo ≠ red neuronal cierra la ambigüedad que quedó abierta.
- **Con el bloque de ciberseguridad**: la arquitectura de agentes se diseña con los mismos principios que una arquitectura segura —zero trust, privilegio mínimo, segmentación—. El instructor lo hizo explícito al hablar de las tools de cada agente.
- **Prompt injection ↔ inyección clásica**: un agente que lee ficheros o repositorios no confiables está expuesto a instrucciones ocultas, igual que una web mal saneada lo está a SQLi o XSS. Es el mismo patrón: datos que se interpretan como instrucciones.
- **Metodología**: el ciclo idea → requisitos → construcción → prueba → corrección es hermano del flujo de auditoría (enumeración → explotación → post-explotación → informe). En ambos: no avanzar sin evidencia y documentar cada paso.
- **Documentación persistente**: el .md de respaldo del orquestador cumple la misma función que un informe de auditoría o un cuaderno de laboratorio: que el trabajo sea reconstruible por otro.

# **15. Práctica 1 (requisitos anunciados)**

Se anunció la primera práctica del bloque. Requisitos indicados en clase:

- Crear una **aplicación con interfaz web**. El alojamiento es libre: localhost con un túnel, un servidor propio o lo que se prefiera.
- **Requisito obligatorio**: la interfaz debe recoger KPIs, métricas y números en un **dashboard** que permita comprobar que la aplicación hace lo que dice hacer.
- Comunicar los **grupos antes del viernes de la semana siguiente**. Quien no lo comunique se considera que la hace individualmente.
- Los requisitos y propuestas se publicarán en la plataforma del máster.

| **ℹ Pendiente de confirmar en la plataforma**  Las fechas y condiciones proceden de la conversación de clase y pueden haberse concretado después en la plataforma. Confirma los requisitos definitivos allí antes de organizar el trabajo.Para la próxima sesión se anunció continuar con el proyecto del **ajedrez**: aplicación web, agentes que jueguen entre sí, machine learning para que aprendan, y estructura completa con subagentes y grafos. |
| --- |

# **16. Resumen final**

La sesión bajó a los cimientos que se habían dado por supuestos. Un **token** no es una letra ni una palabra, sino un fragmento; el modelo predice el siguiente a partir de todo lo anterior, y por eso el **contexto** determina tanto la calidad como el coste. De ahí se deriva la regla más rentable de la clase: elegir el modelo más adecuado a cada tarea, no el más potente por defecto —entre el más caro y el más económico hay diez veces de diferencia en precio de entrada.

El recorrido práctico demostró el argumento mejor que la teoría. El mismo encargo —un Buscaminas que se resuelva solo— fracasó repetidamente en el chat de navegador y salió adelante en Claude Code, no por un modelo mejor, sino porque el agente **puede ejecutar, ver el error real y corregirse**. Esa capacidad de cerrar el bucle es la diferencia estructural entre un chat y un agente.

La última parte aporta lo más reutilizable: la arquitectura. Instrucciones persistentes en CLAUDE.md (donde lo específico prevalece sobre lo general), skills que definen cómo se hace el trabajo y se heredan por la cadena, tools limitadas por agente y un flujo orquestador → prompter → selector de modelo → agente destino. Con dos cautelas que la clase no subrayó lo suficiente: **saltarse los permisos solo tiene sentido en entornos aislados**, y una arquitectura de agentes es superficie de ataque, no solo productividad.

# **17. Checklist de repaso**

1. Sé explicar qué es un token y por qué no coincide con una palabra.
2. Puedo describir cómo se elige el siguiente token y qué papel juega el contexto.
3. Distingo entrenamiento de inferencia, y sé que crear agentes y skills no es entrenar.
4. Diferencio un grafo de conocimiento de una red neuronal y sé por qué no son lo mismo.
5. Distingo aprendizaje por refuerzo de A/B testing.
6. Sé por qué el chat de navegador no puede verificar el código que produce.
7. Distingo script, chatbot, agente y subagente.
8. Conozco la jerarquía de CLAUDE.md y sé cuál prevalece en un conflicto.
9. Entiendo qué define una skill frente a lo que define un agente.
10. Sé por qué limitar las tools de un agente y qué es prompt injection.
11. Sé por qué --dangerously-skip-permissions no va en el equipo de trabajo y qué alternativas existen.
12. Sé aplicar el criterio de enrutado de modelos y estimar su impacto en coste.

# **18. Preguntas de repaso**

## **18.1. Preguntas cortas**

1. ¿Qué es un token y por qué no equivale a una palabra?
2. ¿Por qué aumenta el coste de una conversación a medida que se alarga?
3. ¿Qué diferencia hay entre un grafo de conocimiento y una red neuronal?
4. ¿Por qué el chat de navegador no pudo entregar un script funcional a la primera?
5. ¿Qué prevalece si el CLAUDE.md global y el del proyecto se contradicen?
6. ¿Qué define una skill que no defina un agente?
7. ¿Por qué dos pestañas de Claude Code no comparten contexto y cómo se soluciona?
8. ¿Qué es la adulación (*sycophancy*) y por qué es un problema práctico?

## **18.2. Preguntas de desarrollo**

1. Explica por qué un agente puede resolver una tarea que un chat de navegador no, usando el Buscaminas como ejemplo. Céntrate en el bucle de verificación, no en la potencia del modelo.
2. Diseña la arquitectura de agentes para un proyecto propio: qué agentes, qué skills, qué tools tendría cada uno y por qué limitarías esas tools.
3. Relaciona el principio de privilegio mínimo de una arquitectura de red con la asignación de tools a agentes. ¿Qué ataque previene y qué equivalente clásico tiene?
4. Un compañero afirma que "tiene su IA entrenada" porque lleva meses dándole instrucciones y creando agentes. ¿Es correcto? Explica qué está haciendo realmente y en qué se diferencia del entrenamiento y del fine-tuning.

## **18.3. Tipo test**

1. Un LLM, al responder una pregunta de cultura general sin herramientas activas:a) Consulta Internet en tiempo real.b) Busca en una base de datos interna de hechos.c) Predice tokens a partir de los pesos aprendidos en el entrenamiento.d) Recupera literalmente el texto que memorizó.
2. La ventana de contexto es:a) La memoria permanente del modelo entre conversaciones.b) El máximo de tokens que el modelo tiene a la vista en la conversación.c) El número de parámetros del modelo.d) El límite de mensajes del plan contratado.
3. Si el CLAUDE.md de usuario dice "indenta con 4 espacios" y el del proyecto dice "indenta con 2":a) Gana el de usuario, por ser más general.b) Gana el del proyecto, por ser más específico.c) Se produce un error y no se carga ninguno.d) Se aplica alfabéticamente.
4. Pedir a un modelo que construya nodos y ontologías en un grafo equivale a:a) Entrenar una red neuronal.b) Hacer fine-tuning del modelo.c) Construir una estructura de conocimiento relacional, sin modificar pesos.d) Aplicar aprendizaje por refuerzo.
5. --dangerously-skip-permissions es apropiado:a) En el portátil de trabajo, para evitar aprobaciones.b) Solo en un entorno aislado y desechable, sin credenciales de producción.c) Siempre que el proyecto sea propio.d) Cuando se confía en la capacidad del modelo.
6. Para clasificar diez mil mensajes cortos, el criterio de enrutado de modelos recomienda:a) El modelo más potente, para maximizar precisión.b) Un modelo pequeño y rápido, adecuado a la tarea.c) Repartir la tarea entre todos los modelos.d) Es indiferente: el coste no depende del modelo.
7. Que un modelo cambie su respuesta cuando el usuario insiste sin aportar datos nuevos se llama:a) Alucinación.b) Adulación (*sycophancy*).c) Sobreajuste.d) Deriva de contexto.
8. La diferencia esencial entre un script y un agente es:a) El lenguaje de programación empleado.b) Que el agente recibe un objetivo, usa herramientas, observa resultados e itera.c) Que el script es más rápido.d) Que el agente siempre necesita conexión a Internet.

## **18.4. Ejercicios prácticos**

1. Escribe un CLAUDE.md mínimo para uno de tus proyectos: tres reglas de estilo, una de elección de modelo y una de seguridad. Compruébalo con /context y verifica que se ha cargado.
2. Repite el ejercicio de prompting de la clase: describe una utilidad que quieras, pide al modelo preguntas y mejoras antes del entregable, y compara el resultado con el que darías pidiéndolo directamente.
3. Coge un script que ya tengas y pídele a un agente que lo ejecute, detecte los errores reales y los corrija. Observa cuántas iteraciones necesita y qué comprobaciones hace que tú no harías.

## **18.5. Tarjetas de memoria**

**Pregunta:** ¿Qué es un token? · **Respuesta:** Un fragmento de palabra, la unidad con la que el modelo procesa y predice texto.

**Pregunta:** ¿Qué es la ventana de contexto? · **Respuesta:** El máximo de tokens que el modelo tiene a la vista en una conversación, respuesta incluida.

**Pregunta:** ¿Qué es un LLM? · **Respuesta:** Un modelo de lenguaje grande: una red neuronal entrenada para predecir texto.

**Pregunta:** ¿Genera o busca un LLM? · **Respuesta:** Genera prediciendo tokens desde sus pesos. Solo busca si se le da una herramienta.

**Pregunta:** ¿Qué es la temperatura? · **Respuesta:** El parámetro que regula la aleatoriedad al elegir el siguiente token.

**Pregunta:** ¿Entrenamiento o inferencia al usar un chat? · **Respuesta:** Inferencia: los pesos no cambian.

**Pregunta:** ¿Qué es el fine-tuning? · **Respuesta:** Reentrenar ajustando pesos con datos nuevos; distinto de RAG y de dar instrucciones.

**Pregunta:** ¿Qué es RAG? · **Respuesta:** Recuperar documentos relevantes e inyectarlos en el contexto; los pesos no cambian.

**Pregunta:** ¿Chatbot o agente? · **Respuesta:** El chatbot responde; el agente persigue un objetivo con herramientas, en bucle.

**Pregunta:** ¿Qué es una skill? · **Respuesta:** La definición de *cómo* se ejecuta un tipo de tarea.

**Pregunta:** ¿Para qué sirve CLAUDE.md? · **Respuesta:** Instrucciones persistentes que se cargan al inicio de cada sesión.

**Pregunta:** ¿Qué prevalece, proyecto o global? · **Respuesta:** El proyecto: lo más específico gana.

**Pregunta:** ¿Qué es prompt injection? · **Respuesta:** Instrucciones ocultas en contenido que el agente lee y acaba ejecutando.

**Pregunta:** ¿Qué es el enrutado de modelos? · **Respuesta:** Elegir el modelo más adecuado por tarea para optimizar coste y latencia.

**Pregunta:** ¿Qué es una alucinación? · **Respuesta:** Una afirmación plausible y bien redactada pero falsa.

**Pregunta:** ¿Grafo o red neuronal? · **Respuesta:** El grafo tiene aristas con significado explícito; la red, pesos numéricos entrenados.

| **✓ Soluciones**  **Tipo test:** 1-c · 2-b · 3-b · 4-c · 5-b · 6-b · 7-b · 8-b**Cortas (referencia):** 1) Fragmento subléxico; permite cubrir cualquier palabra con un vocabulario finito. 2) Cada turno reprocesa todo el contexto acumulado: más cómputo y más tokens facturados. 3) El grafo tiene aristas con significado explícito y se consulta por lógica; la red neuronal guarda el conocimiento distribuido en pesos numéricos ajustados por entrenamiento. 4) Porque no ejecuta lo que produce: sin entorno de pruebas no puede detectar ni corregir sus propios errores. 5) El del proyecto, por ser más específico. 6) La skill define cómo se hace la tarea; el agente define quién la hace, con qué objetivo, límites y herramientas. 7) Cada sesión tiene su contexto aislado; se comparte a través de ficheros en disco. 8) La tendencia a priorizar la conformidad del usuario sobre la exactitud; hace que la conformidad del modelo no sirva como confirmación. |
| --- |

# **19. Glosario**

| **Término** | **Definición breve** |
| --- | --- |
| Token | Fragmento de palabra; unidad con la que el modelo procesa y predice texto. |
| Contexto (*context window*) | Máximo de tokens que el modelo tiene a la vista en una conversación. |
| LLM | *Large language model*: red neuronal entrenada para predecir texto. |
| Prompt | Texto de entrada que se envía al modelo. |
| Pesos | Números ajustados durante el entrenamiento; en ellos reside lo aprendido. |
| Inferencia | Cada consulta al modelo ya entrenado; los pesos no cambian. |
| Entrenamiento | Proceso de ajustar los pesos con un dataset. |
| Fine-tuning | Reentrenar un modelo con datos nuevos para ajustar comportamiento o formato. |
| RAG | Recuperar documentos y añadirlos al contexto en tiempo de inferencia. |
| Temperatura | Parámetro que regula la aleatoriedad al elegir el siguiente token. |
| Alucinación | Afirmación plausible pero falsa generada por el modelo. |
| Adulación (*sycophancy*) | Tendencia a priorizar la conformidad del usuario sobre la exactitud. |
| Agente | Sistema que persigue un objetivo usando herramientas y decidiendo pasos en bucle. |
| Subagente | Agente especializado invocado por otro para una subtarea. |
| Skill | Definición de cómo debe ejecutarse un tipo de tarea. |
| Tools | Herramientas que un agente puede invocar; se limitan por seguridad. |
| Orquestador | Agente que coordina el flujo y conoce el estado del proyecto. |
| CLAUDE.md | Fichero de instrucciones persistentes cargado al inicio de cada sesión. |
| Prompt injection | Instrucciones maliciosas ocultas en contenido que el agente lee. |
| Enrutado de modelos | Elegir el modelo más adecuado a cada tarea por coste y capacidad. |
| Aprendizaje por refuerzo | Aprender por recompensa y castigo a partir de la propia acción. |
| Grafo de conocimiento | Estructura de nodos y aristas con significado explícito. |

# **20. Actualización del registro de IA**

Escala de niveles: Mencionado → Introducido → Comprendido → Practicado → Aplicado → Recurrente.

| **Concepto / Herramienta** | **Categoría** | **Nivel** |
| --- | --- | --- |
| Token / predicción del siguiente token | Fundamento | Comprendido |
| Ventana de contexto y su coste | Fundamento | Comprendido |
| LLM (definición y funcionamiento) | Fundamento | Comprendido |
| Modelo vs aplicación vs herramienta vs agente | Fundamento | Comprendido |
| Claude Code (CLAUDE.md, tools, sesiones) | Agente / Herramienta | Practicado |
| Jerarquía de CLAUDE.md (global vs proyecto) | Técnica | Comprendido |
| Skills (definición de cómo se ejecuta) | Agente | Introducido |
| Subagentes y orquestación | Agente | Introducido |
| Agente prompter | Agente | Introducido |
| Enrutado de modelos | Técnica | Comprendido |
| Familia de modelos y su coste relativo | Modelo | Introducido |
| Script vs agente | Fundamento | Comprendido |
| Aprendizaje por refuerzo | Técnica de entrenamiento | Introducido |
| Adulación (*sycophancy*) | Método de evaluación | Introducido |
| Temperatura | Fundamento | Mencionado |
| Prompt injection y límite de tools | Técnica de seguridad | Introducido |
| Modos de permisos de Claude Code | Técnica de seguridad | Introducido |
| Grafo de conocimiento ≠ red neuronal | Datos / Conocimiento | Comprendido |
| Técnica de prompting con preguntas previas | Técnica | Practicado |

# **21. Fuentes consultadas**

El contenido de clase es la fuente primaria. Lo siguiente respalda únicamente las ampliaciones y correcciones marcadas. Fecha de consulta: 24/07/2026.

- **Anthropic — Models overview** (documentación oficial, platform.claude.com/docs/en/about-claude/models/overview). Respalda: nombres de modelos, ventanas de contexto y precios de la sección 10.
- **Anthropic — How Claude remembers your project** (documentación oficial de Claude Code, code.claude.com/docs/en/memory). Respalda: jerarquía y orden de carga de CLAUDE.md, y que es contexto y no configuración obligatoria (sección 6.6).
- **Anthropic — Choose a permission mode** (documentación oficial de Claude Code, code.claude.com/docs/en/permission-modes). Respalda: comportamiento de --dangerously-skip-permissions, ausencia de protección frente a prompt injection y alternativas (sección 6.8).
- **Anthropic — How we built Claude Code auto mode** (blog de ingeniería, anthropic.com/engineering/claude-code-auto-mode). Respalda: el modo automático como alternativa intermedia a saltarse los permisos (sección 6.8).

| **ℹ Sobre el alcance de las fuentes**  Las explicaciones conceptuales de las secciones 4, 6.1 y 6.9 (predicción de tokens, distinción entre grafo y red neuronal, aprendizaje por refuerzo frente a A/B testing) son fundamentos generales aplicables a cualquier modelo Transformer, no información específica de ningún proveedor.Los datos de modelos, precios y features cambian con frecuencia. Verifica en la documentación oficial antes de usarlos como referencia definitiva. |
| --- |
