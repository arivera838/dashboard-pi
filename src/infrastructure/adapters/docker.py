# -*- coding: utf-8 -*-
import subprocess
from src.domain.models import DockerContainer
from src.domain.ports import DockerManagerPort

class SubprocessDockerAdapter(DockerManagerPort):
    """Adaptador de infraestructura que gestiona Docker mediante comandos del sistema (CLI)."""

    def list_containers(self) -> list:
        containers = []
        try:
            # Listar todos los contenedores con formato tabulado
            cmd = ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.State}}"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = res.stdout.strip().split("\n")
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) >= 5:
                    c_id, name, image, status, state = parts[:5]
                    containers.append(DockerContainer(
                        id=c_id,
                        name=name,
                        image=image,
                        status=status,
                        state=state
                    ))
        except Exception as e:
            print(f"Error al listar contenedores Docker: {e}")
            return []
        return containers

    def _execute_command(self, cmd: list) -> bool:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Error al ejecutar comando Docker {' '.join(cmd)}: {e}")
            return False

    def pause_container(self, container_id: str) -> bool:
        return self._execute_command(["docker", "pause", container_id])

    def unpause_container(self, container_id: str) -> bool:
        return self._execute_command(["docker", "unpause", container_id])

    def restart_container(self, container_id: str) -> bool:
        return self._execute_command(["docker", "restart", container_id])

    def get_container_logs(self, container_id: str) -> str:
        try:
            # Obtener las últimas 100 líneas de logs
            cmd = ["docker", "logs", "--tail", "100", container_id]
            res = subprocess.run(cmd, capture_output=True, text=True)
            # Los logs de docker a veces se escriben en stderr, unimos ambos
            return (res.stdout or "") + (res.stderr or "")
        except Exception as e:
            return f"Error al recuperar logs del contenedor {container_id}: {str(e)}"
