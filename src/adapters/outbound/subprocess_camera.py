import os
import sys
import time
import threading
import numpy as np
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
            self._load_face_cascade()
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

    def _scan_hardware_cameras(self) -> List[dict]:
        detected = []
        for i in range(10):
            dev_path = f"/dev/video{i}"
            if os.path.exists(dev_path):
                name = f"Dispositivo de Video {i}"
                try:
                    with open(f"/sys/class/video4linux/video{i}/name", "r") as f:
                        name = f.read().strip()
                except Exception:
                    pass
                
                name_lower = name.lower()
                if "metadata" in name_lower or "params" in name_lower or "bcm2835-isp" in name_lower or "bcm2835-codec" in name_lower:
                    continue
                
                is_csi = any(x in name_lower for x in ["unicam", "rpivid", "imx219", "ov5647", "imx708", "libcameradev", "camera-nativa", "bcm2835"])
                
                detected.append({
                    "index": i,
                    "name": name,
                    "is_csi": is_csi,
                    "dev_path": dev_path
                })
        return detected

    def _start_all_captures(self):
        devices = self._scan_hardware_cameras()
        usb_count = 0
        csi_found = False
        
        for dev in devices:
            if dev["is_csi"]:
                cam_id = "csi"
                self._camera_device_indices[cam_id] = dev["index"]
                self._start_camera_thread(cam_id, dev["index"])
                csi_found = True
            else:
                cam_id = f"usb{usb_count}"
                self._camera_device_indices[cam_id] = dev["index"]
                self._start_camera_thread(cam_id, dev["index"])
                usb_count += 1

        if not csi_found:
            csi_hardware_exists = False
            try:
                import subprocess
                res = subprocess.run(["rpicam-hello", "--list-cameras"], capture_output=True, text=True, timeout=1.5)
                if "No cameras available" not in res.stderr and ("Available cameras" in res.stdout or "/base/soc/" in res.stdout or "/base/soc/" in res.stderr):
                    csi_hardware_exists = True
            except Exception:
                pass
            
            if not csi_hardware_exists:
                try:
                    import subprocess
                    res = subprocess.run(["libcamera-hello", "--list-cameras"], capture_output=True, text=True, timeout=1.5)
                    if "No cameras available" not in res.stderr and ("Available cameras" in res.stdout or "/base/soc/" in res.stdout or "/base/soc/" in res.stderr):
                        csi_hardware_exists = True
                except Exception:
                    pass
            
            if csi_hardware_exists:
                cam_id = "csi"
                self._camera_device_indices[cam_id] = 0
                self._start_camera_thread(cam_id, 0)

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
                
                # Procesar recognition en el fotograma antes de codificar y transmitir
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
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (16, 185, 129), 2)
                    cv2.putText(frame, "ROSTRO DETECTADO", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (16, 185, 129), 2)
            except Exception:
                pass

        # 2. Reconocimiento de Manos (MediaPipe o Algoritmo Nativo RPi de alto rendimiento por Piel/Contornos)
        if self._hand_detection_enabled:
            if MEDIAPIPE_AVAILABLE and self._mp_hands is not None:
                # Método A: MediaPipe
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self._mp_hands.process(rgb_frame)
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            self._mp_draw.draw_landmarks(
                                frame, 
                                hand_landmarks, 
                                mp.solutions.hands.HAND_CONNECTIONS,
                                self._mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                                self._mp_draw.DrawingSpec(color=(59, 130, 246), thickness=2)
                            )
                            
                            # Clasificación de Gestos
                            try:
                                tip_ids = [8, 12, 16, 20]
                                pip_ids = [6, 10, 14, 18]
                                fingers_open = []
                                
                                # Pulgar
                                if hand_landmarks.landmark[4].x < hand_landmarks.landmark[2].x:
                                    fingers_open.append(True)
                                else:
                                    fingers_open.append(False)
                                    
                                for tip, pip in zip(tip_ids, pip_ids):
                                    if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                                        fingers_open.append(True)
                                    else:
                                        fingers_open.append(False)
                                        
                                gesture = "MANO DETECTADA"
                                total_open = sum(fingers_open)
                                if total_open == 0:
                                    gesture = "PUNO (Fist)"
                                elif total_open == 5:
                                    gesture = "PALMA ABIERTA (Open Hand)"
                                elif fingers_open[1] and fingers_open[2] and not fingers_open[0] and not fingers_open[3] and not fingers_open[4]:
                                    gesture = "AMOR Y PAZ (Peace)"
                                elif fingers_open[0] and total_open == 1:
                                    gesture = "BIEN (Like / Thumbs Up)"
                                elif fingers_open[1] and total_open == 1:
                                    gesture = "SENALANDO (Pointing)"
                                
                                x_wrist = int(hand_landmarks.landmark[0].x * frame.shape[1])
                                y_wrist = int(hand_landmarks.landmark[0].y * frame.shape[0])
                                cv2.putText(frame, gesture, (x_wrist - 40, y_wrist + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (59, 130, 246), 2, cv2.LINE_AA)
                            except Exception:
                                pass
                except Exception:
                    pass
            else:
                # Método B: Algoritmo Nativo de Alto Rendimiento (Skin-Color segmentación + Contornos + Casco Convexo)
                # Diseñado para correr a 30 FPS en la RPi 3 sin dependencias pesadas
                try:
                    # 1. Convertir a espacio de color YCrCb (ideal para segmentar tonos de piel humana)
                    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
                    # Rangos estándar de color de piel en YCrCb
                    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
                    upper_skin = np.array([255, 173, 127], dtype=np.uint8)
                    
                    # 2. Crear máscara y suavizar para remover ruido
                    mask = cv2.inRange(ycrcb, lower_skin, upper_skin)
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                    mask = cv2.dilate(mask, kernel, iterations=2)
                    mask = cv2.GaussianBlur(mask, (5, 5), 100)
                    
                    # 3. Encontrar contornos
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        # Obtener el contorno más grande (que asumimos es la mano)
                        large_contour = max(contours, key=cv2.contourArea)
                        
                        # Filtrar contornos muy pequeños para evitar falsos positivos
                        if cv2.contourArea(large_contour) > 5000:
                            # Dibujar contorno de la mano en azul
                            cv2.drawContours(frame, [large_contour], -1, (239, 68, 68), 2)
                            
                            # Obtener casco convexo
                            hull = cv2.convexHull(large_contour, returnPoints=False)
                            defects = cv2.convexityDefects(large_contour, hull)
                            
                            # Contar dedos extendidos analizando defectos de convexidad
                            fingers = 0
                            if defects is not None:
                                for j in range(defects.shape[0]):
                                    s, e, f, d = defects[j, 0]
                                    start = tuple(large_contour[s][0])
                                    end = tuple(large_contour[e][0])
                                    far = tuple(large_contour[f][0])
                                    
                                    # Calcular longitudes de los lados del triángulo de defecto
                                    a = np.linalg.norm(np.array(end) - np.array(start))
                                    b = np.linalg.norm(np.array(far) - np.array(start))
                                    c = np.linalg.norm(np.array(end) - np.array(far))
                                    
                                    # Aplicar teorema del coseno para encontrar el ángulo del defecto
                                    angle = np.arccos((b**2 + c**2 - a**2) / (2 * b * c)) * 57.29
                                    
                                    # Si el ángulo es menor de 90 grados y la profundidad es considerable, es un espacio interdigital
                                    if angle <= 90 and d > 12000:
                                        fingers += 1
                                        cv2.circle(frame, far, 4, (59, 130, 246), -1)
                                
                                # Un conteo de defectos N se asocia a N+1 dedos levantados
                                if fingers > 0:
                                    fingers += 1
                                    
                            # Clasificar el gesto en base a los dedos detectados
                            gesture = "MANO DETECTADA"
                            if fingers == 0:
                                gesture = "PUNO (Fist)"
                            elif fingers == 1:
                                gesture = "SENALANDO (Pointing)"
                            elif fingers == 2:
                                gesture = "AMOR Y PAZ (Peace)"
                            elif fingers >= 4:
                                gesture = "PALMA ABIERTA (Open Hand)"
                                
                            # Dibujar rectángulo delimitador y escribir el gesto
                            x, y, w, h = cv2.boundingRect(large_contour)
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (59, 130, 246), 1)
                            cv2.putText(frame, gesture, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (59, 130, 246), 2, cv2.LINE_AA)
                except Exception as err:
                    print(f"[Vision] Error en procesador nativo de manos: {err}")

    def _load_face_cascade(self):
        cascade_filename = "haarcascade_frontalface_default.xml"
        if not os.path.exists(cascade_filename):
            try:
                import urllib.request
                url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
                print(f"[Vision] Descargando Haar Cascade de Rostros desde GitHub...")
                urllib.request.urlretrieve(url, cascade_filename)
                print(f"[Vision] Descarga completada.")
            except Exception as e:
                print(f"[Vision] Error al descargar cascade: {e}")
        
        if os.path.exists(cascade_filename):
            self._face_cascade = cv2.CascadeClassifier(cascade_filename)
            if not self._face_cascade.empty():
                print("[Vision] Haar Cascade de Rostros cargado correctamente desde archivo local.")
                return
                
        # Fallback al path por defecto de OpenCV
        try:
            self._face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if not self._face_cascade.empty():
                print("[Vision] Haar Cascade de Rostros cargado desde cv2.data.haarcascades.")
                return
        except Exception:
            pass
        print("[Vision] ADVERTENCIA: No se pudo cargar ningún Haar Cascade para rostros.")

    def list_cameras(self) -> List[CameraInfo]:
        devices = self._scan_hardware_cameras()
        cameras = []
        usb_count = 0
        csi_found = False
        
        for dev in devices:
            if dev["is_csi"]:
                cameras.append(CameraInfo(
                    id="csi",
                    name="Cámara Nativa Raspberry Pi (CSI Flex)",
                    type="CSI"
                ))
                csi_found = True
            else:
                cameras.append(CameraInfo(
                    id=f"usb{usb_count}",
                    name=f"Cámara USB ({dev['name']})",
                    type="USB"
                ))
                usb_count += 1

        if not csi_found:
            csi_hardware_exists = False
            try:
                import subprocess
                res = subprocess.run(["rpicam-hello", "--list-cameras"], capture_output=True, text=True, timeout=1.5)
                if "No cameras available" not in res.stderr and ("Available cameras" in res.stdout or "/base/soc/" in res.stdout):
                    csi_hardware_exists = True
            except Exception:
                pass
            
            if not csi_hardware_exists:
                try:
                    import subprocess
                    res = subprocess.run(["libcamera-hello", "--list-cameras"], capture_output=True, text=True, timeout=1.5)
                    if "No cameras available" not in res.stderr and ("Available cameras" in res.stdout or "/base/soc/" in res.stdout):
                        csi_hardware_exists = True
                except Exception:
                    pass
            
            if csi_hardware_exists:
                cameras.append(CameraInfo(
                    id="csi",
                    name="Cámara Nativa Raspberry Pi (CSI Flex - libcamera)",
                    type="CSI"
                ))
                csi_found = True

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
                # Utilizar codec 'MJPG' (Motion JPEG) que está compilado nativamente
                # en todas las versiones de OpenCV en RPi (evita errores con XVID/H264)
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                writer = cv2.VideoWriter(filepath, fourcc, 20.0, (640, 480))
                
                # Comprobar si el grabador se inició correctamente
                if not writer.isOpened():
                    raise Exception("VideoWriter no pudo abrirse con el codec MJPG")
                
                self._video_writers[camera_id] = writer
                self._recording_active[camera_id] = True
                self._recording_start[camera_id] = time.time()
                self._recording_path[camera_id] = filepath
                
                print(f"[Camera] Grabación iniciada exitosamente en: {filepath}")
                return True, f"Grabación iniciada: {filename}"
            except Exception as e:
                return False, f"Fallo al iniciar el grabador de video (MJPG): {e}"

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
