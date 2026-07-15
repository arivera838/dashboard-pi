import subprocess
from typing import List
from src.domain.models import DockerContainer
from src.application.ports.outputs import DockerControllerPort

class CliDockerController(DockerControllerPort):
    def list_containers(self) -> List[DockerContainer]:
        containers = []
        try:
            res = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}"],
                capture_output=True, text=True
            )
            lines = res.stdout.strip().split("\n")
            for line in lines:
                if "|" in line:
                    cid, name, status, img = line.split("|")
                    is_running = "Up" in status
                    containers.append(DockerContainer(
                        id=cid,
                        name=name,
                        status=status,
                        image=img,
                        running=is_running
                    ))
        except Exception as e:
            print(f"Error al listar Docker: {e}")
        return containers

    def control_container(self, container_id: str, action: str) -> tuple[bool, str]:
        if action not in ["start", "stop", "restart", "remove"]:
            return False, "Acción inválida"
        try:
            cmd = ["docker", "rm", "-f", container_id] if action == "remove" else ["docker", action, container_id]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                action_msg = "eliminado" if action == "remove" else f"{action}eado"
                return True, f"Contenedor {action_msg} con éxito."
            else:
                return False, res.stderr.strip()
        except Exception as e:
            return False, str(e)

    def get_container_logs(self, container_id: str) -> tuple[bool, str]:
        try:
            res = subprocess.run(["docker", "logs", "--tail", "200", container_id], capture_output=True, text=True)
            logs = res.stdout + res.stderr
            return True, logs
        except Exception as e:
            return False, str(e)
