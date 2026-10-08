---
tags:
- Inteligencia artificial
---

# IA Redes Neuronales

**EVOLVE ACADEMY · MÁSTER EN CIBERSEGURIDAD OFENSIVA**

**IA: Redes Neuronales, Grafos y Machine Learning**

Instructor: Carlos Gómez Pintado · 23/07/2026

*Bloque de Inteligencia Artificial — De la base de datos a la red neuronal*

# **1. Cómo leer estos apuntes**

| **ℹ Cómo leer estos apuntes**  Estos apuntes recogen **lo que se explicó en clase** y añaden, marcadas aparte, las **correcciones y ampliaciones** necesarias. La sesión fue muy rica en intuiciones válidas, pero mezcló terminología de tres campos distintos (bases de datos, grafos de conocimiento y redes neuronales) que conviene separar con precisión.Cada corrección indica **qué se dijo**, **qué conviene precisar** y **por qué**. El objetivo no es contradecir al instructor —cuya intuición de fondo suele ser correcta— sino evitar que una imprecisión terminológica se arrastre al examen o a la práctica de verano. |
| --- |

# **2. Objetivos de aprendizaje**

- Distinguir con rigor **base de datos**, **grafo de conocimiento**, **grafo vectorial** y **red neuronal**.
- Comprender qué es un **dataset**, por qué debe estar **etiquetado** y qué papel juega el **entrenamiento supervisado**.
- Entender el mecanismo de **pesos**, **capas** y **aprendizaje por prueba y error** en una red neuronal.
- Identificar el **envenenamiento de datos de entrenamiento** (*training data poisoning*) como vector de ataque.
- Reconocer los **sesgos espurios** en modelos entrenados (caso lobo/husky) y por qué obligan a validar siempre.
- Diseñar una **arquitectura de agentes jerárquica** (agente por usuario + agente global) sin corromper el modelo.
- Situar el panorama industrial de la IA: carrera de modelos, hardware y estrategias de coste.

# **3. Resumen inicial**

La sesión recorre la **evolución del almacenamiento de conocimiento**: de una base de datos relacional plana, a un grafo de notas enlazadas (Obsidian), a un grafo vectorial con relaciones ponderadas (Neo4j), y finalmente a una red neuronal con aprendizaje automático. Sobre ese hilo conductor se explican los fundamentos del *machine learning* supervisado —datasets etiquetados, pesos, prueba y error— usando el Tetris como ejemplo práctico.

La segunda mitad aborda el **contexto industrial**: por qué la IA ha crecido de forma exponencial, la estrategia de los fabricantes de hardware frente a los laboratorios de modelos, la irrupción de los modelos abiertos chinos, y el diseño de **arquitecturas de agentes** para proyectos reales. Se cierra con la propuesta de proyectos para la práctica de verano.

# **4. Conceptos y terminología**

La sesión gira en torno a cuatro formas de guardar conocimiento. Distinguirlas es **el núcleo de la clase**, y es donde más se mezcló la terminología.

## **4.1. Las cuatro estructuras**

| **Estructura** | **Qué es** | **Cómo se relaciona la información** | **¿Aprende?** |
| --- | --- | --- | --- |
| **Base de datos relacional** (SQL/SQLite) | Tablas de filas y columnas con un esquema fijo | Mediante claves ajenas (*foreign keys*) definidas por el diseñador | No |
| **Grafo de notas** (Obsidian) | Ficheros de texto en Markdown enlazados entre sí | Por **hipervínculos**: el enlace existe, pero no dice *qué* significa | No |
| **Grafo de conocimiento vectorial** (Neo4j) | Nodos y aristas con **tipo y propiedades**, y pesos numéricos | Por relaciones con significado explícito (*ontología*) y peso | No por sí solo |
| **Red neuronal** | Capas de neuronas conectadas por pesos numéricos | Por **pesos ajustados durante el entrenamiento**, no por aristas con texto | Sí, ajustando pesos |
| **⚠ Corrección clave: grafo de conocimiento ≠ red neuronal**  **Se dijo en clase:** que al pasar de Obsidian a Neo4j y añadir ontologías y pesos ya se tiene *«una red neuronal»*, y que Obsidian es *«2D»* frente a Neo4j que sería *«3D, como las capas de Anthropic»*.**Conviene precisar:** son **dos tecnologías distintas, no dos fases de la misma**.• Un **grafo de conocimiento** (Neo4j) guarda el conocimiento de forma **explícita y legible**: el nodo Jaguar XE está unido al nodo Jaguar por una arista que literalmente dice ES\_MODELO\_DE. Razona por **lógica simbólica y consultas** (Cypher). Puedes abrirlo y leer por qué respondió lo que respondió.• Una **red neuronal** guarda el conocimiento de forma **distribuida e implícita** en millones o miles de millones de **pesos numéricos**, ajustados automáticamente durante el entrenamiento mediante *backpropagation* y descenso del gradiente. No hay ninguna arista que ponga ES\_MODELO\_DE: hay números.**Por qué importa:** pedirle a un LLM que construya nodos y ontologías produce un grafo excelente y muy útil —el trabajo mostrado en clase lo es— pero **no es entrenar una red neuronal**. Son herramientas complementarias: hoy lo habitual es combinarlas (*GraphRAG*: un grafo que alimenta de contexto a un modelo ya entrenado). |

## **4.2. Vocabulario base**

| **Término** | **Definición** |
| --- | --- |
| **Dataset** | Conjunto de datos de entrenamiento. Para aprendizaje supervisado debe estar **clasificado y etiquetado**. |
| **Etiquetado** (*labeling*) | Asignar a cada dato la respuesta correcta que el modelo debe aprender a predecir. |
| **Entrenamiento supervisado** | Aprendizaje a partir de ejemplos con la respuesta correcta ya marcada. |
| **Peso** (*weight*) | Número que indica cuánto influye la salida de una neurona sobre la siguiente. Se ajusta al entrenar. |
| **Capa** (*layer*) | Conjunto de neuronas al mismo nivel de profundidad de la red. |
| **Inferencia** | Usar un modelo ya entrenado para obtener una predicción. **No modifica los pesos.** |
| **Ontología** | Definición explícita del **significado** de las relaciones entre conceptos. Propia de grafos, no de redes neuronales. |
| **Grafo vectorial** | Grafo cuyas relaciones llevan asociado un valor numérico (peso o vector) que gradúa su importancia. |

## **4.3. Distinciones que deben quedar claras**

