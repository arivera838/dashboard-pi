import os
import sys

# Asegurar que el directorio raíz está en el path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.adapters.outbound.system_metrics import LinuxSystemMetricsRepository
from src.adapters.outbound.systemd_gui import SystemdGuiController
from src.adapters.outbound.docker_cli import CliDockerController
from src.adapters.outbound.git_deployer import SubprocessDeployer
from src.adapters.outbound.subprocess_camera import SubprocessCameraAdapter
from src.adapters.outbound.linux_network import LinuxNetworkAdapter

from src.application.services import (
    SystemStatusService,
    GuiService,
    DockerService,
    DockerLogsService,
    DeploymentService,
    GetCamerasService,
    CaptureCameraFrameService,
    GetWifiClientsService
)
from src.adapters.inbound.web_server import WebServer

PORT = 8080

def main():
    # 1. Instanciar adaptadores de salida (infraestructura)
    metrics_repo = LinuxSystemMetricsRepository()
    gui_controller = SystemdGuiController()
    docker_controller = CliDockerController()
    deployer = SubprocessDeployer()
    camera_adapter = SubprocessCameraAdapter()
    network_adapter = LinuxNetworkAdapter()

    # 2. Instanciar servicios de aplicación (casos de uso) inyectando adaptadores de salida
    status_service = SystemStatusService(metrics_repo, gui_controller, docker_controller)
    gui_service = GuiService(gui_controller)
    docker_service = DockerService(docker_controller)
    docker_logs_service = DockerLogsService(docker_controller)
    deploy_service = DeploymentService(deployer)
    get_cameras_service = GetCamerasService(camera_adapter)
    capture_frame_service = CaptureCameraFrameService(camera_adapter)
    get_wifi_clients_service = GetWifiClientsService(network_adapter)

    # 3. Instanciar y arrancar adaptador de entrada (servidor web) inyectando los casos de uso
    server = WebServer(
        port=PORT,
        status_use_case=status_service,
        gui_use_case=gui_service,
        docker_use_case=docker_service,
        docker_logs_use_case=docker_logs_service,
        deploy_use_case=deploy_service,
        get_cameras_use_case=get_cameras_service,
        capture_frame_use_case=capture_frame_service,
        get_wifi_clients_use_case=get_wifi_clients_service
    )

    server.start()

if __name__ == "__main__":
    main()