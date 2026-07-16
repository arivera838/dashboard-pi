import os
import subprocess
import threading
import time
from typing import Dict
from src.application.ports.outputs import DeployerPort

class SubprocessDeployer(DeployerPort):
    # Diccionario en memoria para almacenar logs en tiempo real por app_name
    _active_logs: Dict[str, Dict] = {}

    def deploy(self, repo_url: str, target_dir: str | None, app_name: str) -> tuple[bool, str]:
        # Si ya hay un proceso en ejecución para este app_name, no iniciar otro
        if app_name in self._active_logs and self._active_logs[app_name]["status"] == "running":
            return False, "Ya hay un despliegue en curso para esta aplicación."

        # Iniciar hilo de despliegue
        t = threading.Thread(
            target=self._run_deploy_thread,
            args=(repo_url, target_dir, app_name),
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

    def _run_deploy_thread(self, repo_url: str, target_dir: str | None, app_name: str):
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
                self._active_logs[app_name]["log"] += f"📂 [Git] Clonando repositorio en {base_path}...\n"
                cmd = f"git clone {repo_url} {base_path}"
            else:
                self._active_logs[app_name]["log"] += f"📂 [Git] Proyecto existente encontrado. Limpiando y haciendo git pull...\n"
                cmd = f"cd {base_path} && git reset --hard && git pull"

            # Ejecución asíncrona de Git capturando la salida en vivo
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Leer en vivo stdout/stderr
            for line in process.stdout:
                self._active_logs[app_name]["log"] += line
            process.wait()

            if process.returncode != 0:
                self._active_logs[app_name]["status"] = "error"
                self._active_logs[app_name]["log"] += "\n❌ [ERROR] Falló el paso de Git. Despliegue abortado.\n"
                return

            # 3. Detectar docker-compose y desplegar
            compose_file = os.path.join(base_path, "docker-compose.yml")
            if os.path.exists(compose_file):
                self._active_logs[app_name]["log"] += "\n🐳 [Docker] Detectado docker-compose.yml, construyendo e iniciando contenedores en segundo plano...\n"
                # docker compose up -d --build (el puerto se gestiona directamente en el docker-compose.yml del proyecto)
                docker_cmd = f"cd {base_path} && docker compose up -d --build"
                
                process = subprocess.Popen(
                    docker_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                for line in process.stdout:
                    self._active_logs[app_name]["log"] += line
                process.wait()

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
