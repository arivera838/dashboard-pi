from abc import ABC, abstractmethod
from typing import List
from src.domain.models import SystemMetrics, DockerContainer, CameraInfo, WifiClient, RecordingStatus

class SystemMetricsRepositoryPort(ABC):
    @abstractmethod
    def get_metrics(self) -> SystemMetrics:
        pass

class GuiControllerPort(ABC):
    @abstractmethod
    def is_active(self) -> bool:
        pass

    @abstractmethod
    def execute_action(self, action: str) -> tuple[bool, str]:
        pass

class DockerControllerPort(ABC):
    @abstractmethod
    def list_containers(self) -> List[DockerContainer]:
        pass

    @abstractmethod
    def control_container(self, container_id: str, action: str) -> tuple[bool, str]:
        pass

    @abstractmethod
    def get_container_logs(self, container_id: str) -> tuple[bool, str]:
        pass

class DeployerPort(ABC):
    @abstractmethod
    def deploy(self, repo_url: str, target_dir: str | None, app_name: str, app_port: str | None) -> tuple[bool, str]:
        pass

class CameraPort(ABC):
    @abstractmethod
    def list_cameras(self) -> List[CameraInfo]:
        pass

    @abstractmethod
    def capture_frame(self, camera_id: str) -> bytes:
        pass

    @abstractmethod
    def start_recording(self, camera_id: str) -> tuple[bool, str]:
        pass

    @abstractmethod
    def stop_recording(self, camera_id: str) -> tuple[bool, str]:
        pass

    @abstractmethod
    def get_recording_status(self, camera_id: str) -> RecordingStatus:
        pass

    @abstractmethod
    def list_recordings(self) -> List[str]:
        pass

class NetworkPort(ABC):
    @abstractmethod
    def list_wifi_clients(self) -> List[WifiClient]:
        pass
