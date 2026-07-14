from typing import List
from src.domain.models import SystemStatus, DeploymentResult
from src.application.ports.inputs import (
    GetSystemStatusUseCase,
    ToggleGuiUseCase,
    ControlDockerContainerUseCase,
    DeployAppUseCase
)
from src.application.ports.outputs import (
    SystemMetricsRepositoryPort,
    GuiControllerPort,
    DockerControllerPort,
    DeployerPort
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

    def execute(self, action: str) -> bool:
        if action == "start":
            return self._gui_controller.start_gui()
        elif action == "stop":
            return self._gui_controller.stop_gui()
        return False

class DockerService(ControlDockerContainerUseCase):
    def __init__(self, docker_controller: DockerControllerPort):
        self._docker_controller = docker_controller

    def execute(self, container_id: str, action: str) -> tuple[bool, str]:
        return self._docker_controller.control_container(container_id, action)

class DeploymentService(DeployAppUseCase):
    def __init__(self, deployer: DeployerPort):
        self._deployer = deployer

    def execute(self, repo_url: str, target_dir: str | None, app_name: str) -> DeploymentResult:
        success, log = self._deployer.deploy(repo_url, target_dir, app_name)
        message = "¡Despliegue completado!" if success else "Error durante el despliegue"
        return DeploymentResult(success=success, log=log, message=message)
