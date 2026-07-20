from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass(frozen=True)
class SystemMetrics:
    cpu_load: str
    cpu_temp: float
    ram_total: int
    ram_used: int
    ram_free: int
    ram_percent: float
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float
    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_load": self.cpu_load,
            "cpu_temp": self.cpu_temp,
            "ram_total": self.ram_total,
            "ram_used": self.ram_used,
            "ram_free": self.ram_free,
            "ram_percent": self.ram_percent,
            "swap_total": self.swap_total,
            "swap_used": self.swap_used,
            "swap_free": self.swap_free,
            "swap_percent": self.swap_percent,
            "disk_total": self.disk_total,
            "disk_used": self.disk_used,
            "disk_free": self.disk_free,
            "disk_percent": self.disk_percent,
        }

@dataclass(frozen=True)
class DockerContainer:
    id: str
    name: str
    status: str
    image: str
    running: bool
    ports: str
    memory_usage: str = "N/A"
    git_branch: str = None
    git_url: str = None
    is_managed_app: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "image": self.image,
            "running": self.running,
            "ports": self.ports,
            "memory_usage": self.memory_usage,
            "git_branch": self.git_branch,
            "git_url": self.git_url,
            "is_managed_app": self.is_managed_app
        }

@dataclass(frozen=True)
class SystemStatus:
    system: SystemMetrics
    gui_active: bool
    docker_containers: List[DockerContainer]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system.to_dict(),
            "gui_active": self.gui_active,
            "docker_containers": [c.to_dict() for c in self.docker_containers]
        }

@dataclass(frozen=True)
class DeploymentResult:
    success: bool
    log: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "success" if self.success else "error",
            "message": self.message,
            "log": self.log
        }

@dataclass(frozen=True)
class CameraInfo:
    id: str
    name: str
    type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type
        }

@dataclass(frozen=True)
class WifiClient:
    ip: str
    mac: str
    device: str
    hostname: str
    bandwidth: str
    manufacturer: str = "Desconocido"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip": self.ip,
            "mac": self.mac,
            "device": self.device,
            "hostname": self.hostname,
            "bandwidth": self.bandwidth,
            "manufacturer": self.manufacturer
        }

@dataclass(frozen=True)
class RecordingStatus:
    camera_id: str
    is_recording: bool
    recording_time: int
    file_path: str | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "is_recording": self.is_recording,
            "recording_time": self.recording_time,
            "file_path": self.file_path
        }

# CI/CD Models
@dataclass(frozen=True)
class WebhookPayload:
    repo_name: str
    repo_url: str
    branch: str
    commit_hash: str
    commit_message: str
    author: str
    provider: str # github | gitlab
    signature: str | None = None
    raw_payload: str | bytes = ""

@dataclass
class BuildJob:
    id: str
    repo_name: str
    branch: str
    status: str # queued, building, success, failed
    logs: List[str]
    start_time: float
    end_time: float | None = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "repo_name": self.repo_name,
            "branch": self.branch,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "log_tail": self.logs[-50:] if self.logs else []
        }
