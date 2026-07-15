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
        
        <!-- Tabs Navigation -->
        <div class="flex border-b border-gray-800 mb-8 gap-2">
            <button onclick="switchTab('dashboard')" id="tab-btn-dashboard" class="px-5 py-3 border-b-2 border-emerald-500 text-emerald-400 font-bold text-sm transition-all flex items-center gap-2">
                <i class="fa-solid fa-gauge-high"></i> Dashboard
            </button>
            <button onclick="switchTab('cameras')" id="tab-btn-cameras" class="px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-white font-bold text-sm transition-all flex items-center gap-2">
                <i class="fa-solid fa-camera"></i> Cámaras
            </button>
            <button onclick="switchTab('network')" id="tab-btn-network" class="px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-white font-bold text-sm transition-all flex items-center gap-2">
                <i class="fa-solid fa-wifi"></i> Clientes de Red
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
                                <span class="code-font text-gray-200">/root/apps/</span>
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
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">Ruta Destino (Opcional)</label>
                                    <input type="text" id="deploy-path" placeholder="Dejar vacío para usar ruta default (~/apps)" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                                </div>
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">Puerto de la App (Opcional)</label>
                                    <input type="number" id="deploy-port" placeholder="ej. 8000" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
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
                                        <th class="py-3 px-4 font-semibold">Puertos</th>
                                        <th class="py-3 px-4 font-semibold">Estado</th>
                                        <th class="py-3 px-4 font-semibold text-right">Controles Rápidos</th>
                                    </tr>
                                </thead>
                                <tbody id="docker-list" class="divide-y divide-gray-800/50 text-sm">
                                    <tr>
                                        <td colspan="5" class="py-8 text-center text-gray-500 text-xs">Cargando contenedores Docker activos...</td>
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
                    <button onclick="refreshNetworkClients()" class="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs text-gray-400 hover:text-white transition-colors">
                        <i class="fa-solid fa-arrows-rotate"></i>
                    </button>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-gray-800 text-xs uppercase text-gray-400 tracking-wider">
                                <th class="py-3 px-4 font-semibold">Dispositivo</th>
                                <th class="py-3 px-4 font-semibold">Dirección IP</th>
                                <th class="py-3 px-4 font-semibold">Dirección MAC</th>
                                <th class="py-3 px-4 font-semibold">Interfaz</th>
                            </tr>
                        </thead>
                        <tbody id="network-clients-list" class="divide-y divide-gray-800/50 text-sm">
                            <tr>
                                <td colspan="4" class="py-8 text-center text-gray-500 text-xs">Cargando lista de red...</td>
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

    <!-- Script de lógica e interacción en el Frontend -->
    <script>
        let activeTab = "dashboard";
        let recordingStatusInterval = null;

        function switchTab(tabId) {
            activeTab = tabId;
            
            // Ocultar todos los contenidos
            document.getElementById("tab-content-dashboard").classList.add("hidden");
            document.getElementById("tab-content-cameras").classList.add("hidden");
            document.getElementById("tab-content-network").classList.add("hidden");

            // Mostrar el activo
            document.getElementById(`tab-content-${tabId}`).classList.remove("hidden");

            // Actualizar diseño de botones
            const tabs = ["dashboard", "cameras", "network"];
            tabs.forEach(t => {
                const btn = document.getElementById(`tab-btn-${t}`);
                if (t === tabId) {
                    btn.className = "px-5 py-3 border-b-2 border-emerald-500 text-emerald-400 font-bold text-sm transition-all flex items-center gap-2";
                } else {
                    btn.className = "px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-white font-bold text-sm transition-all flex items-center gap-2";
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
        }

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
                tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-gray-500 text-xs">No se encontraron contenedores Docker activos en esta Raspberry.</td></tr>`;
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
            const app_port = document.getElementById("deploy-port").value;

            // Bloquear interfaz
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Desplegando app en segundo plano...`;
            logsContainer.classList.remove("hidden");
            logsPre.innerText = "Iniciando pipeline de despliegue...\\n[Git] Conectando con el repositorio remoto...\\n[Docker] Preparando ambiente...";

            try {
                const res = await fetch("/api/cicd/deploy", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ repo_url, target_dir, app_name, app_port })
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

                grid.innerHTML = cameras.map(cam => `
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
                            <img class="w-full h-full object-cover" src="/api/camera/stream?id=${cam.id}" alt="Stream">
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

                pollRecordingsStatus();
            } catch (err) {
                console.error("Error cargando cámaras:", err);
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
                        <td class="py-3.5 px-4 text-right">
                            <a href="/api/camera/recordings/download?file=${file}" class="px-3 py-1.5 bg-indigo-600/15 hover:bg-indigo-600/30 border border-indigo-500/20 text-indigo-300 hover:text-white rounded-lg text-xs font-bold transition-all inline-flex items-center gap-1.5">
                                <i class="fa-solid fa-download"></i> Descargar
                            </a>
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
        async function refreshNetworkClients() {
            const tbody = document.getElementById("network-clients-list");
            tbody.innerHTML = `<tr><td colspan="4" class="py-8 text-center text-gray-500 text-xs">Escaneando red local...</td></tr>`;
            try {
                const res = await fetch("/api/network/clients");
                const clients = await res.json();
                
                if (!clients || clients.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="4" class="py-8 text-center text-gray-500 text-xs">No se detectaron dispositivos de red conectados.</td></tr>`;
                    return;
                }

                tbody.innerHTML = clients.map(client => `
                    <tr class="border-b border-gray-800/30 hover:bg-gray-800/10">
                        <td class="py-3.5 px-4 font-bold text-gray-200">${client.hostname}</td>
                        <td class="py-3.5 px-4 code-font text-emerald-400">${client.ip}</td>
                        <td class="py-3.5 px-4 code-font text-gray-400">${client.mac}</td>
                        <td class="py-3.5 px-4 text-xs font-semibold text-gray-500 uppercase">${client.device}</td>
                    </tr>
                `).join('');
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="4" class="py-8 text-center text-red-500 text-xs">Error cargando clientes de red.</td></tr>`;
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
