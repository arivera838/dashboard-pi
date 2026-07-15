import http.server
import socketserver
import json
import subprocess
import os
import shutil
import re
from urllib.parse import parse_qs, urlparse

# Puerto donde correrá el Panel de Control
PORT = 8080

def get_system_metrics():
    """Extrae las métricas reales del hardware de la Raspberry Pi leyendo archivos del sistema."""
    metrics = {
        "cpu_load": "0.00",
        "cpu_temp": 0.0,
        "ram_total": 0,
        "ram_used": 0,
        "ram_free": 0,
        "ram_percent": 0,
        "swap_total": 0,
        "swap_used": 0,
        "swap_free": 0,
        "swap_percent": 0,
        "disk_total": 0,
        "disk_used": 0,
        "disk_free": 0,
        "disk_percent": 0
    }

    # 1. Carga de CPU (último minuto)
    try:
        with open("/proc/loadavg", "r") as f:
            metrics["cpu_load"] = f.read().strip().split()[0]
    except Exception:
        metrics["cpu_load"] = "0.00"

    # 2. Temperatura del Procesador
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            metrics["cpu_temp"] = round(float(f.read().strip()) / 1000.0, 1)
    except Exception:
        metrics["cpu_temp"] = 0.0

    # 3. RAM y SWAP (leyendo /proc/meminfo de manera súper eficiente)
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].replace(":", "")
                    val = int(parts[1]) * 1024  # Convertir KB a Bytes
                    meminfo[key] = val

        # Cálculos de RAM
        total_ram = meminfo.get("MemTotal", 0)
        free_ram = meminfo.get("MemFree", 0)
        avail_ram = meminfo.get("MemAvailable", free_ram)
        used_ram = total_ram - avail_ram
        metrics["ram_total"] = total_ram
        metrics["ram_used"] = used_ram
        metrics["ram_free"] = avail_ram
        metrics["ram_percent"] = round((used_ram / total_ram) * 100, 1) if total_ram > 0 else 0

        # Cálculos de SWAP
        total_swap = meminfo.get("SwapTotal", 0)
        free_swap = meminfo.get("SwapFree", 0)
        used_swap = total_swap - free_swap
        metrics["swap_total"] = total_swap
        metrics["swap_used"] = used_swap
        metrics["swap_free"] = free_swap
        metrics["swap_percent"] = round((used_swap / total_swap) * 100, 1) if total_swap > 0 else 0
    except Exception:
        pass

    # 4. Almacenamiento en Disco (USB principal /)
    try:
        total, used, free = shutil.disk_usage("/")
        metrics["disk_total"] = total
        metrics["disk_used"] = used
        metrics["disk_free"] = free
        metrics["disk_percent"] = round((used / total) * 100, 1) if total > 0 else 0
    except Exception:
        pass

    return metrics

def get_gui_status():
    """Consulta si la interfaz de escritorio gráfica (lightdm) está activa."""
    try:
        res = subprocess.run(["systemctl", "is-active", "lightdm"], capture_output=True, text=True)
        return res.stdout.strip() == "active"
    except Exception:
        return False

def get_docker_containers():
    """Obtiene la lista de contenedores Docker activos y pausados."""
    containers = []
    try:
        res = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}"],
            capture_output=True, text=True
        )
        lines = res.stdout.strip().split("\n")
        for line in lines:
            if "|" in line:
                cid, name, status, img = line.split("|")
                # Filtrar estados para simplificar vista en el UI
                is_running = "Up" in status
                containers.append({
                    "id": cid,
                    "name": name,
                    "status": status,
                    "image": img,
                    "running": is_running
                })
    except Exception as e:
        print(f"Error al listar Docker: {e}")
    return containers

