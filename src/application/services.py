from typing import List
from src.domain.models import SystemStatus, DeploymentResult, CameraInfo, WifiClient
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
from src.application.ports.outputs import (
    SystemMetricsRepositoryPort,
    GuiControllerPort,
    DockerControllerPort,
    DeployerPort,
    CameraPort,
    NetworkPort
)

class SystemStatusService(GetSystemStatusUseCase):
    def __init__(
        self,
        metrics_repo: SystemMetricsRepositoryPort,
        gui_controller: GuiControllerPort,
        docker_controller: DockerControllerPort
    ):
        self._metrics_repo = metrics_repo
        self._gui_controller = gui_controller
        self._docker_controller = docker_controller

    def execute(self) -> SystemStatus:
        metrics = self._metrics_repo.get_metrics()
        gui_active = self._gui_controller.is_active()
        containers = self._docker_controller.list_containers()
        return SystemStatus(system=metrics, gui_active=gui_active, docker_containers=containers)

class GuiService(ToggleGuiUseCase):
    def __init__(self, gui_controller: GuiControllerPort):
        self._gui_controller = gui_controller

    def execute(self, action: str) -> tuple[bool, str]:
        return self._gui_controller.execute_action(action)

class DockerService(ControlDockerContainerUseCase):
    def __init__(self, docker_controller: DockerControllerPort):
        self._docker_controller = docker_controller

    def execute(self, container_id: str, action: str) -> tuple[bool, str]:
        return self._docker_controller.control_container(container_id, action)

class DockerLogsService(GetDockerContainerLogsUseCase):
    def __init__(self, docker_controller: DockerControllerPort):
        self._docker_controller = docker_controller

    def execute(self, container_id: str) -> tuple[bool, str]:
        return self._docker_controller.get_container_logs(container_id)

class DeploymentService(DeployAppUseCase):
    def __init__(self, deployer: DeployerPort):
        self._deployer = deployer

    def execute(self, repo_url: str, target_dir: str | None, app_name: str) -> DeploymentResult:
        success, log = self._deployer.deploy(repo_url, target_dir, app_name)
        message = "¡Despliegue completado!" if success else "Error durante el despliegue"
        return DeploymentResult(success=success, log=log, message=message)

class CameraService(GetCamerasUseCase, CaptureCameraFrameUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute_list(self) -> List[CameraInfo]:
        # Implementa GetCamerasUseCase.
        # Python abstract classes permit different implementation method names or matching signature.
        # We will use execute() for Use Cases or separate methods depending on design.
        return self._camera_port.list_cameras()

    # To satisfy both interfaces under a clean Execute structure:
    # We will split it into two Use Cases to follow Single Responsibility Principle.
    pass

class GetCamerasService(GetCamerasUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self) -> List[CameraInfo]:
        return self._camera_port.list_cameras()

class CaptureCameraFrameService(CaptureCameraFrameUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self, camera_id: str) -> bytes:
        return self._camera_port.capture_frame(camera_id)

class GetWifiClientsService(GetWifiClientsUseCase):
    def __init__(self, network_port: NetworkPort):
        self._network_port = network_port

    def execute(self) -> List[WifiClient]:
        return self._network_port.list_wifi_clients()
