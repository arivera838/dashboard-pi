import os
import subprocess
from src.application.ports.outputs import GitPort

class GitManagerAdapter(GitPort):
    def clone_or_pull(self, repo_url: str, branch: str, target_dir: str) -> tuple[bool, str]:
        try:
            # Ensure target directory's parent exists
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            
            # Inyectar token de autenticación de Git si está presente en las variables de entorno
            git_token = os.environ.get("GIT_TOKEN")
            actual_url = repo_url
            if git_token and actual_url.startswith("https://"):
                # Reemplazar https://github.com/... por https://TOKEN@github.com/...
                actual_url = actual_url.replace("https://", f"https://{git_token}@")

            # Use credentials from env or config if needed (assuming public repo or ssh config is set)
            if not os.path.exists(os.path.join(target_dir, ".git")):
                # Directorio no existe o no es un repositorio git
                print(f"[Git] Clonando repositorio {repo_url} (rama {branch}) en {target_dir}")
                res = subprocess.run(
                    ["git", "clone", "-b", branch, actual_url, target_dir],
                    capture_output=True, text=True, timeout=120
                )
                if res.returncode != 0:
                    return False, f"Error clonando: {res.stderr}"
                return True, f"Clonado correctamente: {res.stdout}"
            else:
                # Repositorio existe, hacer pull
                print(f"[Git] Actualizando repositorio en {target_dir} (rama {branch})")
                
                # Fetch
                subprocess.run(["git", "fetch", "origin"], cwd=target_dir, capture_output=True, timeout=60)
                
                # Checkout branch (in case we were on detached or another branch)
                res_checkout = subprocess.run(
                    ["git", "checkout", branch],
                    cwd=target_dir, capture_output=True, text=True, timeout=30
                )
                
                if res_checkout.returncode != 0 and "did not match any file" in res_checkout.stderr:
                    # Probablemente una rama nueva localmente
                    subprocess.run(["git", "checkout", "-b", branch, f"origin/{branch}"], cwd=target_dir)

                # Reset hard to origin branch to avoid any conflicts with local changes
                res_reset = subprocess.run(
                    ["git", "reset", "--hard", f"origin/{branch}"],
                    cwd=target_dir, capture_output=True, text=True, timeout=60
                )
                
                if res_reset.returncode != 0:
                    return False, f"Error haciendo reset --hard: {res_reset.stderr}"
                    
                # Limpiar archivos no trackeados
                subprocess.run(["git", "clean", "-fd"], cwd=target_dir, capture_output=True)
                
                return True, f"Repositorio actualizado correctamente."
                
        except subprocess.TimeoutExpired:
            return False, "La operación de Git excedió el tiempo límite (Timeout)."
        except Exception as e:
            return False, f"Error inesperado en git_manager: {e}"

    def create_github_webhook(self, owner: str, repo: str, public_url: str, secret: str, token: str) -> tuple[bool, str]:
        import urllib.request
        import json
        
        url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
        webhook_target = public_url.rstrip("/") + "/api/webhooks/github"
        
        payload = {
            "name": "web",
            "active": True,
            "events": ["push"],
            "config": {
                "url": webhook_target,
                "content_type": "json",
                "insecure_ssl": "1"
            }
        }
        if secret:
            payload["config"]["secret"] = secret
            
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "DashboardPi-Agent",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 201:
                    return True, "Webhook de GitHub creado exitosamente."
                body = response.read().decode('utf-8')
                return False, f"Respuesta inesperada de GitHub ({response.status}): {body}"
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            try:
                err_json = json.loads(err_body)
                errors = err_json.get("errors", [])
                for err in errors:
                    if err.get("message") == "Hook already exists on this repository":
                        return True, "El webhook ya existía en este repositorio."
                message = err_json.get("message", err_body)
            except Exception:
                message = err_body
            return False, f"Error de GitHub API ({e.code}): {message}"
        except Exception as e:
            return False, f"Error conectando con la API de GitHub: {str(e)}"
