# Arquitectura y Reglas del Proyecto (Raspberry Pi 3 B+ Dashboard)

Este archivo define las directrices arquitectónicas y de desarrollo del proyecto `dashboardPi`. Cualquier agente de IA que trabaje en esta base de código debe leer y aplicar estrictamente estas reglas.

---

## 1. Entorno de Ejecución Objetivo

*   **Hardware**: Raspberry Pi 3 B+ (CPU Quad-Core de 1.4 GHz, 1 GB de RAM LPDDR2).
*   **Restricciones de Rendimiento**: 
    *   La RAM y el procesador son limitados. Evitar la instalación de dependencias pesadas en Python o frameworks Web de gran tamaño (como Django o FastAPI si no son estrictamente necesarios).
    *   Mantener el uso de las bibliotecas del sistema nativas de Python (`http.server`, `socketserver`, `subprocess`, etc.) para optimizar el consumo de recursos.
    *   Cualquier procesamiento continuo de cámara o escaneo de red debe realizarse en hilos en segundo plano (`threading`) e incorporar retardos (`time.sleep`) para evitar saturar el procesador.

---

## 2. Arquitectura de Software: Hexagonal (Puertos y Adaptadores)

El proyecto está estructurado bajo **Clean Architecture** y **Arquitectura Hexagonal**. Es crítico mantener este desacoplamiento en cualquier cambio:

*   **Dominio (`src/domain/`)**:
    *   **Modelos (`models.py`)**: Entidades puras de datos (`SystemMetric`, `NetworkDevice`, `RegisteredDevice`, `DockerContainer`). No deben tener dependencias externas de infraestructura o frameworks.
    *   **Puertos (`ports.py`)**: Definiciones de interfaces abstractas que establecen los contratos de comunicación de entrada y salida.
*   **Aplicación/Servicios (`src/application/`)**:
    *   **Caso de Uso (`services.py`)**: Orquestador principal de la lógica de negocio (`DashboardApplication`). Solo interactúa con las abstracciones de los puertos. No debe conocer los detalles de las bases de datos, APIs web o hardware subyacente.
*   **Infraestructura (`src/infrastructure/`)**:
    *   **Adaptadores (`adapters/`)**: Implementaciones físicas de los puertos (lectura de `/proc`, tabla ARP de red, captura de cámaras OpenCV, lectura/escritura de archivos JSON).
    *   **Controlador Web (`web/server.py`)**: Traduce las peticiones HTTP y delega las acciones a la capa de aplicación.
    *   **Vistas (`web/templates/index.html`)**: Frontend en Tailwind CSS y JavaScript desacoplado del servidor.

---

## 3. Reglas de Desarrollo y Despliegue

1.  **Persistencia Ligera**: Toda la base de datos de dispositivos se gestiona a través de un archivo local `known_devices.json` en lugar de una base de datos pesada.
2.  **Integración con Docker**: El despliegue de producción se gestiona a través de contenedores de Docker.
    *   El socket de Docker `/var/run/docker.sock` debe ser montado en el contenedor en `docker-compose.yml` para posibilitar el control de los contenedores locales.
    *   Para el escaneo de la red de todo el hogar, la propiedad `network_mode: host` debe estar activa en entornos Linux/Raspberry Pi.
3.  **Compatibilidad de Cámara**:
    *   El adaptador de cámara debe gestionar de forma robusta las cámaras físicas USB y la cámara nativa CSI, cayendo limpiamente (mediante capturas `try/except`) a una simulación gráfica Pillow si la cámara no está conectada o está ocupada.
