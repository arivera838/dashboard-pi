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
    def __init__(self, ip, mac, interface, name="Dispositivo Desconocido", is_known=False, owner_status="Invitado", phone="", alert_on_connect=False):
        self.ip = ip
        self.mac = mac
        self.interface = interface
        self.name = name
        self.is_known = is_known
        self.owner_status = owner_status
        self.phone = phone
        self.alert_on_connect = alert_on_connect

    def to_dict(self):
        return self.__dict__


class RegisteredDevice:
    """Representa los detalles de un usuario registrado en la base de datos local."""
    def __init__(self, mac, name, phone="", alert_on_connect=False):
        self.mac = mac
        self.name = name
        self.phone = phone
        self.alert_on_connect = alert_on_connect

    def to_dict(self):
        return self.__dict__


class DockerContainer:
    """Entidad que representa el estado de un contenedor Docker en el sistema."""
    def __init__(self, id, name, image, status, state):
        self.id = id
        self.name = name
        self.image = image
        self.status = status
        self.state = state  # running, paused, exited, etc.

    def to_dict(self):
        return self.__dict__