def execute_ci_cd_deploy(repo_url, target_dir, app_name):
    """Clona un repositorio de Git, se ubica en su directorio y lanza docker-compose."""
    try:
        # 1. Asegurar ruta destino limpia
        base_path = os.path.expanduser(f"~/apps/{app_name}")
        if target_dir:
            base_path = os.path.abspath(target_dir)

        # 2. Clonar o Pull del Repositorio
        if not os.path.exists(base_path):
            os.makedirs(os.path.dirname(base_path), exist_ok=True)
            cmd = f"git clone {repo_url} {base_path}"
        else:
            cmd = f"cd {base_path} && git reset --hard && git pull"

        # Ejecución del comando de Git
        git_res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if git_res.returncode != 0:
            return False, f"Error Git: {git_res.stderr}"

        # 3. Detectar docker-compose y desplegar
        compose_file = os.path.join(base_path, "docker-compose.yml")
        deploy_log = "Repositorio descargado con éxito.\n"
        if os.path.exists(compose_file):
            deploy_log += "Detectado docker-compose.yml, levantando servicios...\n"
            docker_cmd = f"cd {base_path} && docker compose up -d --build"
            dock_res = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
            deploy_log += dock_res.stdout + "\n" + dock_res.stderr
            if dock_res.returncode != 0:
                return False, deploy_log

        return True, deploy_log
    except Exception as e:
        return False, str(e)

class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url_parsed = urlparse(self.path)
        
        # 1. API: Obtener Métricas de Sistema (JSON)
        if url_parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "system": get_system_metrics(),
                "gui_active": get_gui_status(),
                "docker_containers": get_docker_containers()
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 2. Servir la interfaz gráfica principal
        if url_parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        # Comportamiento por defecto para estáticos fallidos
        self.send_error(404, "Recurso no encontrado")

    def do_POST(self):
        url_parsed = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            params = json.loads(post_data)
        except Exception:
            params = {}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response_data = {"status": "error", "message": "Acción no reconocida"}

        # 1. API POST: Alternar la Interfaz de Escritorio (Desktop)
        if url_parsed.path == "/api/gui/toggle":
            action = params.get("action")
            if action == "start":
                res = subprocess.run(["sudo", "systemctl", "start", "lightdm"], capture_output=True, text=True)
                response_data = {"status": "success", "message": "Interfaz gráfica iniciada temporalmente."}
            elif action == "stop":
                res = subprocess.run(["sudo", "systemctl", "stop", "lightdm"], capture_output=True, text=True)
                response_data = {"status": "success", "message": "Interfaz gráfica detenida para ahorrar RAM."}

        # 2. API POST: Controlar Contenedores Docker (Start/Stop/Restart)
        elif url_parsed.path == "/api/docker/control":
            container_id = params.get("id")
            action = params.get("action") # start, stop, restart
            if container_id and action in ["start", "stop", "restart"]:
                res = subprocess.run(["docker", action, container_id], capture_output=True, text=True)
                if res.returncode == 0:
                    response_data = {"status": "success", "message": f"Contenedor {action}eado con éxito."}
                else:
                    response_data = {"status": "error", "message": res.stderr}

        # 3. API POST: CI/CD Desplegar Repositorio Git
        elif url_parsed.path == "/api/cicd/deploy":
            repo_url = params.get("repo_url")
            target_dir = params.get("target_dir")
            app_name = params.get("app_name", "mi-proyecto-web")
            
            if repo_url:
                success, log = execute_ci_cd_deploy(repo_url, target_dir, app_name)
                if success:
                    response_data = {"status": "success", "message": "¡Despliegue completado!", "log": log}
                else:
                    response_data = {"status": "error", "message": "Error durante el despliegue", "log": log}
            else:
                response_data = {"status": "error", "message": "Falta la URL del repositorio de Git."}

        self.wfile.write(json.dumps(response_data).encode("utf-8"))

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raspberry Pi 3 B+ Control Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #0b0f19;
        }
        .code-font {
            font-family: 'JetBrains Mono', monospace;
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0d1220;
        }
        ::-webkit-scrollbar-thumb {
            background: #10b981;
            border-radius: 4px;
        }
    </style>
