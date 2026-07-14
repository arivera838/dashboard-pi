# -*- coding: utf-8 -*-
import os
from src.domain.models import NetworkDevice
from src.domain.ports import NetworkScannerPort

# Dispositivos conocidos de la red local para asociar MACs con nombres de personas
KNOWN_PEOPLE = {
    "00:11:22:33:44:55": {"name": "Juan Pérez (Móvil)", "status": "Familiar"},
    "aa:bb:cc:dd:ee:ff": {"name": "María Gómez (Laptop)", "status": "Familiar"},
    "b8:27:eb:11:22:33": {"name": "Raspberry Pi Auxiliar", "status": "Servidor"},
}

class LinuxARPNetworkScannerAdapter(NetworkScannerPort):
    """Adaptador que lee la tabla ARP del kernel para saber quién está en el WiFi sin saturar de pings."""
    
    def scan_network(self) -> list:
        devices = []
        # En Linux, /proc/net/arp contiene los dispositivos detectados en la red local
        arp_path = "/proc/net/arp"
        
        if os.path.exists(arp_path):
            try:
                with open(arp_path, "r") as f:
                    lines = f.readlines()[1:] # Ignorar la cabecera
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 6:
                            ip = parts[0]
                            mac = parts[3].lower()
                            interface = parts[5]
                            
                            # Omitir entradas incompletas o nulas de la tabla ARP
                            if mac == "00:00:00:00:00:00" or not mac:
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
