# Vidlii Downloader

Este es un script de utilidad diseñado para descargar de forma automática videos de la plataforma **VidLii**, permitiendo bajar tanto videos individuales como todos los videos subidos a un canal completo.

El script está desarrollado en **Python 3** usando únicamente librerías estándar del sistema, por lo que **no requiere instalar ningún tipo de dependencias adicionales** (sin necesidad de configurar `pip` o instalar frameworks externos).

## Características principales
* **Autodetección inteligente**: Pega el enlace de un video, de un canal, o simplemente un ID/usuario, y el script determinará automáticamente qué procesar.
* **Descarga de Canales**: Extrae automáticamente la lista completa de videos de cualquier creador navegando a través de la paginación interna.
* **Barra de progreso animada**: Muestra el progreso en porcentaje, tamaño total, velocidad en tiempo real (MB/s) y tiempo estimado de finalización (ETA).
* **Función de reanudación automática (Resume)**: Si la descarga se interrumpe (por corte de luz, desconexión de internet o cancelación voluntaria con `Ctrl+C`), el script utilizará solicitudes de rango HTTP para continuar descargando el video desde el último byte guardado en lugar de iniciar desde cero.
* **Sanitización de nombres**: Convierte títulos complejos con caracteres especiales en nombres de archivos válidos para Windows y Linux.

---

## Cómo usar el programa

### Opción 1: Ejecución Interactiva (Recomendado en Windows)
1. Haz doble clic sobre el archivo `descargar.bat`.
2. Se abrirá una ventana de comandos solicitándote la entrada:
   ```text
   Ingresa el enlace del video o del canal de VidLii:
   ```
3. Escribe o pega el enlace y presiona **Enter**.
4. Si ingresaste un canal, te mostrará la cantidad de videos encontrados y te solicitará confirmación (`¿Deseas iniciar la descarga de los X videos? [S/n]`). Escribe `S` y presiona **Enter**.

### Opción 2: Ejecución desde la Consola de comandos
Abre la consola en el directorio del descargador y ejecuta:

**Para modo interactivo:**
```bash
python vidlii_downloader.py
```

**Pasando el enlace directamente por argumento:**
```bash
python vidlii_downloader.py https://www.vidlii.com/user/ByGeremiXD
```

---

## Ejemplos de entradas soportadas
El script es muy inteligente para procesar tus entradas. Puedes introducir:

* **Video por URL completa**: `https://www.vidlii.com/watch?v=VIDEO_ID`
* **Video por ID directo**: `VIDEO_ID`
* **Canal por URL completa**: `https://www.vidlii.com/user/ByGeremiXD` o `https://www.vidlii.com/user/ByGeremiXD/videos`
* **Canal por nombre de usuario**: `ByGeremiXD`

---

## Ubicación de las descargas
Los archivos descargados se guardarán dentro del mismo directorio en la carpeta `downloads/`:
* Los videos individuales se guardan directamente en `downloads/`.
* Los videos de canales se organizan en subcarpetas con el nombre del canal respectivo (ej. `downloads/ByGeremiXD/[VIDEO_ID] Titulo.mp4`).
