FROM python:3.11-slim

# Instalar dependencias necesarias del sistema (Git, Docker CLI, libcamera-tools para libcamerify y fswebcam)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    fswebcam \
    libcamera-tools \
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
