# -*- coding: utf-8 -*-
import os
import socket
import threading
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from src.domain.models import NetworkDevice
from src.domain.ports import NetworkScannerPort

# Dispositivos conocidos de la red local para asociar MACs con nombres de personas
KNOWN_PEOPLE = {
    "00:11:22:33:44:55": {"name": "Juan Pérez (Móvil)", "status": "Familiar"},
    "aa:bb:cc:dd:ee:ff": {"name": "María Gómez (Laptop)", "status": "Familiar"},
    "b8:27:eb:11:22:33": {"name": "Raspberry Pi Auxiliar", "status": "Servidor"},
}

class LinuxARPNetworkScannerAdapter(NetworkScannerPort):
    """Adaptador de red que realiza barridos de ping en segundo plano para poblar la tabla ARP y detectar todos los dispositivos."""
    
    def __init__(self):
        # Iniciar el hilo de barrido automático de red en segundo plano
        self.subnet = self._detect_local_subnet()
        print(f"[NetworkScanner] Subred detectada para escaneo: {self.subnet}.0/24")
        
        self.scanner_thread = threading.Thread(target=self._periodic_subnet_sweep, daemon=True)
        self.scanner_thread.start()

    def _detect_local_subnet(self) -> str:
        """Intenta detectar el prefijo IP de la red local (ej: 192.168.1)."""
        try:
            # Conectar temporalmente a un host externo para ver qué interfaz e IP local elige el OS
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}"
        except Exception:
            pass
        return "192.168.1"  # Fallback por defecto

    def _ping_ip(self, ip: str):
        """Envía un único paquete ping rápido para forzar respuesta ARP."""
        try:
            # En Linux, -c 1 envía 1 paquete, -W 1 pone 1 segundo de timeout
            subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _periodic_subnet_sweep(self):
        """Hilo de segundo plano que barre la subred periódicamente."""
        # Esperar a que el servidor web inicialice antes del primer barrido pesado
        time.sleep(5)
        while True:
            ips_to_scan = [f"{self.subnet}.{i}" for i in range(1, 255)]
            # Usar ThreadPool para disparar pings rápidos en paralelo (toma ~2-3 segundos en total)
            with ThreadPoolExecutor(max_workers=60) as executor:
                executor.map(self._ping_ip, ips_to_scan)
            
            # Repetir cada 45 segundos para mantener la caché ARP del kernel fresca
            time.sleep(45)

    def scan_network(self) -> list:
        devices = []
        arp_path = "/proc/net/arp"
        
        if os.path.exists(arp_path):
            try:
                with open(arp_path, "r") as f:
                    lines = f.readlines()[1:] # Ignorar la cabecera
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 6:
                            ip = parts[0]
                            mac = parts[3].lower().strip()
                            interface = parts[5]
                            
                            # Omitir entradas incompletas o nulas de la tabla ARP
                            if mac == "00:00:00:00:00:00" or not mac or len(mac) != 17:
                                continue
                                
                            # Determinar si conocemos a este usuario
                            is_known = mac in KNOWN_PEOPLE
                            name = KNOWN_PEOPLE[mac]["name"] if is_known else f"Dispositivo ({ip})"
                            owner_status = KNOWN_PEOPLE[mac]["status"] if is_known else "Desconocido"
                            
                            devices.append(NetworkDevice(
                                ip=ip,
                                mac=mac,
                                interface=interface,
                                name=name,
                                is_known=is_known,
                                owner_status=owner_status
                            ))
            except Exception as e:
                print(f"Error al leer la tabla ARP: {e}")
                
        # Fallback de desarrollo para demostración si la tabla ARP está vacía
        if not devices:
            devices = [
                NetworkDevice("192.168.1.10", "00:11:22:33:44:55", "wlan0", "Juan Pérez (Móvil)", True, "Familiar"),
                NetworkDevice("192.168.1.15", "aa:bb:cc:dd:ee:ff", "wlan0", "María Gómez (Laptop)", True, "Familiar"),
                NetworkDevice("192.168.1.45", "40:b0:34:de:12:ef", "wlan0", "SmartTV Salón", False, "Desconocido")
            ]
        return devices
