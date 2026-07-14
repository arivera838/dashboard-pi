# -*- coding: utf-8 -*-
import os
import shutil
from src.domain.models import SystemMetric
from src.domain.ports import SystemMetricsPort

class LinuxSystemMetricsAdapter(SystemMetricsPort):
    """Adaptador de infraestructura que consulta el hardware nativo de Linux."""
    
    def get_metrics(self) -> SystemMetric:
        cpu_load = "0.00"
        cpu_temp = 0.0
        
        # 1. Carga CPU
        try:
            with open("/proc/loadavg", "r") as f:
                cpu_load = f.read().strip().split()[0]
        except Exception:
            cpu_load = "0.00"

        # 2. Temperatura
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                cpu_temp = round(float(f.read().strip()) / 1000.0, 1)
        except Exception:
            cpu_temp = 37.2 # Temperatura simulada por defecto si no es una Pi real

        # 3. RAM & SWAP
        ram_percent, swap_percent = 0, 0
        ram_text, swap_text = "N/A", "N/A"
        try:
            meminfo = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].replace(":", "")
                        meminfo[key] = int(parts[1]) * 1024 # Convertir a Bytes

            # Operaciones RAM
            total_ram = meminfo.get("MemTotal", 0)
            free_ram = meminfo.get("MemFree", 0)
            avail_ram = meminfo.get("MemAvailable", free_ram)
            used_ram = total_ram - avail_ram
            if total_ram > 0:
                ram_percent = round((used_ram / total_ram) * 100, 1)
                ram_text = f"{round(used_ram/(1024**2))}MB / {round(total_ram/(1024**2))}MB"

            # Operaciones SWAP
            total_swap = meminfo.get("SwapTotal", 0)
            free_swap = meminfo.get("SwapFree", 0)
            used_swap = total_swap - free_swap
            if total_swap > 0:
                swap_percent = round((used_swap / total_swap) * 100, 1)
                swap_text = f"{round(used_swap/(1024**2))}MB / {round(total_swap/(1024**2))}MB"
        except Exception:
            pass

        # 4. Disco Duro
        disk_percent = 0
        disk_text = "N/A"
        try:
            total, used, free = shutil.disk_usage("/")
            disk_percent = round((used / total) * 100, 1)
            disk_text = f"{round(used/(1024**3))}GB / {round(total/(1024**3))}GB"
        except Exception:
            pass

        return SystemMetric(cpu_load, cpu_temp, ram_percent, ram_text, swap_percent, swap_text, disk_percent, disk_text)
