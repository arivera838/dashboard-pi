import os
import subprocess
import threading
import time
from typing import Dict
from src.application.ports.outputs import DeployerPort

class SubprocessDeployer(DeployerPort):
    # Diccionario en memoria para almacenar logs en tiempo real por app_name
    _active_logs: Dict[str, Dict] = {}
    # Diccionario de procesos activos de Git/Docker para cancelación
    _active_processes: Dict[str, subprocess.Popen] = {}

    def deploy(self, repo_url: str, target_dir: str | None, app_name: str, branch: str = "main") -> tuple[bool, str]:
        # Si ya hay un proceso en ejecución para este app_name, no iniciar otro
        if app_name in self._active_logs and self._active_logs[app_name]["status"] == "running":
            return False, "Ya hay un despliegue en curso para esta aplicación."

        # Iniciar hilo de despliegue
        t = threading.Thread(
            target=self._run_deploy_thread,
            args=(repo_url, target_dir, app_name, branch),
            daemon=True
        )
        t.start()
        return True, "Despliegue iniciado correctamente."

    def get_deploy_status(self, app_name: str) -> dict:
        if app_name not in self._active_logs:
            return {"status": "idle", "log": "Esperando inicio..."}
        status = dict(self._active_logs[app_name])
        start_time = status.get("start_time")
        if start_time:
            end_time = status.get("end_time") or time.time()
            status["elapsed_seconds"] = int(end_time - start_time)
        return status

    def get_all_deployments(self) -> dict:
        copy_logs = {}
        for app, data in self._active_logs.items():
            app_data = dict(data)
            start_time = app_data.get("start_time")
            if start_time:
                end_time = app_data.get("end_time") or time.time()
                app_data["elapsed_seconds"] = int(end_time - start_time)
            copy_logs[app] = app_data
        return copy_logs

    def cancel_deploy(self, app_name: str) -> tuple[bool, str]:
        process = self._active_processes.get(app_name)
        if process:
            try:
                process.terminate()
                process.kill()
                self._active_processes.pop(app_name, None)
                if app_name in self._active_logs:
                    self._active_logs[app_name]["status"] = "error"
                    self._active_logs[app_name]["log"] += "\n❌ [CI/CD] Despliegue cancelado por el usuario.\n"
                    self._active_logs[app_name]["end_time"] = time.time()
                return True, "Despliegue cancelado con éxito."
            except Exception as e:
                return False, f"Error al cancelar: {e}"
        return False, "No hay ningún despliegue activo para esta aplicación."

    def _run_deploy_thread(self, repo_url: str, target_dir: str | None, app_name: str, branch: str = "main"):
        self._active_logs[app_name] = {
            "status": "running",
            "log": "🚀 [CI/CD] Iniciando pipeline de despliegue...\n",
            "start_time": time.time(),
            "end_time": None
        }

        try:
            # 1. Asegurar ruta destino limpia
            # Resolver la ruta de home del usuario real (evita usar /home/frivera o /root bajo sudo)
            sudo_user = os.environ.get("SUDO_USER")
            if sudo_user and sudo_user != "root":
                home_dir = f"/home/{sudo_user}"
            else:
                home_dir = os.path.expanduser("~")
                
            base_path = os.path.join(home_dir, "apps", app_name)
            if target_dir:
                base_path = os.path.abspath(target_dir)

            # 2. Clonar o realizar Pull
            if not os.path.exists(base_path):
                self._active_logs[app_name]["log"] += f"📂 [Git] Clonando repositorio (rama {branch}) en {base_path}...\n"
                cmd = f"git clone -b {branch} {repo_url} {base_path}"
            else:
                self._active_logs[app_name]["log"] += f"📂 [Git] Proyecto existente en {base_path}. Haciendo checkout a {branch} y pull...\n"
                cmd = f"cd {base_path} && git reset --hard && git fetch origin && git checkout {branch} && git pull origin {branch}"

            # Ejecución asíncrona de Git capturando la salida en vivo
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self._active_processes[app_name] = process
            
            # Leer en vivo stdout/stderr
            for line in process.stdout:
                self._active_logs[app_name]["log"] += line
            process.wait()
            self._active_processes.pop(app_name, None)

            if process.returncode != 0:
                self._active_logs[app_name]["status"] = "error"
                self._active_logs[app_name]["log"] += "\n❌ [ERROR] Falló el paso de Git o Checkout de rama. Despliegue abortado.\n"
                return

            # 3. Detectar docker-compose y desplegar
            compose_file = os.path.join(base_path, "docker-compose.yml")
            if os.path.exists(compose_file):
                self._active_logs[app_name]["log"] += "\n🐳 [Docker] Detectado docker-compose.yml, construyendo e iniciando contenedores en segundo plano...\n"
                
                # Generar override de Traefik dinámicamente
                subdomain = f"{app_name}.local" if branch == "main" else f"{branch}.{app_name}.local"
                project_name = f"{app_name}-{branch}"
                
                override_content = f"""
services:
  app:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{project_name}.rule=Host(`{subdomain}`)"
    networks:
      - web

networks:
  web:
    external: true
    name: web
"""
                override_path = os.path.join(base_path, "docker-compose.override.yml")
                try:
                    with open(override_path, "w") as f:
                        f.write(override_content)
                    self._active_logs[app_name]["log"] += f"📝 [Traefik] Generado docker-compose.override.yml para dominio: {subdomain}\n"
                    # Asegurar red web
                    subprocess.run(["docker", "network", "create", "web"], capture_output=True)
                except Exception as e:
                    self._active_logs[app_name]["log"] += f"⚠️ [Traefik] Error generando override: {e}\n"
                
                # docker compose -p {project_name} up -d --build
                docker_cmd = f"cd {base_path} && docker compose -p {project_name} up -d --build"
                
                process = subprocess.Popen(
                    docker_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                self._active_processes[app_name] = process
                
                for line in process.stdout:
                    self._active_logs[app_name]["log"] += line
                process.wait()
                self._active_processes.pop(app_name, None)

                if process.returncode != 0:
                    self._active_logs[app_name]["status"] = "error"
                    self._active_logs[app_name]["log"] += "\n❌ [ERROR] Falló la compilación o levantamiento con Docker Compose.\n"
                    return
                
                self._active_logs[app_name]["log"] += "\n🚀 [CI/CD] ¡Despliegue completado con éxito! Los servicios de Docker están corriendo.\n"
            else:
                self._active_logs[app_name]["log"] += "\n⚠️ [Advertencia] No se encontró un archivo docker-compose.yml. Repositorio descargado, pero no se inició ningún contenedor.\n"

            self._active_logs[app_name]["status"] = "success"

        except Exception as e:
            self._active_logs[app_name]["status"] = "error"
            self._active_logs[app_name]["log"] += f"\n❌ [ERROR CRÍTICO] Excepción ocurrida: {str(e)}\n"
        finally:
            self._active_logs[app_name]["end_time"] = time.time()
