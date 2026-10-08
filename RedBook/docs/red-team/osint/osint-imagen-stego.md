---
tags:
- OSINT e ingeniería social
---

# OSINT Imagen Stego

EVOLVE ACADEMY - MASTER EN CIBERSEGURIDAD

**Lo que tu imagen no te cuenta: OSINT y Esteganografía**

Evolve Academy · Metadatos e información oculta

*Temas: Metadatos EXIF · exiftool · steghide · binwalk · Búsqueda inversa de imágenes · Shodan avanzado · Geolocalización*

# **① Metadatos de imagen: EXIF**

Las imágenes digitales llevan metadatos EXIF incrustados. Pueden revelar información muy sensible de forma involuntaria.

| **Campo EXIF** | **Información revelada** |
| --- | --- |
| GPS Coordinates | Geolocalización exacta donde se tomó la foto |
| Camera Make/Model | Marca y modelo del dispositivo |
| Date/Time Original | Fecha y hora exacta de la captura |
| Software | Programa usado para editar/exportar |
| Author/Artist | Nombre del autor en documentos Word/PDF |
| GPS Altitude | Altitud sobre el nivel del mar |
| Serial Number | Número de serie del dispositivo (algunos modelos) |

| **🔐 CASO REAL** | John McAfee fue localizado por periodistas gracias a las coordenadas GPS en la EXIF de una foto publicada en Twitter. Las redes sociales eliminan EXIF, pero muchas webs corporativas y foros NO. |
| --- | --- |

# **② exiftool — Extracción de metadatos**

| # Instalación:  sudo apt install exiftool  # Uso básico:  exiftool imagen.jpg # ver todos los metadatos  exiftool -GPS\* imagen.jpg # solo datos GPS  exiftool -Author documento.pdf # autor del PDF  # Procesar múltiples ficheros:  exiftool \*.jpg # todos los JPG del directorio  exiftool -r /directorio/ # recursivo  # Exportar a CSV:  exiftool -csv \*.jpg > metadatos.csv  # Eliminar todos los metadatos (antes de publicar):  exiftool -all= imagen.jpg  exiftool -all= -r /directorio/ # recursivo  # Modificar metadatos:  exiftool -Author='Anónimo' fichero.docx  exiftool -GPSLatitude= -GPSLongitude= imagen.jpg # borrar GPS |
| --- |

| **💡 OSINT** | En una auditoría: descargar imágenes del sitio web corporativo y analizar sus EXIF puede revelar: nombres de empleados (Author), software interno, y hasta coordenadas de la oficina. |
| --- | --- |

# **③ Búsqueda inversa de imágenes**

Permite encontrar dónde más aparece una imagen o identificar personas/lugares a partir de una foto.

| **Herramienta** | **Uso** |
| --- | --- |
| Google Lens | Análisis de imagen completo, objetos y lugares |
| Google Images | Búsqueda inversa clásica (arrastrar imagen) |
| Yandex Images | Muy efectivo para encontrar rostros (mejor que Google) |
| TinEye | Rastrea copia exacta de imágenes en internet |
| PimEyes | Reconocimiento facial (uso ético discutible) |
| FaceCheck.ID | Búsqueda por rostro en redes sociales |

| # Técnica 4chan / Forza: geolocalización por imagen  # Caso famoso: localizar una bandera solo viendo el cielo  # Proceso:  # 1. Analizar objetos en la imagen (señales, edificios, vegetación)  # 2. Analizar patrones de estrellas visibles → hora y latitud aprox.  # 3. Rastrear patrones de aviones sobrevolando (flightradar24)  # 4. Cruzar con mapas de satélite (Google Earth)  # → En <48 horas encontraron la bandera en un campo de Tennessee |
| --- |

# **④ Steghide — Esteganografía**

La esteganografía oculta información **dentro** de otro fichero (imagen, audio). A diferencia de la criptografía, el objetivo es que nadie sepa que hay información oculta.

