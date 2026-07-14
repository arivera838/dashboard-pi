# -*- coding: utf-8 -*-
import subprocess
from src.domain.ports import SystemMetricsPort, NetworkScannerPort, CameraPort

class DashboardApplication:
    """La central de control (Orquestador Hexagonal) que une los puertos con su lógica de negocio."""
    
    def __init__(self, metrics_adapter: SystemMetricsPort, network_adapter: NetworkScannerPort, camera_adapter: CameraPort):
        self.metrics = metrics_adapter
        self.network = network_adapter
        self.camera = camera_adapter

    def get_system_status(self):
        """Usa los puertos para construir la respuesta unificada del servidor."""
        metrics_data = self.metrics.get_metrics()
        devices_list = self.network.scan_network()
        
        # Verificar cuántas personas conocidas de nuestra lista están en el WiFi actualmente
        connected_family = [d.name for d in devices_list if d.is_known]
        
        return {
            "system": metrics_data.to_dict(),
            "gui_active": self.get_gui_status(),
            "wifi_devices": [d.to_dict() for d in devices_list],
            "family_near": connected_family,
            "person_on_camera": self.camera.is_person_detected()
        }

    def get_gui_status(self) -> bool:
        try:
            res = subprocess.run(["systemctl", "is-active", "lightdm"], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except Exception:
            return False
