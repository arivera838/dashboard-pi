import os
import time
import threading
from typing import List, Dict
from src.domain.models import CameraInfo
from src.application.ports.outputs import CameraPort

# Intentar importar OpenCV para captura fluida y de alto rendimiento
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

class SubprocessCameraAdapter(CameraPort):
    _latest_frames: Dict[str, bytes] = {}
    _threads: Dict[str, threading.Thread] = {}
    _running: Dict[str, bool] = {}
    _caps: Dict[str, any] = {}
    _lock = threading.Lock()

    def __init__(self):
        # Si OpenCV está disponible, iniciar hilos de captura para cámaras reales encontradas
        if OPENCV_AVAILABLE:
            self._start_all_captures()

    def _start_all_captures(self):
        # Escanear y arrancar cámaras USB reales
        for i in range(5):
            dev_path = f"/dev/video{i}"
            if os.path.exists(dev_path):
                cam_id = f"usb{i}"
                self._start_camera_thread(cam_id, i)

        # Cámara CSI (usualmente index 0 o 1 si no hay USBs)
        # OpenCV a veces mapea la cámara CSI como index 0 o 2.
        # Si no hay cámaras mapeadas, intentamos el index 0.
        if not self._threads:
            self._start_camera_thread("csi", 0)

    def _start_camera_thread(self, camera_id: str, device_index: int):
        with self._lock:
            if camera_id in self._threads and self._threads[camera_id].is_alive():
                return
            
            self._running[camera_id] = True
            thread = threading.Thread(
                target=self._capture_loop,
                args=(camera_id, device_index),
                daemon=True,
                name=f"CameraThread-{camera_id}"
            )
            self._threads[camera_id] = thread
            thread.start()

    def _capture_loop(self, camera_id: str, device_index: int):
        print(f"[Camera] Iniciando captura continua para {camera_id} (Dispositivo {device_index})")
        cap = None
        consecutive_errors = 0
        
        while self._running.get(camera_id, False):
            if cap is None or not cap.isOpened():
                try:
                    # wlan/camera init
                    cap = cv2.VideoCapture(device_index)
                    # Configurar resolución moderada para fluidez en RPi 3 B+
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    consecutive_errors = 0
                except Exception as e:
                    print(f"[Camera] Error abriendo camara {camera_id}: {e}")
                    time.sleep(2.0)
                    continue

            try:
                ret, frame = cap.read()
                if not ret or frame is None:
                    raise Exception("No se pudo leer el frame")
                
                # Codificar en JPEG
                success, jpeg = cv2.imencode('.jpg', frame)
                if success:
                    with self._lock:
                        self._latest_frames[camera_id] = jpeg.tobytes()
                    consecutive_errors = 0
                else:
                    raise Exception("Fallo en la codificación JPEG")
                
                # Un pequeño sleep para no consumir 100% de un core si la cámara es muy rápida
                time.sleep(0.03) # ~30 FPS
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors > 10:
                    print(f"[Camera] Reiniciando conexión de {camera_id} debido a errores consecutivos: {e}")
                    if cap:
                        cap.release()
                    cap = None
                time.sleep(0.5)

        if cap:
            cap.release()
        print(f"[Camera] Hilo de captura finalizado para {camera_id}")

    def list_cameras(self) -> List[CameraInfo]:
        cameras = []
        
        # Detectar cámaras USB físicas
        for i in range(5):
            dev_path = f"/dev/video{i}"
            if os.path.exists(dev_path):
                cameras.append(CameraInfo(
                    id=f"usb{i}",
                    name=f"Cámara USB ({dev_path})",
                    type="USB"
                ))
        
        # Detectar CSI (Nativa)
        csi_detected = False
        try:
            import subprocess
            res = subprocess.run(["vcgencmd", "get_camera"], capture_output=True, text=True)
            if "detected=1" in res.stdout:
                csi_detected = True
        except Exception:
            pass

        if csi_detected:
            cameras.append(CameraInfo(
                id="csi",
                name="Cámara Nativa Raspberry Pi (CSI Flex)",
                type="CSI"
            ))

        # Simuladores si no hay nada físico
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
        if "mock" in camera_id:
            return self._get_placeholder_image(f"Camara Simulada: {camera_id.upper()}")

        # Si OpenCV está disponible y tenemos un frame en cache, entregarlo instantáneamente
        if OPENCV_AVAILABLE:
            # Asegurar de que el hilo está corriendo para este dispositivo
            if camera_id not in self._threads or not self._threads[camera_id].is_alive():
                # Obtener el índice del dispositivo
                try:
                    dev_index = int(camera_id.replace("usb", ""))
                except Exception:
                    dev_index = 0
                self._start_camera_thread(camera_id, dev_index)

            with self._lock:
                frame = self._latest_frames.get(camera_id)
            if frame:
                return frame

        # Si OpenCV no está disponible, retornar placeholder con instrucciones
        if not OPENCV_AVAILABLE:
            return self._get_placeholder_image("Por favor instala python3-opencv\\npara activar transmision de video fluida")

        return self._get_placeholder_image(f"Cargando {camera_id.upper()}...")

    def _get_placeholder_image(self, label: str) -> bytes:
        # PNG de 1x1 píxel transparente
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01\x00\x00\xff\xff\x03\x00\x00\x06\x00\x05\x57\xbf\xab\xd4\x00\x00\x00\x00IEND\xaeB`\x82'
