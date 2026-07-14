import subprocess
from src.application.ports.outputs import GuiControllerPort

class SystemdGuiController(GuiControllerPort):
    def is_active(self) -> bool:
        try:
            res = subprocess.run(["systemctl", "is-active", "lightdm"], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except Exception:
            return False

    def start_gui(self) -> bool:
        try:
            res = subprocess.run(["sudo", "systemctl", "start", "lightdm"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return False

    def stop_gui(self) -> bool:
        try:
            res = subprocess.run(["sudo", "systemctl", "stop", "lightdm"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return False
