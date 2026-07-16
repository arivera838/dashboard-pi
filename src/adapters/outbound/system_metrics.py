import shutil
from src.domain.models import SystemMetrics
from src.application.ports.outputs import SystemMetricsRepositoryPort

class LinuxSystemMetricsRepository(SystemMetricsRepositoryPort):
    def get_metrics(self) -> SystemMetrics:
        metrics_dict = {
            "cpu_load": "0.00",
            "cpu_temp": 0.0,
            "ram_total": 0,
            "ram_used": 0,
            "ram_free": 0,
            "ram_percent": 0.0,
            "swap_total": 0,
            "swap_used": 0,
            "swap_free": 0,
            "swap_percent": 0.0,
            "disk_total": 0,
            "disk_used": 0,
            "disk_free": 0,
            "disk_percent": 0.0
        }

        import os
        prefix = "/host" if os.path.exists("/host/proc") else ""

        # 1. CPU Load
        try:
            with open(f"{prefix}/proc/loadavg", "r") as f:
                metrics_dict["cpu_load"] = f.read().strip().split()[0]
        except Exception:
            metrics_dict["cpu_load"] = "0.00"

        # 2. CPU Temperature
        try:
            with open(f"{prefix}/sys/class/thermal/thermal_zone0/temp", "r") as f:
                metrics_dict["cpu_temp"] = round(float(f.read().strip()) / 1000.0, 1)
        except Exception:
            metrics_dict["cpu_temp"] = 0.0

        # 3. RAM & SWAP
        try:
            meminfo = {}
            with open(f"{prefix}/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].replace(":", "")
                        val = int(parts[1]) * 1024  # Convert to Bytes
                        meminfo[key] = val

            total_ram = meminfo.get("MemTotal", 0)
            free_ram = meminfo.get("MemFree", 0)
            avail_ram = meminfo.get("MemAvailable", free_ram)
            used_ram = total_ram - avail_ram
            metrics_dict["ram_total"] = total_ram
            metrics_dict["ram_used"] = used_ram
            metrics_dict["ram_free"] = avail_ram
            metrics_dict["ram_percent"] = round((used_ram / total_ram) * 100, 1) if total_ram > 0 else 0.0

            total_swap = meminfo.get("SwapTotal", 0)
            free_swap = meminfo.get("SwapFree", 0)
            used_swap = total_swap - free_swap
            metrics_dict["swap_total"] = total_swap
            metrics_dict["swap_used"] = used_swap
            metrics_dict["swap_free"] = free_swap
            metrics_dict["swap_percent"] = round((used_swap / total_swap) * 100, 1) if total_swap > 0 else 0.0
        except Exception:
            pass

        # 4. Storage Disk
        try:
            total, used, free = shutil.disk_usage(prefix if prefix else "/")
            metrics_dict["disk_total"] = total
            metrics_dict["disk_used"] = used
            metrics_dict["disk_free"] = free
            metrics_dict["disk_percent"] = round((used / total) * 100, 1) if total > 0 else 0.0
        except Exception:
            pass

        return SystemMetrics(**metrics_dict)
