import http.server
import json
import socketserver
import time
import os
import uuid
from urllib.parse import urlparse, parse_qs
from src.adapters.inbound.templates import HTML_TEMPLATE, LOGIN_HTML
from src.adapters.outbound.auth_pam import authenticate_pam

SESSION_TOKEN = str(uuid.uuid4())
from src.application.ports.inputs import (
    GetSystemStatusUseCase,
    ToggleGuiUseCase,
    ControlDockerContainerUseCase,
    GetDockerContainerLogsUseCase,
    DeployAppUseCase,
    GetDeployStatusUseCase,
    ListDeploymentsUseCase,
    GetCamerasUseCase,
    CaptureCameraFrameUseCase,
    GetWifiClientsUseCase,
    StartRecordingUseCase,
    StopRecordingUseCase,
    GetRecordingStatusUseCase,
    ListRecordingsUseCase,
    GetVisionSettingsUseCase,
    UpdateVisionSettingsUseCase,
    SaveClientAliasUseCase,
    CancelDeploymentUseCase
)

def create_handler_class(
    status_use_case: GetSystemStatusUseCase,
    gui_use_case: ToggleGuiUseCase,
    docker_use_case: ControlDockerContainerUseCase,
    docker_logs_use_case: GetDockerContainerLogsUseCase,
    deploy_use_case: DeployAppUseCase,
    get_deploy_status_use_case: GetDeployStatusUseCase,
    list_deployments_use_case: ListDeploymentsUseCase,
    cancel_deploy_use_case: CancelDeploymentUseCase,
    get_cameras_use_case: GetCamerasUseCase,
    capture_frame_use_case: CaptureCameraFrameUseCase,
    get_wifi_clients_use_case: GetWifiClientsUseCase,
    start_recording_use_case: StartRecordingUseCase,
    stop_recording_use_case: StopRecordingUseCase,
    get_recording_status_use_case: GetRecordingStatusUseCase,
    list_recordings_use_case: ListRecordingsUseCase,
    get_vision_settings_use_case: GetVisionSettingsUseCase,
    update_vision_settings_use_case: UpdateVisionSettingsUseCase,
    save_client_alias_use_case: SaveClientAliasUseCase,
    webhook_use_case=None,
    get_git_branches_use_case=None
):
    class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _send_json(self, data, status_code=200):
            try:
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                pass

        def is_authenticated(self):
            if self.path.startswith("/api/webhooks/"):
                return True
            cookie_header = self.headers.get("Cookie", "")
            cookies = {}
            for cookie in cookie_header.split(";"):
                parts = cookie.strip().split("=")
                if len(parts) == 2:
                    cookies[parts[0]] = parts[1]
            return cookies.get("session_token") == SESSION_TOKEN

        def do_GET(self):
            url_parsed = urlparse(self.path)
            
            if not self.is_authenticated():
                if url_parsed.path == "/":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(LOGIN_HTML.encode("utf-8"))
                    return
                else:
                    self._send_json({"status": "error", "message": "No autorizado (Inicia sesión)"}, 401)
                    return
            
            # 1. API: Obtener Métricas de Sistema (JSON)
            if url_parsed.path == "/api/status":
                status = status_use_case.execute()
                self._send_json(status.to_dict())
                return

            # 1.1 API: Obtener Logs de Contenedor Docker (JSON)
            elif url_parsed.path == "/api/docker/logs":
                query_params = parse_qs(url_parsed.query)
                container_id = query_params.get("id", [None])[0]
                
                if container_id:
                    success, logs = docker_logs_use_case.execute(container_id)
                    response_data = {"status": "success" if success else "error", "logs": logs}
                else:
                    response_data = {"status": "error", "message": "Falta el ID del contenedor"}
                    
                self._send_json(response_data)
                return

            # 1.2 API: Obtener lista de cámaras
            elif url_parsed.path == "/api/camera/list":
                cameras = get_cameras_use_case.execute()
                self._send_json([c.to_dict() for c in cameras])
                return

            # 1.3 API: Capturar frame de cámara (Retorna imagen directa)
            elif url_parsed.path == "/api/camera/frame":
                query_params = parse_qs(url_parsed.query)
                camera_id = query_params.get("id", [None])[0]
                
                if camera_id:
                    frame_bytes = capture_frame_use_case.execute(camera_id)
                    self.send_response(200)
                    
                    if frame_bytes.startswith(b'\x89PNG'):
                        self.send_header("Content-Type", "image/png")
                    elif frame_bytes.startswith(b'BM'):
                        self.send_header("Content-Type", "image/bmp")
                    else:
                        self.send_header("Content-Type", "image/jpeg")
                        
                    self.end_headers()
                    try:
                        self.wfile.write(frame_bytes)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                else:
                    self.send_error(400, "Falta el ID de la camara")
                return

            # 1.35 API: Streaming MJPEG fluido de cámara (Transmisión continua)
            elif url_parsed.path == "/api/camera/stream":
                query_params = parse_qs(url_parsed.query)
                camera_id = query_params.get("id", [None])[0]
                
                if not camera_id:
                    self.send_error(400, "Falta el ID de la camara")
                    return
                
                self.send_response(200)
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                self.end_headers()
                
                last_frame_idx = -1
                try:
                    while True:
                        frame_bytes, frame_idx = capture_frame_use_case.execute_packet(camera_id)
                        if frame_idx == last_frame_idx or not frame_bytes:
                            # Espera mínima por un nuevo fotograma para liberar CPU
                            time.sleep(0.005)
                            continue
                        
                        last_frame_idx = frame_idx
                        self.wfile.write(b'--frame\r\n')
                        if frame_bytes.startswith(b'\x89PNG'):
                            self.wfile.write(b'Content-Type: image/png\r\n\r\n')
                        elif frame_bytes.startswith(b'BM'):
                            self.wfile.write(b'Content-Type: image/bmp\r\n\r\n')
                        else:
                            self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                        self.wfile.write(frame_bytes)
                        self.wfile.write(b'\r\n')
                        time.sleep(0.002)
                except Exception as e:
                    # El cliente cerró la pestaña, detuvo la reproducción, o hubo un error de red
                    pass
                return

            # 1.36 API: Obtener estado de grabación
            elif url_parsed.path == "/api/camera/record/status":
                query_params = parse_qs(url_parsed.query)
                camera_id = query_params.get("id", [None])[0]
                if camera_id:
                    status = get_recording_status_use_case.execute(camera_id)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(status.to_dict()).encode("utf-8"))
                else:
                    self.send_error(400, "Falta el ID de la camara")
                return

            # 1.37 API: Listar grabaciones guardadas
            elif url_parsed.path == "/api/camera/recordings":
                files = list_recordings_use_case.execute()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(files).encode("utf-8"))
                return

            # 1.375 API: Obtener ajustes de visión artificial (rostro/manos)
            elif url_parsed.path == "/api/camera/vision/settings":
                settings = get_vision_settings_use_case.execute()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(settings).encode("utf-8"))
                return

            # 1.38 API: Descargar archivo de video
            elif url_parsed.path == "/api/camera/recordings/download":
                query_params = parse_qs(url_parsed.query)
                filename = query_params.get("file", [None])[0]
                if not filename or ".." in filename or "/" in filename:
                    self.send_error(400, "Nombre de archivo invalido")
                    return
                
                # API: Webhook para GitHub
            elif url_parsed.path == "/api/cicd/github/webhook":
                if not webhook_use_case:
                    self.send_error(501, "Módulo de webhooks no habilitado")
                    return
                # handled by do_POST
                pass

            # API: Obtener ramas de un repositorio git remoto
            elif url_parsed.path == "/api/cicd/git/branches":
                query_params = parse_qs(url_parsed.query)
                repo_url = query_params.get("repo_url", [None])[0]
                
                if not repo_url:
                    self._send_json({"status": "error", "message": "Falta la URL del repositorio"}, 400)
                    return
                    
                if not get_git_branches_use_case:
                    self._send_json({"status": "error", "message": "Caso de uso no inyectado"}, 500)
                    return
                    
                success, data = get_git_branches_use_case.execute(repo_url)
                if success:
                    self._send_json({"status": "success", "branches": data})
                else:
                    self._send_json({"status": "error", "message": data}, 400)
                return

            elif url_parsed.path == "/api/camera/recordings/download":
                filepath = os.path.join("./recordings", filename)
                if not os.path.exists(filepath):
                    self.send_error(404, "Archivo no encontrado")
                    return
                
                self.send_response(200)
                self.send_header("Content-Type", "video/x-msvideo")
                self.send_header("Content-Disposition", f"attachment; filename={filename}")
                self.send_header("Content-Length", str(os.path.getsize(filepath)))
                self.end_headers()
                
                try:
                    with open(filepath, "rb") as f:
                        self.wfile.write(f.read())
                except Exception:
                    pass
            # 1.39 API: Obtener configuración de CI/CD
            elif url_parsed.path == "/api/cicd/config":
                from src.adapters.outbound.cicd_config import get_cicd_config
                cfg = get_cicd_config()
                masked = {
                    "git_token": "********" if cfg.get("git_token") else "",
                    "webhook_secret": "********" if cfg.get("webhook_secret") else "",
                    "telegram_token": "********" if cfg.get("telegram_token") else "",
                    "telegram_chat_id": cfg.get("telegram_chat_id", "")
                }
                self._send_json(masked)
                return

            # 1.39 API: Obtener logs de despliegue en tiempo real
            elif url_parsed.path == "/api/cicd/deploy/status":
                query_params = parse_qs(url_parsed.query)
                app_name = query_params.get("app_name", [None])[0]
                if app_name:
                    status = get_deploy_status_use_case.execute(app_name)
                    self._send_json(status)
                else:
                    self.send_error(400, "Falta el nombre de la app")
                return

            # 1.395 API: Listar todos los despliegues activos y pasados
            elif url_parsed.path == "/api/cicd/deployments":
                status = list_deployments_use_case.execute()
                self._send_json(status)
                return

            # 1.4 API: Clientes de red conectados
            elif url_parsed.path == "/api/network/clients":
                clients = get_wifi_clients_use_case.execute()
                self._send_json([c.to_dict() for c in clients])
                return

            # 2. Servir la interfaz gráfica principal
            elif url_parsed.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
                return

            self.send_error(404, "Recurso no encontrado")

        def do_POST(self):
            url_parsed = urlparse(self.path)
            content_length = int(self.headers['Content-Length'])
            post_data_bytes = self.rfile.read(content_length)
            post_data = post_data_bytes.decode('utf-8', errors='ignore')
            
            # --- NUEVA API: Webhooks de CI/CD (GitHub / GitLab) ---
            if url_parsed.path.startswith("/api/webhooks/"):
                provider = url_parsed.path.split("/")[-1]
                # Inyectar el handler de webhook usando los headers reales y los raw bytes
                from src.application.use_cases.cicd_use_cases import HandleWebhookUseCase
                success, msg = webhook_use_case.execute(provider, dict(self.headers), post_data_bytes)
                self.send_response(200 if success else 400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success" if success else "error", "message": msg}).encode("utf-8"))
                return
                
            try:
                params = json.loads(post_data)
            except Exception:
                params = {}

            # --- API POST: Login ---
            if url_parsed.path == "/api/login":
                username = params.get("username", "")
                password = params.get("password", "")
                if authenticate_pam(username, password):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Set-Cookie", f"session_token={SESSION_TOKEN}; Path=/; HttpOnly")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "message": "Autenticación exitosa"}).encode("utf-8"))
                else:
                    self._send_json({"status": "error", "message": "Usuario o contraseña inválidos"}, 401)
                return

            # Si no está autenticado, denegar acceso a otras acciones POST
            if not self.is_authenticated():
                self._send_json({"status": "error", "message": "No autorizado (Inicia sesión)"}, 401)
                return

            response_data = {"status": "error", "message": "Acción no reconocida"}

            # --- API POST: Guardar configuración de CI/CD ---
            if url_parsed.path == "/api/cicd/config":
                from src.adapters.outbound.cicd_config import get_cicd_config, save_cicd_config
                current = get_cicd_config()
                
                git_token = params.get("git_token", "")
                webhook_secret = params.get("webhook_secret", "")
                telegram_token = params.get("telegram_token", "")
                telegram_chat_id = params.get("telegram_chat_id", "")
                
                new_cfg = {}
                new_cfg["git_token"] = current.get("git_token", "") if git_token == "********" else git_token
                new_cfg["webhook_secret"] = current.get("webhook_secret", "") if webhook_secret == "********" else webhook_secret
                new_cfg["telegram_token"] = current.get("telegram_token", "") if telegram_token == "********" else telegram_token
                new_cfg["telegram_chat_id"] = telegram_chat_id
                
                success = save_cicd_config(new_cfg)
                response_data = {"status": "success" if success else "error", "message": "Configuración guardada con éxito." if success else "Error guardando configuración."}
                self._send_json(response_data)
                return

            # --- API POST: Registrar Webhook de GitHub ---
            elif url_parsed.path == "/api/cicd/github/webhook/create":
                from src.adapters.outbound.cicd_config import get_cicd_config
                cfg = get_cicd_config()
                
                owner = params.get("owner", "")
                repo = params.get("repo", "")
                public_url = params.get("public_url", "")
                
                token = cfg.get("git_token", "")
                secret = cfg.get("webhook_secret", "")
                
                if not owner or not repo or not public_url:
                    self._send_json({"status": "error", "message": "Faltan parámetros requeridos: owner, repo o public_url"}, 400)
                    return
                    
                if not token:
                    self._send_json({"status": "error", "message": "Token de Git no configurado. Configúralo en Ajustes."}, 400)
                    return
                    
                success, msg = webhook_use_case.cicd_manager.git.create_github_webhook(
                    owner, repo, public_url, secret, token
                )
                self._send_json({"status": "success" if success else "error", "message": msg})
                return

            # 1. API POST: Alternar la Interfaz de Escritorio (Desktop)
            if url_parsed.path == "/api/gui/toggle":
                action = params.get("action", "")
                success, msg = gui_use_case.execute(action)
                response_data = {"status": "success" if success else "error", "message": msg}

            # 2. API POST: Controlar Contenedores Docker (Start/Stop/Restart/Remove)
            elif url_parsed.path == "/api/docker/control":
                container_id = params.get("id")
                action = params.get("action")
                if container_id and action:
                    success, msg = docker_use_case.execute(container_id, action)
                    response_data = {"status": "success" if success else "error", "message": msg}

            # 3. API POST: CI/CD Desplegar Repositorio Git
            elif url_parsed.path == "/api/cicd/deploy":
                repo_url = params.get("repo_url")
                target_dir = params.get("target_dir")
                app_name = params.get("app_name", "mi-proyecto-web")
                
                if repo_url:
                    # Tarea: registrar webhook automáticamente en GitHub si está el token configurado
                    try:
                        from src.adapters.outbound.cicd_config import get_cicd_config
                        cfg = get_cicd_config()
                        token = cfg.get("git_token")
                        secret = cfg.get("webhook_secret")
                        
                        if token:
                            clean_url = repo_url.strip()
                            if clean_url.endswith(".git"):
                                clean_url = clean_url[:-4]
                            
                            owner, repo = None, None
                            if "github.com/" in clean_url:
                                parts = clean_url.split("github.com/")[-1].split("/")
                                if len(parts) >= 2:
                                    owner, repo = parts[0], parts[1]
                            elif "github.com:" in clean_url:
                                parts = clean_url.split("github.com:")[-1].split("/")
                                if len(parts) >= 2:
                                    owner, repo = parts[0], parts[1]
                                    
                            if owner and repo:
                                host_header = self.headers.get("Host", "")
                                if host_header:
                                    public_url = f"http://{host_header}"
                                    import threading
                                    threading.Thread(
                                        target=webhook_use_case.cicd_manager.git.create_github_webhook,
                                        args=(owner, repo, public_url, secret, token),
                                        daemon=True
                                    ).start()
                                    print(f"[CI/CD] Disparado registro automático de Webhook para {owner}/{repo} en {public_url}")
                    except Exception as e:
                        print(f"[CI/CD] Error intentando registrar webhook automático: {e}")

                    res = deploy_use_case.execute(repo_url, target_dir, app_name, branch=params.get("branch", "main"))
                    response_data = res.to_dict()
                else:
                    response_data = {"status": "error", "message": "Falta la URL del repositorio de Git."}

            # 3.5 API POST: CI/CD Cancelar Despliegue Activo
            elif url_parsed.path == "/api/cicd/deploy/cancel":
                app_name = params.get("app_name")
                if app_name:
                    success, msg = cancel_deploy_use_case.execute(app_name)
                    response_data = {"status": "success" if success else "error", "message": msg}
                else:
                    response_data = {"status": "error", "message": "Falta el nombre de la app a cancelar."}

            # 4. API POST: Iniciar grabación de cámara
            elif url_parsed.path == "/api/camera/record/start":
                camera_id = params.get("id")
                if camera_id:
                    success, msg = start_recording_use_case.execute(camera_id)
                    response_data = {"status": "success" if success else "error", "message": msg}
                else:
                    response_data = {"status": "error", "message": "Falta el ID de la camara"}

            # 5. API POST: Detener grabación de cámara
            elif url_parsed.path == "/api/camera/record/stop":
                camera_id = params.get("id")
                if camera_id:
                    success, msg = stop_recording_use_case.execute(camera_id)
                    response_data = {"status": "success" if success else "error", "message": msg}
                else:
                    response_data = {"status": "error", "message": "Falta el ID de la camara"}

            # 6. API POST: Actualizar ajustes de visión artificial (rostro/manos)
            elif url_parsed.path == "/api/camera/vision/settings":
                face_enabled = params.get("face_enabled") == "true" or params.get("face_enabled") is True
                hand_enabled = params.get("hand_enabled") == "true" or params.get("hand_enabled") is True
                success, msg = update_vision_settings_use_case.execute(face_enabled, hand_enabled)
                response_data = {"status": "success" if success else "error", "message": msg}

            # 7. API POST: Guardar alias de cliente de red
            elif url_parsed.path == "/api/network/alias":
                mac = params.get("mac")
                alias = params.get("alias")
                if mac and alias is not None:
                    success, msg = save_client_alias_use_case.execute(mac, alias)
                    response_data = {"status": "success" if success else "error", "message": msg}
                else:
                    response_data = {"status": "error", "message": "Faltan parametros mac o alias"}

            self._send_json(response_data)

    return DashboardRequestHandler


class WebServer:
    def __init__(
        self,
        port: int,
        status_use_case: GetSystemStatusUseCase,
        gui_use_case: ToggleGuiUseCase,
        docker_use_case: ControlDockerContainerUseCase,
        docker_logs_use_case: GetDockerContainerLogsUseCase,
        deploy_use_case: DeployAppUseCase,
        get_deploy_status_use_case: GetDeployStatusUseCase,
        list_deployments_use_case: ListDeploymentsUseCase,
        cancel_deploy_use_case: CancelDeploymentUseCase,
        get_cameras_use_case: GetCamerasUseCase,
        capture_frame_use_case: CaptureCameraFrameUseCase,
        get_wifi_clients_use_case: GetWifiClientsUseCase,
        start_recording_use_case: StartRecordingUseCase,
        stop_recording_use_case: StopRecordingUseCase,
        get_recording_status_use_case: GetRecordingStatusUseCase,
        list_recordings_use_case: ListRecordingsUseCase,
        get_vision_settings_use_case: GetVisionSettingsUseCase,
        update_vision_settings_use_case: UpdateVisionSettingsUseCase,
        save_client_alias_use_case: SaveClientAliasUseCase,
        webhook_use_case=None,
        get_git_branches_use_case=None
    ):
        self.port = port
        self.handler_class = create_handler_class(
            status_use_case,
            gui_use_case,
            docker_use_case,
            docker_logs_use_case,
            deploy_use_case,
            get_deploy_status_use_case,
            list_deployments_use_case,
            cancel_deploy_use_case,
            get_cameras_use_case,
            capture_frame_use_case,
            get_wifi_clients_use_case,
            start_recording_use_case,
            stop_recording_use_case,
            get_recording_status_use_case,
            list_recordings_use_case,
            get_vision_settings_use_case,
            update_vision_settings_use_case,
            save_client_alias_use_case,
            webhook_use_case,
            get_git_branches_use_case
        )

    def start(self):
        import socket
        local_ip = "localhost"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        with socketserver.ThreadingTCPServer(("", self.port), self.handler_class) as httpd:
            print(f"==========================================================")
            print(f"🚀 ¡CENTRO DE CONTROL RASPBERRY PI 3 B+ INICIADO!")
            print(f"👉 Local:   http://localhost:{self.port}")
            print(f"👉 En Red:  http://{local_ip}:{self.port}")
            print(f"==========================================================")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServidor detenido por el usuario.")
