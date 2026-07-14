# Imagen base de Python ligera
FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc y habilitar logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema requeridas por OpenCV (headless), Pillow y Docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY src/ /app/src/

# Exponer el puerto del servidor HTTP
EXPOSE 8080

# Comando para ejecutar la aplicación
CMD ["python", "-m", "src.main"]
