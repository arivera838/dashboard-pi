# -*- coding: utf-8 -*-

class SystemMetric:
    """Entidad de dominio que representa el rendimiento del hardware."""
    def __init__(self, cpu_load, cpu_temp, ram_percent, ram_text, swap_percent, swap_text, disk_percent, disk_text):
        self.cpu_load = cpu_load
        self.cpu_temp = cpu_temp
        self.ram_percent = ram_percent
        self.ram_text = ram_text
        self.swap_percent = swap_percent
        self.swap_text = swap_text
        self.disk_percent = disk_percent
        self.disk_text = disk_text

    def to_dict(self):
        return self.__dict__


class NetworkDevice:
    """Entidad que representa un dispositivo conectado al WiFi de casa."""
    def __init__(self, ip, mac, interface, name="Dispositivo Desconocido", is_known=False, owner_status="Invitado"):
        self.ip = ip
        self.mac = mac
        self.interface = interface
        self.name = name
        self.is_known = is_known
        self.owner_status = owner_status

    def to_dict(self):
        return self.__dict__
