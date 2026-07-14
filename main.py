import os
import sys

# Asegurar que el directorio raíz está en el path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.adapters.outbound.system_metrics import LinuxSystemMetricsRepository
from src.adapters.outbound.systemd_gui import SystemdGuiController
from src.adapters.outbound.docker_cli import CliDockerController
from src.adapters.outbound.git_deployer import SubprocessDeployer

from src.application.services import SystemStatusService, GuiService, DockerService, DeploymentService
from src.adapters.inbound.web_server import WebServer

PORT = 8080

def main():
    # 1. Instanciar adaptadores de salida (infraestructura)
    metrics_repo = LinuxSystemMetricsRepository()
    gui_controller = SystemdGuiController()
    docker_controller = CliDockerController()
    deployer = SubprocessDeployer()

    # 2. Instanciar servicios de aplicación (casos de uso) inyectando adaptadores de salida
    status_service = SystemStatusService(metrics_repo, gui_controller, docker_controller)
    gui_service = GuiService(gui_controller)
    docker_service = DockerService(docker_controller)
    deploy_service = DeploymentService(deployer)

    # 3. Instanciar y arrancar adaptador de entrada (servidor web) inyectando los casos de uso
    server = WebServer(
        port=PORT,
        status_use_case=status_service,
        gui_use_case=gui_service,
        docker_use_case=docker_service,
        deploy_use_case=deploy_service
    )

    server.start()

if __name__ == "__main__":
    main()