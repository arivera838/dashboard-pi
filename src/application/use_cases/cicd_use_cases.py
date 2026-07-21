from typing import Optional, Union, Dict, Any, List
import os
import subprocess
import time
import hmac
import hashlib
import json
from typing import Dict, Any, List, Optional
from src.domain.models import WebhookPayload, BuildJob
from src.application.ports.outputs import GitPort, NotificationPort

class HandleWebhookUseCase:
    def __init__(self, cicd_manager, deployer=None):
        self.cicd_manager = cicd_manager
        self.deployer = deployer
        # Leer secreto desde cicd_config.json (con fallback a variable de entorno)
        self._load_secret()

    def _load_secret(self):
        """Lee el webhook_secret desde cicd_config.json, con fallback a env var."""
        try:
            from src.adapters.outbound.cicd_config import get_cicd_config
            cfg = get_cicd_config()
            secret = cfg.get("webhook_secret", "")
            if not secret:
                secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
            self.secret = secret.encode('utf-8') if secret else b""
        except Exception:
            self.secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "").encode('utf-8')

    def _log_webhook(self, provider: str, msg: str):
        import time
        if not hasattr(self, 'deployer') or not self.deployer:
            return
            
        if "Webhook-Listener" not in self.deployer._active_logs:
            self.deployer._active_logs["Webhook-Listener"] = {
                "status": "success",
                "log": "📡 [Webhook Listener] Historial de Eventos...\n",
                "start_time": time.time(),
                "repo_url": "Webhooks"
            }
            
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.deployer._active_logs["Webhook-Listener"]["log"] += f"[{timestamp}] [{provider.upper()}] {msg}\n"
        self.deployer._active_logs["Webhook-Listener"]["end_time"] = time.time()

    def execute(self, provider: str, headers: dict, body: bytes) -> tuple[bool, str]:
        # Recargar secreto en cada ejecución (puede cambiar desde la UI)
        self._load_secret()

        if provider == "github":
            # Convertir headers a minúsculas para búsqueda case-insensitive
            headers_lower = {k.lower(): v for k, v in headers.items()}
            
            # Validar firma HMAC SHA-256 si hay un secreto configurado
            if self.secret:
                signature_header = headers_lower.get("x-hub-signature-256")
                if not signature_header:
                    msg = "Falta la firma X-Hub-Signature-256"
                    self._log_webhook(provider, msg)
                    return False, msg
                
                expected_signature = "sha256=" + hmac.new(self.secret, body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected_signature, signature_header):
                    msg = "Firma criptográfica inválida (Webhook Secret mismatch)"
                    self._log_webhook(provider, msg)
                    return False, msg
            
            try:
                payload_json = json.loads(body.decode('utf-8'))
                
                # Filtrar solo eventos de push
                if headers_lower.get("x-github-event") != "push":
                    msg = f"Evento ignorado (no es un push). Evento recibido: {headers_lower.get('x-github-event')}"
                    self._log_webhook(provider, msg)
                    return True, msg
                    
                ref = payload_json.get("ref", "")
                if not ref.startswith("refs/heads/"):
                    msg = f"Evento ignorado (no es una rama). Ref: {ref}"
                    self._log_webhook(provider, msg)
                    return True, msg
                    
                branch = ref.replace("refs/heads/", "")
                repo_name = payload_json.get("repository", {}).get("name", "unknown")
                repo_url = payload_json.get("repository", {}).get("clone_url", "")
                commit_hash = payload_json.get("after", "")
                head_commit = payload_json.get("head_commit") or {}
                commit_message = head_commit.get("message", "")
                author = head_commit.get("author", {}).get("username", "unknown")

                # --- Auto-Redeploy: verificar si la rama tiene un despliegue local activo ---
                if self.deployer:
                    deployed_apps = self.deployer.get_local_apps()
                    matching_app = next(
                        (app for app in deployed_apps
                         if repo_name in app.get("repo_url", "")
                         and app.get("current_branch") == branch),
                        None
                    )

                    if matching_app:
                        app_name = matching_app["app_name"]
                        apps_dir = self.deployer._get_apps_dir()
                        target_dir = os.path.join(apps_dir, app_name)

                        # Notificar inicio del auto-redeploy
                        self.cicd_manager.notify.send_notification(
                            title=f"🔄 Auto-Redeploy: {app_name} ({branch})",
                            message=f"Push detectado de @{author}\n📝 {commit_message[:100]}\nIniciando pull y reconstrucción..."
                        )

                        msg = f"Auto-Redeploy disparado para {app_name} (rama {branch}) por push de {author}"
                        print(f"[CI/CD] {msg}")
                        self._log_webhook(provider, msg)
                        self.deployer.deploy(repo_url, target_dir, app_name, branch)
                        return True, f"Auto-Redeploy disparado para {app_name} ({branch})"
                    else:
                        msg = f"Push recibido para {repo_name}/{branch} pero no hay despliegue local activo. Encolando."
                        print(f"[CI/CD] {msg}")
                        self._log_webhook(provider, msg)

                # Fallback: encolar en el CICDManager antiguo si no hay match local
                payload = WebhookPayload(
                    repo_name=repo_name,
                    repo_url=repo_url,
                    branch=branch,
                    commit_hash=commit_hash,
                    commit_message=commit_message,
                    author=author,
                    provider="github",
                    raw_payload=body
                )
                self.cicd_manager.add_to_queue(payload)
                self.cicd_manager.process_queue()
                msg = f"Push procesado exitosamente y encolado para {repo_name} (rama {branch})"
                self._log_webhook(provider, msg)
                return True, msg
            except json.JSONDecodeError:
                msg = "Payload JSON inválido"
                self._log_webhook(provider, msg)
                return False, msg

        elif provider == "gitlab":
            # Convertir headers a minúsculas para búsqueda case-insensitive
            headers_lower = {k.lower(): v for k, v in headers.items()}
            
            if self.secret:
                token_header = headers_lower.get("x-gitlab-token")
                if not token_header or token_header.encode('utf-8') != self.secret:
                    msg = "Token de GitLab inválido"
                    self._log_webhook(provider, msg)
                    return False, msg
            
            try:
                payload_json = json.loads(body.decode('utf-8'))
                
                # Filtrar solo eventos de push
                if headers_lower.get("x-gitlab-event") != "Push Hook":
                    msg = "Evento ignorado (no es un push)"
                    self._log_webhook(provider, msg)
                    return True, msg
                    
                ref = payload_json.get("ref", "")
                if not ref.startswith("refs/heads/"):
                    msg = "Evento ignorado (no es una rama)"
                    self._log_webhook(provider, msg)
                    return True, msg
                    
                branch = ref.replace("refs/heads/", "")
                repo_name = payload_json.get("repository", {}).get("name", "unknown")
                repo_url = payload_json.get("repository", {}).get("git_http_url", "")
                commit_hash = payload_json.get("after", "")
                commits = payload_json.get("commits", [])
                head_commit = commits[0] if commits else {}
                commit_message = head_commit.get("message", "")
                author = payload_json.get("user_username", "unknown")

                # --- Auto-Redeploy: verificar si la rama tiene un despliegue local activo ---
                if self.deployer:
                    deployed_apps = self.deployer.get_local_apps()
                    matching_app = next(
                        (app for app in deployed_apps
                         if repo_name in app.get("repo_url", "")
                         and app.get("current_branch") == branch),
                        None
                    )

                    if matching_app:
                        app_name = matching_app["app_name"]
                        apps_dir = self.deployer._get_apps_dir()
                        target_dir = os.path.join(apps_dir, app_name)

                        self.cicd_manager.notify.send_notification(
                            title=f"🔄 Auto-Redeploy: {app_name} ({branch})",
                            message=f"Push detectado de @{author}\n📝 {commit_message[:100]}\nIniciando pull y reconstrucción..."
                        )

                        msg = f"Auto-Redeploy disparado para {app_name} (rama {branch}) por push de {author}"
                        print(f"[CI/CD] {msg}")
                        self._log_webhook(provider, msg)
                        self.deployer.deploy(repo_url, target_dir, app_name, branch)
                        return True, f"Auto-Redeploy disparado para {app_name} ({branch})"
                    else:
                        msg = f"Push recibido para {repo_name}/{branch} pero no hay despliegue local activo. Encolando."
                        print(f"[CI/CD] {msg}")
                        self._log_webhook(provider, msg)

                payload = WebhookPayload(
                    repo_name=repo_name,
                    repo_url=repo_url,
                    branch=branch,
                    commit_hash=commit_hash,
                    commit_message=commit_message,
                    author=author,
                    provider="gitlab",
                    raw_payload=body
                )
                self.cicd_manager.add_to_queue(payload)
                self.cicd_manager.process_queue()
                msg = f"Push procesado exitosamente y encolado para {repo_name} (rama {branch})"
                self._log_webhook(provider, msg)
                return True, msg
                
            except json.JSONDecodeError:
                msg = "Payload JSON inválido"
                self._log_webhook(provider, msg)
                return False, msg
                
        return False, f"Proveedor {provider} no soportado."

