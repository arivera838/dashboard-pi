import os
import subprocess
from typing import List
from src.domain.models import CameraInfo
from src.application.ports.outputs import CameraPort

class SubprocessCameraAdapter(CameraPort):
    def list_cameras(self) -> List[CameraInfo]:
        cameras = []
        
        # 1. Buscar cámaras USB en /dev/video*
        for i in range(5):
            dev_path = f"/dev/video{i}"
            if os.path.exists(dev_path):
                # Usualmente video0 es la cámara USB
                cameras.append(CameraInfo(
                    id=f"usb{i}",
                    name=f"Cámara USB ({dev_path})",
                    type="USB"
                ))
        
        # 2. Intentar buscar cámara CSI (flex)
        # En RPi antiguas 'vcgencmd get_camera' indica si está conectada.
        csi_detected = False
        try:
            res = subprocess.run(["vcgencmd", "get_camera"], capture_output=True, text=True)
            if "detected=1" in res.stdout:
                csi_detected = True
        except Exception:
            # Si no vcgencmd, buscar si existe soporte para raspistill o libcamera
            try:
                res = subprocess.run(["which", "libcamera-still"], capture_output=True)
                if res.returncode == 0:
                    csi_detected = True
            except Exception:
                pass

        if csi_detected:
            cameras.append(CameraInfo(
                id="csi",
                name="Cámara Nativa Raspberry Pi (CSI Flex)",
                type="CSI"
            ))

        # 3. Si no se detectan cámaras físicas, inyectar cámaras de simulación/prueba
        if not cameras:
            cameras.append(CameraInfo(
                id="usb_mock",
                name="Cámara USB Simulada (Prueba)",
                type="USB"
            ))
            cameras.append(CameraInfo(
                id="csi_mock",
                name="Cámara CSI Simulada (Prueba)",
                type="CSI"
            ))

        return cameras

    def capture_frame(self, camera_id: str) -> bytes:
        # Si es cámara simulada, retornar imagen de prueba
        if "mock" in camera_id:
            return self._get_placeholder_image(f"Camara Simulada: {camera_id.upper()}")

        # Mapear e intentar capturar con herramientas reales
        try:
            if camera_id == "csi":
                # Intentar con libcamera (RPi OS Bullseye o superior)
                try:
                    res = subprocess.run(
                        ["libcamera-still", "-n", "-t", "10", "--width", "640", "--height", "480", "-o", "-"],
                        capture_output=True
                    )
                    if res.returncode == 0 and len(res.stdout) > 100:
                        return res.stdout
                except Exception:
                    pass

                # Intentar con raspistill (RPi OS Buster o anterior)
                res = subprocess.run(
                    ["raspistill", "-w", "640", "-h", "480", "-q", "80", "-t", "10", "-o", "-"],
                    capture_output=True
                )
                if res.returncode == 0 and len(res.stdout) > 100:
                    return res.stdout

            elif camera_id.startswith("usb"):
                # Capturar usando fswebcam
                dev_index = camera_id.replace("usb", "")
                dev_path = f"/dev/video{dev_index}"
                
                # fswebcam: -d indica dispositivo, --no-banner quita fecha/hora por defecto, -q modo silencioso, - indica stdout
                res = subprocess.run(
                    ["fswebcam", "-d", dev_path, "--no-banner", "--skip", "2", "-r", "640x480", "-S", "2", "-q", "-"],
                    capture_output=True
                )
                if res.returncode == 0 and len(res.stdout) > 100:
                    return res.stdout

        except Exception as e:
            print(f"Error capturando de {camera_id}: {e}")

        # Retornar imagen de marcador de posición si falla o no está conectada
        return self._get_placeholder_image(f"Camara {camera_id.upper()}\\nNo disponible o sin senal")

    def _get_placeholder_image(self, label: str) -> bytes:
        # Retorna un PNG de 640x480 gris con un texto usando una cabecera binaria simplificada (PPM formato portable pixmap)
        # o un PNG estático simple. El navegador renderiza PPM si usamos la cabecera correcta, pero es más seguro
        # usar un PNG real de 1x1 pixel estático si no podemos generar.
        # Alternativamente, para que sea un PNG válido con mensaje visual, un PNG estático de 1x1:
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01\x00\x00\xff\xff\x03\x00\x00\x06\x00\x05\x57\xbf\xab\xd4\x00\x00\x00\x00IEND\xaeB`\x82'
