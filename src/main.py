# -*- coding: utf-8 -*-
import sys
import socketserver
from src.application.services import DashboardApplication
from src.infrastructure.adapters.metrics import LinuxSystemMetricsAdapter
from src.infrastructure.adapters.network import LinuxARPNetworkScannerAdapter
from src.infrastructure.adapters.camera import AdaptiveCameraAdapter
from src.infrastructure.adapters.docker import SubprocessDockerAdapter
from src.infrastructure.adapters.device_repository import JSONDeviceRepositoryAdapter
from src.infrastructure.web.server import HexagonalHTTPRequestHandler

PORT = 8080

def main():
    # 1. Instanciar adaptadores de infraestructura
    metrics_service = LinuxSystemMetricsAdapter()
    network_service = LinuxARPNetworkScannerAdapter()
    docker_service = SubprocessDockerAdapter()
    device_repo = JSONDeviceRepositoryAdapter()
    
    # Soporte multi-cámara (Cámara Nativa e indexada USB)
    camera_native = AdaptiveCameraAdapter(camera_index=0, camera_name="Cámara Nativa Pi")
    camera_usb = AdaptiveCameraAdapter(camera_index=1, camera_name="Cámara Periférica USB")

    # 2. Instanciar orquestador de aplicación inyectando puertos
    app_orchestrator = DashboardApplication(
        metrics_adapter=metrics_service, 
        network_adapter=network_service, 
        camera_adapter=camera_native,
        docker_adapter=docker_service,
        device_repo=device_repo
    )

    # 3. Registrar servicios en el controlador HTTP
    HexagonalHTTPRequestHandler.app_orchestrator = app_orchestrator
    HexagonalHTTPRequestHandler.camera_services = {
        "native": camera_native,
        "usb": camera_usb
    }

    # 4. Configurar el puerto reutilizable
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), HexagonalHTTPRequestHandler) as httpd:
        print("==================================================================")
        print("🚀 SERVIDOR WEB CORRIENDO BAJO ARQUITECTURA HEXAGONAL CLEAN")
        print("==================================================================")
        print(f"👉 Accede a tu panel en: http://localhost:{PORT}")
        print("------------------------------------------------------------------")
        print("🔧 Adaptadores de Entrada activos:")
        print(f"  - Web Interface (Dashboard): http://localhost:{PORT}/")
        print(f"  - API de Métricas de Sistema: http://localhost:{PORT}/api/status")
        print(f"  - Stream de Cámara Nativa: http://localhost:{PORT}/api/camera/stream?id=native")
        print(f"  - Stream de Cámara USB: http://localhost:{PORT}/api/camera/stream?id=usb")
        print(f"  - API Docker: http://localhost:{PORT}/api/docker/list")
        print("🔧 Adaptadores de Salida en ejecución:")
        print("  - Lector de estado de hardware (/proc/meminfo y /sys/class/thermal)")
        print("  - Lector de presencia de red local (/proc/net/arp)")
        print("  - Gestor de Docker (Subprocess CLI)")
        print("  - Repositorio de dispositivos (JSON)")
        
        # Determinar el tipo de cámaras
        cam_native_type = "Simulada (Pillow)" if not (hasattr(camera_native, 'cap') and camera_native.cap) else "Física (OpenCV)"
        cam_usb_type = "Simulada (Pillow)" if not (hasattr(camera_usb, 'cap') and camera_usb.cap) else "Física (OpenCV)"
        print(f"  - Cámara Nativa: {cam_native_type}")
        print(f"  - Cámara USB: {cam_usb_type}")
        print("==================================================================")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor apagado por orden del usuario.")
            camera_native.close()
            camera_usb.close()
            sys.exit(0)

if __name__ == "__main__":
    main()
