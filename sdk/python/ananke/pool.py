"""
Ananke Database Connection Pooler & Anti-RDS Proxy (Powered by Sockpool)
Client-side eBPF sockmap connection pooler and fast PostgreSQL wire-multiplexer.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class PoolManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "sockpool.exe" if os.name == "nt" else "sockpool"
        p = shutil.which(bin_name) or shutil.which("sockpool")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "11_ebpf_client_side_connection_pooler", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def probe(self) -> Dict[str, Any]:
        """Inspect host kernel eBPF sockmap, BPF JIT, and socket splicing support."""
        self._authority.assert_feature("pool_basic")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "probe"], capture_output=True, text=True, check=True)
        try:
            return json.loads(res.stdout)
        except Exception:
            return {"raw": res.stdout.strip()}

    def benchmark(self, target: str = "127.0.0.1:6432", clients: int = 50, queries: int = 100) -> Dict[str, Any]:
        """Run high-concurrency client load test against sockpool proxy."""
        self._authority.assert_feature("pool_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "bench",
            "--target", target,
            "--clients", str(clients),
            "--queries", str(queries)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def start_pooler(self, listen: str = ":6432", upstream: str = "127.0.0.1:5432", pool_size: int = 10, user: str = "postgres", db: str = "postgres") -> subprocess.Popen:
        """Launch background client-side connection pooling daemon."""
        self._authority.assert_feature("pool_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "run",
            "--listen", listen,
            "--upstream", upstream,
            "--pool-size", str(pool_size),
            "--user", user,
            "--database", db
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

