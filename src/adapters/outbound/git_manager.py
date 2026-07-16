import os
import subprocess
from src.application.ports.outputs import GitPort

class GitManagerAdapter(GitPort):
    def clone_or_pull(self, repo_url: str, branch: str, target_dir: str) -> tuple[bool, str]:
        try:
            # Ensure target directory's parent exists
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            
            # Use credentials from env or config if needed (assuming public repo or ssh config is set)
            if not os.path.exists(os.path.join(target_dir, ".git")):
                # Directorio no existe o no es un repositorio git
                print(f"[Git] Clonando repositorio {repo_url} (rama {branch}) en {target_dir}")
                res = subprocess.run(
                    ["git", "clone", "-b", branch, repo_url, target_dir],
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
