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
    def deploy(self, repo_url: str, target_dir: str | None, app_name: str) -> tuple[bool, str]:
        pass

    @abstractmethod
    def get_deploy_status(self, app_name: str) -> dict:
        pass

    @abstractmethod
    def get_all_deployments(self) -> dict:
        pass

class CameraPort(ABC):
    @abstractmethod
    def list_cameras(self) -> List[CameraInfo]:
        pass

    @abstractmethod
    def capture_frame(self, camera_id: str) -> bytes:
        pass

    @abstractmethod
    def get_latest_frame_packet(self, camera_id: str) -> tuple[bytes, int]:
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

    @abstractmethod
    def set_vision_settings(self, face_enabled: bool, hand_enabled: bool):
        pass

    @abstractmethod
    def get_vision_settings(self) -> dict:
        pass

class NetworkPort(ABC):
    @abstractmethod
    def list_wifi_clients(self) -> List[WifiClient]:
        pass

    @abstractmethod
    def save_client_alias(self, mac: str, alias: str) -> bool:
        pass

class GitPort(ABC):
    @abstractmethod
    def clone_or_pull(self, repo_url: str, branch: str, target_dir: str) -> tuple[bool, str]:
        pass

class NotificationPort(ABC):
    @abstractmethod
    def send_notification(self, title: str, message: str, status: str = "info") -> bool:
        pass
