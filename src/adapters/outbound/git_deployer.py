import os
import subprocess
from src.application.ports.outputs import DeployerPort

class SubprocessDeployer(DeployerPort):
    def deploy(self, repo_url: str, target_dir: str | None, app_name: str, app_port: str | None) -> tuple[bool, str]:
        try:
            # 1. Asegurar ruta destino limpia
            base_path = os.path.expanduser(f"~/apps/{app_name}")
            if target_dir:
                base_path = os.path.abspath(target_dir)

            # 2. Clonar o Pull del Repositorio
            if not os.path.exists(base_path):
                os.makedirs(os.path.dirname(base_path), exist_ok=True)
                cmd = f"git clone {repo_url} {base_path}"
            else:
                cmd = f"cd {base_path} && git reset --hard && git pull"

            # Ejecución del comando de Git
            git_res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if git_res.returncode != 0:
                return False, f"Error Git: {git_res.stderr}"

            # 3. Detectar docker-compose y desplegar
            compose_file = os.path.join(base_path, "docker-compose.yml")
            deploy_log = "Repositorio descargado con éxito.\n"
            if os.path.exists(compose_file):
                deploy_log += "Detectado docker-compose.yml, levantando servicios...\n"
                env_prefix = f"PORT={app_port} " if app_port else ""
                docker_cmd = f"cd {base_path} && {env_prefix}docker compose up -d --build"
                dock_res = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
                deploy_log += dock_res.stdout + "\n" + dock_res.stderr
                if dock_res.returncode != 0:
                    return False, deploy_log

            return True, deploy_log
        except Exception as e:
            return False, str(e)