| # Instalación:  sudo apt install steghide  # Ocultar mensaje en imagen:  steghide embed -cf imagen.jpg -sf secreto.txt  # -cf = cover file (la imagen contenedora)  # -sf = secret file (el fichero a ocultar)  # Te pedirá contraseña para proteger el secreto  # Extraer mensaje oculto:  steghide extract -sf imagen.jpg  # Te pedirá la contraseña  # Ver información sobre el contenido oculto (sin extraer):  steghide info imagen.jpg  # Fuerza bruta de contraseña (con stegcracker):  pip install stegcracker  stegcracker imagen.jpg /usr/share/wordlists/rockyou.txt |
| --- |

| **🎯 CTF** | En CTFs, la esteganografía es muy común. Siempre que veas una imagen o audio, comprueba si contiene datos ocultos con steghide, binwalk o strings. |
| --- | --- |

# **⑤ binwalk — Análisis forense de ficheros**

| # binwalk analiza ficheros binarios buscando ficheros incrustados  sudo apt install binwalk  # Analizar un fichero:  binwalk imagen.jpg  # Muestra ficheros embebidos (ZIP, PDF, EXE...)  # Extraer todo lo encontrado:  binwalk -e imagen.jpg  # Crea directorio \_imagen.jpg.extracted/ con los ficheros  # Recursivo (extrae dentro de lo extraído):  binwalk -Me imagen.jpg  # También útil para firmware de routers y dispositivos IoT |
| --- |

# **⑥ strings — Texto en ficheros binarios**

| # strings extrae cadenas de texto legibles de cualquier fichero binario  strings imagen.jpg  strings ejecutable.exe | grep -i password  strings firmware.bin | grep -E 'http|ftp|admin'  # Filtrar solo strings relevantes:  strings fichero | grep -i 'pass\|user\|key\|secret\|token'  # En CTFs, buscar flags:  strings fichero | grep 'CTF{\|FLAG{'  # Combinado con file para identificar primero el tipo:  file imagen.jpg # verifica si es realmente una imagen  xxd imagen.jpg | head -20 # ver bytes en hex (magic bytes) |
| --- |

# **⑦ Shodan para OSINT de cámaras e IoT**

| # Shodan indexa miles de dispositivos IoT expuestos  # Búsqueda de cámaras IP:  title:'webcamXP 5' # cámaras con panel web  product:'Hikvision' # marca específica  port:554 has\_screenshot:true # cámaras RTSP con captura  # Bases de datos expuestas:  product:MongoDB port:27017 # MongoDB sin autenticación  product:Elasticsearch # Elasticsearch expuesto  # ICS/SCADA (infraestructura crítica):  product:'Siemens' # PLCs Siemens  # ⚠ ACLARACIÓN:  # Las cámaras 'públicas' son accesibles porque están mal configuradas  # Acceder a ellas puede ser legal (son públicas) pero:  # - Manipularlas es ilegal  # - Usarlas para vigilancia sin consentimiento es ilegal  # - En auditorías: documenta y notifica, no manipules |
| --- |

| **🔐 FOOTPRINTING** | En una auditoría externa real: buscar en Shodan los activos del cliente revela cámaras, paneles de administración y servicios desconocidos que el propio cliente olvidó que tenía expuestos. |
| --- | --- |

# **⑧ Resumen: herramientas por caso de uso**

| **Herramienta** | **Uso principal** |
| --- | --- |
| exiftool | Metadatos de imagen, documentos Office, PDF |
| steghide | Ocultar/extraer datos en imágenes JPEG/BMP |
| binwalk | Ficheros incrustados en binarios, firmware IoT |
| strings | Texto en binarios, credenciales hardcodeadas |
| Google Lens / Yandex | Búsqueda inversa de imágenes, reconocimiento facial |
| Shodan | Dispositivos IoT, cámaras, servicios expuestos |
| stegcracker | Fuerza bruta contraseña de steghide |
| pngcheck | Validar/analizar PNGs (CTFs) |
| zsteg | Esteganografía en PNG y BMP |
