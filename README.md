# Raspberry Pi 3 B+ Smart Dashboard

Este proyecto es una refactorización bajo **Arquitectura Hexagonal (Clean Architecture)** del panel de control domótico y de despliegue para Raspberry Pi.

La interfaz web consume APIs limpias inyectadas a través de puertos y expone un sistema de telemetría de hardware, detección de presencia en red local (ARP) y visualización de cámara en tiempo real mediante un modelo simulado (o cámara física USB/CSI si está presente).

---

## Estructura de Arquitectura Hexagonal

El código está dividido en componentes desacoplados con responsabilidades claras:

*   **`src/domain`**: Contiene los modelos de negocio (`models.py`) y las interfaces abstractas / puertos (`ports.py`) que definen cómo se comunica el dominio con el exterior.
*   **`src/application`**: Contiene la lógica del caso de uso (`services.py`) encapsulada en el orquestador principal.
*   **`src/infrastructure`**: Implementación de adaptadores específicos:
    *   `adapters/metrics.py`: Lectura nativa de Linux del rendimiento del sistema.
    *   `adapters/network.py`: Analizador de presencia en red local (tabla ARP).
    *   `adapters/camera.py`: Captura de cámara (OpenCV/Pillow).
    *   `web/server.py`: Controlador HTTP del servidor.
    *   `web/templates/index.html`: Interfaz de usuario web interactiva (desacoplada).

---

## Cómo Correr el Proyecto

Se incluye un script unificado de inicio llamado `run.sh` para facilitar la ejecución con un solo comando en terminales tipo Unix (Linux, macOS).

### 1. Ejecución con un solo comando (Local sin Docker)
Este modo creará automáticamente un entorno virtual de Python, instalará las dependencias necesarias de `requirements.txt` e iniciará el servidor:

```bash
./run.sh
```
*(Opcionalmente puedes forzar este modo con `./run.sh --local`)*.

### 2. Ejecución con Docker (Recomendado para servidores)
Este modo levantará el servicio dentro de un contenedor aislado usando Docker Compose:

```bash
./run.sh --docker
```
*(Opcionalmente puedes correrlo directamente usando `docker compose up --build`)*.

Una vez iniciado el servidor, accede a la interfaz desde tu navegador en:
👉 **[http://localhost:8080](http://localhost:8080)**

---

## Requisitos Previos

Si decides no usar el script `run.sh` y correr el proyecto manualmente paso a paso:

### Pasos Manuales (Sin Docker)
1. Crea y activa tu entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicia la aplicación:
   ```bash
   python -m src.main
   ```
