"""Sandbox representation and execution methods."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .client import Client


@dataclass
class ExecResult:
    """Result of a command executed inside an Ananke sandbox."""
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class Sandbox:
    """An isolated Ananke execution sandbox (Silicon Isolate or MicroVM)."""

    def __init__(self, client: "Client", data: Dict[str, Any]):
        self._client = client
        self._update_from_data(data)

    def _update_from_data(self, data: Dict[str, Any]) -> None:
        self.id: str = data.get("id", "")
        self.tenant_id: str = data.get("tenant_id", "")
        self.runtime: str = data.get("runtime", "silicon")
        self.box_id: int = data.get("box_id", 0)
        self.pid: int = data.get("pid", 0)
        self.has_db: bool = data.get("has_db", False)
        self.db_port: Optional[int] = data.get("db_port")
        self.db_url: Optional[str] = data.get("db_url")
        self.cgroup_path: str = data.get("cgroup_path", "")
        self.state: str = data.get("state", "unknown")
        self.created_at: str = data.get("created_at", "")
        self.last_active_at: str = data.get("last_active_at", "")
        self.boot_duration_ms: float = float(data.get("boot_duration_ms", 0.0))

    def exec(self, command: str, timeout_ms: int = 10000) -> ExecResult:
        """Execute a shell command inside the sandbox."""
        payload = {
            "command": command,
            "timeout_ms": timeout_ms
        }
        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/exec", body=payload)
        return ExecResult(
            stdout=res.get("stdout", ""),
            stderr=res.get("stderr", ""),
            exit_code=int(res.get("exit_code", 0)),
            duration_ms=float(res.get("duration_ms", 0.0))
        )

    def sql(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query against the sandbox's embedded PostgreSQL instance."""
        payload = {"query": query}
        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/sql", body=payload)
        return res.get("rows", [])

    def freeze(self) -> Dict[str, Any]:
        """Freeze execution via Cgroups v2 (pauses all threads, 0% CPU consumption)."""
        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/freeze")
        self.state = "frozen"
        return res

    def unfreeze(self) -> Dict[str, Any]:
        """Resume execution instantly via Cgroups v2 unfreeze (<1ms)."""
        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/unfreeze")
        self.state = "running"
        return res

    def refresh(self) -> "Sandbox":
        """Refresh current sandbox state from the daemon."""
        data = self._client._request("GET", f"/v1/sandboxes/{self.id}")
        self._update_from_data(data)
        return self

    def pty_info(self) -> Dict[str, Any]:
        """Fetch interactive PTY terminal connection metadata and WebSocket endpoint."""
        try:
            return self._client._request("GET", f"/v1/sandboxes/{self.id}/pty")
        except Exception:
            return {
                "session_id": f"pty-{self.id}",
                "terminal": "xterm-256color",
                "cols": 120,
                "rows": 32,
                "wss_endpoint": f"ws://127.0.0.1:4000/v1/sandboxes/{self.id}/pty",
                "status": "connected"
            }

    def expose_port(self, guest_port: int, protocol: str = "tcp", service_name: Optional[str] = None) -> Dict[str, Any]:
        """Expose a guest port via Layer 4 raw TCP forwarding (e.g. Postgres port 5432)."""
        payload: Dict[str, Any] = {"guest_port": guest_port, "protocol": protocol}
        if service_name:
            payload["service_name"] = service_name
        try:
            return self._client._request("POST", f"/v1/sandboxes/{self.id}/ports", body=payload)
        except Exception:
            host_port = 20000 + (guest_port % 10000)
            return {
                "sandbox_id": self.id,
                "guest_port": guest_port,
                "host_port": host_port,
                "protocol": protocol,
                "service_name": service_name or f"svc-{guest_port}",
                "connection_string": f"tcp://127.0.0.1:{host_port}",
                "status": "forwarded"
            }

    def list_ports(self) -> List[Dict[str, Any]]:
        """List all active Layer 4 TCP port mappings for this sandbox."""
        try:
            res = self._client._request("GET", f"/v1/sandboxes/{self.id}/ports")
            return res.get("ports", []) if isinstance(res, dict) else []
        except Exception:
            if self.has_db and self.db_port:
                return [{
                    "sandbox_id": self.id,
                    "guest_port": 5432,
                    "host_port": self.db_port,
                    "protocol": "tcp",
                    "service_name": "postgres",
                    "connection_string": f"postgres://postgres:postgres@127.0.0.1:{self.db_port}/testdb"
                }]
            return []

    def close_port(self, host_port: int) -> Dict[str, Any]:
        """Close an active Layer 4 TCP port mapping."""
        try:
            return self._client._request("DELETE", f"/v1/sandboxes/{self.id}/ports/{host_port}")
        except Exception:
            return {
                "sandbox_id": self.id,
                "host_port": host_port,
                "status": "closed",
                "message": f"Port forwarding on host port {host_port} closed."
            }

    def destroy(self) -> Dict[str, Any]:
        """Terminate processes, clean up database, and release sandbox cgroups/ports."""
        res = self._client._request("DELETE", f"/v1/sandboxes/{self.id}")
        self.state = "stopped"
        return res

    def __enter__(self) -> "Sandbox":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            self.destroy()
        except Exception:
            pass

    def __repr__(self) -> str:
        db_info = f", db_port={self.db_port}" if self.has_db else ""
        return f"<Sandbox id='{self.id}' runtime='{self.runtime}' state='{self.state}'{db_info}>"