class CICDManager:
    """Administra la cola de builds y orquesta los despliegues"""
    def __init__(self, git_port: GitPort, notification_port: NotificationPort):
        self.git = git_port
        self.notify = notification_port
        self.build_queue: List[BuildJob] = []
        self.current_build: Optional[BuildJob] = None
        self.deployments_dir = "./deployments"
        
    def add_to_queue(self, payload: WebhookPayload) -> BuildJob:
        job = BuildJob(
            id=f"{payload.repo_name}-{payload.branch}-{payload.commit_hash[:7]}",
            repo_name=payload.repo_name,
            branch=payload.branch,
            status="queued",
            logs=[],
            start_time=time.time()
        )
        self.build_queue.append(job)
        return job
        
    def _log(self, job: BuildJob, message: str):
        job.logs.append(message)
        print(f"[CI/CD - {job.id}] {message}")
        
    def process_queue(self):
        if self.current_build is not None:
            # Ya hay un build en progreso, respetar límite de 1
            return
            
        if not self.build_queue:
            return
            
        self.current_build = self.build_queue.pop(0)
        self.current_build.status = "building"
        
        # Ejecutar despliegue en un hilo separado o sincrónicamente si somos un worker
        import threading
        threading.Thread(target=self._execute_build, args=(self.current_build,)).start()
        
    def _execute_build(self, job: BuildJob):
        try:
            self.notify.send_notification(
                title=f"🚀 Inciando Despliegue: {job.repo_name} ({job.branch})",
                message=f"ID: {job.id}\nPreparando entorno..."
            )
            
            repo_url = f"https://github.com/afrivera/{job.repo_name}.git" # TODO: Extraer de payload o config
            target_dir = os.path.join(self.deployments_dir, job.repo_name, job.branch)
            
            # 1. Clone or Pull
            self._log(job, "Obteniendo código fuente...")
            success, msg = self.git.clone_or_pull(repo_url, job.branch, target_dir)
            self._log(job, msg)
            if not success:
                raise Exception("Fallo en la operación Git")
                
            # 2. Detectar si hay docker-compose
            compose_file = os.path.join(target_dir, "docker-compose.yml")
            if not os.path.exists(compose_file):
                self._log(job, "No se encontró docker-compose.yml. Se requiere para inyectar Traefik.")
                raise Exception("docker-compose.yml no encontrado")
                
            # 3. Generar docker-compose.override.yml dinámicamente para Traefik
            # Subdominio basado en rama (ej. dev.rivera-cv.local)
            # Si es main, el subdominio es solo el nombre del repo (ej. rivera-cv.local)
            subdomain = f"{job.repo_name}.local" if job.branch == "main" else f"{job.branch}.{job.repo_name}.local"
            project_name = f"{job.repo_name}-{job.branch}"
            
            # Asumimos que el servicio principal se llama "app" o tomamos el primer servicio
            # Para mayor robustez, inyectamos labels de Traefik mediante variables de entorno o un override
            override_content = f"""
services:
  app:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{project_name}.rule=Host(`{subdomain}`)"
    networks:
      - web

networks:
  web:
    external: true
    name: web
"""
            override_path = os.path.join(target_dir, "docker-compose.override.yml")
            with open(override_path, "w") as f:
                f.write(override_content)
            self._log(job, f"Archivo override generado para el subdominio: {subdomain}")
            
            # 4. Asegurar que la red externa existe
            subprocess.run(["docker", "network", "create", "web"], capture_output=True)
            
            # 5. Levantar con Docker Compose
            self._log(job, "Construyendo y levantando contenedores...")
            res = subprocess.run(
                ["docker-compose", "-p", project_name, "up", "-d", "--build"],
                cwd=target_dir, capture_output=True, text=True
            )
            self._log(job, res.stdout)
            if res.returncode != 0:
                self._log(job, res.stderr)
                raise Exception("Fallo al levantar docker-compose")
                
            job.status = "success"
            job.end_time = time.time()
            self._log(job, "¡Despliegue finalizado con éxito!")
            self.notify.send_notification(
                title=f"✅ Despliegue Exitoso: {job.repo_name} ({job.branch})",
                message=f"URL: http://{subdomain}\nTiempo: {int(job.end_time - job.start_time)}s",
                status="success"
            )
            
        except Exception as e:
            job.status = "failed"
            job.end_time = time.time()
            self._log(job, f"Error crítico: {e}")
            self.notify.send_notification(
                title=f"❌ Fallo en Despliegue: {job.repo_name} ({job.branch})",
                message=f"Error: {e}\nRevisar logs en el dashboard.",
                status="error"
            )
        finally:
            self.current_build = None
            self.process_queue() # Iniciar el siguiente si hay
