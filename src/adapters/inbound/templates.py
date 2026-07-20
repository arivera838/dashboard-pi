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

    <!-- Alerta Global de Despliegue en curso -->
    <div id="global-deploy-alert" class="bg-indigo-600 border-b border-indigo-500 text-white px-4 py-2.5 text-center text-xs font-bold flex items-center justify-center gap-2 hidden z-40 relative">
        <i class="fa-solid fa-spinner animate-spin"></i>
        <span>Hay un despliegue de CI/CD ejecutándose en segundo plano para: <span id="global-deploy-app-name" class="underline"></span> (<span id="global-deploy-time">0s</span>)</span>
        <button onclick="focusDeploymentTab()" class="ml-4 px-2 py-0.5 bg-white/20 hover:bg-white/30 rounded text-[10px] uppercase font-bold tracking-wider transition-colors">Ver Progreso</button>
    </div>

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
        
        <!-- Tabs Navigation -->
        <div class="flex border-b border-gray-800 mb-8 gap-2">
            <button onclick="switchTab('dashboard')" id="tab-btn-dashboard" class="px-5 py-3 border-b-2 border-emerald-500 text-emerald-400 font-bold text-sm transition-all flex items-center gap-2">
                <i class="fa-solid fa-gauge-high"></i> Dashboard
            </button>
            <button onclick="switchTab('cameras')" id="tab-btn-cameras" class="px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-white font-bold text-sm transition-all flex items-center gap-2">
                <i class="fa-solid fa-camera"></i> Cámaras
            </button>
            <button onclick="switchTab('network')" id="tab-btn-network" class="px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-white font-bold text-sm transition-all flex items-center gap-2">
                <i class="fa-solid fa-network-wired"></i> Clientes de Red
            </button>
            <button onclick="switchTab('cicd')" id="tab-btn-cicd" class="px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-white font-bold text-sm transition-all flex items-center gap-2">
                <i class="fa-solid fa-rocket"></i> CI/CD & Despliegues
            </button>
        </div>

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

            <!-- Processor Temp Card -->
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

        <!-- SECCIÓN 1: DASHBOARD -->
        <section id="tab-content-dashboard" class="space-y-8">
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
                                <span class="code-font text-gray-200">~/apps/</span>
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
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">Nombre de la Aplicación</label>
                                    <input type="text" id="deploy-name" placeholder="ej. mi-chatbot-telegram" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                                </div>
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1 flex justify-between">
                                        <span>Rama (Git Branch)</span>
                                        <span id="branch-loader" class="text-indigo-400 hidden"><i class="fa-solid fa-circle-notch fa-spin"></i> Cargando...</span>
                                    </label>
                                    <select id="deploy-branch" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                                        <option value="main">main</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">Ruta Destino (Opcional)</label>
                                    <input type="text" id="deploy-path" placeholder="Dejar vacío para usar default (~/apps)" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                                </div>
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-gray-400 mb-1">URL del Repositorio Git (HTTPS)</label>
                                <input type="url" id="deploy-repo" list="deployed-apps-datalist" placeholder="https://github.com/usuario/mi-repositorio.git" required class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500" onblur="fetchBranches()">
                                <datalist id="deployed-apps-datalist"></datalist>
                            </div>

                            <div class="flex justify-end gap-3 pt-2">
                                <button type="button" id="btn-cancel-deploy" onclick="cancelActiveDeploy()" class="hidden px-5 py-3 bg-red-600 hover:bg-red-700 active:scale-95 transition-all text-white font-bold text-sm rounded-xl flex items-center gap-2">
                                    <i class="fa-solid fa-ban"></i> Cancelar Despliegue
                                </button>
                                <button type="submit" id="deploy-btn" class="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 active:scale-95 transition-all text-white font-bold text-sm rounded-xl flex items-center gap-2">
                                    <i class="fa-solid fa-code-branch"></i> Lanzar pipeline de Despliegue
                                </button>
                            </div>
                        </form>

                        <!-- Terminal Deployment Logs -->
                        <div id="logs-container" class="mt-6 hidden">
                            <div class="flex justify-between items-center mb-2">
                                <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                                    <i class="fa-solid fa-terminal text-emerald-400"></i> Log del Servidor en tiempo real:
                                </h3>
                                <span id="deploy-time-badge" class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20"></span>
                            </div>
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
                                        <th class="py-3 px-4 font-semibold">Puertos</th>
                                        <th class="py-3 px-4 font-semibold">Memoria</th>
                                        <th class="py-3 px-4 font-semibold">Estado</th>
                                        <th class="py-3 px-4 font-semibold text-right">Controles Rápidos</th>
                                    </tr>
                                </thead>
                                <tbody id="docker-list" class="divide-y divide-gray-800/50 text-sm">
                                    <tr>
                                        <td colspan="6" class="py-8 text-center text-gray-500 text-xs">Cargando contenedores Docker activos...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- SECCIÓN 2: CÁMARAS -->
        <section id="tab-content-cameras" class="hidden space-y-8">
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                <h2 class="text-lg font-bold mb-2 flex items-center gap-2">
                    <i class="fa-solid fa-video text-emerald-400"></i> Cámaras Conectadas (Streaming a 30 FPS)
                </h2>
                <p class="text-xs text-gray-400 mb-6">
                    Muestra las transmisiones en tiempo real. Utiliza los botones inferiores para iniciar/detener grabaciones directamente en tu Raspberry Pi.
                </p>

                <!-- Control de Plugins de Inteligencia Artificial (Visión) -->
                <div class="bg-gray-950 p-4 rounded-xl border border-gray-800 mb-6 flex flex-wrap items-center justify-between gap-4">
                    <div class="flex flex-col">
                        <span class="font-bold text-sm text-white flex items-center gap-1.5">
                            <i class="fa-solid fa-brain text-indigo-400"></i> Plugins de Inteligencia Artificial
                        </span>
                        <span class="text-[11px] text-gray-400">Activa el reconocimiento en tiempo real sobre los flujos de video.</span>
                    </div>
                    <div class="flex items-center gap-6">
                        <label class="relative inline-flex items-center cursor-pointer select-none">
                            <input type="checkbox" id="vision-face-toggle" onchange="updateVisionSettings()" class="sr-only peer">
                            <div class="w-9 h-5 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-gray-300 after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                            <span class="ml-2 text-xs font-bold text-gray-300">Reconocimiento Facial</span>
                        </label>
                        <label class="relative inline-flex items-center cursor-pointer select-none">
                            <input type="checkbox" id="vision-hand-toggle" onchange="updateVisionSettings()" class="sr-only peer">
                            <div class="w-9 h-5 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-gray-300 after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-500"></div>
                            <span class="ml-2 text-xs font-bold text-gray-300">Reconocimiento de Manos</span>
                        </label>
                    </div>
                </div>

                <div id="cameras-grid" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="col-span-2 text-center py-8 text-gray-500 text-xs">Cargando cámaras disponibles...</div>
                </div>
            </div>

            <!-- Listado de Grabaciones Guardadas -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                <div class="flex justify-between items-center mb-5">
                    <h2 class="text-lg font-bold flex items-center gap-2">
                        <i class="fa-solid fa-photo-film text-indigo-400"></i> Grabaciones de Video Almacenadas
                    </h2>
                    <button onclick="loadRecordings()" class="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs text-gray-400 hover:text-white transition-colors">
                        <i class="fa-solid fa-arrows-rotate"></i>
                    </button>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-gray-800 text-xs uppercase text-gray-400 tracking-wider">
                                <th class="py-3 px-4 font-semibold">Nombre del Archivo</th>
                                <th class="py-3 px-4 font-semibold text-right">Descargar</th>
                            </tr>
                        </thead>
                        <tbody id="recordings-list" class="divide-y divide-gray-800/50 text-sm">
                            <tr>
                                <td colspan="2" class="py-8 text-center text-gray-500 text-xs">No hay grabaciones de video registradas.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- SECCIÓN 3: RED WIFI -->
        <section id="tab-content-network" class="hidden">
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                <div class="flex justify-between items-center mb-5">
                    <h2 class="text-lg font-bold flex items-center gap-2">
                        <i class="fa-solid fa-wifi text-sky-400"></i> Dispositivos Conectados en la Red Local
                    </h2>
                    <div class="flex items-center gap-4">
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Ancho de Banda Total:</span>
                            <span id="total-bandwidth-indicator" class="text-sm font-bold text-sky-400 code-font bg-sky-500/10 px-3 py-1 rounded-full border border-sky-500/20">0.00 KB/s</span>
                        </div>
                        <label class="flex items-center cursor-pointer gap-2" title="Alertar cuando se conecte cualquier dispositivo nuevo">
                            <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Alerta Global</span>
                            <div class="relative">
                                <input type="checkbox" id="global-alert-toggle" class="sr-only" onchange="saveGlobalAlertPreference()">
                                <div class="block bg-gray-800 w-10 h-6 rounded-full border border-gray-700 transition-colors" id="global-alert-bg"></div>
                                <div class="dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition transform" id="global-alert-dot"></div>
                            </div>
                        </label>
                        <button onclick="refreshNetworkClients()" class="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs text-gray-400 hover:text-white transition-colors">
                            <i class="fa-solid fa-arrows-rotate"></i>
                        </button>
                    </div>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-gray-800 text-xs uppercase text-gray-400 tracking-wider">
                                <th class="py-3 px-4 font-semibold">Dispositivo</th>
                                <th class="py-3 px-4 font-semibold">Dirección IP</th>
                                <th class="py-3 px-4 font-semibold">Dirección MAC</th>
                                <th class="py-3 px-4 font-semibold">Interfaz</th>
                                <th class="py-3 px-4 font-semibold text-right">Consumo de Internet</th>
                            </tr>
                        </thead>
                        <tbody id="network-clients-list" class="divide-y divide-gray-800/50 text-sm">
                            <tr>
                                <td colspan="5" class="py-8 text-center text-gray-500 text-xs">Cargando lista de red...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

    </main>

    <!-- Modal Notificación -->
    <div id="toast" class="fixed bottom-6 right-6 bg-gray-900 border border-emerald-500/30 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-24 opacity-0 transition-all duration-300 z-50">
        <i id="toast-icon" class="fa-solid fa-circle-check text-emerald-400 text-lg"></i>
        <div>
            <h4 id="toast-title" class="font-bold text-sm text-white">Éxito</h4>
            <p id="toast-desc" class="text-xs text-gray-400">Configuración guardada de manera impecable.</p>
        </div>
    </div>

    <!-- Modal de Logs de Docker -->
    <div id="logs-modal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center hidden">
        <div class="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden mx-4">
            <!-- Modal Header -->
            <div class="px-6 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-950/40">
                <div class="flex items-center gap-2 text-sky-400">
                    <i class="fa-solid fa-terminal text-lg"></i>
                    <h3 class="font-bold text-white text-base">Logs del Contenedor: <span id="modal-container-name" class="text-sky-400"></span></h3>
                </div>
                <button onclick="closeLogsModal()" class="text-gray-400 hover:text-white transition-colors">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>
            <!-- Modal Body -->
            <div class="p-6 overflow-y-auto flex-1 bg-gray-950">
                <pre id="modal-logs-content" class="text-xs text-emerald-400 code-font whitespace-pre-wrap select-text"></pre>
            </div>
            <!-- Modal Footer -->
            <div class="px-6 py-4 border-t border-gray-800 flex justify-end bg-gray-950/40">
                <button onclick="closeLogsModal()" class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white font-bold text-sm rounded-lg transition-colors">
                    Cerrar
                </button>
            </div>
        </div>
    </div>

    <!-- Modal de Editar Nombre de Dispositivo (Alias) -->
    <div id="alias-modal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center hidden">
        <div class="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden mx-4">
            <div class="px-6 py-4 border-b border-gray-800 bg-gray-950/40 flex justify-between items-center">
                <h3 class="font-bold text-white text-base">Editar Nombre de Dispositivo</h3>
                <button onclick="closeAliasModal()" class="text-gray-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Dirección MAC</label>
                    <input type="text" id="alias-mac" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-sm text-gray-400 code-font outline-none" readonly>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Nombre Personalizado (Alias)</label>
                    <input type="text" id="alias-name" class="w-full bg-gray-950 border border-gray-800 focus:border-emerald-500 rounded-xl px-4 py-3 text-sm text-white outline-none transition-colors" placeholder="Ej. Mi Laptop Principal">
                </div>
                <div class="mt-4 pt-4 border-t border-gray-800">
                    <label class="flex items-center cursor-pointer gap-3">
                        <input type="checkbox" id="alias-alert-toggle" class="form-checkbox h-5 w-5 text-emerald-500 rounded bg-gray-950 border-gray-700 focus:ring-emerald-500 focus:ring-offset-gray-900">
                        <span class="text-sm font-semibold text-gray-300">Alertarme cuando este dispositivo se conecte</span>
                    </label>
                    <p class="text-[10px] text-gray-500 mt-1 ml-8">Reproducirá un sonido especial si este dispositivo aparece en la red.</p>
                </div>
                <div class="flex justify-end gap-3 pt-2">
                    <button onclick="closeAliasModal()" class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-bold transition-all">Cancelar</button>
                    <button onclick="saveAlias()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-all">Guardar</button>
                </div>
            </div>
        </div>
    </div>

    <!-- CI/CD Tab -->
    <section id="tab-content-cicd" class="hidden grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Deployments & Live Console -->
        <div class="lg:col-span-2 space-y-6">
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center gap-3">
                    <i class="fa-solid fa-rocket text-indigo-400"></i> Despliegues Activos (Ramas)
                </h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-800/50 text-gray-400 text-[10px] uppercase tracking-wider">
                                <th class="py-3 px-4 font-semibold rounded-tl-lg">Repositorio / App</th>
                                <th class="py-3 px-4 font-semibold">Rama / Ambiente</th>
                                <th class="py-3 px-4 font-semibold">Estado</th>
                                <th class="py-3 px-4 font-semibold">Subdominio Traefik</th>
                                <th class="py-3 px-4 font-semibold text-right rounded-tr-lg">Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="cicd-deployments-list" class="text-sm">
                            <tr><td colspan="5" class="py-8 text-center text-gray-500 text-xs">Cargando despliegues...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="bg-gray-950 border border-gray-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-indigo-500"></div>
                <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-3">
                    <i class="fa-solid fa-terminal text-emerald-400"></i> Consola de Build en Vivo
                </h2>
                <div class="bg-black border border-gray-800 rounded-lg p-4 font-mono text-xs overflow-y-auto h-64 text-gray-300" id="cicd-terminal">
                    <div class="text-gray-500 italic">Esperando eventos de Webhook...</div>
                </div>
            </div>
        </div>

        <!-- Columna de Configuración (1/3 de ancho en pantallas grandes) -->
        <div class="space-y-6">
            <!-- Autocreador de Webhooks -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
                <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-3">
                    <i class="fa-brands fa-github text-emerald-400 text-2xl"></i> Autocreador de Webhooks
                </h2>
                <p class="text-xs text-gray-400 mb-4">Registra automáticamente el webhook de push en tu repositorio de GitHub usando tu Token guardado.</p>
                <form id="cicd-webhook-form" class="space-y-3">
                    <div>
                        <label class="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Dueño / Organización</label>
                        <input type="text" id="webhook-owner" placeholder="Ej: afrivera" required class="w-full bg-gray-950 border border-gray-800 text-white rounded-xl py-2 px-3 text-xs placeholder-gray-700 focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Nombre del Repositorio</label>
                        <input type="text" id="webhook-repo" placeholder="Ej: Rivera-cv" required class="w-full bg-gray-950 border border-gray-800 text-white rounded-xl py-2 px-3 text-xs placeholder-gray-700 focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">URL Pública / IP de tu Raspberry</label>
                        <input type="text" id="webhook-public-url" placeholder="Ej: http://tu-ip-o-dominio:8083" required class="w-full bg-gray-950 border border-gray-800 text-white rounded-xl py-2 px-3 text-xs placeholder-gray-700 focus:outline-none focus:border-emerald-500">
                    </div>
                    <button type="submit" id="btn-create-webhook" class="w-full bg-emerald-600 hover:bg-emerald-700 active:scale-95 transition-all text-white py-2.5 rounded-xl font-bold text-xs shadow-lg shadow-emerald-500/10">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> Crear Webhook en GitHub
                    </button>
                </form>
            </div>

            <!-- Credentials configuration form -->
            <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center gap-3">
                    <i class="fa-solid fa-key text-indigo-400"></i> Credenciales de Git & Alertas
                </h2>
                <form id="cicd-config-form" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Token de Git (Access Token)</label>
                        <input type="password" id="cfg-git-token" placeholder="Ej: github_pat_..." class="w-full bg-gray-950 border border-gray-800 text-white rounded-xl py-2.5 px-3.5 text-xs placeholder-gray-700 focus:outline-none focus:border-indigo-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Secreto de Webhook</label>
                        <input type="password" id="cfg-webhook-secret" placeholder="Secreto compartido para validar firmas" class="w-full bg-gray-950 border border-gray-800 text-white rounded-xl py-2.5 px-3.5 text-xs placeholder-gray-700 focus:outline-none focus:border-indigo-500">
                    </div>
                    
                    <div class="border-t border-gray-800 my-4 pt-4">
                        <h3 class="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                            <i class="fa-brands fa-telegram text-sky-400"></i> Alertas Telegram
                        </h3>
                        <div class="space-y-3">
                            <div>
                                <label class="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Bot Token</label>
                                <input type="password" id="cfg-telegram-token" placeholder="Token del bot" class="w-full bg-gray-950 border border-gray-800 text-white rounded-xl py-2 px-3 text-xs placeholder-gray-700 focus:outline-none focus:border-indigo-500">
                            </div>
                            <div>
                                <label class="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Chat ID</label>
                                <input type="text" id="cfg-telegram-chat-id" placeholder="ID de chat" class="w-full bg-gray-950 border border-gray-800 text-white rounded-xl py-2 px-3 text-xs placeholder-gray-700 focus:outline-none focus:border-indigo-500">
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 active:scale-95 transition-all text-white py-2.5 rounded-xl font-bold text-xs shadow-lg shadow-indigo-500/10">
                        <i class="fa-solid fa-save"></i> Guardar Configuración
                    </button>
                </form>
            </div>
        </div>
    </section>

    <!-- Script de lógica e interacción en el Frontend -->
    <!-- Wi-Fi Scan Modal -->
    <div id="wifi-modal" class="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-gray-900 border border-gray-800 w-full max-w-lg rounded-2xl shadow-2xl p-6 flex flex-col gap-6 relative">
            <button onclick="closeWifiModal()" class="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors">
                <i class="fa-solid fa-xmark text-xl"></i>
            </button>
            
            <h2 class="text-xl font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-wifi text-emerald-400"></i> Redes Disponibles
            </h2>
            
            <div id="wifi-loader" class="flex flex-col items-center justify-center py-10 hidden">
                <i class="fa-solid fa-circle-notch fa-spin text-3xl text-emerald-500 mb-4"></i>
                <p class="text-gray-400 text-sm">Escaneando redes WiFi...</p>
            </div>
            
            <div id="wifi-list" class="flex flex-col gap-2 max-h-60 overflow-y-auto hidden">
                <!-- Redes inyectadas via JS -->
            </div>
            
            <div id="wifi-connect-box" class="bg-gray-950 p-4 rounded-xl border border-gray-800 hidden flex flex-col gap-3 mt-2">
                <p class="text-sm text-gray-300 font-medium">Conectar a <span id="wifi-selected-ssid" class="text-sky-400 font-bold"></span></p>
                <input type="password" id="wifi-password" placeholder="Contraseña (opcional)" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors">
                <div class="flex gap-2">
                    <button onclick="cancelWifiConnect()" class="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm font-semibold transition-colors">Cancelar</button>
                    <button onclick="connectWifi()" class="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition-colors flex justify-center items-center gap-2">
                        <i id="wifi-connecting-icon" class="fa-solid fa-circle-notch fa-spin hidden"></i> Conectar
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Video Player Modal -->
    <div id="video-modal" class="fixed inset-0 bg-black/95 z-50 hidden flex items-center justify-center p-4">
        <div class="relative w-full max-w-4xl">
            <button onclick="closeVideoModal()" class="absolute -top-10 right-0 text-white hover:text-gray-300 transition-colors z-10">
                <i class="fa-solid fa-xmark text-2xl"></i>
            </button>
            <video id="video-player" controls autoplay class="w-full rounded-lg shadow-2xl bg-black aspect-video border border-gray-800"></video>
            <p id="video-title" class="text-center text-gray-400 mt-2 font-mono text-sm"></p>
        </div>
    </div>

    <script>
        let activeTab = "dashboard";
        let recordingStatusInterval = null;

        function switchTab(tabId) {
            activeTab = tabId;
            
            // Ocultar todos los contenidos
            document.getElementById("tab-content-dashboard").classList.add("hidden");
            document.getElementById("tab-content-cameras").classList.add("hidden");
            document.getElementById("tab-content-network").classList.add("hidden");
            document.getElementById("tab-content-cicd").classList.add("hidden");

            // Mostrar el activo
            document.getElementById(`tab-content-${tabId}`).classList.remove("hidden");

            // Actualizar diseño de botones
            const tabs = ["dashboard", "cameras", "network", "cicd"];
            tabs.forEach(t => {
                const btn = document.getElementById(`tab-btn-${t}`);
                if (btn) {
                    if (t === tabId) {
                        btn.className = "px-5 py-3 border-b-2 border-emerald-500 text-emerald-400 font-bold text-sm transition-all flex items-center gap-2";
                    } else {
                        btn.className = "px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-white font-bold text-sm transition-all flex items-center gap-2";
                    }
                }
            });

            // Disparar acciones según pestaña activa
            if (tabId === "cameras") {
                loadCameraList();
                loadRecordings();
                loadVisionSettings();
                startStatusPolling();
            } else {
                stopStatusPolling();
            }

            if (tabId === "network") {
                refreshNetworkClients();
            }

            if (tabId === "cicd") {
                loadCICDConfig();
                loadDeploymentsList();
            }
        }

        async function loadCICDConfig() {
            try {
                const res = await fetch("/api/cicd/config");
                const data = await res.json();
                
                document.getElementById("cfg-git-token").value = data.git_token || "";
                document.getElementById("cfg-webhook-secret").value = data.webhook_secret || "";
                document.getElementById("cfg-telegram-token").value = data.telegram_token || "";
                document.getElementById("cfg-telegram-chat-id").value = data.telegram_chat_id || "";
            } catch (err) {
                console.error("Error al cargar config de CI/CD:", err);
            }
        }

        async function loadDeploymentsList() {
            try {
                const res = await fetch("/api/cicd/deployments");
                const deployments = await res.json();
                const tbody = document.getElementById("cicd-deployments-list");
                
                if (!deployments || Object.keys(deployments).length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-gray-500 text-xs">No hay proyectos de despliegues o ramas activas en Docker.</td></tr>`;
                    return;
                }
                
                tbody.innerHTML = Object.entries(deployments).map(([name, app]) => {
                    let repo = name;
                    let env = "producción (main)";
                    
                    const branches = ["-dev", "-stage", "-main"];
                    for (const b of branches) {
                        if (name.endsWith(b)) {
                            repo = name.slice(0, -b.length);
                            env = b.slice(1);
                            break;
                        }
                    }
                    
                    const statusClass = app.status === "running" || app.status === "success" 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : (app.status === "queued" ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20');
                        
                    const statusLabel = app.status === "running" || app.status === "success" ? "Activo" : (app.status === "queued" ? "En Cola" : "Error");
                    const subdomainLink = app.subdomain && app.subdomain !== "—" 
                        ? `<a href="http://${app.subdomain}" target="_blank" class="text-indigo-400 hover:text-indigo-300 underline font-semibold">${app.subdomain}</a>` 
                        : "—";
                        
                    return `
                        <tr class="border-b border-gray-800/30 hover:bg-gray-800/10">
                            <td class="py-3.5 px-4 font-bold text-gray-200">${repo}</td>
                            <td class="py-3.5 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">${env}</td>
                            <td class="py-3.5 px-4">
                                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${statusClass}">
                                    ${statusLabel}
                                </span>
                            </td>
                            <td class="py-3.5 px-4 text-xs code-font">${subdomainLink}</td>
                            <td class="py-3.5 px-4 text-right">
                                <button onclick="showDockerLogs('${name}', '${name}')" class="p-1.5 bg-gray-800 hover:bg-sky-500/15 text-gray-400 hover:text-sky-400 rounded-lg text-xs transition-colors" title="Ver Logs">
                                    <i class="fa-solid fa-file-lines"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            } catch (err) {
                console.error("Error al cargar la lista de despliegues:", err);
            }
        }

        // Listener para guardar la configuración de CI/CD
        document.getElementById("cicd-config-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const git_token = document.getElementById("cfg-git-token").value;
            const webhook_secret = document.getElementById("cfg-webhook-secret").value;
            const telegram_token = document.getElementById("cfg-telegram-token").value;
            const telegram_chat_id = document.getElementById("cfg-telegram-chat-id").value;
            
            try {
                const res = await fetch("/api/cicd/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        git_token,
                        webhook_secret,
                        telegram_token,
                        telegram_chat_id
                    })
                });
                
                const data = await res.json();
                if (data.status === "success") {
                    showToast("CI/CD Ajustes", "¡Configuración guardada correctamente!", "success");
                    loadCICDConfig(); // Recargar para enmascarar valores
                } else {
                    showToast("Error", data.message || "No se pudo guardar la configuración.", "error");
                }
            } catch (err) {
                showToast("Error", "Error de conexión con el servidor.", "error");
            }
        });

        // Listener para registrar webhook en GitHub automáticamente
        document.getElementById("cicd-webhook-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("btn-create-webhook");
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-circle-notch animate-spin"></i> Creando Webhook...`;
            
            const owner = document.getElementById("webhook-owner").value;
            const repo = document.getElementById("webhook-repo").value;
            const public_url = document.getElementById("webhook-public-url").value;
            
            try {
                const res = await fetch("/api/cicd/github/webhook/create", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ owner, repo, public_url })
                });
                const data = await res.json();
                
                if (data.status === "success") {
                    showToast("GitHub Webhook", data.message, "success");
                } else {
                    showToast("Error Webhook", data.message || "No se pudo crear el webhook.", "error");
                }
            } catch (err) {
                showToast("Error", "Error de conexión con el servidor.", "error");
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Crear Webhook en GitHub`;
            }
        });

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
            if (activeTab !== "dashboard") return;
            try {
                const res = await fetch("/api/status");
                const data = await res.json();
                
                // Actualizar métricas del sistema
                document.getElementById("stat-cpu-load").innerText = data.system.cpu_load;
                const cpuVal = Math.min(parseFloat(data.system.cpu_load) * 100, 100);
                document.getElementById("stat-cpu-bar").style.width = `${cpuVal}%`;

                document.getElementById("stat-cpu-temp").innerText = data.system.cpu_temp;
                const tempVal = Math.min((data.system.cpu_temp / 85) * 100, 100);
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
                tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-gray-500 text-xs">No se encontraron contenedores Docker activos en esta Raspberry.</td></tr>`;
                return;
            }

            tbody.innerHTML = containers.map(c => `
                <tr class="border-b border-gray-800/30 hover:bg-gray-800/10">
                    <td class="py-3.5 px-4">
                        <div class="font-bold text-gray-200 code-font">${c.name}</div>
                        <div class="text-[10px] text-gray-500 code-font">${c.id}</div>
                    </td>
                    <td class="py-3.5 px-4 text-xs code-font text-gray-400">${c.image}</td>
                    <td class="py-3.5 px-4 text-xs code-font text-gray-400">${c.ports || '—'}</td>
                    <td class="py-3.5 px-4 text-xs code-font text-emerald-400">${c.memory_usage || 'N/A'}</td>
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
                            <button onclick="showDockerLogs('${c.id}', '${c.name}')" class="p-1.5 bg-gray-800 hover:bg-sky-500/15 text-gray-400 hover:text-sky-400 rounded-lg text-xs transition-colors" title="Ver Logs">
                                <i class="fa-solid fa-file-lines"></i>
                            </button>
                            <button onclick="controlDocker('${c.id}', 'remove')" class="p-1.5 bg-gray-800 hover:bg-red-500/15 text-gray-400 hover:text-red-500 rounded-lg text-xs transition-colors" title="Eliminar">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }

        // Acciones Docker
        async function controlDocker(id, action) {
            if (action === "remove") {
                if (!confirm("¿Estás seguro de que deseas eliminar este contenedor de forma permanente?")) {
                    return;
                }
            }
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

        // Logs de Docker
        async function showDockerLogs(id, name) {
            document.getElementById("modal-container-name").innerText = name;
            document.getElementById("modal-logs-content").innerText = "Cargando logs...";
            document.getElementById("logs-modal").classList.remove("hidden");
            try {
                const res = await fetch(`/api/docker/logs?id=${id}`);
                const data = await res.json();
                if (data.status === "success") {
                    document.getElementById("modal-logs-content").innerText = data.logs || "No hay logs registrados para este contenedor.";
                } else {
                    document.getElementById("modal-logs-content").innerText = data.message || "Error al leer logs.";
                }
            } catch (err) {
                document.getElementById("modal-logs-content").innerText = "Error de conexión al cargar los logs.";
            }
        }

        function closeLogsModal() {
            document.getElementById("logs-modal").classList.add("hidden");
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
            const branch = document.getElementById("deploy-branch").value;

            try {
                const res = await fetch("/api/cicd/deploy", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ repo_url, target_dir, app_name, branch })
                });
                const result = await res.json();
                
                if (result.status === "success" || result.status === "running") {
                    showToast("CI/CD Despliegue", "Inicio del pipeline solicitado en segundo plano.", "success");
                    // Disparar chequeo inmediato
                    setTimeout(checkActiveDeployments, 100);
                } else {
                    showToast("Error de Despliegue", result.message, "error");
                    logsContainer.classList.remove("hidden");
                    logsPre.innerText = result.message;
                }
            } catch (err) {
                showToast("Error", "La petición de despliegue se interrumpió.", "error");
                logsContainer.classList.remove("hidden");
                logsPre.innerText = "Error crítico de conexión durante la solicitud de despliegue.";
            }
        }

        async function cancelActiveDeploy() {
            if (!activeDeployApp) {
                showToast("Atención", "No hay despliegue activo para cancelar en esta pestaña.", "error");
                return;
            }
            if (!confirm(`¿Estás seguro de cancelar el despliegue actual de ${activeDeployApp}?`)) return;

            const cancelBtn = document.getElementById("btn-cancel-deploy");
            if (cancelBtn) cancelBtn.disabled = true;
            
            try {
                const res = await fetch("/api/cicd/deploy/cancel", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ app_name: activeDeployApp })
                });
                const result = await res.json();
                
                if (result.status === "success") {
                    showToast("Cancelado", result.message, "success");
                } else {
                    showToast("Error", result.message, "error");
                }
            } catch (err) {
                showToast("Error", "La petición de cancelación falló.", "error");
            } finally {
                if (cancelBtn) cancelBtn.disabled = false;
            }
        }

        // --- MÉTODOS DE CÁMARAS ---
        async function loadCameraList() {
            try {
                const res = await fetch("/api/camera/list");
                const cameras = await res.json();
                const grid = document.getElementById("cameras-grid");
                
                if (!cameras || cameras.length === 0) {
                    grid.innerHTML = `<div class="col-span-2 text-center py-8 text-gray-500 text-xs">No se detectaron cámaras conectadas en la Raspberry Pi.</div>`;
                    return;
                }

                const internalCamerasHTML = cameras.map(cam => `
                    <div class="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden p-4 flex flex-col gap-3">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-sm text-white">${cam.name}</span>
                            <div class="flex gap-1.5 items-center">
                                <span id="recording-badge-${cam.id}" class="hidden px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 uppercase animate-pulse flex items-center gap-1">
                                    <span class="h-1.5 w-1.5 bg-red-500 rounded-full"></span> REC <span id="recording-timer-${cam.id}">00:00</span>
                                </span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">${cam.type}</span>
                            </div>
                        </div>
                        
                        <!-- Transmisión de Video Fluido vía MJPEG /api/camera/stream -->
                        <div class="bg-gray-900 border border-gray-800/50 rounded-lg aspect-video flex items-center justify-center overflow-hidden relative">
                            <img class="w-full h-full object-cover" src="/api/camera/stream?id=${cam.id}" alt="Stream" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'100%\' height=\'100%\'><rect width=\'100%\' height=\'100%\' fill=\'%23111827\'/><text x=\'50%\' y=\'50%\' font-family=\'sans-serif\' font-size=\'14\' fill=\'%23ef4444\' text-anchor=\'middle\'>Conexión Perdida</text></svg>'; showToast('Cámara', 'La conexión con la cámara se ha perdido', 'error');">
                            <div class="absolute bottom-2 left-2 px-2 py-1 rounded bg-black/70 text-[9px] text-gray-300 code-font flex items-center gap-1">
                                <span class="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse"></span> LIVE (30 FPS)
                            </div>
                        </div>
                        
                        <!-- Botón para Iniciar/Detener Grabación -->
                        <div class="flex justify-end pt-1">
                            <button id="record-btn-${cam.id}" onclick="toggleRecording('${cam.id}')" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2">
                                <i class="fa-solid fa-circle text-[8px] text-red-400 animate-pulse"></i> Iniciar Grabación
                            </button>
                        </div>
                    </div>
                `).join('');

                const externalCameraHTML = `
                    <div class="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden p-4 flex flex-col gap-3">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-sm text-white">Cámara Externa (IP)</span>
                            <div class="flex gap-1.5 items-center">
                                <span id="recording-badge-external_ip" class="hidden px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 uppercase animate-pulse flex items-center gap-1">
                                    <span class="h-1.5 w-1.5 bg-red-500 rounded-full"></span> REC <span id="recording-timer-external_ip">00:00</span>
                                </span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20 uppercase">192.168.25.1</span>
                            </div>
                        </div>
                        
                        <div class="bg-gray-900 border border-gray-800/50 rounded-lg aspect-video flex items-center justify-center overflow-hidden relative">
                            <img id="external-cam-stream" class="w-full h-full object-cover" src="/api/camera/external_stream?w=1920&h=1080&fps=30" alt="External Stream" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'100%\' height=\'100%\'><rect width=\'100%\' height=\'100%\' fill=\'%23111827\'/><text x=\'50%\' y=\'50%\' font-family=\'sans-serif\' font-size=\'14\' fill=\'%23ef4444\' text-anchor=\'middle\'>Conexión Perdida</text></svg>';">
                            <div class="absolute bottom-2 left-2 px-2 py-1 rounded bg-black/70 text-[9px] text-gray-300 code-font flex items-center gap-1">
                                <span class="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse"></span> LIVE
                            </div>
                        </div>
                        
                        <!-- Controles de Calidad -->
                        <div class="flex items-center gap-3 pt-1">
                            <select id="external-cam-res" onchange="updateExternalCamera()" class="bg-gray-900 border border-gray-800 text-xs text-white rounded-lg px-2 py-2 focus:outline-none focus:border-emerald-500 cursor-pointer">
                                <option value="1920x1080">1920x1080 (FHD)</option>
                                <option value="1280x720">1280x720 (HD)</option>
                                <option value="640x480">640x480 (VGA)</option>
                            </select>
                            <select id="external-cam-fps" onchange="updateExternalCamera()" class="bg-gray-900 border border-gray-800 text-xs text-white rounded-lg px-2 py-2 focus:outline-none focus:border-emerald-500 cursor-pointer">
                                <option value="30">30 FPS</option>
                                <option value="15">15 FPS</option>
                                <option value="5">5 FPS</option>
                            </select>
                        </div>

                        <!-- Botones de Acción Externa -->
                        <div class="flex justify-between items-center pt-2 mt-1 border-t border-gray-800">
                            <button onclick="openWifiModal()" class="px-3 py-2 bg-gray-800 hover:bg-gray-700 active:scale-95 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2">
                                <i class="fa-solid fa-wifi text-[10px] text-sky-400"></i> Buscar Cámaras IP
                            </button>
                            <button id="record-btn-external_ip" onclick="toggleRecording('external_ip')" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2">
                                <i class="fa-solid fa-circle text-[8px] text-red-400 animate-pulse"></i> Iniciar Grabación
                            </button>
                        </div>
                    </div>
                `;

                grid.innerHTML = internalCamerasHTML + externalCameraHTML;

                pollRecordingsStatus();
            } catch (err) {
                console.error("Error cargando cámaras:", err);
            }
        }

        // --- MÉTODOS DE CÁMARA EXTERNA ---
        function updateExternalCamera() {
            const res = document.getElementById("external-cam-res").value.split("x");
            const fps = document.getElementById("external-cam-fps").value;
            const img = document.getElementById("external-cam-stream");
            
            if (img) {
                // Se genera un timestamp o random query param extra para forzar el recargo de MJPEG
                const cacheBuster = new Date().getTime();
                img.src = `/api/camera/external_stream?w=${res[0]}&h=${res[1]}&fps=${fps}&_t=${cacheBuster}`;
                showToast("Ajustes Actualizados", `Cámara configurada a ${res[0]}x${res[1]} @ ${fps} FPS`);
            }
        }

        // Grabar/Detener cámara
        async function toggleRecording(cameraId) {
            const btn = document.getElementById(`record-btn-${cameraId}`);
            const isRecording = btn.classList.contains("bg-red-600"); // Si está en rojo, está grabando

            const endpoint = isRecording ? "/api/camera/record/stop" : "/api/camera/record/start";
            
            try {
                const res = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id: cameraId })
                });
                const result = await res.json();
                
                if (result.status === "success") {
                    showToast("Grabadora", result.message, "success");
                    pollRecordingsStatus();
                    loadRecordings();
                } else {
                    showToast("Error", result.message, "error");
                }
            } catch (e) {
                showToast("Error", "No se pudo comunicar con el servidor de cámara.", "error");
            }
        }

        // --- MÉTODOS DE AJUSTES DE INTELIGENCIA ARTIFICIAL (ROSTROS/MANOS) ---
        async function loadVisionSettings() {
            try {
                const res = await fetch("/api/camera/vision/settings");
                const settings = await res.json();
                document.getElementById("vision-face-toggle").checked = settings.face_enabled;
                document.getElementById("vision-hand-toggle").checked = settings.hand_enabled;
            } catch (err) {
                console.error("Error al cargar ajustes de visión:", err);
            }
        }

        async function updateVisionSettings() {
            const face = document.getElementById("vision-face-toggle").checked;
            const hand = document.getElementById("vision-hand-toggle").checked;
            
            try {
                const res = await fetch("/api/camera/vision/settings", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ face_enabled: face, hand_enabled: hand })
                });
                const result = await res.json();
                if (result.status === "success") {
                    showToast("IA Visión", "Ajustes de reconocimiento actualizados", "success");
                } else {
                    showToast("Error", result.message, "error");
                }
            } catch (err) {
                showToast("Error", "No se pudieron guardar los ajustes de visión.", "error");
            }
        }

        // Consulta estado de grabación y actualiza temporizadores
        async function pollRecordingsStatus() {
            const imgs = document.querySelectorAll("[id^='record-btn-']");
            for (let btn of imgs) {
                const cameraId = btn.id.replace("record-btn-", "");
                try {
                    const res = await fetch(`/api/camera/record/status?id=${cameraId}`);
                    const status = await res.json();
                    
                    const badge = document.getElementById(`recording-badge-${cameraId}`);
                    const timer = document.getElementById(`recording-timer-${cameraId}`);
                    
                    if (status.is_recording) {
                        // Cambiar botón a Detener
                        btn.className = "px-4 py-2 bg-red-600 hover:bg-red-700 active:scale-95 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2";
                        btn.innerHTML = `<i class="fa-solid fa-square text-[8px]"></i> Detener Grabación`;
                        
                        // Mostrar Badge y Temporizador
                        badge.classList.remove("hidden");
                        
                        const mins = String(Math.floor(status.elapsed_time / 60)).padStart(2, '0');
                        const secs = String(status.elapsed_time % 60).padStart(2, '0');
                        timer.innerText = `${mins}:${secs}`;
                    } else {
                        // Cambiar botón a Iniciar
                        btn.className = "px-4 py-2 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-2";
                        btn.innerHTML = `<i class="fa-solid fa-circle text-[8px] text-red-400 animate-pulse"></i> Iniciar Grabación`;
                        badge.classList.add("hidden");
                    }
                } catch (e) {
                    console.error("Error al consultar estado de grabación:", e);
                }
            }
        }

        // Cargar grabaciones guardadas en disco
        async function loadRecordings() {
            const tbody = document.getElementById("recordings-list");
            try {
                const res = await fetch("/api/camera/recordings");
                const files = await res.json();
                
                if (!files || files.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="2" class="py-8 text-center text-gray-500 text-xs">No hay grabaciones de video guardadas en la Raspberry Pi.</td></tr>`;
                    return;
                }

                tbody.innerHTML = files.map(file => `
                    <tr class="border-b border-gray-800/30 hover:bg-gray-800/10">
                        <td class="py-3.5 px-4 font-bold text-gray-300 code-font flex items-center gap-2">
                            <i class="fa-solid fa-file-video text-indigo-400"></i> ${file}
                        </td>
                        <td class="py-3.5 px-4 text-right flex justify-end gap-2">
                            <button onclick="playVideo('${file}')" class="px-3 py-1.5 bg-emerald-600/15 hover:bg-emerald-600/30 border border-emerald-500/20 text-emerald-400 hover:text-white rounded-lg text-xs font-bold transition-all inline-flex items-center gap-1.5">
                                <i class="fa-solid fa-play"></i> Reproducir
                            </button>
                            <a href="/api/camera/recordings/download?file=${file}" class="px-3 py-1.5 bg-indigo-600/15 hover:bg-indigo-600/30 border border-indigo-500/20 text-indigo-300 hover:text-white rounded-lg text-xs font-bold transition-all inline-flex items-center gap-1.5">
                                <i class="fa-solid fa-download"></i> Descargar
                            </a>
                            <button onclick="deleteRecording('${file}')" class="px-3 py-1.5 bg-red-600/15 hover:bg-red-600/30 border border-red-500/20 text-red-400 hover:text-white rounded-lg text-xs font-bold transition-all inline-flex items-center gap-1.5">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="2" class="py-8 text-center text-red-500 text-xs">Error cargando lista de grabaciones.</td></tr>`;
            }
        }

        function startStatusPolling() {
            stopStatusPolling();
            recordingStatusInterval = setInterval(pollRecordingsStatus, 1000);
        }

        function stopStatusPolling() {
            if (recordingStatusInterval) {
                clearInterval(recordingStatusInterval);
                recordingStatusInterval = null;
            }
        }

        // --- MÉTODOS DE RED WIFI ---
        function getDeviceIcon(hostname) {
            const name = (hostname || "").toLowerCase();
            if (name.includes("phone") || name.includes("android") || name.includes("iphone") || name.includes("smart")) return "fa-mobile-button text-emerald-400";
            if (name.includes("ipad") || name.includes("tablet")) return "fa-tablet-screen-button text-teal-400";
            if (name.includes("laptop") || name.includes("macbook") || name.includes("notebook") || name.includes("pc-") || name.includes("desktop")) return "fa-laptop text-indigo-400";
            if (name.includes("tv") || name.includes("roku") || name.includes("chromecast") || name.includes("smarttv") || name.includes("television")) return "fa-tv text-purple-400";
            if (name.includes("printer") || name.includes("epson") || name.includes("hp")) return "fa-print text-amber-400";
            if (name.includes("raspberry") || name.includes("pi")) return "fa-microchip text-rose-400";
            return "fa-laptop-code text-gray-400";
        }

        let knownMacs = new Set();
        let isFirstScan = true;

        function playNetworkAlert() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = "sine";
                osc.frequency.setValueAtTime(880, ctx.currentTime);
                gain.gain.setValueAtTime(0.1, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.5);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.5);
            } catch (e) {
                console.log("Audio not supported", e);
            }
        }

        function loadGlobalAlertPreference() {
            const toggle = document.getElementById("global-alert-toggle");
            const bg = document.getElementById("global-alert-bg");
            const dot = document.getElementById("global-alert-dot");
            const isEnabled = localStorage.getItem("globalNetworkAlert") === "true";
            
            if (toggle) {
                toggle.checked = isEnabled;
                if (isEnabled) {
                    bg.classList.replace("bg-gray-800", "bg-sky-500");
                    dot.classList.add("translate-x-4");
                } else {
                    bg.classList.replace("bg-sky-500", "bg-gray-800");
                    dot.classList.remove("translate-x-4");
                }
            }
        }

        function saveGlobalAlertPreference() {
            const toggle = document.getElementById("global-alert-toggle");
            const bg = document.getElementById("global-alert-bg");
            const dot = document.getElementById("global-alert-dot");
            
            localStorage.setItem("globalNetworkAlert", toggle.checked ? "true" : "false");
            
            if (toggle.checked) {
                bg.classList.replace("bg-gray-800", "bg-sky-500");
                dot.classList.add("translate-x-4");
                showToast("Alerta Global Activada", "Recibirás una notificación cuando cualquier dispositivo se conecte.");
            } else {
                bg.classList.replace("bg-sky-500", "bg-gray-800");
                dot.classList.remove("translate-x-4");
                showToast("Alerta Global Desactivada", "Ya no recibirás alertas globales.");
            }
        }

        async function refreshNetworkClients() {
            const tbody = document.getElementById("network-clients-list");
            if (isFirstScan) {
                tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-gray-500 text-xs">Escaneando red local...</td></tr>`;
            }
            try {
                const res = await fetch("/api/network/clients");
                const clients = await res.json();
                
                if (!clients || clients.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-gray-500 text-xs">No se detectaron dispositivos de red conectados.</td></tr>`;
                    document.getElementById("total-bandwidth-indicator").innerText = "0.00 KB/s";
                    return;
                }

                let totalKB = 0;
                let currentMacs = new Set();
                let newDevicesConnected = [];
                const globalAlert = localStorage.getItem("globalNetworkAlert") === "true";
                const specificAlerts = JSON.parse(localStorage.getItem("specificNetworkAlerts") || "[]");

                clients.forEach(c => {
                    currentMacs.add(c.mac);
                    
                    // Parse bandwidth for total sum
                    let bw = c.bandwidth || "0 KB/s";
                    let num = parseFloat(bw);
                    if (!isNaN(num)) {
                        if (bw.includes("MB/s")) totalKB += num * 1024;
                        else if (bw.includes("KB/s")) totalKB += num;
                    }

                    // Check for new devices (if not first scan)
                    if (!isFirstScan && !knownMacs.has(c.mac)) {
                        if (globalAlert || specificAlerts.includes(c.mac)) {
                            newDevicesConnected.push(c.hostname || c.device || c.mac);
                        }
                    }
                });

                if (newDevicesConnected.length > 0) {
                    playNetworkAlert();
                    showToast("Nuevo Dispositivo Conectado", `Se ha conectado: ${newDevicesConnected.join(", ")}`, "success");
                }

                knownMacs = currentMacs;
                isFirstScan = false;

                // Update Total Bandwidth UI
                let totalStr = totalKB > 1024 ? (totalKB / 1024).toFixed(2) + " MB/s" : totalKB.toFixed(2) + " KB/s";
                document.getElementById("total-bandwidth-indicator").innerText = totalStr;

                tbody.innerHTML = clients.map(client => {
                    const isIdle = client.bandwidth === "0 KB/s";
                    const badgeColor = isIdle 
                        ? "bg-gray-800 text-gray-400 border-gray-700" 
                        : (client.bandwidth.includes("MB/s") ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-sky-500/10 text-sky-400 border-sky-500/20");
                    
                    return `
                        <tr class="border-b border-gray-800/30 hover:bg-gray-800/10">
                            <td class="py-3.5 px-4 font-bold text-gray-200">
                                <div class="flex items-center justify-between">
                                    <span class="flex items-center gap-2">
                                        <i class="fa-solid ${getDeviceIcon(client.hostname)} text-sm"></i>
                                        ${client.hostname}
                                    </span>
                                    <button onclick="openAliasModal('${client.mac}', '${client.hostname}')" class="p-1 hover:bg-gray-800 rounded text-gray-500 hover:text-white transition-colors" title="Editar Nombre">
                                        <i class="fa-solid fa-pencil text-xs"></i>
                                    </button>
                                </div>
                            </td>
                            <td class="py-3.5 px-4 code-font text-emerald-400">${client.ip}</td>
                            <td class="py-3.5 px-4">
                                <div class="code-font text-gray-400">${client.mac}</div>
                                <div class="text-[10px] text-gray-500 font-sans font-semibold mt-0.5 uppercase tracking-wider">${client.manufacturer || 'Desconocido'}</div>
                            </td>
                            <td class="py-3.5 px-4 text-xs font-semibold text-gray-500 uppercase">${client.device}</td>
                            <td class="py-3.5 px-4 text-right">
                                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${badgeColor}">
                                    ${client.bandwidth}
                                </span>
                            </td>
                        </tr>
                    `;
                }).join('');
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-red-500 text-xs">Error cargando clientes de red.</td></tr>`;
            }
        }

        // Control del Modal de Alias
        function openAliasModal(mac, currentAlias) {
            document.getElementById("alias-mac").value = mac;
            document.getElementById("alias-name").value = currentAlias === "Dispositivo sin nombre" ? "" : currentAlias;
            
            const specificAlerts = JSON.parse(localStorage.getItem("specificNetworkAlerts") || "[]");
            document.getElementById("alias-alert-toggle").checked = specificAlerts.includes(mac);
            
            document.getElementById("alias-modal").classList.remove("hidden");
        }

        function closeAliasModal() {
            document.getElementById("alias-modal").classList.add("hidden");
        }

        async function saveAlias() {
            const mac = document.getElementById("alias-mac").value;
            const alias = document.getElementById("alias-name").value;
            const alertEnabled = document.getElementById("alias-alert-toggle").checked;

            // Guardar preferencia de alerta
            let specificAlerts = JSON.parse(localStorage.getItem("specificNetworkAlerts") || "[]");
            if (alertEnabled && !specificAlerts.includes(mac)) {
                specificAlerts.push(mac);
            } else if (!alertEnabled && specificAlerts.includes(mac)) {
                specificAlerts = specificAlerts.filter(m => m !== mac);
            }
            localStorage.setItem("specificNetworkAlerts", JSON.stringify(specificAlerts));

            try {
                const res = await fetch("/api/network/alias", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mac, alias })
                });
                const result = await res.json();
                if (result.status === "success") {
                    showToast("Red WiFi", "Configuración de dispositivo guardada correctamente", "success");
                    closeAliasModal();
                    refreshNetworkClients();
                } else {
                    showToast("Error", result.message, "error");
                }
            } catch (err) {
                showToast("Error", "No se pudo comunicar con el servidor.", "error");
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

        function focusDeploymentTab() {
            switchTab("dashboard");
            const form = document.getElementById("cicd-form");
            if (form) form.scrollIntoView({ behavior: 'smooth' });
        }

        function formatTime(sec) {
            if (sec === undefined || sec === null) return "0s";
            if (sec < 60) return `${sec}s`;
            const m = Math.floor(sec / 60);
            const s = sec % 60;
            return `${m}m ${s}s`;
        }

        let activeDeployPolling = null;
        let activeDeployApp = null;

        async function checkActiveDeployments() {
            try {
                const res = await fetch("/api/cicd/deployments");
                const deployments = await res.json();
                
                let runningApp = null;
                let runningSec = 0;
                for (const app in deployments) {
                    if (deployments[app].status === "running") {
                        runningApp = app;
                        runningSec = deployments[app].elapsed_seconds || 0;
                        break;
                    }
                }
                
                const alertDiv = document.getElementById("global-deploy-alert");
                const nameSpan = document.getElementById("global-deploy-app-name");
                const globalTimeSpan = document.getElementById("global-deploy-time");
                const badgeSpan = document.getElementById("deploy-time-badge");
                
                if (runningApp) {
                    nameSpan.innerText = runningApp;
                    globalTimeSpan.innerText = formatTime(runningSec);
                    alertDiv.classList.remove("hidden");
                    
                    if (badgeSpan) {
                        badgeSpan.innerText = `⏱️ En progreso: ${formatTime(runningSec)}`;
                        badgeSpan.className = "text-[10px] px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 font-bold border border-indigo-500/20";
                    }
                    
                    // Si detectamos que hay un deploy corriendo y no estamos sondeándolo en la UI local,
                    // activar la sincronización automáticamente
                    if (activeDeployApp !== runningApp) {
                        activeDeployApp = runningApp;
                        
                        const logsContainer = document.getElementById("logs-container");
                        const logsPre = document.getElementById("deploy-logs");
                        const btn = document.getElementById("deploy-btn");
                        const cancelBtn = document.getElementById("btn-cancel-deploy");
                        
                        logsContainer.classList.remove("hidden");
                        btn.disabled = true;
                        btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Desplegando app en segundo plano...`;
                        if (cancelBtn) cancelBtn.classList.remove("hidden");
                        
                        if (activeDeployPolling) clearInterval(activeDeployPolling);
                        
                        activeDeployPolling = setInterval(async () => {
                            try {
                                const statusRes = await fetch(`/api/cicd/deploy/status?app_name=${encodeURIComponent(runningApp)}`);
                                const statusData = await statusRes.json();
                                
                                logsPre.innerText = statusData.log || "Esperando logs...";
                                logsPre.scrollTop = logsPre.scrollHeight;
                                
                                const elapsed = statusData.elapsed_seconds || 0;
                                globalTimeSpan.innerText = formatTime(elapsed);
                                if (badgeSpan) {
                                    badgeSpan.innerText = `⏱️ En progreso: ${formatTime(elapsed)}`;
                                }

                                if (statusData.status !== "running") {
                                    clearInterval(activeDeployPolling);
                                    activeDeployPolling = null;
                                    activeDeployApp = null;
                                    alertDiv.classList.add("hidden");
                                    btn.disabled = false;
                                    btn.innerHTML = `<i class="fa-solid fa-code-branch"></i> Lanzar pipeline de Despliegue`;
                                    if (cancelBtn) cancelBtn.classList.add("hidden");
                                    
                                    if (badgeSpan) {
                                        if (statusData.status === "success") {
                                            badgeSpan.innerText = `✅ Completado en: ${formatTime(elapsed)}`;
                                            badgeSpan.className = "text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20";
                                            showToast("CI/CD Despliegue", "¡Tu aplicación se ha desplegado correctamente!", "success");
                                        } else {
                                            badgeSpan.innerText = `❌ Fallido en: ${formatTime(elapsed)}`;
                                            badgeSpan.className = "text-[10px] px-2.5 py-0.5 rounded-full bg-red-500/10 text-red-400 font-bold border border-red-500/20";
                                            showToast("Error de Despliegue", "El proceso de despliegue ha fallado.", "error");
                                        }
                                    }
                                    refreshData();
                                }
                            } catch (e) {
                                // Ignorar fallos de red transitorios (ej: reinicio de contenedor)
                            }
                        }, 1000);
                    }
                } else {
                    if (!activeDeployPolling) {
                        alertDiv.classList.add("hidden");
                    }
                }
                
                if (activeTab === "cicd") {
                    loadDeploymentsList();
                }
            } catch (err) {
                // Ignorar fallos de red transitorios (ej: reinicio de contenedor)
            }
        }

        // Polling constante cada 4 segundos
        refreshData();
        checkActiveDeployments();
        async function initDeploymentsForm() {
            try {
                const res = await fetch("/api/cicd/deployments");
                const deployments = await res.json();
                const datalist = document.getElementById("deployed-apps-datalist");
                datalist.innerHTML = "";
                for (const app in deployments) {
                    const option = document.createElement("option");
                    option.value = `https://github.com/afrivera/${app}.git`;
                    datalist.appendChild(option);
                }
            } catch (err) {
                console.error("Error populating deployments form:", err);
            }
        }

        let fetchBranchesTimeout = null;
        function fetchBranchesDebounced() {
            if (fetchBranchesTimeout) clearTimeout(fetchBranchesTimeout);
            fetchBranchesTimeout = setTimeout(fetchBranches, 500);
        }

        async function fetchBranches() {
            const repoUrl = document.getElementById("deploy-repo").value;
            if (!repoUrl || !repoUrl.startsWith("http")) return;

            const loader = document.getElementById("branch-loader");
            const select = document.getElementById("deploy-branch");
            
            loader.classList.remove("hidden");
            select.disabled = true;

            try {
                const res = await fetch(`/api/cicd/git/branches?repo_url=${encodeURIComponent(repoUrl)}`);
                const data = await res.json();
                
                if (data.status === "success" && data.branches && data.branches.length > 0) {
                    select.innerHTML = "";
                    data.branches.forEach(branch => {
                        const option = document.createElement("option");
                        option.value = branch;
                        option.textContent = branch;
                        if (branch === "main" || branch === "master") option.selected = true;
                        select.appendChild(option);
                    });
                }
            } catch (err) {
                console.error("Error fetching branches:", err);
            } finally {
                loader.classList.add("hidden");
                select.disabled = false;
            }
        }

        async function openWifiModal() {
            document.getElementById('wifi-modal').classList.remove('hidden');
            document.getElementById('wifi-loader').classList.remove('hidden');
            document.getElementById('wifi-list').classList.add('hidden');
            document.getElementById('wifi-connect-box').classList.add('hidden');
            
            try {
                const res = await fetch("/api/wifi/scan");
                const data = await res.json();
                
                document.getElementById('wifi-loader').classList.add('hidden');
                
                if (data.status === 'success' && data.networks.length > 0) {
                    const listHtml = data.networks.map(n => `
                        <button onclick="selectWifi('${n.ssid}')" class="w-full text-left bg-gray-800 hover:bg-gray-700 p-3 rounded-lg flex justify-between items-center transition-colors">
                            <span class="text-white font-semibold">${n.ssid}</span>
                            <span class="text-xs ${n.signal > 70 ? 'text-emerald-400' : 'text-yellow-400'}">Señal: ${n.signal}%</span>
                        </button>
                    `).join('');
                    document.getElementById('wifi-list').innerHTML = listHtml;
                    document.getElementById('wifi-list').classList.remove('hidden');
                } else {
                    document.getElementById('wifi-list').innerHTML = '<p class="text-center text-gray-400 text-sm py-4">No se encontraron redes.</p>';
                    document.getElementById('wifi-list').classList.remove('hidden');
                }
            } catch (err) {
                console.error(err);
                document.getElementById('wifi-loader').classList.add('hidden');
                showToast("WiFi", "Error escaneando redes", "error");
            }
        }
        
        function closeWifiModal() {
            document.getElementById('wifi-modal').classList.add('hidden');
        }
        
        function selectWifi(ssid) {
            document.getElementById('wifi-selected-ssid').textContent = ssid;
            document.getElementById('wifi-password').value = '';
            document.getElementById('wifi-connect-box').classList.remove('hidden');
            document.getElementById('wifi-list').classList.add('hidden');
        }
        
        function cancelWifiConnect() {
            document.getElementById('wifi-connect-box').classList.add('hidden');
            document.getElementById('wifi-list').classList.remove('hidden');
        }
        
        async function connectWifi() {
            const ssid = document.getElementById('wifi-selected-ssid').textContent;
            const password = document.getElementById('wifi-password').value;
            const icon = document.getElementById('wifi-connecting-icon');
            
            icon.classList.remove('hidden');
            
            try {
                const res = await fetch("/api/wifi/connect", {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ssid, password})
                });
                const data = await res.json();
                icon.classList.add('hidden');
                if (data.status === 'success') {
                    showToast("WiFi", `Conectado a ${ssid} exitosamente`, "success");
                    closeWifiModal();
                } else {
                    showToast("WiFi Error", data.message, "error");
                }
            } catch (err) {
                icon.classList.add('hidden');
                showToast("WiFi", "Error al intentar conectar", "error");
            }
        }
        
        function playVideo(filename) {
            const player = document.getElementById('video-player');
            player.src = `/api/camera/recordings/play?file=${filename}`;
            document.getElementById('video-title').textContent = filename;
            document.getElementById('video-modal').classList.remove('hidden');
        }
        
        function closeVideoModal() {
            const player = document.getElementById('video-player');
            player.pause();
            player.src = '';
            document.getElementById('video-modal').classList.add('hidden');
        }
        
        async function deleteRecording(filename) {
            if (!confirm(`¿Estás seguro de que deseas eliminar la grabación ${filename}?`)) return;
            
            try {
                const res = await fetch(`/api/camera/recordings?file=${filename}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.status === 'success') {
                    showToast("Cámara", `Grabación ${filename} eliminada`, "success");
                    loadRecordings();
                } else {
                    showToast("Error", data.message, "error");
                }
            } catch (err) {
                showToast("Error", "No se pudo eliminar la grabación", "error");
            }
        }

        setInterval(refreshData, 4000);
        setInterval(checkActiveDeployments, 4000);
        setInterval(refreshNetworkClients, 4000);
        initDeploymentsForm();
        loadGlobalAlertPreference();
    </script>
</body>
</html>
"""

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesión - Centro de Control Raspberry Pi</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome para iconos -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Outfit', sans-serif;
            background-color: #030712;
        }
        .code-font {
            font-family: 'JetBrains Mono', monospace;
        }
        .glass {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
    <!-- Glow Effects -->
    <div class="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

    <div class="w-full max-w-md glass rounded-3xl p-8 shadow-2xl relative z-10">
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-white text-2xl font-bold shadow-lg shadow-emerald-500/20 mb-4">
                <i class="fa-solid fa-microchip"></i>
            </div>
            <h1 class="text-2xl font-bold text-white">Centro de Control</h1>
            <p class="text-xs text-gray-400 mt-1">Raspberry Pi 3 B+</p>
        </div>

        <form id="login-form" class="space-y-5">
            <div>
                <label for="username" class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Usuario de la Raspberry</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                        <i class="fa-solid fa-user"></i>
                    </span>
                    <input type="text" id="username" name="username" required placeholder="ej: pi o ubuntu" 
                        class="w-full bg-gray-950/80 border border-gray-800 text-white rounded-xl py-3 pl-10 pr-4 text-sm placeholder-gray-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all">
                </div>
            </div>

            <div>
                <label for="password" class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Contraseña (sudo)</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                        <i class="fa-solid fa-lock"></i>
                    </span>
                    <input type="password" id="password" name="password" required placeholder="••••••••" 
                        class="w-full bg-gray-950/80 border border-gray-800 text-white rounded-xl py-3 pl-10 pr-4 text-sm placeholder-gray-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all">
                </div>
            </div>

            <div id="error-message" class="hidden text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                Credenciales incorrectas. Intenta de nuevo.
            </div>

            <button type="submit" id="btn-submit"
                class="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 active:scale-[0.98] transition-all text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-emerald-500/10 flex items-center justify-center gap-2">
                <i class="fa-solid fa-right-to-bracket"></i> Iniciar Sesión
            </button>
        </form>
    </div>

    <script>
        document.getElementById("login-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("btn-submit");
            const errDiv = document.getElementById("error-message");
            
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-circle-notch animate-spin"></i> Verificando...`;
            errDiv.classList.add("hidden");

            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            try {
                const res = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });
                const data = await res.json();
                
                if (data.status === "success") {
                    window.location.reload();
                } else {
                    errDiv.innerText = data.message || "Error al iniciar sesión.";
                    errDiv.classList.remove("hidden");
                }
            } catch (err) {
                errDiv.innerText = "Error de conexión con el servidor.";
                errDiv.classList.remove("hidden");
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-right-to-bracket"></i> Iniciar Sesión`;
            }
        });
    </script>
</body>
</html>
"""

