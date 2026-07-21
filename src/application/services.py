from typing import List
from src.domain.models import SystemStatus, DeploymentResult, CameraInfo, WifiClient, RecordingStatus
from src.application.ports.inputs import (
    GetSystemStatusUseCase,
    ToggleGuiUseCase,
    ControlDockerContainerUseCase,
    GetDockerContainerLogsUseCase,
    DeployAppUseCase,
    GetDeployStatusUseCase,
    ListDeploymentsUseCase,
    GetCamerasUseCase,
    CaptureCameraFrameUseCase,
    GetWifiClientsUseCase,
    StartRecordingUseCase,
    StopRecordingUseCase,
    GetRecordingStatusUseCase,
    ListRecordingsUseCase,
    GetVisionSettingsUseCase,
    UpdateVisionSettingsUseCase,
    GetExternalCameraIpUseCase,
    SetExternalCameraIpUseCase,
    SaveClientAliasUseCase,
    CancelDeploymentUseCase,
    GetGitBranchesUseCase,
    GetLocalAppsUseCase
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

    def execute(self, repo_url: str, target_dir: Optional[str], app_name: str, branch: str = "main") -> DeploymentResult:
        success, log = self._deployer.deploy(repo_url, target_dir, app_name, branch)
        message = "¡Despliegue iniciado!" if success else "Error al iniciar el despliegue"
        return DeploymentResult(success=success, log=log, message=message)

class CancelDeploymentService(CancelDeploymentUseCase):
    def __init__(self, deployer: DeployerPort):
        self._deployer = deployer

    def execute(self, app_name: str) -> tuple[bool, str]:
        return self._deployer.cancel_deploy(app_name)

class GetDeployStatusService(GetDeployStatusUseCase):
    def __init__(self, deployer: DeployerPort):
        self._deployer = deployer

    def execute(self, app_name: str) -> dict:
        return self._deployer.get_deploy_status(app_name)

class ListDeploymentsService(ListDeploymentsUseCase):
    def __init__(self, deployer: DeployerPort, docker_controller: DockerControllerPort):
        self._deployer = deployer
        self._docker = docker_controller

    def execute(self) -> dict:
        import time
        # 1. Obtener despliegues activos en memoria (del pipeline actual)
        deployments = dict(self._deployer.get_all_deployments())
        
        # 2. Escanear contenedores corriendo en Docker para reconocer proyectos compose
        try:
            projects = self._docker.list_compose_projects()
            for p in projects:
                name = p["name"]
                if name not in deployments:
                    deployments[name] = {
                        "status": "success" if p["status"] == "running" else p["status"],
                        "log": "Proyecto detectado de forma autónoma corriendo en Docker.",
                        "subdomain": p["subdomain"],
                        "start_time": time.time(),
                        "end_time": time.time(),
                        "elapsed_seconds": 0
                    }
                else:
                    deployments[name]["subdomain"] = p["subdomain"]
        except Exception as e:
            print(f"[ListDeploymentsService] Error al escanear proyectos compose: {e}")
            
        return deployments
class GetLocalAppsService(GetLocalAppsUseCase):
    def __init__(self, deployer: DeployerPort):
        self._deployer = deployer

    def execute(self) -> list:
        return self._deployer.get_local_apps()

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

    def execute_packet(self, camera_id: str) -> tuple[bytes, int]:
        return self._camera_port.get_latest_frame_packet(camera_id)

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

class GetExternalCameraIpService(GetExternalCameraIpUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self) -> str:
        return self._camera_port.get_external_camera_ip()

class SetExternalCameraIpService(SetExternalCameraIpUseCase):
    def __init__(self, camera_port: CameraPort):
        self._camera_port = camera_port

    def execute(self, ip: str) -> None:
        self._camera_port.set_external_camera_ip(ip)

class SaveClientAliasService(SaveClientAliasUseCase):
    def __init__(self, network_port: NetworkPort):
        self._network_port = network_port

    def execute(self, mac: str, alias: str) -> tuple[bool, str]:
        success = self._network_port.save_client_alias(mac, alias)
        if success:
            return True, f"Alias guardado con éxito para {mac}"
        return False, "No se pudo guardar el alias para este dispositivo"

class GetGitBranchesService(GetGitBranchesUseCase):
    def execute(self, repo_url: str) -> tuple[bool, Union[list[str], str]]:
        import subprocess
        try:
            # Ejecutamos git ls-remote sin prompt de contraseña y con timeout de 10s
            result = subprocess.run(
                ["git", "ls-remote", "--heads", repo_url],
                capture_output=True,
                text=True,
                timeout=10,
                env={"GIT_TERMINAL_PROMPT": "0"}
            )
            
            if result.returncode != 0:
                return False, f"Error al acceder al repositorio: {result.stderr.strip()}"
            
            branches = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # El formato es: <hash>\trefs/heads/<branch>
                    parts = line.split('\t')
                    if len(parts) == 2:
                        ref = parts[1]
                        branch = ref.replace("refs/heads/", "")
                        branches.append(branch)
            
            if not branches:
                return False, "No se encontraron ramas en el repositorio."
                
            return True, branches
            
        except subprocess.TimeoutExpired:
            return False, "Tiempo de espera agotado al conectar con el repositorio."
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
