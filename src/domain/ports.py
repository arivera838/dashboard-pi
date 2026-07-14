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
