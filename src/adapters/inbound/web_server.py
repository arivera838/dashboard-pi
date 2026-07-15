import http.server
import json
import socketserver
from urllib.parse import urlparse, parse_qs
from src.adapters.inbound.templates import HTML_TEMPLATE
from src.application.ports.inputs import (
    GetSystemStatusUseCase,
    ToggleGuiUseCase,
    ControlDockerContainerUseCase,
    GetDockerContainerLogsUseCase,
    DeployAppUseCase,
    GetCamerasUseCase,
    CaptureCameraFrameUseCase,
    GetWifiClientsUseCase
)

def create_handler_class(
    status_use_case: GetSystemStatusUseCase,
    gui_use_case: ToggleGuiUseCase,
    docker_use_case: ControlDockerContainerUseCase,
    docker_logs_use_case: GetDockerContainerLogsUseCase,
    deploy_use_case: DeployAppUseCase,
    get_cameras_use_case: GetCamerasUseCase,
    capture_frame_use_case: CaptureCameraFrameUseCase,
    get_wifi_clients_use_case: GetWifiClientsUseCase
):
    class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            url_parsed = urlparse(self.path)
            
            # 1. API: Obtener Métricas de Sistema (JSON)
            if url_parsed.path == "/api/status":
                status = status_use_case.execute()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(status.to_dict()).encode("utf-8"))
                return

            # 1.1 API: Obtener Logs de Contenedor Docker (JSON)
            elif url_parsed.path == "/api/docker/logs":
                query_params = parse_qs(url_parsed.query)
                container_id = query_params.get("id", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                if container_id:
                    success, logs = docker_logs_use_case.execute(container_id)
                    response_data = {"status": "success" if success else "error", "logs": logs}
                else:
                    response_data = {"status": "error", "message": "Falta el ID del contenedor"}
                    
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                return

            # 1.2 API: Obtener lista de cámaras
            elif url_parsed.path == "/api/camera/list":
                cameras = get_cameras_use_case.execute()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps([c.to_dict() for c in cameras]).encode("utf-8"))
                return

            # 1.3 API: Capturar frame de cámara (Retorna imagen directa)
            elif url_parsed.path == "/api/camera/frame":
                query_params = parse_qs(url_parsed.query)
                camera_id = query_params.get("id", [None])[0]
                
                if camera_id:
                    frame_bytes = capture_frame_use_case.execute(camera_id)
                    self.send_response(200)
                    
                    # Detectar si es PNG o JPEG a partir de los bytes mágicos
                    if frame_bytes.startswith(b'\x89PNG'):
                        self.send_header("Content-Type", "image/png")
                    else:
                        self.send_header("Content-Type", "image/jpeg")
                        
                    self.end_headers()
                    self.wfile.write(frame_bytes)
                else:
                    self.send_error(400, "Falta el ID de la camara")
                return

            # 1.4 API: Clientes de red conectados
            elif url_parsed.path == "/api/network/clients":
                clients = get_wifi_clients_use_case.execute()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps([c.to_dict() for c in clients]).encode("utf-8"))
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
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                params = json.loads(post_data)
            except Exception:
                params = {}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response_data = {"status": "error", "message": "Acción no reconocida"}

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
                    res = deploy_use_case.execute(repo_url, target_dir, app_name)
                    response_data = res.to_dict()
                else:
                    response_data = {"status": "error", "message": "Falta la URL del repositorio de Git."}

            self.wfile.write(json.dumps(response_data).encode("utf-8"))

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
        get_cameras_use_case: GetCamerasUseCase,
        capture_frame_use_case: CaptureCameraFrameUseCase,
        get_wifi_clients_use_case: GetWifiClientsUseCase
    ):
        self.port = port
        self.handler_class = create_handler_class(
            status_use_case,
            gui_use_case,
            docker_use_case,
            docker_logs_use_case,
            deploy_use_case,
            get_cameras_use_case,
            capture_frame_use_case,
            get_wifi_clients_use_case
        )

    def start(self):
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", self.port), self.handler_class) as httpd:
            print(f"==========================================================")
            print(f"🚀 ¡CENTRO DE CONTROL RASPBERRY PI 3 B+ INICIADO!")
            print(f"👉 Accede desde tu red en: http://localhost:{self.port}")
            print(f"==========================================================")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServidor detenido por el usuario.")