</head>
<body class="text-gray-100 min-height-screen">

    <!-- Header -->
    <header class="border-b border-emerald-500/20 bg-gray-900/80 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="bg-emerald-500/10 text-emerald-400 p-2.5 rounded-xl border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                    <i class="fa-solid fa-microchip text-2xl"></i>
                </div>
                <div>
                    <h1 class="text-xl font-extrabold tracking-tight">Raspberry Pi 3 B+</h1>
                    <p class="text-xs text-emerald-400 font-semibold uppercase tracking-wider">Centro de Control & CI/CD</p>
                </div>
            </div>
            <div class="flex items-center gap-4">
                <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 animate-pulse">
                    <span class="h-2 w-2 rounded-full bg-emerald-400"></span> Online
                </span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-8">
        <!-- Grid de Estado y Métricas -->
        <section class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            
            <!-- CPU Load Card -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 relative overflow-hidden group hover:border-emerald-500/30 transition-all duration-300">
                <div class="flex justify-between items-start mb-4">
                    <span class="text-xs font-semibold tracking-wider uppercase text-gray-400">Carga CPU (1 min)</span>
                    <i class="fa-solid fa-gauge-high text-xl text-emerald-400"></i>
                </div>
                <div class="flex items-baseline gap-2">
                    <span id="stat-cpu-load" class="text-4xl font-extrabold tracking-tight code-font text-white">0.00</span>
                    <span class="text-sm text-gray-500">load</span>
                </div>
                <div class="w-full bg-gray-800 h-1.5 rounded-full mt-4 overflow-hidden">
                    <div id="stat-cpu-bar" class="bg-emerald-500 h-full transition-all duration-500" style="width: 10%"></div>
                </div>
            </div>

            <!-- Procesor Temp Card -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 relative overflow-hidden group hover:border-orange-500/30 transition-all duration-300">
                <div class="flex justify-between items-start mb-4">
                    <span class="text-xs font-semibold tracking-wider uppercase text-gray-400">Temperatura CPU</span>
                    <i class="fa-solid fa-temperature-three-quarters text-xl text-orange-400"></i>
                </div>
                <div class="flex items-baseline gap-2">
                    <span id="stat-cpu-temp" class="text-4xl font-extrabold tracking-tight code-font text-white">0.0</span>
                    <span class="text-sm text-gray-500">°C</span>
                </div>
                <div class="w-full bg-gray-800 h-1.5 rounded-full mt-4 overflow-hidden">
                    <div id="stat-temp-bar" class="bg-orange-500 h-full transition-all duration-500" style="width: 45%"></div>
                </div>
            </div>

            <!-- RAM Card -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 relative overflow-hidden group hover:border-blue-500/30 transition-all duration-300">
                <div class="flex justify-between items-start mb-4">
                    <span class="text-xs font-semibold tracking-wider uppercase text-gray-400">Memoria RAM</span>
                    <i class="fa-solid fa-memory text-xl text-blue-400"></i>
                </div>
                <div class="flex items-baseline gap-2">
                    <span id="stat-ram-percent" class="text-4xl font-extrabold tracking-tight code-font text-white">0%</span>
                    <span id="stat-ram-val" class="text-xs text-gray-500">0 / 0 MB</span>
                </div>
                <div class="w-full bg-gray-800 h-1.5 rounded-full mt-4 overflow-hidden">
                    <div id="stat-ram-bar" class="bg-blue-500 h-full transition-all duration-500" style="width: 50%"></div>
                </div>
            </div>

            <!-- SWAP Card (SD Virtual Memory) -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 relative overflow-hidden group hover:border-purple-500/30 transition-all duration-300">
                <div class="flex justify-between items-start mb-4">
                    <span class="text-xs font-semibold tracking-wider uppercase text-gray-400">SWAP (Memoria SD)</span>
                    <i class="fa-solid fa-sd-card text-xl text-purple-400"></i>
                </div>
                <div class="flex items-baseline gap-2">
                    <span id="stat-swap-percent" class="text-4xl font-extrabold tracking-tight code-font text-white">0%</span>
                    <span id="stat-swap-val" class="text-xs text-gray-500">0 / 0 MB</span>
                </div>
                <div class="w-full bg-gray-800 h-1.5 rounded-full mt-4 overflow-hidden">
                    <div id="stat-swap-bar" class="bg-purple-500 h-full transition-all duration-500" style="width: 20%"></div>
                </div>
            </div>

        </section>

        <!-- Bloque Principal de Configuración y CI/CD -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            <!-- Columna Izquierda: Configuración Rápida & Almacenamiento -->
            <div class="space-y-6 lg:col-span-1">
                
                <!-- Quick Settings -->
                <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                    <h2 class="text-lg font-bold mb-5 flex items-center gap-2">
                        <i class="fa-solid fa-sliders text-emerald-400"></i> Ajustes Rápidos
                    </h2>
                    
                    <!-- Toggle GUI Command -->
                    <div class="bg-gray-950 p-4 rounded-xl border border-gray-800/80 flex flex-col gap-3">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="font-bold text-sm text-white">Interfaz Gráfica (VNC)</h3>
                                <p class="text-xs text-gray-400">Controla el servidor de ventanas Desktop.</p>
                            </div>
                            <span id="gui-badge" class="px-2.5 py-0.5 rounded text-xs font-semibold bg-gray-800 text-gray-400">Consultando...</span>
                        </div>
                        <div class="grid grid-cols-2 gap-2 mt-2">
                            <button onclick="controlGUI('start')" class="px-3 py-2 bg-emerald-500 hover:bg-emerald-600 active:scale-95 transition-all text-white text-xs font-bold rounded-lg flex items-center justify-center gap-1.5">
                                <i class="fa-solid fa-play"></i> Encender
                            </button>
                            <button onclick="controlGUI('stop')" class="px-3 py-2 bg-red-500/15 hover:bg-red-500/25 border border-red-500/20 active:scale-95 transition-all text-red-400 text-xs font-bold rounded-lg flex items-center justify-center gap-1.5">
                                <i class="fa-solid fa-power-off"></i> Apagar RAM
                            </button>
                        </div>
                    </div>

                    <!-- Host Information -->
                    <div class="mt-6 space-y-3">
                        <div class="flex justify-between text-xs py-2 border-b border-gray-800">
                            <span class="text-gray-400">Host IP</span>
                            <span class="code-font font-semibold text-emerald-400">192.168.1.22</span>
                        </div>
                        <div class="flex justify-between text-xs py-2 border-b border-gray-800">
                            <span class="text-gray-400">Sistema Base</span>
                            <span class="font-semibold text-gray-200">Linux (ARM 64-bit)</span>
                        </div>
                        <div class="flex justify-between text-xs py-2">
                            <span class="text-gray-400">Ruta de despliegues</span>
                            <span class="code-font text-gray-200">/home/frivera/apps/</span>
                        </div>
                    </div>
                </div>

                <!-- USB Storage Status Card -->
                <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                    <h2 class="text-lg font-bold mb-5 flex items-center gap-2">
                        <i class="fa-solid fa-hard-drive text-blue-400"></i> Disco Principal (256GB USB)
                    </h2>
                    <div class="flex justify-between text-xs text-gray-400 mb-2">
                        <span>Espacio Utilizado: <strong id="stat-disk-used-val" class="text-white">0 GB</strong></span>
                        <span id="stat-disk-percent">0%</span>
                    </div>
                    <div class="w-full bg-gray-800 h-3 rounded-full overflow-hidden mb-4">
                        <div id="stat-disk-bar" class="bg-blue-500 h-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                    <div class="flex justify-between text-xs text-gray-500">
                        <span>Límite de Disco</span>
                        <span id="stat-disk-total-val">0 GB</span>
                    </div>
                </div>

            </div>

            <!-- Columna Derecha: Consola CI/CD y Aplicaciones Desplegadas -->
            <div class="space-y-6 lg:col-span-2">
                
                <!-- CI/CD Deploy App form -->
                <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                    <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-rocket text-indigo-400"></i> Desplegar Nueva App o Base de Datos (CI/CD)
                    </h2>
                    <p class="text-xs text-gray-400 mb-5">
                        Pega la URL de tu repositorio Git de GitHub o GitLab. Si tu proyecto tiene un archivo <strong class="text-indigo-400">docker-compose.yml</strong>, la Raspberry construirá la imagen y levantará el servicio en Docker automáticamente.
                    </p>

                    <form id="cicd-form" onsubmit="handleDeploy(event)" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-semibold text-gray-400 mb-1">Nombre de la Aplicación</label>
                                <input type="text" id="deploy-name" placeholder="ej. mi-chatbot-telegram" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-gray-400 mb-1">Ruta Destino (Opcional)</label>
                                <input type="text" id="deploy-path" placeholder="Dejar vacío para usar ruta default (~/apps)" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-400 mb-1">URL del Repositorio Git (HTTPS)</label>
                            <input type="url" id="deploy-repo" placeholder="https://github.com/usuario/mi-repositorio.git" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                        </div>

                        <div class="flex justify-end pt-2">
                            <button type="submit" id="deploy-btn" class="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 active:scale-95 transition-all text-white font-bold text-sm rounded-xl flex items-center gap-2">
                                <i class="fa-solid fa-code-branch"></i> Lanzar pipeline de Despliegue
                            </button>
                        </div>
                    </form>

                    <!-- Terminal Deployment Logs -->
                    <div id="logs-container" class="mt-6 hidden">
                        <h3 class="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
                            <i class="fa-solid fa-terminal text-emerald-400"></i> Log del Servidor en tiempo real:
                        </h3>
                        <pre id="deploy-logs" class="bg-gray-950 border border-gray-800 rounded-xl p-4 text-xs text-emerald-400 code-font overflow-x-auto max-h-60 overflow-y-auto">Iniciando pipeline...</pre>
                    </div>
                </div>

                <!-- Docker App Status Dashboard -->
                <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                    <div class="flex justify-between items-center mb-5">
                        <h2 class="text-lg font-bold flex items-center gap-2">
                            <i class="fa-brands fa-docker text-sky-400 text-xl"></i> Administrador de Docker
                        </h2>
                        <button onclick="refreshData()" class="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs text-gray-400 hover:text-white transition-colors">
                            <i class="fa-solid fa-arrows-rotate"></i>
                        </button>
                    </div>

                    <!-- Containers table -->
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="border-b border-gray-800 text-xs uppercase text-gray-400 tracking-wider">
                                    <th class="py-3 px-4 font-semibold">Contenedor</th>
                                    <th class="py-3 px-4 font-semibold">Imagen</th>
                                    <th class="py-3 px-4 font-semibold">Estado</th>
                                    <th class="py-3 px-4 font-semibold text-right">Controles Rápidos</th>
                                </tr>
                            </thead>
                            <tbody id="docker-list" class="divide-y divide-gray-800/50 text-sm">
                                <!-- Se rellena vía Javascript -->
                                <tr>
                                    <td colspan="4" class="py-8 text-center text-gray-500 text-xs">Cargando contenedores Docker activos...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>

        </div>
    </main>

    <!-- Modal Notificación -->
    <div id="toast" class="fixed bottom-6 right-6 bg-gray-900 border border-emerald-500/30 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-24 opacity-0 transition-all duration-300 z-50">
        <i id="toast-icon" class="fa-solid fa-circle-check text-emerald-400 text-lg"></i>
        <div>
            <h4 id="toast-title" class="font-bold text-sm text-white">Éxito</h4>
            <p id="toast-desc" class="text-xs text-gray-400">Configuración guardada de manera impecable.</p>
        </div>
    </div>

    <!-- Script de lógica e interacción en el Frontend -->
    <script>
        // Formateadores de Bytes
        function formatBytes(bytes, decimals = 2) {
            if (!+bytes) return '0 Bytes'
            const k = 1024
            const dm = decimals < 0 ? 0 : decimals
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
            const i = Math.floor(Math.log(bytes) / Math.log(k))
            return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
        }

        // Consultar métricas del backend de Python
        async function refreshData() {
            try {
                const res = await fetch("/api/status");
                const data = await res.json();
                
                // Actualizar métricas del sistema
                document.getElementById("stat-cpu-load").innerText = data.system.cpu_load;
                const cpuVal = Math.min(parseFloat(data.system.cpu_load) * 100, 100);
                document.getElementById("stat-cpu-bar").style.width = `${cpuVal}%`;

                document.getElementById("stat-cpu-temp").innerText = data.system.cpu_temp;
                const tempVal = Math.min((data.system.cpu_temp / 85) * 100, 100); // 85C es limite crítico
                document.getElementById("stat-temp-bar").style.width = `${tempVal}%`;

                document.getElementById("stat-ram-percent").innerText = `${data.system.ram_percent}%`;
                document.getElementById("stat-ram-bar").style.width = `${data.system.ram_percent}%`;
                document.getElementById("stat-ram-val").innerText = `${formatBytes(data.system.ram_used, 0)} / ${formatBytes(data.system.ram_total, 0)}`;

                document.getElementById("stat-swap-percent").innerText = `${data.system.swap_percent}%`;
                document.getElementById("stat-swap-bar").style.width = `${data.system.swap_percent}%`;
                document.getElementById("stat-swap-val").innerText = `${formatBytes(data.system.swap_used, 0)} / ${formatBytes(data.system.swap_total, 0)}`;

                // Disco USB
                document.getElementById("stat-disk-percent").innerText = `${data.system.disk_percent}%`;
                document.getElementById("stat-disk-bar").style.width = `${data.system.disk_percent}%`;
                document.getElementById("stat-disk-used-val").innerText = formatBytes(data.system.disk_used);
                document.getElementById("stat-disk-total-val").innerText = formatBytes(data.system.disk_total);

                // Badge de la Interfaz gráfica
                const guiBadge = document.getElementById("gui-badge");
                if (data.gui_active) {
                    guiBadge.innerText = "Activo (Desktop)";
                    guiBadge.className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                } else {
                    guiBadge.innerText = "Apagado (Consola)";
                    guiBadge.className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20";
                }

                // Lista de Docker
                renderDocker(data.docker_containers);

            } catch (err) {
                console.error("Error al refrescar estado:", err);
            }
        }

        function renderDocker(containers) {
            const tbody = document.getElementById("docker-list");
            if (!containers || containers.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="py-8 text-center text-gray-500 text-xs">No se encontraron contenedores Docker activos en esta Raspberry.</td></tr>`;
                return;
            }

            tbody.innerHTML = containers.map(c => `
                <tr class="border-b border-gray-800/30 hover:bg-gray-800/10">
                    <td class="py-3.5 px-4">
                        <div class="font-bold text-gray-200 code-font">${c.name}</div>
                        <div class="text-[10px] text-gray-500 code-font">${c.id}</div>
                    </td>
                    <td class="py-3.5 px-4 text-xs code-font text-gray-400">${c.image}</td>
                    <td class="py-3.5 px-4">
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${c.running ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}">
                            <span class="h-1.5 w-1.5 rounded-full ${c.running ? 'bg-emerald-400' : 'bg-red-400'}"></span>
                            ${c.running ? 'Corriendo' : 'Detenido'}
                        </span>
                    </td>
                    <td class="py-3.5 px-4 text-right">
                        <div class="flex justify-end gap-1.5">
                            ${c.running ? `
                                <button onclick="controlDocker('${c.id}', 'stop')" class="p-1.5 bg-gray-800 hover:bg-red-500/15 text-gray-400 hover:text-red-400 rounded-lg text-xs transition-colors" title="Detener">
                                    <i class="fa-solid fa-stop"></i>
                                </button>
                            ` : `
                                <button onclick="controlDocker('${c.id}', 'start')" class="p-1.5 bg-gray-800 hover:bg-emerald-500/15 text-gray-400 hover:text-emerald-400 rounded-lg text-xs transition-colors" title="Iniciar">
                                    <i class="fa-solid fa-play"></i>
                                </button>
                            `}
                            <button onclick="controlDocker('${c.id}', 'restart')" class="p-1.5 bg-gray-800 hover:bg-indigo-500/15 text-gray-400 hover:text-indigo-400 rounded-lg text-xs transition-colors" title="Reiniciar">
                                <i class="fa-solid fa-arrows-rotate"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }

        // Acciones Docker
        async function controlDocker(id, action) {
            try {
                const res = await fetch("/api/docker/control", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id, action })
                });
                const result = await res.json();
                if (result.status === "success") {
                    showToast("Docker", result.message, "success");
                    refreshData();
                } else {
                    showToast("Error", result.message, "error");
                }
            } catch (e) {
                showToast("Error", "No se pudo comunicar con el servidor.", "error");
            }
        }

        // Acciones Desktop GUI (lightdm)
        async function controlGUI(action) {
            try {
                const res = await fetch("/api/gui/toggle", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ action })
                });
                const result = await res.json();
                if (result.status === "success") {
                    showToast("Interfaz Gráfica", result.message, "success");
                    refreshData();
                } else {
                    showToast("Error", result.message, "error");
                }
            } catch (e) {
                showToast("Error", "Ocurrió un error en el servidor.", "error");
            }
        }

        // Pipeline de Despliegue de Aplicaciones (CI/CD)
        async function handleDeploy(event) {
            event.preventDefault();
            
            const btn = document.getElementById("deploy-btn");
            const logsContainer = document.getElementById("logs-container");
            const logsPre = document.getElementById("deploy-logs");
            
            const repo_url = document.getElementById("deploy-repo").value;
            const target_dir = document.getElementById("deploy-path").value;
            const app_name = document.getElementById("deploy-name").value;

            // Bloquear interfaz
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Desplegando app en segundo plano...`;
            logsContainer.classList.remove("hidden");
            logsPre.innerText = "Iniciando pipeline de despliegue...\\n[Git] Conectando con el repositorio remoto...\\n[Docker] Preparando ambiente...";

            try {
                const res = await fetch("/api/cicd/deploy", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ repo_url, target_dir, app_name })
                });
                const result = await res.json();
                
                if (result.status === "success") {
                    showToast("CI/CD Despliegue", "¡Tu aplicación se ha desplegado correctamente!", "success");
                    logsPre.innerText = result.log || "Despliegue completado con éxito sin logs adicionales.";
                } else {
                    showToast("Error de Despliegue", "El proceso falló en un paso intermedio.", "error");
                    logsPre.innerText = result.log || result.message;
                }
            } catch (err) {
                showToast("Error", "La petición de despliegue se interrumpió.", "error");
                logsPre.innerText = "Error crítico de conexión durante el despliegue.";
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-code-branch"></i> Lanzar pipeline de Despliegue`;
                refreshData();
            }
        }

        // Mostrar Notificación flotante (Toast)
        function showToast(title, desc, type = "success") {
            const toast = document.getElementById("toast");
            const icon = document.getElementById("toast-icon");
            document.getElementById("toast-title").innerText = title;
            document.getElementById("toast-desc").innerText = desc;

            if (type === "success") {
                toast.className = "fixed bottom-6 right-6 bg-gray-900 border border-emerald-500/30 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-0 opacity-100 transition-all duration-300 z-50";
                icon.className = "fa-solid fa-circle-check text-emerald-400 text-lg";
            } else {
                toast.className = "fixed bottom-6 right-6 bg-gray-900 border border-red-500/30 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-0 opacity-100 transition-all duration-300 z-50";
                icon.className = "fa-solid fa-circle-xmark text-red-400 text-lg";
            }

            setTimeout(() => {
                toast.className = "fixed bottom-6 right-6 bg-gray-900 border border-emerald-500/30 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-24 opacity-0 transition-all duration-300 z-50";
            }, 4000);
        }

        // Polling constante cada 4 segundos
        refreshData();
        setInterval(refreshData, 4000);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    handler = DashboardRequestHandler
    # Permitir la reutilización del puerto para evitar errores de enlace al reiniciar
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"==========================================================")
        print(f"🚀 ¡CENTRO DE CONTROL RASPBERRY PI 3 B+ INICIADO!")
        print(f"👉 Accede desde tu red en: http://192.168.1.22:{PORT}")
        print(f"==========================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido por el usuario.") 