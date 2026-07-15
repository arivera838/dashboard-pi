import os
import socket
import subprocess
import threading
import time
import json
from typing import List, Dict
from src.domain.models import WifiClient
from src.application.ports.outputs import NetworkPort

class LinuxNetworkAdapter(NetworkPort):
    _last_scan_time = 0.0
    _scan_lock = threading.Lock()
    _aliases_file = "./recordings/network_aliases.json"

    def __init__(self):
        # Iniciar primer barrido de red en segundo plano al arrancar
        threading.Thread(target=self._async_ping_sweep, daemon=True).start()

    def _load_aliases(self) -> Dict[str, str]:
        if os.path.exists(self._aliases_file):
            try:
                with open(self._aliases_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_client_alias(self, mac: str, alias: str) -> bool:
        aliases = self._load_aliases()
        aliases[mac.lower()] = alias
        try:
            # Asegurar directorio de recordings por si acaso
            os.makedirs(os.path.dirname(self._aliases_file), exist_ok=True)
            with open(self._aliases_file, "w") as f:
                json.dump(aliases, f)
            return True
        except Exception as e:
            print(f"[Network] Error al guardar alias: {e}")
            return False

    def list_wifi_clients(self) -> List[WifiClient]:
        clients = []
        hostnames: Dict[str, str] = {}
        aliases = self._load_aliases()

        # Lanzar barrido de red si han pasado más de 120 segundos desde el último escaneo
        if time.time() - self._last_scan_time > 120:
            threading.Thread(target=self._async_ping_sweep, daemon=True).start()

        # 1. Intentar leer leases de dnsmasq (si es un hotspot)
        dnsmasq_path = "/var/lib/misc/dnsmasq.leases"
        if os.path.exists(dnsmasq_path):
            try:
                with open(dnsmasq_path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            mac = parts[1].lower()
                            hostname = parts[3]
                            hostnames[mac] = hostname
            except Exception:
                pass

        # 2. Leer la tabla ARP de Linux (/proc/net/arp)
        arp_path = "/proc/net/arp"
        if os.path.exists(arp_path):
            try:
                with open(arp_path, "r") as f:
                    # Omitir cabecera
                    lines = f.readlines()[1:]
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) >= 6:
                            ip = parts[0]
                            flags = parts[2]
                            mac = parts[3].lower()
                            dev = parts[5]

                            # Filtrar entradas incompletas, vacías y loopbacks
                            if flags != "0x0" and mac != "00:00:00:00:00:00" and not ip.startswith("127."):
                                # Prioridad 1: Alias guardado por el usuario
                                hostname = aliases.get(mac)
                                
                                # Prioridad 2: Lease de dnsmasq
                                if not hostname:
                                    hostname = hostnames.get(mac)
                                
                                # Prioridad 3: Resolución inversa DNS local
                                if not hostname:
                                    try:
                                        socket.setdefaulttimeout(0.2)
                                        hostname = socket.gethostbyaddr(ip)[0]
                                    except Exception:
                                        hostname = "Dispositivo sin nombre"
                                
                                clients.append(WifiClient(
                                    ip=ip,
                                    mac=mac,
                                    device=dev,
                                    hostname=hostname
                                ))
            except Exception as e:
                print(f"[Network] Error al leer tabla ARP: {e}")

        # 3. Si no hay dispositivos detectados (ej: macOS en desarrollo local), inyectar mocks con alias si los hay
        if not clients:
            mock1_mac = "ac:37:43:11:aa:bb"
            mock2_mac = "00:11:22:33:44:55"
            clients.append(WifiClient(
                ip="192.168.1.55",
                mac=mock1_mac,
                device="wlan0",
                hostname=aliases.get(mock1_mac, "Smart-Hotspot-User")
            ))
            clients.append(WifiClient(
                ip="192.168.1.92",
                mac=mock2_mac,
                device="wlan0",
                hostname=aliases.get(mock2_mac, "iPhone-Mariana")
            ))

        return clients

    def _async_ping_sweep(self):
        # Evitar escaneos paralelos duplicados
        if not self._scan_lock.acquire(blocking=False):
            return
        
        try:
            print("[Network] Iniciando barrido de red (Ping Sweep) en segundo plano...")
            local_ip = self._get_local_ip()
            if not local_ip or local_ip == "127.0.0.1":
                return
            
            # Obtener el prefijo del segmento de red (ej. 192.168.1.)
            prefix = ".".join(local_ip.split(".")[:-1]) + "."
            
            # Hacer pings concurrentes con hilos para no colgar el servidor
            threads = []
            for i in range(1, 255):
                ip_to_ping = prefix + str(i)
                if ip_to_ping == local_ip:
                    continue
                
                t = threading.Thread(target=self._ping, args=(ip_to_ping,), daemon=True)
                threads.append(t)
                t.start()
                
                # Limitar a un máximo de 50 hilos simultáneos para no saturar CPU en la RPi 3 B+
                if len(threads) >= 50:
                    for active_t in threads:
                        active_t.join(timeout=0.05)
                    threads = [active_t for active_t in threads if active_t.is_alive()]

            # Esperar a que terminen los restantes
            for t in threads:
                t.join(timeout=0.1)
                
            self._last_scan_time = time.time()
            print("[Network] Barrido de red (Ping Sweep) finalizado. Tabla ARP actualizada.")
        except Exception as e:
            print(f"[Network] Error durante barrido de red: {e}")
        finally:
            self._scan_lock.release()

    def _ping(self, ip: str):
        try:
            # Comando ping ligero: 1 paquete, timeout de 1 segundo
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # No realiza conexión real, solo obtiene interfaz de salida
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "192.168.1.1"
