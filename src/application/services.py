# -*- coding: utf-8 -*-
import subprocess
from src.domain.ports import (
    SystemMetricsPort, 
    NetworkScannerPort, 
    CameraPort, 
    DockerManagerPort, 
    DeviceRepositoryPort
)

class DashboardApplication:
    """La central de control (Orquestador Hexagonal) que une los puertos con su lógica de negocio."""
    
    def __init__(
        self, 
        metrics_adapter: SystemMetricsPort, 
        network_adapter: NetworkScannerPort, 
        camera_adapter: CameraPort,
        docker_adapter: DockerManagerPort,
        device_repo: DeviceRepositoryPort
    ):
        self.metrics = metrics_adapter
        self.network = network_adapter
        self.camera = camera_adapter
        self.docker = docker_adapter
        self.device_repo = device_repo

    def get_system_status(self):
        """Usa los puertos para construir la respuesta unificada del servidor."""
        metrics_data = self.metrics.get_metrics()
        devices_list = self.network.scan_network()
        
        # Obtener los usuarios registrados de la base de datos local (JSON)
        registered_devices = self.device_repo.get_all_devices()
        
        alert_triggered = False
        alert_devices = []

        # Enriquecer la lista de dispositivos ARP con la información del repositorio JSON
        for device in devices_list:
            mac_key = device.mac.lower().strip()
            if mac_key in registered_devices:
                reg_info = registered_devices[mac_key]
                device.name = reg_info.get("name", device.name)
                device.phone = reg_info.get("phone", "")
                device.alert_on_connect = reg_info.get("alert_on_connect", False)
                device.is_known = True
                device.owner_status = "Registrado"
                
                if device.alert_on_connect:
                    alert_triggered = True
                    alert_devices.append(device.name)
        
        # Personas conocidas/registradas activas en red
        connected_family = [d.name for d in devices_list if d.is_known]
        
        return {
            "system": metrics_data.to_dict(),
            "gui_active": self.get_gui_status(),
            "wifi_devices": [d.to_dict() for d in devices_list],
            "family_near": connected_family,
            "person_on_camera": self.camera.is_person_detected(),
            "alert_triggered": alert_triggered,
            "alert_devices": alert_devices
        }

    def get_gui_status(self) -> bool:
        try:
            res = subprocess.run(["systemctl", "is-active", "lightdm"], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except Exception:
            return False

    # --- CASOS DE USO DE DISPOSITIVOS ---
    def register_device(self, mac: str, name: str, phone: str, alert_on_connect: bool) -> bool:
        return self.device_repo.save_device(mac, name, phone, alert_on_connect)

    def list_registered_devices(self) -> dict:
        return self.device_repo.get_all_devices()

    # --- CASOS DE USO DE DOCKER ---
    def list_docker_containers(self) -> list:
        containers = self.docker.list_containers()
        return [c.to_dict() for c in containers]

    def manage_container(self, container_id: str, action: str) -> bool:
        if action == "pause":
            return self.docker.pause_container(container_id)
        elif action == "unpause":
            return self.docker.unpause_container(container_id)
        elif action == "restart":
            return self.docker.restart_container(container_id)
        return False

    def get_container_logs(self, container_id: str) -> str:
        return self.docker.get_container_logs(container_id)
