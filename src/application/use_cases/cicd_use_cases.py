import os
import subprocess
import time
import hmac
import hashlib
import json
from typing import Dict, Any, List
from src.domain.models import WebhookPayload, BuildJob
from src.application.ports.outputs import GitPort, NotificationPort

class HandleWebhookUseCase:
    def __init__(self, cicd_manager):
        self.cicd_manager = cicd_manager
        # Secreto de GitHub webhook (opcionalmente configurado vía env)
        self.secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "").encode('utf-8')
        self.allowed_branches = ["main", "dev", "stage"]

    def execute(self, provider: str, headers: dict, body: bytes) -> tuple[bool, str]:
        if provider == "github":
            # Validar firma HMAC SHA-256 si hay un secreto configurado
            if self.secret:
                signature_header = headers.get("X-Hub-Signature-256")
                if not signature_header:
                    return False, "Falta la firma X-Hub-Signature-256"
                
                expected_signature = "sha256=" + hmac.new(self.secret, body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected_signature, signature_header):
                    return False, "Firma criptográfica inválida (Webhook Secret mismatch)"
            
            try:
                payload_json = json.loads(body.decode('utf-8'))
                
                # Filtrar solo eventos de push
                if headers.get("X-GitHub-Event") != "push":
                    return True, "Evento ignorado (no es un push)"
                    
                ref = payload_json.get("ref", "")
                if not ref.startswith("refs/heads/"):
                    return True, "Evento ignorado (no es una rama)"
                    
                branch = ref.replace("refs/heads/", "")
                if branch not in self.allowed_branches:
                    return True, f"Rama '{branch}' ignorada. Solo se admiten: {self.allowed_branches}"
                    
                repo_name = payload_json.get("repository", {}).get("name", "unknown")
                repo_url = payload_json.get("repository", {}).get("clone_url", "")
                commit_hash = payload_json.get("after", "")
                head_commit = payload_json.get("head_commit") or {}
                commit_message = head_commit.get("message", "")
                author = head_commit.get("author", {}).get("username", "unknown")
                
                payload = WebhookPayload(
                    repo_name=repo_name,
                    repo_url=repo_url,
                    branch=branch,
                    commit_hash=commit_hash,
                    commit_message=commit_message,
                    author=author,
                    provider=provider
                )
                
                job = self.cicd_manager.add_to_queue(payload)
                self.cicd_manager.process_queue()
                return True, f"Build encolado: {job.id}"
            except Exception as e:
                return False, f"Error parseando webhook: {str(e)}"
        
        return False, f"Proveedor {provider} no soportado."

class CICDManager:
    """Administra la cola de builds y orquesta los despliegues"""
    def __init__(self, git_port: GitPort, notification_port: NotificationPort):
        self.git = git_port
        self.notify = notification_port
        self.build_queue: List[BuildJob] = []
        self.current_build: BuildJob | None = None
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
