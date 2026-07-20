import socket
import http.client
import json
from typing import List
from src.domain.models import DockerContainer
from src.application.ports.outputs import DockerControllerPort

class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, unix_socket_path):
        super().__init__("localhost", timeout=10.0)
        self.unix_socket_path = unix_socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(10.0)
        self.sock.connect(self.unix_socket_path)

class CliDockerController(DockerControllerPort):
    def _query_api(self, path: str, method: str = "GET", body: str = None, raw: bool = False) -> tuple[int, any]:
        socket_path = "/var/run/docker.sock"
        try:
            conn = UnixHTTPConnection(socket_path)
            headers = {"Content-Type": "application/json"} if body else {}
            conn.request(method, path, body, headers)
            res = conn.getresponse()
            data = res.read()
            conn.close()
            if raw:
                return res.status, data
            return res.status, data.decode("utf-8", errors="ignore")
        except Exception as e:
            return 500, str(e)

    def list_containers(self) -> List[DockerContainer]:
        containers = []
        status_code, data_str = self._query_api("/containers/json?all=1")
        if status_code != 200:
            print(f"[Docker] Error al listar contenedores API ({status_code}): {data_str}")
            return containers

        try:
            raw_list = json.loads(data_str)
            for item in raw_list:
                cid = item.get("Id", "")[:12]
                names = item.get("Names", [])
                name = names[0].replace("/", "") if names else cid
                state = item.get("State", "")
                status = item.get("Status", "")
                image = item.get("Image", "")
                
                # Parsear puertos
                ports_list = item.get("Ports", [])
                ports_str_parts = []
                for p in ports_list:
                    ip = p.get("IP", "")
                    priv = p.get("PrivatePort", "")
                    pub = p.get("PublicPort", "")
                    ptype = p.get("Type", "")
                    if pub:
                        ports_str_parts.append(f"{ip}:{pub}->{priv}/{ptype}" if ip else f"{pub}->{priv}/{ptype}")
                    else:
                        ports_str_parts.append(f"{priv}/{ptype}")
                ports = ", ".join(ports_str_parts)

                is_running = state.lower() == "running"
                
                memory_usage = "N/A"
                if is_running:
                    # Consultar stats del contenedor
                    stat_code, stat_data = self._query_api(f"/containers/{cid}/stats?stream=false")
                    if stat_code == 200:
                        try:
                            stats = json.loads(stat_data)
                            mem_stats = stats.get("memory_stats", {})
                            usage = mem_stats.get("usage", 0)
                            limit = mem_stats.get("limit", 0)
                            
                            if limit > 0:
                                def to_human(num_bytes):
                                    for unit in ['B', 'KB', 'MB', 'GB']:
                                        if num_bytes < 1024.0:
                                            return f"{num_bytes:.1f} {unit}"
                                        num_bytes /= 1024.0
                                    return f"{num_bytes:.1f} TB"
                                
                                memory_usage = f"{to_human(usage)} / {to_human(limit)}"
                        except Exception:
                            pass

                containers.append(DockerContainer(
                    id=cid,
                    name=name,
                    status=status,
                    image=image,
                    running=is_running,
                    ports=ports,
                    memory_usage=memory_usage
                ))
        except Exception as e:
            print(f"[Docker] Error al parsear JSON de Docker API: {e}")
        return containers

    def control_container(self, container_id: str, action: str) -> tuple[bool, str]:
        if action not in ["start", "stop", "restart", "remove"]:
            return False, "Acción inválida"
        
        if action == "remove":
            status_code, data_str = self._query_api(f"/containers/{container_id}?v=true&force=true", "DELETE")
            if status_code in [204, 200]:
                return True, "Contenedor eliminado con éxito."
            return False, f"Error Docker API ({status_code}): {data_str}"
        else:
            status_code, data_str = self._query_api(f"/containers/{container_id}/{action}", "POST")
            if status_code in [204, 200]:
                action_msg = f"{action}eado" if action != "stop" else "detenido"
                return True, f"Contenedor {action_msg} con éxito."
            return False, f"Error Docker API ({status_code}): {data_str}"

    def get_container_logs(self, container_id: str) -> tuple[bool, str]:
        # tail=200, stdout=1, stderr=1
        status_code, raw_bytes = self._query_api(
            f"/containers/{container_id}/logs?stdout=1&stderr=1&tail=200", 
            "GET", 
            raw=True
        )
        if status_code != 200:
            return False, f"Error al leer logs ({status_code})"

        # Limpiar headers de flujo multiplexado de Docker
        cleaned = []
        i = 0
        n = len(raw_bytes)
        while i + 8 <= n:
            stream_type = raw_bytes[i]
            if stream_type not in [1, 2]:
                # Si no está multiplexado, decodificar directo
                return True, raw_bytes.decode("utf-8", errors="ignore")
            size = int.from_bytes(raw_bytes[i+4:i+8], byteorder="big")
            if i + 8 + size > n:
                break
            frame = raw_bytes[i+8:i+8+size]
            cleaned.append(frame.decode("utf-8", errors="ignore"))
            i += 8 + size
        
        if not cleaned and n > 0:
            return True, raw_bytes.decode("utf-8", errors="ignore")
            
        return True, "".join(cleaned)

    def list_compose_projects(self) -> List[dict]:
        status_code, data_str = self._query_api("/containers/json?all=1")
        if status_code != 200:
            return []
            
        import re
        projects = {}
        try:
            raw_list = json.loads(data_str)
            for item in raw_list:
                labels = item.get("Labels", {})
                project_name = labels.get("com.docker.compose.project")
                if not project_name:
                    continue
                    
                state = item.get("State", "")
                
                if project_name not in projects:
                    projects[project_name] = {
                        "name": project_name,
                        "status": "stopped",
                        "subdomain": "—",
                        "containers_count": 0,
                        "running_count": 0
                    }
                    
                projects[project_name]["containers_count"] += 1
                if state.lower() == "running":
                    projects[project_name]["running_count"] += 1
                    projects[project_name]["status"] = "running"
                    
                # Buscar reglas de Traefik para extraer el subdominio
                for k, v in labels.items():
                    if k.startswith("traefik.http.routers.") and k.endswith(".rule"):
                        m = re.search(r'Host\(`([^`]+)`\)', v)
                        if m:
                            projects[project_name]["subdomain"] = m.group(1)
        except Exception as e:
            print(f"[Docker] Error parsing compose projects: {e}")
            
        return list(projects.values())
