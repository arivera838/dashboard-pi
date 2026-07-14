# Raspberry Pi 3 B+ Control Center

Centro de control ligero y panel de despliegues automatizado (CI/CD) diseñado específicamente para una **Raspberry Pi 3 B+**. Permite monitorear la salud del hardware, prender/apagar la interfaz gráfica de usuario para liberar RAM, interactuar con contenedores de Docker y clonar/desplegar repositorios Git mediante Docker Compose.

Este proyecto fue refactorizado utilizando una **Arquitectura Hexagonal (Ports & Adapters)** y sigue rigurosamente los principios **SOLID**.

---

## Estructura del Proyecto

```
dashboardPi/
├── Dockerfile              # Imagen ligera para dockerizar la app
├── docker-compose.yml      # Configuración de despliegue con montajes del sistema host
├── main.py                 # Punto de entrada y composición (Dependency Injection Root)
└── src/
    ├── domain/             # Modelos puros del negocio
    ├── application/        # Puertos (interfaces) y Servicios (Casos de Uso)
    └── adapters/
        ├── inbound/        # Servidor Web HTTP nativo (SimpleHTTPRequestHandler)
        └── outbound/       # Comandos del sistema, Git, Docker CLI y lecturas de /proc
```

---

## Cómo Ejecutar el Proyecto

### Opción 1: Con Docker (Recomendado)

Esta opción aísla la aplicación y monta de forma segura los recursos del host necesarios.

1. **Asegúrate de tener Docker y Docker Compose instalados en tu Raspberry Pi**:
   ```bash
   curl -sSL https://get.docker.com | sh
   ```

2. **Iniciar el panel de control**:
   ```bash
   docker compose up -d --build
   ```

3. **Verificar el estado**:
   ```bash
   docker compose ps
   ```

4. **Acceder**:
   Abre un navegador en la misma red local e ingresa a: `http://<IP-DE-TU-RASPBERRY>:8080` (ej: `http://192.168.1.22:8080`).

---

### Opción 2: Sin Docker (Ejecución Directa en Python)

Esta aplicación no tiene dependencias externas de librerías de Python (usa la librería estándar para mantener el consumo de recursos al mínimo).

1. **Clonar el proyecto** y ubicarse en la carpeta:
   ```bash
   cd dashboardPi
   ```

2. **Ejecutar el script principal**:
   ```bash
   python3 main.py
   ```

3. **Acceder**:
   Abre en tu navegador `http://localhost:8080` o `http://<IP-DE-TU-RASPBERRY>:8080`.

> **Nota**: Para interactuar con Docker y `lightdm` (GUI) sin Docker, asegúrate de que el usuario que ejecuta el script tenga permisos adecuados de sudoer o pertenezca al grupo `docker`.

---

## Funcionalidades del Centro de Control

* **Métricas de Hardware en Tiempo Real**: Carga de CPU (load 1 min), Temperatura en Celsius del procesador (`/sys/class/thermal`), consumo detallado de memoria RAM y SWAP (SD), y estado del almacenamiento principal.
* **Control de Interfaz de Escritorio**: Encendido y apagado del servidor de ventanas (`lightdm`) para liberar ~200MB de memoria RAM cuando no se use un monitor físico.
* **Administración de Docker**: Listado de contenedores instalados con capacidad de Encender, Apagar y Reiniciar contenedores desde la UI.
* **Despliegues Automáticos (CI/CD)**: Clona cualquier repositorio HTTPS de Git público y, si incluye un archivo `docker-compose.yml`, levanta los servicios construyendo las imágenes en segundo plano.
