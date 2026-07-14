FROM python:3.11-slim

# Instalar dependencias necesarias del sistema (Git, Docker CLI y cliente de Docker Compose)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && curl -fsSL https://get.docker.com | sh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar el código fuente
COPY main.py .
COPY src/ ./src/

# Exponer el puerto
EXPOSE 8080

# Ejecutar el servidor
CMD ["python", "main.py"]
