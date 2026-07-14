# -*- coding: utf-8 -*-
from src.domain.models import SystemMetric

class SystemMetricsPort:
    """Puerto para la recolección de métricas de la Raspberry."""
    def get_metrics(self) -> SystemMetric:
        raise NotImplementedError


class NetworkScannerPort:
    """Puerto para descubrir dispositivos en la red local/WiFi."""
    def scan_network(self) -> list:
        raise NotImplementedError


class CameraPort:
    """Puerto para capturar y procesar flujos de cámara y detección."""
    def get_frame(self) -> bytes:
        raise NotImplementedError

    def is_person_detected(self) -> bool:
        raise NotImplementedError


class DockerManagerPort:
    """Puerto para interactuar con el demonio de Docker y gestionar contenedores."""
    def list_containers(self) -> list:
        raise NotImplementedError

    def pause_container(self, container_id: str) -> bool:
        raise NotImplementedError

    def unpause_container(self, container_id: str) -> bool:
        raise NotImplementedError

    def restart_container(self, container_id: str) -> bool:
        raise NotImplementedError

    def get_container_logs(self, container_id: str) -> str:
        raise NotImplementedError


class DeviceRepositoryPort:
    """Puerto para la persistencia de información extendida de dispositivos."""
    def save_device(self, mac: str, name: str, phone: str, alert_on_connect: bool) -> bool:
        raise NotImplementedError

    def get_device(self, mac: str) -> dict:
        raise NotImplementedError

    def get_all_devices(self) -> dict:
        raise NotImplementedError

