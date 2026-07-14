# -*- coding: utf-8 -*-
import os
import http.server
import json
import subprocess
import time
from urllib.parse import urlparse

class HexagonalHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Controlador que traduce las peticiones HTTP externas en llamadas a los Casos de Uso."""
    
    # Se inyectarán externamente desde main.py
    app_orchestrator = None
    camera_service = None

    # Suprimir logs por consola de peticiones exitosas para no saturar la CPU
    def log_message(self, format, *args):
        if len(args) > 0 and ("api/camera/stream" in args[0] or "api/status" in args[0]):
            return
        super().log_message(format, *args)

    def do_GET(self):
        url_parsed = urlparse(self.path)
        
        # 1. API: Servir Video en Tiempo Real usando el protocolo MJPEG (Stream continuo)
        if url_parsed.path == "/api/camera/stream":
            if not self.camera_service:
                self.send_error(503, "Servicio de cámara no configurado")
                return

            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            
            try:
                while True:
                    frame_bytes = self.camera_service.get_frame()
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame_bytes)))
                    self.end_headers()
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b'\r\n')
                    # Equilibrar entre FPS y consumo de CPU para la Raspberry Pi 3 B+
                    time.sleep(0.08)
            except (ConnectionResetError, BrokenPipeError):
                # El usuario simplemente cerró la pestaña del navegador
                return
            except Exception as e:
                print(f"Error en el stream de vídeo: {e}")
                return

        # 2. API: Consultar Estado y Métricas (JSON)
        elif url_parsed.path == "/api/status":
            if not self.app_orchestrator:
                self.send_error(503, "Orquestador de aplicación no configurado")
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            state = self.app_orchestrator.get_system_status()
            self.wfile.write(json.dumps(state).encode("utf-8"))
            return

        # 3. Interfaz Gráfica de usuario principal (HTML)
        elif url_parsed.path == "/":
            try:
                template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
                with open(template_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Error al cargar la interfaz de usuario: {e}")
            return

        # Fallback 404
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

        response_data = {"status": "error", "message": "Operación no reconocida"}

        # 1. API POST: Alternar Escritorio local (VNC/lightdm)
        if url_parsed.path == "/api/gui/toggle":
            action = params.get("action")
            if action == "start":
                subprocess.run(["sudo", "systemctl", "start", "lightdm"])
                response_data = {"status": "success", "message": "Interfaz gráfica iniciada de forma segura."}
            elif action == "stop":
                subprocess.run(["sudo", "systemctl", "stop", "lightdm"])
                response_data = {"status": "success", "message": "Escritorio apagado. RAM liberada correctamente."}

        # 2. API POST: CI/CD Pipeline
        elif url_parsed.path == "/api/cicd/deploy":
            repo_url = params.get("repo_url")
            target_dir = params.get("target_dir")
            app_name = params.get("app_name", "web-app")
            
            # Ejecutar el proceso de despliegue coordinado en segundo plano
            success, log_output = self._run_deployment(repo_url, target_dir, app_name)
            if success:
                response_data = {"status": "success", "message": "¡Despliegue exitoso!", "log": log_output}
            else:
                response_data = {"status": "error", "message": "Error al compilar el proyecto.", "log": log_output}

        self.wfile.write(json.dumps(response_data).encode("utf-8"))

    def _run_deployment(self, repo_url, target_dir, app_name) -> tuple:
        """Rutina automatizada de clonación, construcción e inicio de Docker."""
        try:
            base_path = os.path.expanduser(f"~/apps/{app_name}")
            if target_dir:
                base_path = os.path.abspath(target_dir)

            if not os.path.exists(base_path):
                os.makedirs(os.path.dirname(base_path), exist_ok=True)
                cmd = f"git clone {repo_url} {base_path}"
            else:
                cmd = f"cd {base_path} && git reset --hard && git pull"

            git_res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if git_res.returncode != 0:
                return False, f"Error Git: {git_res.stderr}"

            compose_file = os.path.join(base_path, "docker-compose.yml")
            deploy_log = "Repositorio descargado correctamente.\n"
            if os.path.exists(compose_file):
                deploy_log += "Detectado docker-compose.yml. Levantando con Docker...\n"
                docker_cmd = f"cd {base_path} && docker compose up -d --build"
                dock_res = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
                deploy_log += dock_res.stdout + "\n" + dock_res.stderr
                if dock_res.returncode != 0:
                    return False, deploy_log

            return True, deploy_log
        except Exception as e:
            return False, str(e)
