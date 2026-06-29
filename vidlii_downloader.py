import os
import sys
import re
import time
import urllib.request
import urllib.error
import html
import json
import urllib.parse

# Reconfigurar salida estándar para UTF-8 si está disponible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Inicializar soporte ANSI en Windows
if os.name == 'nt':
    os.system('')

# Códigos de colores ANSI para la consola
CLEAR_LINE = "\033[K"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[32m"
COLOR_CYAN = "\033[36m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_MAGENTA = "\033[35m"

def safe_write(text):
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except UnicodeEncodeError:
        # Reemplazar caracteres no soportados por la codificación de la consola (ej. cp1252 o cp850)
        text = text.replace('█', '#').replace('░', '-')
        text = text.replace('✓', 'OK').replace('¡', '').replace('¿', '')
        enc = sys.stdout.encoding or 'ascii'
        try:
            sys.stdout.write(text.encode(enc, errors='replace').decode(enc))
        except Exception:
            sys.stdout.write(text.encode('ascii', errors='replace').decode('ascii'))
        sys.stdout.flush()

def safe_print(*args, sep=' ', end='\n'):
    text = sep.join(str(arg) for arg in args)
    safe_write(text + end)

# Sobrescribir print para usar nuestra versión segura de consola
print = safe_print

# Cabeceras HTTP estándar para evitar bloqueos
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def print_banner():
    banner = f"""
{COLOR_CYAN}{COLOR_BOLD}=============================================================
             DESCUBRIDOR Y DESCARGADOR DE VIDLII
============================================================={COLOR_RESET}
    """
    print(banner)

def log_info(msg):
    print(f"{COLOR_CYAN}[i]{COLOR_RESET} {msg}")

def log_success(msg):
    print(f"{COLOR_GREEN}[✓]{COLOR_RESET} {msg}")

def log_warn(msg):
    print(f"{COLOR_YELLOW}[!]{COLOR_RESET} {msg}")

def log_error(msg):
    print(f"{COLOR_RED}[X]{COLOR_RESET} {msg}")

def clean_filename(title):
    # Desescapar entidades HTML (como &quot;, &amp;)
    title = html.unescape(title)
    # Reemplazar caracteres prohibidos en sistemas operativos (Windows/Linux)
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    # Reemplazar múltiples espacios por uno solo y quitar extremos
    title = re.sub(r'\s+', ' ', title).strip()
    # Limitar longitud para evitar problemas con rutas largas en Windows
    if len(title) > 120:
        title = title[:117] + "..."
    return title if title else "Video_Sin_Titulo"

def parse_input(user_input):
    """
    Analiza la entrada del usuario y determina si es un video o un canal.
    Retorna: (tipo, valor)
    - tipo: 'video' o 'channel'
    - valor: video_id o username
    """
    user_input = user_input.strip()
    
    # Caso 1: Enlace de video de VidLii
    # Ej: https://www.vidlii.com/watch?v=VIDEO_ID o vidlii.com/watch?v=VIDEO_ID
    if 'watch?v=' in user_input:
        match = re.search(r'v=([a-zA-Z0-9_-]+)', user_input)
        if match:
            return 'video', match.group(1)
            
    # Caso 2: Enlace de canal de VidLii
    # Ej: https://www.vidlii.com/user/ByGeremiXD/videos o https://www.vidlii.com/user/ByGeremiXD
    if '/user/' in user_input:
        match = re.search(r'/user/([a-zA-Z0-9_-]+)', user_input)
        if match:
            return 'channel', match.group(1)
            
    # Caso 3: Entrada limpia (ID de video de 11 caracteres o nombre de usuario)
    # Por lo general, los IDs de video en VidLii tienen exactamente 11 caracteres (letras, números, guiones)
    # Vamos a realizar una petición rápida para determinar si es un ID de video válido.
    if re.match(r'^[a-zA-Z0-9_-]{11}$', user_input):
        log_info(f"Detectando si '{user_input}' es un ID de video o un usuario...")
        if verify_video_exists(user_input):
            return 'video', user_input
        else:
            return 'channel', user_input

    # Por defecto, asumimos que es el nombre de un canal/usuario
    return 'channel', user_input

def verify_video_exists(video_id):
    """Verifica si un ID de video existe haciendo una petición HEAD o GET a su página de reproducción"""
    url = f"https://www.vidlii.com/watch?v={video_id}"
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            html_content = res.read().decode('utf-8', errors='ignore')
            # Si contiene el reproductor o la etiqueta de video, existe
            return 'noscript-player-video' in html_content or '/usfi/v/' in html_content
    except Exception:
        return False

def get_video_info(video_id):
    """Obtiene el título y la URL de descarga directa de un video"""
    url = f"https://www.vidlii.com/watch?v={video_id}"
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            html_content = res.read().decode('utf-8', errors='ignore')
            
            # Extraer título
            title_match = re.search(r'<title>(.*?) - VidLii</title>', html_content)
            title = title_match.group(1) if title_match else f"Video_{video_id}"
            
            # Extraer URL directa de video
            # Buscamos primero en el reproductor alternativo sin JS
            src_match = re.search(r'id="noscript-player-video"\s+src="([^"]+)"', html_content)
            if not src_match:
                # Fallback genérico por si cambia el ID del reproductor
                src_match = re.search(r'src="(/usfi/v/[^"]+\.mp4[^"]*)"', html_content)
                
            if src_match:
                video_rel_url = src_match.group(1)
                video_direct_url = f"https://www.vidlii.com{video_rel_url}"
                return {
                    'id': video_id,
                    'title': title,
                    'url': video_direct_url
                }
            else:
                return None
    except Exception as e:
        log_error(f"Error al obtener información para el video {video_id}: {e}")
        return None

def get_channel_videos(username):
    """Escanea el canal y extrae todos los IDs de videos utilizando paginación"""
    log_info(f"Escaneando videos del canal de {COLOR_BOLD}{username}{COLOR_RESET}...")
    
    # 1. Obtener la página principal del canal para resolver el ID de canal e identificar si existe
    channel_url = f"https://www.vidlii.com/user/{username}"
    req_channel = urllib.request.Request(channel_url, headers=HTTP_HEADERS)
    try:
        with urllib.request.urlopen(req_channel, timeout=10) as res:
            final_url = res.geturl()
            # Si redirige a la página de inicio, el canal no existe
            if final_url.strip('/') == "https://www.vidlii.com":
                log_error(f"El canal/usuario '{username}' no existe (redireccionado al inicio).")
                return []
            html_content = res.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log_error(f"El canal/usuario '{username}' no existe o no se pudo acceder a él (Error 404).")
        else:
            log_error(f"Error HTTP al acceder al canal: {e}")
        return []
    except Exception as e:
        log_error(f"Error al conectar con el canal de '{username}': {e}")
        return []

    # 2. Buscar el ID interno de canal en el HTML de la página
    channel_id = username
    ch_user_match = re.search(r'id="ch_user">(.*?)</div>', html_content)
    if ch_user_match:
        channel_id = ch_user_match.group(1).strip()
    else:
        feed_match = re.search(r'/api/feed/channel/([a-zA-Z0-9_-]+)/videos\.xml', html_content)
        if feed_match:
            channel_id = feed_match.group(1)

    log_info(f"ID interno de canal identificado: {channel_id}")
    
    video_ids = []
    cursor_ts = None
    ajax_headers = HTTP_HEADERS.copy()
    ajax_headers['X-Requested-With'] = 'XMLHttpRequest'
    
    # 3. Escanear videos mediante peticiones paginadas al endpoint AJAX
    while True:
        params = {
            'user': channel_id,
            'includeUploads': 'true',
            'uploadsLimit': '100'
        }
        if cursor_ts:
            params['cursorTs'] = cursor_ts
            params['uploadsBefore'] = cursor_ts
            params['uploadsOrder'] = 'createdOn DESC'
            
        url = f"https://www.vidlii.com/ajax/get_channel_cards?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=ajax_headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode('utf-8'))
                
                if not data.get('success') or 'data' not in data or 'uploads' not in data['data']:
                    break
                
                uploads = data['data']['uploads']
                items = uploads.get('items', [])
                if not items:
                    break
                
                page_vids = [item['id'] for item in items if 'id' in item]
                new_vids = [v for v in page_vids if v not in video_ids]
                
                if not new_vids:
                    break
                    
                video_ids.extend(new_vids)
                log_info(f"Encontrados {len(new_vids)} videos nuevos (Total acumulado: {len(video_ids)})")
                
                if len(video_ids) >= uploads.get('total', 0) or len(items) < 100:
                    break
                    
                cursor_ts = items[-1].get('createdOn')
                if not cursor_ts:
                    break
                    
                time.sleep(0.5)
        except Exception as e:
            log_error(f"Error al escanear videos del canal: {e}")
            break
            
    return video_ids

def download_video_file(video_info, output_dir):
    """
    Descarga el archivo de video con soporte de reanudación (Resume) y
    barra de progreso detallada en la consola.
    """
    video_id = video_info['id']
    title = video_info['title']
    video_url = video_info['url']
    
    clean_title = clean_filename(title)
    filename = f"[{video_id}] {clean_title}.mp4"
    filepath = os.path.join(output_dir, filename)
    
    log_info(f"Preparando: {COLOR_BOLD}{clean_title}{COLOR_RESET}")
    
    # 1. Obtener el tamaño total del video (Content-Length) usando HEAD request
    total_size = None
    req_head = urllib.request.Request(video_url, headers=HTTP_HEADERS, method='HEAD')
    try:
        with urllib.request.urlopen(req_head, timeout=10) as res:
            content_length = res.getheader('Content-Length')
            if content_length:
                total_size = int(content_length)
    except Exception:
        # Fallback a GET si HEAD no está permitido o falla
        try:
            req_get_test = urllib.request.Request(video_url, headers=HTTP_HEADERS)
            with urllib.request.urlopen(req_get_test, timeout=5) as res:
                content_length = res.getheader('Content-Length')
                if content_length:
                    total_size = int(content_length)
        except Exception as e:
            log_error(f"No se pudo conectar al servidor de video: {e}")
            return False
            
    if total_size is None:
        log_warn("No se pudo obtener el tamaño del archivo. Descargando sin barra de progreso completa...")
        
    # 2. Configurar reanudación de descarga (Range request)
    local_size = 0
    mode = 'wb'
    headers = HTTP_HEADERS.copy()
    
    if os.path.exists(filepath):
        local_size = os.path.getsize(filepath)
        if total_size is not None:
            if local_size == total_size:
                log_success(f"¡Ya descargado! Omitiendo: {COLOR_GREEN}{filename}{COLOR_RESET}")
                return True
            elif local_size < total_size:
                log_info(f"Descarga incompleta encontrada ({local_size / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB). Reanudando...")
                headers['Range'] = f"bytes={local_size}-"
                mode = 'ab'
            else:
                log_warn("El archivo local es mayor que el del servidor. Re-descargando completo...")
                local_size = 0
        else:
            log_warn("Archivo local existente de tamaño desconocido. Re-descargando completo...")
            local_size = 0
            
    # 3. Descarga chunk por chunk
    req_download = urllib.request.Request(video_url, headers=headers)
    try:
        with urllib.request.urlopen(req_download, timeout=15) as response:
            # Si se solicitó rango y el servidor no responde con 206, volvemos a escribir completo
            status_code = response.status if hasattr(response, 'status') else 200
            if status_code != 206 and 'Range' in headers:
                mode = 'wb'
                local_size = 0
                
            chunk_size = 1024 * 128  # 128 KB
            downloaded = local_size
            
            start_time = time.time()
            last_print_time = start_time
            bytes_since_last_print = 0
            speed = 0.0
            
            with open(filepath, mode) as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    bytes_since_last_print += len(chunk)
                    
                    # Calcular velocidad y ETA cada 0.3 segundos
                    current_time = time.time()
                    elapsed_since_last_print = current_time - last_print_time
                    if elapsed_since_last_print >= 0.3:
                        speed = bytes_since_last_print / elapsed_since_last_print
                        last_print_time = current_time
                        bytes_since_last_print = 0
                        
                    # Mostrar barra de progreso
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        bar_length = 20
                        filled_length = int(round(bar_length * downloaded / float(total_size)))
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        
                        speed_mb = speed / (1024 * 1024)
                        eta_str = "--:--"
                        if speed > 0:
                            remaining_bytes = total_size - downloaded
                            remaining_seconds = remaining_bytes / speed
                            mins, secs = divmod(int(remaining_seconds), 60)
                            eta_str = f"{mins:02d}:{secs:02d}"
                            
                        progress_str = (
                            f"\r{CLEAR_LINE}[Descargando] [{COLOR_CYAN}{bar}{COLOR_RESET}] {percent:.1f}% | "
                            f"{downloaded / (1024*1024):.1f}MB/{total_size / (1024*1024):.1f}MB | "
                            f"{speed_mb:.1f} MB/s | ETA: {eta_str}"
                        )
                    else:
                        progress_str = (
                            f"\r{CLEAR_LINE}[Descargando] {downloaded / (1024*1024):.2f} MB descargados | "
                            f"{speed / (1024*1024):.2f} MB/s"
                        )
                        
                    safe_write(progress_str)
                    
            safe_write(f"\r{CLEAR_LINE}")
            log_success(f"¡Descargado con éxito! -> {filename}")
            return True
            
    except KeyboardInterrupt:
        # Borrar el carácter residual de Ctrl+C en la terminal
        safe_write(f"\r{CLEAR_LINE}")
        log_warn("Descarga pausada por el usuario (Ctrl+C). Archivo guardado parcialmente.")
        raise KeyboardInterrupt
    except Exception as e:
        safe_write(f"\r{CLEAR_LINE}")
        log_error(f"Error al descargar {filename}: {e}")
        return False

def main():
    print_banner()
    
    # Comprobar si se pasó la entrada por línea de comandos
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        print(f"{COLOR_BOLD}Ingresa el enlace del video o del canal de VidLii{COLOR_RESET}")
        print(f"Ejemplos:")
        print(f"  - Canal:  https://www.vidlii.com/user/ByGeremiXD")
        print(f"  - Video:  https://www.vidlii.com/watch?v=VIDEO_ID")
        print(f"  - Nombre: ByGeremiXD (se escaneará como canal)")
        print(f"  - ID:     VIDEO_ID (se escaneará como video)")
        print("-" * 60)
        user_input = input(f"{COLOR_CYAN}Entrada: {COLOR_RESET}").strip()
        
    if not user_input:
        log_error("No se ingresó ninguna entrada. Saliendo...")
        return
        
    tipo, valor = parse_input(user_input)
    
    # Configurar directorio de descargas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    downloads_dir = os.path.join(base_dir, "downloads")
    
    if tipo == 'video':
        log_info(f"Tipo detectado: {COLOR_BOLD}Video Individual{COLOR_RESET} (ID: {valor})")
        log_info("Buscando información del video...")
        v_info = get_video_info(valor)
        if not v_info:
            log_error(f"No se pudo obtener información del video '{valor}'. Verifica si el enlace o ID es correcto.")
            return
            
        os.makedirs(downloads_dir, exist_ok=True)
        try:
            download_video_file(v_info, downloads_dir)
        except KeyboardInterrupt:
            log_info("Proceso terminado.")
            
    elif tipo == 'channel':
        log_info(f"Tipo detectado: {COLOR_BOLD}Canal / Usuario{COLOR_RESET} (Usuario: {valor})")
        video_ids = get_channel_videos(valor)
        
        if not video_ids:
            log_error(f"No se encontraron videos públicos para el usuario '{valor}' o el canal no existe.")
            return
            
        total_vids = len(video_ids)
        log_success(f"Escaneo finalizado. ¡Se encontraron {COLOR_BOLD}{total_vids}{COLOR_RESET} videos en total!")
        
        # Preguntar confirmación de descarga
        try:
            confirm = input(f"\n¿Deseas iniciar la descarga de los {total_vids} videos? [S/n]: ").strip().lower()
            if confirm not in ('', 's', 'si', 'y', 'yes'):
                log_info("Descarga cancelada por el usuario.")
                return
        except KeyboardInterrupt:
            print()
            log_info("Proceso cancelado por el usuario.")
            return
            
        # Crear directorio específico del canal dentro de downloads
        channel_dir = os.path.join(downloads_dir, valor)
        os.makedirs(channel_dir, exist_ok=True)
        log_info(f"Los videos se guardarán en: {COLOR_BOLD}{channel_dir}{COLOR_RESET}\n")
        
        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        try:
            for idx, vid in enumerate(video_ids, 1):
                print(f"{COLOR_MAGENTA}[{idx}/{total_vids}]{COLOR_RESET} Procesando video ID: {vid}")
                
                # Intentar obtener info del video (hasta 3 intentos en caso de fallos de conexión temporales)
                v_info = None
                for attempt in range(1, 4):
                    v_info = get_video_info(vid)
                    if v_info:
                        break
                    log_warn(f"Reintentando obtener información del video {vid} (Intento {attempt}/3)...")
                    time.sleep(1)
                    
                if not v_info:
                    log_error(f"No se pudo procesar el video ID: {vid}. Saltando...")
                    failed_count += 1
                    continue
                    
                # Descargar
                success = download_video_file(v_info, channel_dir)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                print()  # Espacio entre videos
                
        except KeyboardInterrupt:
            print()
            log_warn("Descarga de canal interrumpida por el usuario.")
            
        # Resumen final
        print("-" * 60)
        log_success("Resumen de tareas:")
        print(f"  - Completados / Omitidos por ya existir: {COLOR_GREEN}{success_count}{COLOR_RESET}")
        if failed_count > 0:
            print(f"  - Fallidos: {COLOR_RED}{failed_count}{COLOR_RESET}")
        print(f"  - Ruta de descarga: {downloads_dir}\\{valor}")
        print("-" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{COLOR_YELLOW}[!] Saliendo del programa...{COLOR_RESET}")
        sys.exit(0)
    # Evitar que se cierre la ventana de comandos inmediatamente al ejecutar como .bat
    input(f"\nPresiona Enter para cerrar...")
