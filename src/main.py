# -*- coding: utf-8 -*-
import sys
import socketserver
from src.application.services import DashboardApplication
from src.infrastructure.adapters.metrics import LinuxSystemMetricsAdapter
from src.infrastructure.adapters.network import LinuxARPNetworkScannerAdapter
from src.infrastructure.adapters.camera import AdaptiveCameraAdapter
from src.infrastructure.web.server import HexagonalHTTPRequestHandler

PORT = 8080

def main():
    # 1. Instanciar adaptadores de infraestructura
    metrics_service = LinuxSystemMetricsAdapter()
    network_service = LinuxARPNetworkScannerAdapter()
    camera_service = AdaptiveCameraAdapter()

    # 2. Instanciar orquestador de aplicación inyectando dependencias (puertos)
    app_orchestrator = DashboardApplication(metrics_service, network_service, camera_service)

    # 3. Registrar servicios en el controlador HTTP
    HexagonalHTTPRequestHandler.app_orchestrator = app_orchestrator
    HexagonalHTTPRequestHandler.camera_service = camera_service

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
        print(f"  - Stream de Video con IA: http://localhost:{PORT}/api/camera/stream")
        print("🔧 Adaptadores de Salida en ejecución:")
        print("  - Lector de estado de hardware (/proc/meminfo y /sys/class/thermal)")
        print("  - Lector de presencia de red local (/proc/net/arp)")
        
        # Determinar el tipo de cámara
        camera_type = "Simulador de IA (Pillow)"
        if hasattr(camera_service, 'cap') and camera_service.cap:
            camera_type = "Físico (OpenCV)"
        print(f"  - Capturador de cámara: {camera_type}")
        print("==================================================================")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor apagado por orden del usuario.")
            camera_service.close()
            sys.exit(0)

if __name__ == "__main__":
    main()
