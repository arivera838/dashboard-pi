from abc import ABC, abstractmethod
from src.domain.models import SystemStatus, DeploymentResult

class GetSystemStatusUseCase(ABC):
    @abstractmethod
    def execute(self) -> SystemStatus:
        pass

class ToggleGuiUseCase(ABC):
    @abstractmethod
    def execute(self, action: str) -> bool:
        pass

class ControlDockerContainerUseCase(ABC):
    @abstractmethod
    def execute(self, container_id: str, action: str) -> tuple[bool, str]:
        pass

class DeployAppUseCase(ABC):
    @abstractmethod
    def execute(self, repo_url: str, target_dir: str | None, app_name: str) -> DeploymentResult:
        pass
