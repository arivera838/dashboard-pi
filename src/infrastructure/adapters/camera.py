# -*- coding: utf-8 -*-
import time
import math
import threading
from io import BytesIO
from src.domain.ports import CameraPort

# Intentar importar OpenCV y Pillow de forma segura para la cámara
try:
    # pyrefly: ignore [missing-import]
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    # pyrefly: ignore [missing-import]
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

class AdaptiveCameraAdapter(CameraPort):
    """Adaptador inteligente de vídeo. Utiliza OpenCV si hay cámara física, o simula IA en tiempo real."""
    
    def __init__(self, camera_index=0, camera_name="Cámara Nativa"):
        self.camera_index = camera_index
        self.camera_name = camera_name
        self.cap = None
        self.person_detected = False
        self.frame_counter = 0
        
        # Intentar inicializar la cámara física de OpenCV de forma asíncrona
        if OPENCV_AVAILABLE:
            try:
                # No bloquear el inicio del servidor, intentaremos abrir en segundo plano
                threading.Thread(target=self._init_physical_camera, daemon=True).start()
            except Exception:
                pass

    def _init_physical_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            # Reducir resolución para no saturar la Raspberry Pi 3 B+
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        except Exception as e:
            print(f"No se pudo inicializar la cámara de OpenCV: {e}")
            self.cap = None

    def get_frame(self) -> bytes:
        self.frame_counter += 1
        
        # Caso 1: Intentar capturar desde cámara física real con OpenCV
        if self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    # Retornar el frame puro sin procesamiento de IA
                    self.person_detected = False
                    _, jpeg = cv2.imencode('.jpg', frame)
                    return jpeg.tobytes()
            except Exception as e_cam:
                print(f"Error de captura física en {self.camera_name}: {e_cam}")

        # Caso 2: Simulación interactiva con Pillow (Generador Sintético de IA para Desarrollo)
        return self._generate_simulated_ai_frame()

    def _generate_simulated_ai_frame(self) -> bytes:
        """Generador matemático de fotogramas que emula una cámara de seguridad vigilando."""
        if not PILLOW_AVAILABLE:
            # Fallback definitivo en binario crudo (un pixel negro en JPEG base64) para evitar dependencias
            return b'\xff\xd8\xff\xdb\x00C\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xbf\xff\xd9'

        # Diseñar un cuadro de vigilancia oscuro
        width, height = 480, 270
        img = Image.new("RGB", (width, height), "#111827")
        draw = ImageDraw.Draw(img)

        # Líneas de cuadrícula de cámara de seguridad
        for x in range(0, width, 40):
            draw.line([(x, 0), (x, height)], fill="#1f2937", width=1)
        for y in range(0, height, 40):
            draw.line([(0, y), (width, y)], fill="#1f2937", width=1)

        self.person_detected = False

        # Overlay HUD de la cámara de seguridad
        draw.text((15, 15), "REC ● LIVE FEED", fill="#ef4444")
        draw.text((width - 150, 15), time.strftime("%Y-%m-%d %H:%M:%S"), fill="#9ca3af")
        draw.text((15, height - 25), f"{self.camera_name} (Raspberry Pi)", fill="#6b7280")

        # Convertir a bytes en formato JPG
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def is_person_detected(self) -> bool:
        return self.person_detected

    def close(self):
        if self.cap:
            self.cap.release()
