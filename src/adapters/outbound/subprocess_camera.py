import os
import time
import threading
from typing import List, Dict
from src.domain.models import CameraInfo, RecordingStatus
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

    # Estado de grabación
    _recording_active: Dict[str, bool] = {}
    _video_writers: Dict[str, any] = {}
    _recording_start: Dict[str, float] = {}
    _recording_path: Dict[str, str] = {}
    _recordings_dir = "./recordings"

    def __init__(self):
        # Crear directorio de grabaciones
        os.makedirs(self._recordings_dir, exist_ok=True)
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

        # Cámara CSI
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
                    cap = cv2.VideoCapture(device_index)
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
                
                # Codificar en JPEG para la UI
                success, jpeg = cv2.imencode('.jpg', frame)
                if success:
                    with self._lock:
                        self._latest_frames[camera_id] = jpeg.tobytes()
                    consecutive_errors = 0
                else:
                    raise Exception("Fallo en la codificación JPEG")

                # Escribir al grabador si está activo
                with self._lock:
                    if self._recording_active.get(camera_id, False) and camera_id in self._video_writers:
                        try:
                            self._video_writers[camera_id].write(frame)
                        except Exception as write_err:
                            print(f"[Camera] Error escribiendo frame al video: {write_err}")
                
                time.sleep(0.04) # ~25 FPS
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
        for i in range(5):
            dev_path = f"/dev/video{i}"
            if os.path.exists(dev_path):
                cameras.append(CameraInfo(
                    id=f"usb{i}",
                    name=f"Cámara USB ({dev_path})",
                    type="USB"
                ))
        
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
            # Simular un frame dinámico variando el timestamp
            return self._get_placeholder_image(f"Camara Simulada: {camera_id.upper()}")

        if OPENCV_AVAILABLE:
            if camera_id not in self._threads or not self._threads[camera_id].is_alive():
                try:
                    dev_index = int(camera_id.replace("usb", ""))
                except Exception:
                    dev_index = 0
                self._start_camera_thread(camera_id, dev_index)

            with self._lock:
                frame = self._latest_frames.get(camera_id)
            if frame:
                return frame

        if not OPENCV_AVAILABLE:
            return self._get_placeholder_image("Por favor instala python3-opencv\\npara activar transmision de video fluida")

        return self._get_placeholder_image(f"Cargando {camera_id.upper()}...")

    def start_recording(self, camera_id: str) -> tuple[bool, str]:
        # Para simuladores, solo guardar estado en memoria
        filename = f"recording_{camera_id}_{int(time.time())}.avi"
        filepath = os.path.join(self._recordings_dir, filename)

        if "mock" in camera_id:
            with self._lock:
                self._recording_active[camera_id] = True
                self._recording_start[camera_id] = time.time()
                self._recording_path[camera_id] = filepath
            return True, f"Grabación simulada iniciada para {camera_id}"

        if not OPENCV_AVAILABLE:
            return False, "OpenCV no está disponible para realizar grabaciones de video reales"

        # Asegurar de que la cámara está corriendo
        if camera_id not in self._threads or not self._threads[camera_id].is_alive():
            try:
                dev_index = int(camera_id.replace("usb", ""))
            except Exception:
                dev_index = 0
            self._start_camera_thread(camera_id, dev_index)

        with self._lock:
            if self._recording_active.get(camera_id, False):
                return False, "La cámara ya está siendo grabada actualmente"

            try:
                # Cuatro caracteres de codec de video XVID
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                writer = cv2.VideoWriter(filepath, fourcc, 20.0, (640, 480))
                
                self._video_writers[camera_id] = writer
                self._recording_active[camera_id] = True
                self._recording_start[camera_id] = time.time()
                self._recording_path[camera_id] = filepath
                
                print(f"[Camera] Grabación iniciada en: {filepath}")
                return True, f"Grabación iniciada: {filename}"
            except Exception as e:
                return False, f"Fallo al iniciar el grabador de video: {e}"

    def stop_recording(self, camera_id: str) -> tuple[bool, str]:
        with self._lock:
            if not self._recording_active.get(camera_id, False):
                return False, "La cámara no está grabando"

            self._recording_active[camera_id] = False
            
            # Liberar VideoWriter
            writer = self._video_writers.pop(camera_id, None)
            if writer:
                try:
                    writer.release()
                except Exception as e:
                    print(f"[Camera] Error liberando grabador: {e}")

            start_time = self._recording_start.pop(camera_id, 0.0)
            filepath = self._recording_path.get(camera_id, "")
            elapsed = int(time.time() - start_time) if start_time > 0 else 0
            
            print(f"[Camera] Grabación detenida. Duración: {elapsed}s. Archivo: {filepath}")
            return True, f"Grabación detenida con éxito ({elapsed}s)."

    def get_recording_status(self, camera_id: str) -> RecordingStatus:
        with self._lock:
            is_rec = self._recording_active.get(camera_id, False)
            filepath = self._recording_path.get(camera_id, "")
            start = self._recording_start.get(camera_id, 0.0)
            elapsed = int(time.time() - start) if (is_rec and start > 0) else 0

        return RecordingStatus(
            camera_id=camera_id,
            is_recording=is_rec,
            filepath=filepath,
            elapsed_time=elapsed
        )

    def list_recordings(self) -> List[str]:
        if not os.path.exists(self._recordings_dir):
            return []
        files = []
        for file in os.listdir(self._recordings_dir):
            if file.endswith(".avi") or file.endswith(".mp4"):
                files.append(file)
        # Retornar ordenados inversamente por creación
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self._recordings_dir, x)), reverse=True)
        return files

    def _get_placeholder_image(self, label: str) -> bytes:
        # PNG de 1x1 píxel transparente
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01\x00\x00\xff\xff\x03\x00\x00\x06\x00\x05\x57\xbf\xab\xd4\x00\x00\x00\x00IEND\xaeB`\x82'