| **Concepto A** | **Concepto B** | **Diferencia esencial** |
| --- | --- | --- |
| Entrenamiento | Inferencia | Entrenar **ajusta pesos** (costoso, se hace una vez). Inferir **usa** pesos ya fijos. |
| Modelo | Agente | El modelo predice texto. El **agente** persigue un objetivo usando herramientas en bucle. |
| Herramienta | Modelo | La herramienta (búsqueda, terminal, navegador) es algo que el modelo **invoca**, no forma parte de él. |
| Ventana de contexto | Memoria permanente | El contexto se borra al llenarse. La persistencia real viene de ficheros o de una función de memoria del producto. |
| Grafo de conocimiento | Red neuronal | Aristas con significado explícito frente a pesos numéricos distribuidos. |
| Crear skills/subagentes | Entrenar un modelo | Lo primero es **ingeniería de contexto** sobre un modelo ya entrenado; lo segundo ajusta pesos. |
| **ℹ Simplificación didáctica corregida: crear agentes ≠ entrenar**  **Se dijo en clase:** *«voy entrenando al agente»*, *«tengo mi IA entrenada»*, refiriéndose a crear subagentes, skills y ficheros de contexto en Claude Code.**Conviene precisar:** especializar un modelo con instrucciones, *skills*, subagentes o documentación local es **ingeniería de prompt y de contexto sobre un modelo ya preentrenado**. Es enormemente valioso y es lo que se practica en el máster, pero conviene reservar el verbo *entrenar* para el ajuste de pesos. Los tres mecanismos que sí modifican o amplían un modelo son distintos entre sí:• **Fine-tuning:** reentrena y **ajusta pesos** con datos nuevos. Cambia el comportamiento o el formato.• **RAG** (*Retrieval-Augmented Generation*): recupera documentos y los inyecta en el contexto **en tiempo de inferencia**. Los pesos no cambian. Es lo que de facto se está construyendo con los grafos de la clase.• **Contexto/skills:** instrucciones que guían al modelo en cada sesión. Tampoco cambian pesos. |

# **5. Explicación intuitiva: la analogía de la biblioteca**

El instructor usó una analogía muy buena para separar Obsidian de Neo4j, que conviene conservar y completar:

| **Analogía** | **Estructura** | **Qué permite** |
| --- | --- | --- |
| **La estantería de tu casa** | Obsidian | Tienes los libros ordenados y sabes dónde está cada uno. Cada libro es independiente: para saber algo, lo abres y lo lees entero. |
| **Internet** | Neo4j | Las páginas están enlazadas *con sentido*. Puedes saltar de un tema a otro sin terminar el anterior, siguiendo relaciones que significan algo. |
| **Haber leído y asimilado todo** | Red neuronal | Ya no consultas: respondes desde lo aprendido. No puedes señalar la página exacta donde lo aprendiste, porque está repartido. |
| **ℹ Ampliación técnica**  La tercera fila es una **ampliación de estos apuntes**, no de la clase. Completa la analogía del instructor precisamente en el punto donde grafo y red neuronal se confunden: la red no *consulta* un almacén, **genera** desde pesos. |

# **6. Desarrollo técnico**

## **6.1. Qué era la «IA» antes de los modelos generativos**

Antes del salto generativo, lo que se llamaba inteligencia artificial era, en palabras del instructor, *«un bucle de tantos `if` como casuísticas tuviésemos dentro del árbol de decisiones»*. Se recibía una entrada y se recorría un **árbol de decisión** construido a mano:

| if entrada contiene 'dolor':  if entrada contiene 'rodilla':  if entrada contiene 'inflamada':  responder(...) |
| --- |

La limitación es evidente: **cada casuística hay que preverla y escribirla**. No hay generalización a casos no contemplados.

## **6.2. El ejemplo del Tetris: entrenamiento supervisado**

El instructor planteó un escenario de Tetris con una pieza cuadrada cayendo y varias posiciones posibles, y pidió a los alumnos puntuar cada posición del 1 al 10. Las notas recogidas fueron: **1, 3, 5, 6 y 10**.

Eso es exactamente **entrenamiento supervisado**: un humano proporciona la respuesta correcta (la etiqueta) para cada situación. La red aprende que, dado el estado *«pieza cuadrada + dos huecos»*, la mejor decisión es la puntuada con 10.

| **✓ Buena pregunta de clase**  Las puntuaciones **no son aleatorias**: son la señal que el modelo aprende a reproducir. Un alumno preguntó justamente esto en clase y es la pregunta correcta — sin criterio consistente en las etiquetas, el modelo aprende ruido. |
| --- |

## **6.3. El problema real: la explosión combinatoria**

Si hay que etiquetar a mano cada jugada posible, el problema se vuelve inabordable: en el Tetris las piezas son aleatorias y las combinaciones de tablero, pieza y rotación son astronómicas. Ese fue históricamente **el gran cuello de botella del machine learning**: no el algoritmo, sino **conseguir datasets etiquetados**.

| **ℹ Ampliación técnica: aprendizaje supervisado vs. por refuerzo**  **Ampliación:** el ejemplo del Tetris es de **aprendizaje supervisado**, pero un Tetris que juega solo se resuelve hoy con **aprendizaje por refuerzo** (*reinforcement learning*): el agente juega millones de partidas y recibe una **recompensa** (líneas hechas, supervivencia) en lugar de una etiqueta humana por jugada. Así se esquiva precisamente el problema de tener que puntuar cada posición a mano.Esto también matiza la afirmación de clase de que se obtiene *«una máquina que no puede perder literalmente»*: un agente de Tetris muy bueno alarga enormemente la partida, pero con secuencias de piezas adversas el juego es demostrablemente perdible. Ningún modelo aprendido garantiza el 100 %. |
| --- |

## **6.4. Capas, pesos y jerarquía de importancia**

El instructor explicó las capas con un ejemplo de coches, ordenando los atributos por peso: **marca** (más peso), **modelo**, **motor** y **color** (menos peso). El razonamiento es correcto y es la clave del concepto: el color es común a muchísimas marcas y modelos, luego **discrimina poco**; la marca discrimina mucho más.

| **⚠ Matiz: el peso depende de la tarea**  **Matiz importante:** el peso de un atributo **no es universal, depende de la tarea**. En un buscador de coches por marca, el color pesa poco. En un sistema de identificación de vehículos en una grabación de seguridad, el color puede ser el atributo más discriminante. El propio instructor lo confirmó al responder a un alumno: *depende del contexto de cómo quieras usar esa red*. |
| --- |

## **6.5. Prueba y error: el «A/B testing» de la clase**

En clase se llamó **A/B testing** al mecanismo de prueba y error con el que la red ajusta sus ponderaciones. La intuición —*prueba, mide, corrige*— es correcta, pero el nombre no lo es y conviene fijarlo bien porque son cosas distintas:

