import os
import sys
import time
import threading
from contextlib import contextmanager
from typing import List, Dict
from src.domain.models import CameraInfo, RecordingStatus
from src.application.ports.outputs import CameraPort

# Silenciar advertencias internas de la librería de C++ de OpenCV y GStreamer
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["GST_DEBUG"] = "0"

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Intentar importar MediaPipe para reconocimiento de manos
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

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
    
    # Mapeo de índices de hardware
    _camera_device_indices: Dict[str, int] = {}

    # Configuración de los Plugins de Visión Artificial (Reconocimiento)
    _face_detection_enabled = False
    _hand_detection_enabled = False
    
    # Clasificadores e inicialización de modelos
    _face_cascade = None
    _mp_hands = None
    _mp_draw = None

    def __init__(self):
        # Crear directorio de grabaciones
        os.makedirs(self._recordings_dir, exist_ok=True)
        
        # Inicializar clasificadores si OpenCV está disponible
        if OPENCV_AVAILABLE:
            try:
                self._face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception as e:
                print(f"[Vision] No se pudo cargar Haar Cascades para Rostros: {e}")
            
            self._start_all_captures()

        # Inicializar MediaPipe si está disponible
        if MEDIAPIPE_AVAILABLE:
            try:
                self._mp_hands = mp.solutions.hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self._mp_draw = mp.solutions.drawing_utils
                print("[Vision] Plugin de MediaPipe (Manos) cargado con éxito.")
            except Exception as e:
                print(f"[Vision] Error al inicializar MediaPipe: {e}")
                self._mp_hands = None

    def set_vision_settings(self, face_enabled: bool, hand_enabled: bool):
        with self._lock:
            self._face_detection_enabled = face_enabled
            self._hand_detection_enabled = hand_enabled
            print(f"[Vision] Ajustes actualizados: Rostros={face_enabled}, Manos={hand_enabled}")

    def get_vision_settings(self) -> Dict[str, bool]:
        with self._lock:
            return {
                "face_enabled": self._face_detection_enabled,
                "hand_enabled": self._hand_detection_enabled,
                "mediapipe_installed": MEDIAPIPE_AVAILABLE
            }

    def _start_all_captures(self):
        # Escanear y arrancar cámaras USB/V4L2 reales de índice par (video0, video2...)
        usb_indices = []
        for i in range(5):
            dev_path = f"/dev/video{i}"
            if os.path.exists(dev_path):
                if i % 2 == 0:
                    cam_id = f"usb{i}"
                    self._camera_device_indices[cam_id] = i
                    self._start_camera_thread(cam_id, i)
                    usb_indices.append(i)

        # Arrancar siempre la cámara CSI (si está conectada, usará GStreamer o el índice libre)
        csi_index = 0 if not usb_indices else (max(usb_indices) + 1)
        self._camera_device_indices["csi"] = csi_index
        self._start_camera_thread("csi", csi_index)

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

    @contextmanager
    def _silence_stderr(self):
        try:
            stderr_fd = sys.stderr.fileno()
            saved_stderr_fd = os.dup(stderr_fd)
            try:
                t_fd = os.open(os.devnull, os.O_WRONLY)
                os.dup2(t_fd, stderr_fd)
                os.close(t_fd)
                yield
            finally:
                os.dup2(saved_stderr_fd, stderr_fd)
                os.close(saved_stderr_fd)
        except Exception:
            yield

    def _capture_loop(self, camera_id: str, device_index: int):
        print(f"[Camera] Iniciando captura continua para {camera_id} (Dispositivo {device_index})")
        cap = None
        consecutive_errors = 0
        use_gstreamer = (camera_id == "csi")
        
        while self._running.get(camera_id, False):
            if cap is None or not cap.isOpened():
                try:
                    if use_gstreamer:
                        gst_pipeline = "libcamerasrc ! video/x-raw, width=640, height=480, framerate=25/1 ! videoconvert ! appsink drop=true sync=false"
                        with self._silence_stderr():
                            cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
                        if not cap.isOpened():
                            use_gstreamer = False
                            cap = cv2.VideoCapture(device_index)
                    else:
                        cap = cv2.VideoCapture(device_index)
                    
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    consecutive_errors = 0
                except Exception as e:
                    print(f"[Camera] Error abriendo camara {camera_id}: {e}")
                    use_gstreamer = False
                    time.sleep(2.0)
                    continue

            try:
                ret, frame = cap.read()
                if not ret or frame is None:
                    raise Exception("No se pudo leer el frame")
                
                # Procesar reconocimiento en el fotograma antes de codificar y transmitir
                self._process_frame_vision(frame)

                # Codificar en JPEG para la UI
                success, jpeg = cv2.imencode('.jpg', frame)
                if success:
                    with self._lock:
                        self._latest_frames[camera_id] = jpeg.tobytes()
                    consecutive_errors = 0
                else:
                    raise Exception("Fallo en la codificación JPEG")

                # Escribir al grabador de video si está activo
                with self._lock:
                    if self._recording_active.get(camera_id, False) and camera_id in self._video_writers:
                        try:
                            self._video_writers[camera_id].write(frame)
                        except Exception as write_err:
                            print(f"[Camera] Error escribiendo frame al video: {write_err}")
                
                # Sleep mínimo para liberar el GIL y mantener fluidez máxima nativa sin sobrecalentar
                time.sleep(0.005)
            except Exception as e:
                consecutive_errors += 1
                if use_gstreamer and consecutive_errors >= 3:
                    print(f"[Camera] GStreamer falló al extraer frames de {camera_id}. Cambiando a V4L2 (Dispositivo {device_index})...")
                    use_gstreamer = False
                    if cap:
                        cap.release()
                    cap = None
                    consecutive_errors = 0
                elif consecutive_errors > 10:
                    print(f"[Camera] Reiniciando conexión de {camera_id} debido a errores consecutivos: {e}")
                    if cap:
                        cap.release()
                    cap = None
                time.sleep(0.5)

        if cap:
            cap.release()
        print(f"[Camera] Hilo de captura finalizado para {camera_id}")

    def _process_frame_vision(self, frame):
        # 1. Reconocimiento Facial (Haar Cascade)
        if self._face_detection_enabled and self._face_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self._face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                for (x, y, w, h) in faces:
                    # Dibujar caja de rostro en verde
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (16, 185, 129), 2)
                    cv2.putText(frame, "ROSTRO", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (16, 185, 129), 2)
            except Exception as e:
                pass

        # 2. Reconocimiento de Manos (MediaPipe)
        if self._hand_detection_enabled:
            if MEDIAPIPE_AVAILABLE and self._mp_hands is not None:
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self._mp_hands.process(rgb_frame)
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Dibujar puntos y conexiones de la mano en azul/blanco
                            self._mp_draw.draw_landmarks(
                                frame, 
                                hand_landmarks, 
                                mp.solutions.hands.HAND_CONNECTIONS,
                                self._mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                                self._mp_draw.DrawingSpec(color=(59, 130, 246), thickness=2)
                            )
                except Exception as e:
                    pass
            else:
                # Mostrar marca de agua solicitando la instalación de mediapipe
                cv2.putText(
                    frame, 
                    "Instala MediaPipe para detectar manos: pip install mediapipe", 
                    (10, frame.shape[0] - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.4, 
                    (59, 130, 246), 
                    1, 
                    cv2.LINE_AA
                )

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

        # Alternativa para RPi OS Bullseye/Bookworm con libcamera
        if not csi_detected:
            try:
                import subprocess
                res = subprocess.run(["libcamera-hello", "--list-cameras"], capture_output=True, text=True, timeout=1.5)
                if "No cameras available" not in res.stderr and ("Available cameras" in res.stdout or "Available cameras" in res.stderr or "/base/soc/" in res.stdout or "/base/soc/" in res.stderr):
                    csi_detected = True
            except Exception:
                pass

        if not csi_detected:
            try:
                import subprocess
                res = subprocess.run(["rpicam-hello", "--list-cameras"], capture_output=True, text=True, timeout=1.5)
                if "No cameras available" not in res.stderr and ("Available cameras" in res.stdout or "Available cameras" in res.stderr):
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
                dev_index = self._camera_device_indices.get(camera_id, 0)
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
            dev_index = self._camera_device_indices.get(camera_id, 0)
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
        # Retorna un BMP gris sólido de 640x480
        width, height = 640, 480
        file_size = 54 + (width * height * 3)
        header = bytearray([
            0x42, 0x4D,
            file_size & 0xFF, (file_size >> 8) & 0xFF, (file_size >> 16) & 0xFF, (file_size >> 24) & 0xFF,
            0x00, 0x00, 0x00, 0x00,
            54, 0x00, 0x00, 0x00,
            40, 0x00, 0x00, 0x00,
            width & 0xFF, (width >> 8) & 0xFF, (width >> 16) & 0xFF, (width >> 24) & 0xFF,
            height & 0xFF, (height >> 8) & 0xFF, (height >> 16) & 0xFF, (height >> 24) & 0xFF,
            0x01, 0x00,
            24, 0x00,
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
        ])
        pixels = bytearray([59, 41, 30]) * (width * height) # BGR values for RGB(30, 41, 59)
        return bytes(header + pixels)
