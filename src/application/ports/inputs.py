from abc import ABC, abstractmethod
from typing import Optional
from typing import List
from src.domain.models import SystemStatus, DeploymentResult, CameraInfo, WifiClient, RecordingStatus

class GetSystemStatusUseCase(ABC):
    @abstractmethod
    def execute(self) -> SystemStatus:
        pass

class ToggleGuiUseCase(ABC):
    @abstractmethod
    def execute(self, action: str) -> tuple[bool, str]:
        pass

class ControlDockerContainerUseCase(ABC):
    @abstractmethod
    def execute(self, container_id: str, action: str) -> tuple[bool, str]:
        pass

class GetDockerContainerLogsUseCase(ABC):
    @abstractmethod
    def execute(self, container_id: str) -> tuple[bool, str]:
        pass

class DeployAppUseCase(ABC):
    @abstractmethod
    def execute(self, repo_url: str, target_dir: Optional[str], app_name: str, branch: str = "main") -> DeploymentResult:
        pass

class CancelDeploymentUseCase(ABC):
    @abstractmethod
    def execute(self, app_name: str) -> tuple[bool, str]:
        pass

class GetDeployStatusUseCase(ABC):
    @abstractmethod
    def execute(self, app_name: str) -> dict:
        pass

class ListDeploymentsUseCase(ABC):
    @abstractmethod
    def execute(self) -> dict:
        pass

class GetLocalAppsUseCase(ABC):
    @abstractmethod
    def execute(self) -> list:
        pass

class GetCamerasUseCase(ABC):
    @abstractmethod
    def execute(self) -> List[CameraInfo]:
        pass

class CaptureCameraFrameUseCase(ABC):
    @abstractmethod
    def execute(self, camera_id: str) -> bytes:
        pass

    @abstractmethod
    def execute_packet(self, camera_id: str) -> tuple[bytes, int]:
        pass

class GetWifiClientsUseCase(ABC):
    @abstractmethod
    def execute(self) -> List[WifiClient]:
        pass

class StartRecordingUseCase(ABC):
    @abstractmethod
    def execute(self, camera_id: str) -> tuple[bool, str]:
        pass

class StopRecordingUseCase(ABC):
    @abstractmethod
    def execute(self, camera_id: str) -> tuple[bool, str]:
        pass

class GetRecordingStatusUseCase(ABC):
    @abstractmethod
    def execute(self, camera_id: str) -> RecordingStatus:
        pass

class ListRecordingsUseCase(ABC):
    @abstractmethod
    def execute(self) -> List[str]:
        pass

class GetVisionSettingsUseCase(ABC):
    @abstractmethod
    def execute(self) -> dict:
        pass

class UpdateVisionSettingsUseCase(ABC):
    @abstractmethod
    def execute(self, face_enabled: bool, hand_enabled: bool) -> tuple[bool, str]:
        pass

class GetExternalCameraIpUseCase(ABC):
    @abstractmethod
    def execute(self) -> str:
        pass

class SetExternalCameraIpUseCase(ABC):
    @abstractmethod
    def execute(self, ip: str) -> None:
        pass

class SaveClientAliasUseCase(ABC):
    @abstractmethod
    def execute(self, mac: str, alias: str) -> tuple[bool, str]:
        pass

class GetGitBranchesUseCase(ABC):
    @abstractmethod
    def execute(self, repo_url: str) -> tuple[bool, list[str] | str]:
        pass