| **Término** | **Qué es realmente** | **Dónde se usa** |
| --- | --- | --- |
| **A/B testing** | Experimento con usuarios reales: se muestra la variante A a un grupo y la B a otro, y se compara una métrica | Producto, marketing, UX |
| **Backpropagation + descenso del gradiente** | Mecanismo por el que la red mide su error y **propaga hacia atrás** el ajuste de cada peso | Entrenamiento de redes neuronales |
| \**Validación /* hold-out\*\*\* | Reservar una parte del dataset para medir el acierto sobre datos nunca vistos | Evaluación de modelos |
| **⚠ Corrección clave: A/B testing ≠ backpropagation**  **Corrección:** lo que ajusta los pesos de una red neuronal **no es A/B testing**, es **backpropagation con descenso del gradiente**. La red calcula cuánto se ha equivocado (*función de pérdida*), propaga ese error hacia atrás capa por capa y corrige cada peso en la dirección que reduce el error. Es un proceso matemático automático, no un experimento con variantes. |

## **6.6. Cómo se mide el acierto de un modelo**

Un alumno preguntó cómo puede afirmarse que un modelo tiene un 95 % de exactitud. La respuesta del instructor fue **correcta y es un concepto de examen**: del dataset etiquetado se **reserva un porcentaje** (mencionó en torno al 10 %) que **jamás se usa para entrenar**. Se mide el acierto sobre ese conjunto reservado.

El ejemplo dado: si se reservan un millón de imágenes y el modelo acierta 950 000, la exactitud es del 95 %.

| **ℹ Ampliación técnica: train / validation / test y métricas**  **Ampliación:** ese conjunto reservado se llama **conjunto de prueba** (*test set*), y lo habitual es partir el dataset en tres:• **Entrenamiento** (~70-80 %): ajusta los pesos.• **Validación** (~10-15 %): ajusta decisiones de diseño (arquitectura, hiperparámetros) sin tocar el test.• **Prueba** (~10-15 %): se usa **una sola vez**, al final, para reportar el resultado honesto.Si se usa el test repetidamente para decidir mejoras, se acaba *ajustando al test* y la cifra deja de ser fiable. Además, la **exactitud** (*accuracy*) por sí sola engaña con clases desbalanceadas: si el 99 % de las muestras son sanas, un modelo que diga siempre «sano» acierta el 99 % y no sirve para nada. Por eso en medicina se usan **precisión**, **exhaustividad** (*recall*) y **matriz de confusión**. |
| --- |

## **6.7. Entrenar con ejemplos negativos**

Punto valioso y correcto de la clase: no basta con dar ejemplos de lo que **sí** es lo buscado. Para un detector de toros hay que aportar también vacas, cabras y peces etiquetados como *no toro*, porque —en palabras del instructor— hay que **cubrir todas las casuísticas potenciales** que puedan llegar en producción.

# **7. Funcionamiento paso a paso**

Los siguientes diagramas son **representaciones simplificadas**: omiten detalles matemáticos para hacer visible la secuencia.

## **7.1. La neurona artificial**

| **1. Entradas (valores numéricos)** |
| --- |

**↓**

| **2. Multiplicación de cada entrada por su peso** |
| --- |

**↓**

| **3. Suma ponderada de todas las entradas** |
| --- |

**↓**

| **4. Adición del sesgo (bias)** |
| --- |

**↓**

| **5. Función de activación** |
| --- |

**↓**

| **6. Salida hacia la siguiente capa** |
| --- |
| **⚠ Matiz: neurona artificial ≠ neurona biológica**  **Matiz:** la neurona artificial se inspira en la biológica, pero **no es equivalente**. Un peso es un **número** que gradúa la influencia de una neurona sobre la siguiente; no es un cable ni una sinapsis. La analogía ayuda a entender, pero no debe presentarse como identidad — igual que un *«cerebro»* de agente no es un cerebro. |

## **7.2. Ciclo de entrenamiento**

| **1. Datos etiquetados del dataset** |
| --- |

**↓**

| **2. El modelo hace una predicción** |
| --- |

**↓**

| **3. Cálculo de la pérdida (error frente a la etiqueta)** |
| --- |

**↓**

| **4. Backpropagation: se propaga el error hacia atrás** |
| --- |

**↓**

| **5. Actualización de los pesos** |
| --- |

**↓**

| **6. Nueva iteración hasta converger** |
| --- |

## **7.3. Evolución del conocimiento vista en clase**

| **1. Base de datos SQL: 100 000 coches en filas y columnas** |
| --- |

**↓**

| **2. Grafo de notas (Obsidian): un fichero .md por coche, unidos por hipervínculos** |
| --- |

**↓**

| **3. Grafo vectorial (Neo4j): nodos por característica, relaciones con significado y peso** |
| --- |

**↓**

| **4. Sobre el grafo: algoritmo de machine learning para detectar patrones** |
| --- |

# **8. Seguridad: ataques sobre datos y modelos**

## **8.1. Envenenamiento de datos de entrenamiento**

Es el contenido de ciberseguridad más directo de la sesión. El **envenenamiento de datos** (*training data poisoning*) consiste en **inyectar datos falsos o mal etiquetados** en un dataset para que el modelo aprenda mal.

El instructor relató el caso de un dataset público colaborativo en el que un atacante etiquetó incorrectamente muestras (una cabra como lobo), logrando que el modelo aprendiera el patrón equivocado.

| **⚠ Envenenamiento de datos (training data poisoning)**  **Concepto clave que sí quedó bien fijado:** lo determinante es que la muestra envenenada sea **representativa**. Un millón de imágenes malas sobre diez millones es una proporción capaz de desviar el modelo; una imagen sobre diez millones no lo es.**Ampliación:** existen ataques de envenenamiento eficaces con proporciones **muy inferiores** cuando están dirigidos (*backdoor attacks*): en lugar de degradar el modelo entero, se le enseña a fallar **solo** ante un disparador concreto (un patrón de píxeles, una marca de agua), manteniendo un rendimiento normal en el resto de casos. Eso los hace especialmente difíciles de detectar con métricas de exactitud global. |
| --- |

**Defensas** que se derivan de lo tratado: procedencia verificada de los datos, revisión humana del etiquetado, detección de valores atípicos, firma e integridad de los datasets, y no ingerir datos de fuentes no controladas.

## **8.2. Sesgos espurios: el caso lobo/husky**

El instructor contó el experimento clásico: un clasificador para distinguir lobos de huskies obtenía una tasa de acierto muy alta. Al analizar en qué se basaba, resultó que **había aprendido a detectar nieve**: la mayoría de las fotos de lobos tenían fondo nevado.

| **⚠ Correlación espuria: la métrica no basta**  Este es uno de los ejemplos más importantes de toda la sesión. Enseña que **una métrica alta no garantiza que el modelo haya aprendido lo que crees**. Ha aprendido *un* patrón que correlaciona con la respuesta en tu dataset — que no es lo mismo.En producción, ese modelo clasifica como lobo cualquier perro fotografiado en la nieve. Se llama **correlación espuria** o *atajo* (*shortcut learning*), y es la razón de ser de la **IA explicable** (*XAI*): no basta con saber que acierta, hay que saber **por qué** acierta.El experimento original procede del artículo de Ribeiro, Singh y Guestrin sobre el método LIME (2016), que popularizó justamente este ejemplo. |
| --- |

## **8.3. Nunca reentrenar con datos de producción sin curar**

Debate central de la clase, y con conclusión correcta: **no se debe reentrenar un modelo directamente con lo que los usuarios escriben en producción**, sin curación ni supervisión. La propuesta de Asier resume bien la buena práctica y el instructor la validó:

| **1. Se almacenan los datos de uso en producción** |
| --- |

**↓**

| **2. En un entorno separado se sanean, filtran y etiquetan** |
| --- |

**↓**

| **3. Se entrena y evalúa la nueva versión del modelo con supervisión humana** |
| --- |

**↓**

| **4. Solo cuando alcanza la robustez requerida, se despliega a producción** |
| --- |
| **✓ Human in the loop**  El concepto que se nombró en clase es el **humano en el bucle** (*human in the loop*): la supervisión humana como paso obligatorio de la cadena de entrenamiento. Es también la justificación de los **entornos de preproducción**, que Óscar relacionó acertadamente con el desarrollo clásico. |
| **⚠ Matiz: colapso del modelo es real; la atribución a GPT-4 no está confirmada**  **Se dijo en clase:** que GPT-4 funcionó peor que GPT-3.5 porque se alimentó de los datos de uso de sus usuarios y aprendió mal.**Conviene precisar:** el **fenómeno** descrito es real y está documentado — se llama **colapso del modelo** (*model collapse*), y fue publicado en *Nature* en 2024 por Shumailov et al.: entrenar de forma recursiva con contenido generado por modelos degrada la distribución y hace desaparecer los casos poco frecuentes.**Pero la atribución concreta no está respaldada.** No hay evidencia pública de que GPT-4 se entrenara con las conversaciones de usuarios de GPT-3.5 ni de que rindiera peor por ese motivo. Lo que sí se documentó ampliamente fueron **variaciones de comportamiento entre versiones** a lo largo del tiempo, atribuibles a cambios de configuración, alineamiento y mitigaciones, no a un colapso por autoingesta.**Quédate con el principio, no con el ejemplo:** el riesgo de contaminar un dataset con salidas de modelo es real y es la razón de las buenas prácticas de esta sección. |

## **8.4. Datos personales, anonimización y proyectos de medicina**

Al plantear los proyectos médicos surgió la cuestión legal. Los puntos correctos que se fijaron en clase:

- Los datasets deben estar **anonimizados**: sin nombre, apellidos ni identificadores que permitan reidentificar al paciente.
- Se habla de *sujeto clínico*, no de la persona.
- Datos como el margen de edad **sí** pueden conservarse mientras no permitan identificar a nadie.
- Para usar imágenes clínicas hace falta **convenio y consentimiento** del centro y de los pacientes.

| **⚠ Ampliación: anonimización ≠ seudonimización (RGPD)**  **Ampliación necesaria:** la clase mencionó *anonimizar* y *meter un agente anonimizador*, pero conviene distinguir dos figuras que el RGPD trata de forma muy distinta:• **Anonimización:** el dato deja de ser reidentificable de forma irreversible. El dato anonimizado **queda fuera del RGPD**.• **Seudonimización:** se sustituye el identificador por un código, pero existe una tabla que permite revertirlo. **Sigue siendo dato personal** y sigue bajo el RGPD.Lo que suele hacerse en la práctica sanitaria es **seudonimizar**, no anonimizar. Además: los datos de salud son **categoría especial** (art. 9 RGPD) y requieren base jurídica reforzada; las imágenes médicas pueden contener metadatos DICOM identificativos que hay que limpiar aparte; y un proyecto de este tipo normalmente necesita **dictamen de un comité de ética de investigación**, no solo el permiso del contacto. Se citó también la **ISO/IEC 42001** (sistema de gestión de IA), que es la referencia de gobernanza aplicable. |
| --- |
| **⚠ Matiz crítico: IA en diagnóstico**  Sobre la propuesta de un **chatbot de diagnóstico de neurodivergencias**: se discutió en clase que el enfoque correcto es una **herramienta de apoyo al profesional**, no de autodiagnóstico, y esa distinción es acertada. Conviene añadir que una herramienta destinada a diagnóstico entra en la categoría de **producto sanitario** y en la clasificación de **alto riesgo** del Reglamento Europeo de IA, con obligaciones de conformidad, trazabilidad y supervisión humana. Y el argumento de que *«la IA no tiene sesgo porque no es humana»* es falso: **el modelo hereda el sesgo de sus datos** — precisamente el problema del infradiagnóstico femenino que se señaló en clase se reproduciría si el dataset arrastra ese sesgo. |

# **9. Arquitectura de agentes: el patrón cerebro central + minicerebros**

Una de las partes más aprovechables de la sesión para la práctica. El patrón, aplicado tanto al proyecto de orientación profesional del instructor como al de simulación de phishing de Congil:

| **1. Un agente individual por cada usuario, con su propio contexto y su historial de fallos** |
| --- |

**↓**

| **2. Cada agente procesa localmente los datos crudos de su usuario** |
| --- |

**↓**

| **3. Solo el dato ya tratado y el resultado se envían al nivel superior** |
| --- |

**↓**

| **4. Un cerebro central agrega los resultados y detecta patrones comunes** |
| --- |

**↓**

| **5. El cerebro central genera pruebas personalizadas de vuelta a cada agente** |
| --- |
| **✓ Regla de oro: filtrar entre niveles**  **La regla de oro de la sesión:** *«es importante saber qué dato entra, qué dato se procesa y qué dato se envía a la siguiente red»*. Volcar los datos crudos de todos los usuarios al modelo global lo **corrompe**, porque cada usuario se comporta de forma distinta. Al nivel superior solo debe subir el resultado procesado. |

Se planteó la duda de **escalabilidad**: ¿un agente por usuario no es inviable con un millón de usuarios? La respuesta del instructor fue que cada agente es esencialmente un fichero de texto plano, y que 100 000 líneas de texto pesan menos que una fotografía. El argumento sobre el **tamaño del texto es correcto**.

| **⚠ Matiz: el cuello de botella de escalar son las llamadas, no el disco**  **Matiz:** el coste real de escalar no está en el almacenamiento del texto, sino en las **llamadas de inferencia** (tokens procesados por sesión), en la **latencia** y en la **orquestación** de tantos contextos. Un millón de ficheros ocupa poco; un millón de invocaciones al modelo, no. Para volúmenes altos se combina con recuperación selectiva (RAG) en lugar de cargar cada contexto entero. |
| --- |

## **9.1. Enrutado de modelos y optimización de coste**

El instructor describió su **orquestador**: un sistema que decide **qué modelo es el más cualificado para cada acción** entre los que tiene disponibles, en lugar de usar siempre el más potente.

Se planteó en clase si convenía añadir un **validador** con el modelo más potente tras cada tarea. La respuesta fue que no, y el criterio es sólido: *«¿qué tarea hay que validar?»*. Para buscar información en Internet, un modelo ligero basta y no requiere validación. Usar el modelo más caro para todo es **matar moscas a cañonazos**.

| **ℹ Debate de clase: ¿validador fijo o enrutado por tarea?**  **Debate de clase:** Congil defendía un validador fijo con el modelo más potente por seguridad; el instructor defendía el enrutado por tarea. Ambas posturas tienen fondo: un validador **sí** aporta en tareas críticas o irreversibles, pero aplicarlo indiscriminadamente multiplica el coste sin ganancia. El criterio razonable es **validar en función del riesgo de la tarea**, no por sistema. |
| --- |
| **✓ Idea para llevarse**  El razonamiento económico de fondo es correcto y merece retenerse: si te acostumbras a resolverlo todo con el modelo más caro, cuando los precios se ajusten al coste real tu arquitectura será insostenible. **Optimizar tokens y modelo por tarea desde el principio es diseño, no tacañería.** |

## **9.2. Por qué el conocimiento local ahorra tokens**

Afirmación de la clase **correcta**: tener el conocimiento en local (grafo, notas, documentación) consume muchos menos tokens que hacer que el agente busque en Internet, porque se evitan las descargas y el procesamiento de páginas completas.

| **⚠ Matiz**  **Matiz:** el ahorro no es automático. Depende de **cuánto** contexto local se inyecta: cargar un grafo entero en cada consulta puede salir más caro que una búsqueda puntual. El ahorro llega cuando se recupera **solo el fragmento relevante** — que es exactamente para lo que sirve estructurar el conocimiento en nodos. |
| --- |

# **10. Panorama industrial de la IA**

## **10.1. Por qué el crecimiento es exponencial**

La tesis del instructor: una vez se dispuso de modelos capaces, **se usaron los propios modelos para generar y etiquetar datasets**, rompiendo el cuello de botella histórico. Donde antes no existía un dataset especializado, ahora puede construirse. Esta tesis es sustancialmente correcta: los **datos sintéticos** y el etiquetado asistido son hoy una práctica central de la industria.

| **⚠ Conexión: datos sintéticos y colapso del modelo**  **Matiz obligado, y la clase lo tocó sin conectarlo:** los datos sintéticos son útiles **pero no ilimitados**. Es exactamente el fenómeno del *colapso del modelo* de la sección 8.3: si se entrena recursivamente sobre contenido generado, la calidad se degrada. Por eso los datos sintéticos se mezclan con datos reales y se filtran con supervisión, en lugar de sustituirlos. |
| --- |

## **10.2. Modelos abiertos y competencia en precio**

Se comentó **GLM-5.2** como modelo chino de alto rendimiento y coste muy inferior, y el uso de plataformas agregadoras para acceder a varios modelos con precios bajos. Verificado a fecha de estos apuntes:

| **Afirmación de clase** | **Verificación** |
| --- | --- |
| Existe GLM-5.2 y compite con los modelos punteros | **Correcto.** Publicado por Z.ai (antes Zhipu AI) en junio de 2026. El CAISI del NIST lo evaluó como probablemente el modelo de pesos abiertos más capaz en su lanzamiento. |
| Es *«gratuito»* | **Impreciso.** Es de **pesos abiertos** con licencia MIT: puedes descargarlo y autoalojarlo, lo cual no es gratis (requiere hardware). Su API es de pago, aunque notablemente más barata que la de los modelos cerrados. |
| Los laboratorios chinos esperan a los lanzamientos ajenos para publicar | **No verificable.** La coincidencia temporal es observable; la intencionalidad es una interpretación, no un hecho documentado. |
| **⚠ Nota temporal**  Los nombres de modelos, precios, límites y ventanas de contexto **cambian con mucha frecuencia**. Verifica siempre las cifras en la documentación oficial del proveedor antes de usarlas como referencia en un trabajo o una decisión técnica. |

## **10.3. La estrategia del hardware**

Observación acertada de la sesión: mientras los laboratorios de modelos compiten quemando capital, los **fabricantes de hardware** venden la infraestructura que todos ellos necesitan. Se mencionaron equipos optimizados para IA de distintos fabricantes.

| **⚠ Cifras no verificadas**  Las **cifras económicas concretas** citadas en clase (pérdidas mensuales de cada laboratorio, valoraciones, el supuesto récord Guinness de revalorización bursátil de OpenAI) **no se han podido verificar** y no se recogen aquí como datos. La **observación estratégica de fondo** —el hardware captura valor con menos riesgo que los modelos— sí es sólida y ampliamente compartida. |
| --- |

## **10.4. El caso Pokémon GO**

Se contó en clase que Pokémon GO fue **creado como excusa** para mapear el mundo, por un empresario que quería un sistema de reparto con drones, y que compró la licencia a Nintendo con ese fin. La intuición de fondo —**el juego generó un dataset geoespacial de enorme valor**— es correcta, pero la secuencia de los hechos no lo es.

| **Se dijo en clase** | **Qué está documentado** |
| --- | --- |
| El juego se creó **como excusa** para mapear el mundo | Niantic surgió como escisión de Google en 2015 y desarrolló juegos de realidad aumentada basados en localización. El **modelo geoespacial se construyó después**, aprovechando los datos acumulados — no al revés. |
| Se compró la licencia a Nintendo para poder mapear | No hay evidencia pública de esa motivación. La afirmación atribuye una intención no documentada. |
| Niantic tiene hoy drones autónomos gracias a esos datos | Niantic **vendió su división de juegos** (incluido Pokémon GO) a Scopely en 2025 por unos 3 500 millones de dólares, y escindió el negocio geoespacial en **Niantic Spatial**, centrado en un *Large Geospatial Model* para clientes empresariales, robótica y RA. No es un fabricante de drones de reparto. |
| **ℹ La lección que sí se sostiene**  El punto **realmente valioso** de esta anécdota, y que sí se sostiene, es el que cerró el propio debate en clase: **los datos son el activo**. Un producto de consumo masivo puede generar un dataset imposible de construir de otro modo, y ese dataset puede acabar teniendo más valor que el producto que lo generó. Conviene contarlo así, sin la parte de intencionalidad previa que no está documentada. |

## **10.5. Navegación sin GPS por reconocimiento de terreno**

Se comentó que ciertos vehículos aéreos no tripulados navegan por **reconocimiento visual del terreno** en lugar de GPS, porque la señal GPS es fácil de inhibir. El principio técnico es real y se conoce como navegación por **correlación de imagen** o *terrain-referenced navigation*: el sistema compara lo que ve con un mapa de referencia para estimar su posición. Es una aplicación directa de la visión por computador y conecta con el bloque de guerra electrónica.

# **11. Herramientas de la sesión**

| **Herramienta** | **Objetivo** | **Fase / Área** | **Uso visto en clase** | **Nivel** | **Notas** |
| --- | --- | --- | --- | --- | --- |
| **Obsidian** | Notas en Markdown enlazadas con vista de grafo | Datos / Conocimiento | Creación de una bóveda e ingesta de 100 000 coches desde SQLite | Practicado | Grafo **plano**: enlaces sin significado explícito |
| **Neo4j** | Base de datos de grafos con relaciones tipadas | Datos / Conocimiento | Objetivo de la evolución; demostrado con grafos ya construidos | Introducido | Aquí sí hay ontología y pesos |
| **SQLite** | Base de datos relacional ligera | Preparación de datos | Dataset de partida con 100 000 vehículos | Practicado | Punto de partida de la progresión |
| **Claude Code** | Agente de programación en terminal | Agentes / Programación asistida | Conversión automática de SQL a ficheros .md | Recurrente | Usado con subagentes y skills |
| **PyTorch** | Framework de deep learning | Entrenamiento | Mencionado para etiquetado y algoritmos de aprendizaje | Mencionado | El instructor lo usa sobre todo para etiquetar |
| **pandas** | Manipulación y limpieza de datos tabulares | Preparación de datos | Mencionado por Mariana para limpiar y manejar datos | Mencionado | Estándar del análisis de datos en Python |
| **Markdown (.md)** | Formato de texto estructurado | Documentación | Formato de los nodos del grafo | Recurrente | Formato eficiente para contexto de modelos |
| **Agregadores de modelos** | Acceso unificado a múltiples modelos por API | Optimización de tokens | Mencionados para comparar precios por millón de tokens | Mencionado | Verificar precios actuales antes de usar |
| **ℹ Nota sobre los niveles**  Varias herramientas (PyTorch, pandas, los agregadores) **solo se mencionan** en la sesión y no se desarrollan en el material proporcionado. El nivel asignado refleja esa exposición, no dominio. |

# **12. Comandos y acciones**

## **12.1. Preparación del entorno**

| # Obsidian se descarga desde su página oficial: obsidian.md  # Crear bóveda: Nombre de la bóveda -> elegir directorio -> Crear |
| --- |

## **12.2. Instrucciones en lenguaje natural al agente**

Estas **no son comandos de shell**, sino peticiones al agente. Se recogen porque el diseño de la petición es la parte relevante:

| He creado una boveda de Obsidian en el directorio de la base de datos.  Coge el fichero SQL y transforma cada linea en un fichero .md dentro de la boveda.  Crea un nodo por cada marca, ano y modelo, y relaciona cada coche con sus caracteristicas.  No generes nodos duplicados. |
| --- |
| **✓ Patrón útil: el agente de poda**  Fíjate en la última instrucción: **evitar nodos duplicados**. El instructor lo llama *«agente de poda»* o *«el jardinero»* — un agente cuya única función es consolidar nodos repetidos y limpiar relaciones redundantes. Es una buena práctica de mantenimiento de grafos. |

# **13. Comparaciones importantes**

| **Criterio** | **Grafo de conocimiento (Neo4j)** | **Red neuronal** |
| --- | --- | --- |
| Dónde vive el conocimiento | En nodos y aristas legibles | Distribuido en pesos numéricos |
| Cómo se construye | Se define o se genera con reglas y agentes | Se entrena con datos y backpropagation |
| ¿Es inspeccionable? | Sí, se puede leer y consultar | Parcialmente: requiere interpretabilidad |
| Cómo responde | Recorriendo relaciones (consulta) | Generando una predicción |
| Coste de actualizar | Bajo: se añade un nodo | Alto: requiere reentrenar |
| Alucinaciones | No inventa: si no está, no está | Puede generar contenido plausible pero falso |
| **ℹ Ampliación técnica: por qué se combinan**  De esta tabla sale la razón por la que hoy se combinan: el **grafo aporta hechos verificables y actualizables**; el **modelo aporta lenguaje y razonamiento**. Un grafo que alimenta de contexto a un modelo es *RAG sobre grafo* (**GraphRAG**), y es exactamente la arquitectura hacia la que apuntaba el trabajo mostrado en clase — aunque en clase se llamara *red neuronal*. |

# **14. Ética, legalidad y limitaciones**

- **Datos de salud:** categoría especial del RGPD. Requieren base jurídica reforzada, anonimización o seudonimización correcta, y normalmente dictamen de un comité de ética.
- **Simulación de phishing:** los proyectos de concienciación que perfilan empleados a partir de datos públicos (nombre, correo, perfil profesional) tratan **datos personales**. Requieren autorización expresa de la organización y encuadre en un ejercicio autorizado.
- **No entrenar con datos de usuarios** sin base legal ni información previa. El uso de contenido de usuarios para entrenar ha sido objeto de controversia pública precisamente por esto.
- **Sesgo heredado:** un dataset sesgado produce un modelo sesgado. La IA no elimina el sesgo humano por ser automática; lo automatiza y lo escala.
- **Verificación obligatoria:** la fluidez de una respuesta no implica veracidad. Toda salida —cifras, referencias, diagnósticos— requiere validación humana.

| **⚠ Aplicable a la práctica de verano**  Para la práctica de verano: cualquier proyecto que trate datos de personas reales (medicina, perfilado de empleados, diagnóstico) debe partir de datos **anonimizados o sintéticos** y contar con autorización documentada. Es un requisito legal, no una formalidad académica. |
| --- |

# **15. Conexión con sesiones anteriores**

- **Con la sesión de introducción y vibe coding:** allí se introdujeron modelo, agente, tokens y contexto; aquí se baja al mecanismo interno (pesos, capas, entrenamiento) y se corrige la confusión grafo/red neuronal que quedó pendiente.
- **Con el bloque de phishing (Carlos Castillo):** el proyecto de simulación de campañas por departamento es la versión asistida por IA de lo trabajado con GoPhish. Mismo marco legal, misma exigencia de autorización.
- **Con la metodología de auditoría:** enumerar → explotar → documentar tiene el mismo esqueleto que datos → entrenar → validar. En ambos casos, **no se avanza sin evidencia** y se reserva material para verificar el resultado.
- **Con la documentación persistente:** los grafos de conocimiento de auditorías que se comentaron en clase (repositorio de vulnerabilidades encontradas para reutilizar en auditorías futuras) son la aplicación directa de esta sesión al trabajo de ciberseguridad.
- **Con seguridad de agentes:** el envenenamiento de datasets es, conceptualmente, primo de la inyección clásica: **entrada no confiable que altera el comportamiento del sistema**.

# **16. Resumen final**

La sesión construye una progresión clara —**SQL → grafo de notas → grafo vectorial → machine learning**— que es muy útil como mapa mental, siempre que se tenga presente que el último salto **no es una continuación de los anteriores, sino un cambio de tecnología**. Un grafo, por muchos pesos y ontologías que tenga, no aprende solo; una red neuronal aprende ajustando pesos con backpropagation.

Los fundamentos de *machine learning* quedaron bien planteados con el ejemplo del Tetris: **etiquetado supervisado**, **explosión combinatoria** como cuello de botella histórico, **datasets** como activo crítico, y **reserva de un conjunto de prueba** para medir el acierto honestamente.

En seguridad, la sesión aporta dos ideas de peso: el **envenenamiento de datos de entrenamiento** como vector de ataque real —donde lo determinante es la proporción representativa— y el caso **lobo/husky** como recordatorio de que una métrica alta no garantiza que el modelo haya aprendido lo correcto.

En diseño, el patrón **cerebro central + agentes individuales** con filtrado del dato entre niveles, y el **enrutado de modelos por tarea** como disciplina de coste, son las dos ideas directamente aplicables a la práctica de verano.

# **17. Checklist de repaso**

1. Sé explicar por qué un grafo de conocimiento no es una red neuronal, y qué guarda cada uno.
2. Distingo entrenamiento de inferencia, y sé cuál de los dos modifica los pesos.
3. Sé qué es un dataset etiquetado y por qué hay que incluir ejemplos negativos.
4. Puedo explicar cómo se calcula el porcentaje de exactitud de un modelo y por qué se reserva un conjunto de prueba.
5. Entiendo que el peso de un atributo depende de la tarea, no es universal.
6. Sé qué es el envenenamiento de datos de entrenamiento y por qué importa la proporción.
7. Puedo explicar el caso lobo/husky y qué enseña sobre confiar en las métricas.
8. Sé por qué no se reentrena con datos de producción sin curación ni supervisión humana.
9. Distingo RAG de fine-tuning y sé cuál cambia los pesos.
10. Sé diseñar una jerarquía de agentes filtrando qué dato sube al nivel superior.
11. Entiendo la diferencia entre anonimizar y seudonimizar, y sus consecuencias legales.

# **18. Preguntas de repaso**

## **18.1. Preguntas cortas**

1. ¿Dónde está almacenado el conocimiento en una red neuronal?
2. ¿Qué diferencia hay entre un hipervínculo de Obsidian y una relación de Neo4j?
3. ¿Qué es el entrenamiento supervisado?
4. ¿Por qué se reserva parte del dataset sin usarlo para entrenar?
5. ¿Qué es el envenenamiento de datos de entrenamiento?
6. ¿Por qué hay que dar ejemplos negativos al entrenar un clasificador?
7. ¿Cuál es el mecanismo real que ajusta los pesos de una red neuronal?
8. ¿Qué diferencia hay entre RAG y fine-tuning?

## **18.2. Preguntas de desarrollo**

1. Explica la progresión SQL → Obsidian → Neo4j → red neuronal, señalando en qué punto exacto deja de ser una evolución continua y por qué.
2. El caso lobo/husky: describe qué ocurrió, por qué la métrica de acierto no lo detectó y qué medidas habrían servido para descubrirlo antes.
3. Diseña la arquitectura de agentes para una plataforma de formación con 500 empleados, indicando qué dato procesa cada nivel y qué sube al cerebro central.
4. Un compañero afirma que ha *entrenado su propia IA* creando skills y subagentes. Explica con precisión qué ha hecho realmente y qué haría falta para poder decir que la ha entrenado.

## **18.3. Tipo test**

1. En una red neuronal, un peso es:(a) Una arista que describe una relación semántica(b) Un número que gradúa la influencia entre neuronas(c) Una etiqueta del dataset(d) Una capa de la red
2. Reservar un 10 % del dataset sin usarlo para entrenar sirve para:(a) Ahorrar tiempo de cómputo(b) Medir el acierto sobre datos no vistos(c) Evitar el sobrecalentamiento de la GPU(d) Etiquetar más rápido
3. El envenenamiento de datos de entrenamiento es eficaz cuando:(a) Se inyecta una única muestra alterada(b) La muestra alterada es representativa dentro del conjunto(c) Se modifica el código del modelo(d) Se ataca durante la inferencia
4. Neo4j frente a Obsidian aporta principalmente:(a) Mayor velocidad de escritura(b) Relaciones con significado explícito y peso(c) Capacidad de aprender sola(d) Compatibilidad con Markdown
5. El caso lobo/husky demuestra que:(a) Los modelos de visión no funcionan(b) Un modelo puede acertar mucho por la razón equivocada(c) Hacen falta más capas(d) La nieve confunde a las cámaras
6. RAG se caracteriza por:(a) Ajustar los pesos con datos nuevos(b) Recuperar contexto en tiempo de inferencia sin tocar los pesos(c) Sustituir al modelo(d) Entrenar desde cero

## **18.4. Ejercicios prácticos**

1. Crea una bóveda de Obsidian con 10 notas de herramientas de ciberseguridad, enlázalas y observa el grafo. Identifica qué información **no** captura el enlace.
2. Sobre esas mismas 10 notas, diseña en papel el modelo equivalente en Neo4j: qué nodos, qué tipos de relación y qué propiedades tendría cada arista.
3. Toma un dataset público etiquetado y divídelo en entrenamiento, validación y prueba. Documenta las proporciones y justifica el reparto.

| **✓ Soluciones**  **Preguntas cortas:** 1) Distribuido en los pesos numéricos de las conexiones entre neuronas. 2) El hipervínculo solo indica que existe una conexión; la relación de Neo4j indica **qué significa** esa conexión y puede llevar peso y propiedades. 3) Aprendizaje a partir de ejemplos con la respuesta correcta ya etiquetada. 4) Para medir el acierto sobre datos que el modelo nunca ha visto, y que la cifra sea honesta. 5) Inyectar datos falsos o mal etiquetados en el dataset para que el modelo aprenda un comportamiento erróneo. 6) Para que aprenda a delimitar la clase y no clasifique como positivo cualquier entrada inesperada. 7) Backpropagation con descenso del gradiente. 8) RAG recupera contexto en inferencia sin tocar los pesos; el fine-tuning reentrena y **sí** ajusta pesos.**Tipo test:** 1-b · 2-b · 3-b · 4-b · 5-b · 6-b**Desarrollo:** las respuestas se construyen con las secciones 4, 6, 8 y 9 de estos apuntes. |
| --- |

# **19. Glosario**

| **Término** | **Definición breve** |
| --- | --- |
| **Backpropagation** | Propagación del error hacia atrás para ajustar los pesos de cada capa |
| **Capa** (*layer*) | Conjunto de neuronas al mismo nivel de profundidad de la red |
| **Colapso del modelo** | Degradación por entrenar recursivamente con contenido generado por modelos |
| **Conjunto de prueba** (*test set*) | Parte del dataset reservada para medir el acierto final |
| **Correlación espuria** | Patrón que acierta en el dataset pero no es la causa real (caso lobo/husky) |
| **Dataset** | Conjunto de datos de entrenamiento, idealmente etiquetado |
| **Descenso del gradiente** | Método que ajusta los pesos en la dirección que reduce el error |
| **Envenenamiento de datos** | Inyección de datos falsos o mal etiquetados para corromper el aprendizaje |
| **Etiquetado** (*labeling*) | Asignar a cada dato la respuesta correcta esperada |
| **Fine-tuning** | Reentrenamiento que ajusta los pesos con datos nuevos |
| **GraphRAG** | Arquitectura que usa un grafo de conocimiento como fuente de contexto para un modelo |
| **Human in the loop** | Supervisión humana obligatoria dentro del ciclo de entrenamiento o decisión |
| **Inferencia** | Uso de un modelo ya entrenado para obtener una predicción |
| **Ontología** | Definición explícita del significado de las relaciones entre conceptos |
| **Peso** (*weight*) | Número que gradúa la influencia de una neurona sobre la siguiente |
| **RAG** | Recuperación de documentos que se inyectan en el contexto en tiempo de inferencia |
| **Seudonimización** | Sustitución del identificador por un código reversible; sigue siendo dato personal |
| **Sobreajuste** (*overfitting*) | El modelo memoriza el entrenamiento y falla con datos nuevos |

# **20. Actualización del registro de IA**

Escala de niveles: **Mencionado** → **Introducido** → **Comprendido** → **Practicado** → **Aplicado** → **Recurrente**.

| **Concepto / Herramienta** | **Categoría** | **Nivel** |
| --- | --- | --- |
| Grafo de conocimiento vs. red neuronal | Fundamento | **Comprendido** |
| Pesos, capas y arquitectura de red | Red neuronal | Comprendido |
| Backpropagation y descenso del gradiente | Técnica de entrenamiento | Introducido |
| Entrenamiento supervisado | Técnica de entrenamiento | Comprendido |
| Dataset, etiquetado y clasificación | Preparación de datos | Comprendido |
| Conjunto de prueba y medida de exactitud | Método de evaluación | Comprendido |
| Envenenamiento de datos de entrenamiento | Técnica de seguridad | Introducido |
| Correlación espuria (caso lobo/husky) | Método de evaluación | Introducido |
| Human in the loop / preproducción | Técnica de seguridad | Introducido |
| Colapso del modelo (datos sintéticos) | Datos / Conocimiento | Mencionado |
| Arquitectura jerárquica de agentes | Agente | Introducido |
| Enrutado de modelos por tarea | Técnica | **Comprendido** (antes Introducido) |
| Neo4j (grafo vectorial con ontología) | Framework / Datos | **Introducido** (consolidado) |
| Obsidian (grafo plano de notas) | Herramienta | **Practicado** (antes Mencionado) |
| Agente de poda / consolidación de nodos | Agente | Mencionado |
| RAG vs. fine-tuning | Técnica | Introducido |
| Anonimización vs. seudonimización (RGPD) | Datos / Conocimiento | Introducido |
| Aprendizaje por refuerzo | Técnica de entrenamiento | Mencionado |
| GLM-5.2 y modelos de pesos abiertos | Modelo | Mencionado |
| PyTorch | Framework | Mencionado |
| pandas | Herramienta | Mencionado |

# **21. Fuentes consultadas**

El contenido de clase es la **fuente primaria**. Lo siguiente respalda únicamente las ampliaciones y correcciones marcadas en el documento. Fecha de consulta: **23/07/2026**.

| **Fuente** | **Qué afirmación respalda** |
| --- | --- |
| Shumailov, I. et al., *AI models collapse when trained on recursively generated data*, **Nature** 631, 755–759 (2024) | Existencia y mecanismo del **colapso del modelo** por entrenamiento recursivo con datos sintéticos (secciones 8.3 y 10.1) |
| Ribeiro, M. T., Singh, S., Guestrin, C., *«Why Should I Trust You?»: Explaining the Predictions of Any Classifier* (2016) | Origen documentado del experimento **lobo/husky** y la correlación espuria (sección 8.2) |
| CAISI / NIST, *Assessment of Z.ai's GLM-5.2* (julio de 2026) | Fecha de publicación y posición de **GLM-5.2** entre los modelos de pesos abiertos (sección 10.2) |
| Documentación oficial de Z.ai | Licencia MIT y condición de **pesos abiertos** de GLM-5.2, frente a la afirmación de *«gratuito»* (sección 10.2) |
| Comunicados de Niantic y Scopely sobre la venta de la división de juegos (2025) y creación de **Niantic Spatial** | Cronología real del caso **Pokémon GO** y del modelo geoespacial (sección 10.4) |
| **⚠ Sobre lo no verificado**  Las cifras económicas mencionadas en clase (pérdidas de laboratorios, valoraciones bursátiles, el supuesto récord Guinness) **no se han incluido como datos** porque no ha sido posible verificarlas con fuentes fiables. Los nombres, precios y capacidades de los modelos cambian con rapidez: contrasta siempre con la documentación oficial del proveedor antes de usarlos como referencia. |
