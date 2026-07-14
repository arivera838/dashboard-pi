# -*- coding: utf-8 -*-
import json
import os
from src.domain.ports import DeviceRepositoryPort

class JSONDeviceRepositoryAdapter(DeviceRepositoryPort):
    """Adaptador de persistencia en formato JSON para almacenar datos de dispositivos wifi."""
    
    def __init__(self, filepath="known_devices.json"):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            except Exception as e:
                print(f"Error al crear repositorio JSON: {e}")

    def _load(self) -> dict:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al escribir en repositorio JSON: {e}")

    def save_device(self, mac: str, name: str, phone: str, alert_on_connect: bool) -> bool:
        data = self._load()
        data[mac.lower().strip()] = {
            "name": name,
            "phone": phone,
            "alert_on_connect": bool(alert_on_connect)
        }
        self._save(data)
        return True

    def get_device(self, mac: str) -> dict:
        data = self._load()
        return data.get(mac.lower().strip(), {})

    def get_all_devices(self) -> dict:
        return self._load()
