from typing import List
from src.domain.models import SystemStatus, DeploymentResult, CameraInfo, WifiClient, RecordingStatus
from src.application.ports.inputs import (
    GetSystemStatusUseCase,
    ToggleGuiUseCase,
    ControlDockerContainerUseCase,
    GetDockerContainerLogsUseCase,
    DeployAppUseCase,
    GetCamerasUseCase,
    CaptureCameraFrameUseCase,
    GetWifiClientsUseCase,
    StartRecordingUseCase,
    StopRecordingUseCase,
    GetRecordingStatusUseCase,
    ListRecordingsUseCase,
    GetVisionSettingsUseCase,
    UpdateVisionSettingsUseCase
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

    def execute(self, repo_url: str, target_dir: str | None, app_name: str, app_port: str | None) -> DeploymentResult:
        success, log = self._deployer.deploy(repo_url, target_dir, app_name, app_port)
        message = "¡Despliegue completado!" if success else "Error durante el despliegue"
        return DeploymentResult(success=success, log=log, message=message)

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

class StartRecordingService(StartRecordingUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self, camera_id: str) -> tuple[bool, str]:
        return self._camera_port.start_recording(camera_id)

class StopRecordingService(StopRecordingUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self, camera_id: str) -> tuple[bool, str]:
        return self._camera_port.stop_recording(camera_id)

class GetRecordingStatusService(GetRecordingStatusUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self, camera_id: str) -> RecordingStatus:
        return self._camera_port.get_recording_status(camera_id)

class ListRecordingsService(ListRecordingsUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self) -> List[str]:
        return self._camera_port.list_recordings()

class GetVisionSettingsService(GetVisionSettingsUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self) -> dict:
        return self._camera_port.get_vision_settings()

class UpdateVisionSettingsService(UpdateVisionSettingsUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self, face_enabled: bool, hand_enabled: bool) -> tuple[bool, str]:
        self._camera_port.set_vision_settings(face_enabled, hand_enabled)
        return True, "Ajustes de visión artificial actualizados"
