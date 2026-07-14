#!/bin/bash

# Script de arranque unificado para dashboardPi

# Detener la ejecución ante cualquier error simple
set -e

# Directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Función de ayuda
show_help() {
    echo "Uso: ./run.sh [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  --local     Ejecuta el proyecto localmente sin Docker (usa venv)."
    echo "  --docker    Ejecuta el proyecto dentro de un contenedor Docker."
    echo "  --help      Muestra esta ayuda."
    echo ""
    echo "Si no se pasa ninguna opción, se intentará correr localmente."
}

run_local() {
    echo "=== Iniciando dashboardPi localmente ==="
    
    # Crear entorno virtual si no existe
    if [ ! -d ".venv" ]; then
        echo "[INFO] Creando entorno virtual de Python (.venv)..."
        python3 -m venv .venv
    fi
    
    # Activar entorno virtual
    source .venv/bin/activate
    
    # Instalar dependencias
    if [ -f "requirements.txt" ]; then
        echo "[INFO] Instalando dependencias desde requirements.txt..."
        pip install -r requirements.txt
    else
        echo "[WARN] No se encontró requirements.txt. Instalando Pillow por defecto..."
        pip install Pillow
    fi
    
    # Ejecutar aplicación
    echo "[INFO] Iniciando servidor web..."
    python -m src.main
}

run_docker() {
    echo "=== Iniciando dashboardPi con Docker ==="
    
    if ! command -v docker &> /dev/null; then
        echo "[ERROR] Docker no está instalado en este sistema o no está en el PATH."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "[ERROR] Docker Compose no está instalado."
        exit 1
    fi
    
    echo "[INFO] Construyendo y levantando contenedores..."
    docker compose up --build
}

# Procesar parámetros
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_help
    exit 0
elif [ "$1" == "--docker" ]; then
    run_docker
elif [ "$1" == "--local" ] || [ -z "$1" ]; then
    run_local
else
    echo "Opción no reconocida: $1"
    show_help
    exit 1
fi
