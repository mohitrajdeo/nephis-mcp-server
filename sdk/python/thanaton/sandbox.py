"""Sandbox representation and execution methods."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .client import Client


@dataclass
class ExecResult:
    """Result of a command executed inside a Thanaton MicroVM sandbox."""
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class Sandbox:
    """An isolated Thanaton execution sandbox (KVM MicroVM or Silicon Isolate)."""

    def __init__(self, client: "Client", data: Dict[str, Any]):
        self._client = client
        self._update_from_data(data)

    def _update_from_data(self, data: Dict[str, Any]) -> None:
        self.id: str = data.get("id", "")
        self.tenant_id: str = data.get("tenant_id", "")
        self.runtime: str = data.get("runtime", "microvm")
        self.box_id: int = data.get("box_id", 0)
        self.pid: int = data.get("pid", 0)
        self.has_db: bool = data.get("has_db", False)
        self.db_port: Optional[int] = data.get("db_port")
        self.db_url: Optional[str] = data.get("db_url")
        self.cgroup_path: str = data.get("cgroup_path", "")
        self.state: str = data.get("state") or data.get("status") or "unknown"
        self.created_at: str = data.get("created_at", "")
        self.last_active_at: str = data.get("last_active_at", "")
        boot_raw = data.get("boot_duration_ms") or data.get("boot_time_ms") or 0.0
        try:
            self.boot_duration_ms: float = float(boot_raw)
        except (ValueError, TypeError):
            self.boot_duration_ms = 0.0

    def exec(
        self,
        command: str,
        timeout_ms: int = 15000,
        egress_policy: Optional[str] = None,
        allowed_egress_hosts: Optional[List[str]] = None,
        injected_env: Optional[Dict[str, str]] = None,
        target_node: Optional[str] = None,
    ) -> ExecResult:
        """Execute a shell command inside the sandbox with egress guard & SSRF shield."""
        payload: Dict[str, Any] = {
            "command": command,
            "timeout_ms": timeout_ms
        }
        if egress_policy:
            payload["egress_policy"] = egress_policy
        if allowed_egress_hosts:
            payload["allowed_egress_hosts"] = allowed_egress_hosts
        if injected_env:
            payload["injected_env"] = injected_env
        if target_node:
            payload["target_node"] = target_node

        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/exec", body=payload)
        return ExecResult(
            stdout=res.get("stdout") or res.get("output", ""),
            stderr=res.get("stderr", ""),
            exit_code=int(res.get("exit_code", 0)),
            duration_ms=float(res.get("duration_ms", 0.0))
        )

    def run_code(self, code: str, language: str = "python", timeout_ms: int = 15000) -> ExecResult:
        """Directly run a code snippet inside the sandbox."""
        lang = language.lower()
        if lang == "python":
            import shlex
            cmd = f"python3 -c {shlex.quote(code)}"
        elif lang in ("node", "javascript", "js"):
            import shlex
            cmd = f"node -e {shlex.quote(code)}"
        elif lang in ("bash", "sh"):
            import shlex
            cmd = f"bash -c {shlex.quote(code)}"
        else:
            import shlex
            cmd = f"python3 -c {shlex.quote(code)}"
        return self.exec(cmd, timeout_ms=timeout_ms)

    def sql(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query against the sandbox's embedded PostgreSQL instance."""
        payload = {"query": query}
        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/sql", body=payload)
        return res.get("rows", [])

    def freeze(self) -> Dict[str, Any]:
        """Freeze execution via Cgroups v2 (pauses all guest vCPU threads, 0% CPU consumption)."""
        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/freeze")
        self.state = "frozen"
        return res

    def unfreeze(self) -> Dict[str, Any]:
        """Resume execution instantly via Cgroups v2 unfreeze (<1ms)."""
        res = self._client._request("POST", f"/v1/sandboxes/{self.id}/unfreeze")
        self.state = "running"
        return res

    def sleep(self) -> Dict[str, Any]:
        """Scale MicroVM to zero (hibernates to NVMe snapshot, 0% CPU, $0 cost)."""
        res = self._client._request("POST", f"/_thanaton/tenants/{self.id}/sleep")
        self.state = "sleeping"
        return res

    def wake(self) -> Dict[str, Any]:
        """Wake MicroVM instantly from NVMe snapshot in sub-6ms."""
        res = self._client._request("POST", f"/_thanaton/tenants/{self.id}/wake")
        self.state = "running"
        return res

    def refresh(self) -> "Sandbox":
        """Refresh current sandbox state from the daemon."""
        data = self._client._request("GET", f"/v1/sandboxes/{self.id}")
        self._update_from_data(data)
        return self

    def pty_info(self) -> Dict[str, Any]:
        """Fetch interactive PTY terminal connection metadata and WebSocket endpoint."""
        return self._client._request("GET", f"/v1/sandboxes/{self.id}/pty")

    def expose_port(self, guest_port: int, protocol: str = "tcp", service_name: Optional[str] = None) -> Dict[str, Any]:
        """Expose a guest port via Layer 4 raw TCP forwarding (e.g. Postgres port 5432)."""
        payload: Dict[str, Any] = {"guest_port": guest_port, "protocol": protocol}
        if service_name:
            payload["service_name"] = service_name
        return self._client._request("POST", f"/v1/sandboxes/{self.id}/ports", body=payload)

    def list_ports(self) -> List[Dict[str, Any]]:
        """List all active Layer 4 TCP port mappings for this sandbox."""
        res = self._client._request("GET", f"/v1/sandboxes/{self.id}/ports")
        return res.get("ports", []) if isinstance(res, dict) else []

    def close_port(self, host_port: int) -> Dict[str, Any]:
        """Close an active Layer 4 TCP port mapping."""
        return self._client._request("DELETE", f"/v1/sandboxes/{self.id}/ports/{host_port}")

    def create_ram_snapshot(self, warm_packages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Capture running guest RAM state directly to high-speed /dev/shm in ~15ms."""
        return self._client.create_ram_snapshot(self.id, warm_packages=warm_packages)

    def restore_ram_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Restore this sandbox from a pre-warmed RAM snapshot in 12ms."""
        return self._client.restore_ram_snapshot(snapshot_id, sandbox_id=self.id)

    def configure_secret_shield(self, action: str = "get") -> Dict[str, Any]:
        """Inspect or configure eBPF kernel TAP outbound secret exfiltration firewall."""
        return self._client.configure_secret_shield(self.id, action=action)

    def capture_browser_display(self, format: str = "jpeg", quality: int = 80) -> Dict[str, Any]:
        """Capture real-time screenshot or CDP stream frame from headless browser canvas."""
        return self._client.capture_browser_display(self.id, format=format, quality=quality)

    def destroy(self) -> Dict[str, Any]:
        """Terminate processes, clean up database, and release sandbox resources."""
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
        return f"<Thanaton Sandbox id='{self.id}' runtime='{self.runtime}' state='{self.state}'{db_info}>"
