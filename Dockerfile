FROM python:3.11-slim

# Instalar dependencias necesarias del sistema (Git, Docker CLI, libcamera, GStreamer y arp-scan)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    fswebcam \
    libcamera-tools \
    libcamera-v4l2 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libcamera \
    arp-scan \
    && curl -fsSL https://get.docker.com | sh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar el código fuente
COPY main.py .
COPY src/ ./src/

# Exponer el puerto de producción
EXPOSE 8083

# Ejecutar el servidor anteponiendo libcamerify para compatibilidad con cámaras CSI
CMD ["libcamerify", "python", "main.py"]
