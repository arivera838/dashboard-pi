import os
import json

CONFIG_FILE = "cicd_config.json"

def get_cicd_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "git_token": "",
        "webhook_secret": "",
        "telegram_token": "",
        "telegram_chat_id": ""
    }

def save_cicd_config(config: dict) -> bool:
    try:
        # Load existing to avoid wiping out other keys if we add them later
        current = get_cicd_config()
        current.update(config)
        with open(CONFIG_FILE, "w") as f:
            json.dump(current, f, indent=4)
        
        # Propagar a variables de entorno para que los adaptadores las lean al vuelo
        os.environ["GIT_TOKEN"] = current.get("git_token", "")
        os.environ["GITHUB_WEBHOOK_SECRET"] = current.get("webhook_secret", "")
        os.environ["TELEGRAM_TOKEN"] = current.get("telegram_token", "")
        os.environ["TELEGRAM_CHAT_ID"] = current.get("telegram_chat_id", "")
        return True
    except Exception:
        return False

# Cargar configuración al importar el módulo para inicializar variables de entorno
save_cicd_config(get_cicd_config())
