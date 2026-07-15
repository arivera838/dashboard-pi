import subprocess
from src.application.ports.outputs import GuiControllerPort

class SystemdGuiController(GuiControllerPort):
    def is_active(self) -> bool:
        try:
            res = subprocess.run(["systemctl", "is-active", "lightdm"], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except Exception:
            return False

    def execute_action(self, action: str) -> tuple[bool, str]:
        if action == "start":
            subprocess.run(["sudo", "systemctl", "start", "lightdm"], capture_output=True, text=True)
            return True, "Interfaz gráfica iniciada temporalmente."
        elif action == "stop":
            subprocess.run(["sudo", "systemctl", "stop", "lightdm"], capture_output=True, text=True)
            return True, "Interfaz gráfica detenida para ahorrar RAM."
        return False, "Acción no reconocida"
