# -*- coding: utf-8 -*-
import time
import math
import threading
from io import BytesIO
from src.domain.ports import CameraPort

# Intentar importar OpenCV y Pillow de forma segura para la cámara
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
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
            ret, frame = self.cap.read()
            if ret:
                # Mapear detecciones básicas de personas usando el clasificador Haar Cascade si existe
                self.person_detected = False
                # Procesamiento rápido para la Pi: pasar a escala de grises
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Detección simplificada de rostros como proxy de personas
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) > 0:
                    self.person_detected = True
                    for (x, y, w, h) in faces:
                        # Dibujar recuadro verde neón
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, "PERSONA", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                _, jpeg = cv2.imencode('.jpg', frame)
                return jpeg.tobytes()

        # Caso 2: Simulación interactiva con Pillow (Generador Sintético de IA para Desarrollo)
        return self._generate_simulated_ai_frame()

    def _generate_simulated_ai_frame(self) -> bytes:
        """Generador matemático de fotogramas que emula una cámara de seguridad vigilando con detección de IA."""
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

        # Generar movimiento sinusoidal para una "persona simulada" caminando
        t = self.frame_counter * 0.08
        person_x = int(width / 2 + math.sin(t) * 120)
        person_y = int(height / 2 + math.cos(t * 0.5) * 30)

        # Emular detección de persona activa de forma periódica
        self.person_detected = abs(math.sin(t)) > 0.4
        
        if self.person_detected:
            # Dibujar caja de detección verde neón
            box_width, box_height = 60, 120
            x1, y1 = person_x - box_width//2, person_y - box_height//2
            x2, y2 = person_x + box_width//2, person_y + box_height//2
            
            draw.rectangle([x1, y1, x2, y2], outline="#10b981", width=3)
            # Dibujar un avatar simplificado de la persona
            draw.ellipse([person_x - 15, y1 + 10, person_x + 15, y1 + 40], fill="#10b981") # cabeza
            draw.line([(person_x, y1 + 40), (person_x, y2 - 30)], fill="#10b981", width=4) # cuerpo
            
            # Etiqueta de la IA
            confidence = int(85 + math.sin(t) * 12)
            draw.rectangle([x1, y1 - 22, x1 + 115, y1], fill="#10b981")
            draw.text((x1 + 6, y1 - 18), f"PERSONA: {confidence}%", fill="#ffffff")

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
