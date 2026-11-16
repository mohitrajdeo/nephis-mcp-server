"""
Ananke Live TCP Socket Migrator (Powered by Sockmig)
TCP_REPAIR kernel state serialization and seamless socket handoff across hosts.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class LiveMigrationManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "sockmig.exe" if os.name == "nt" else "sockmig"
        p = shutil.which(bin_name) or shutil.which("sockmig")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "19_live_tcp_socket_migrator", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def probe(self) -> Dict[str, Any]:
        """Inspect host kernel TCP_REPAIR (SOL_TCP=6, opt 19) capabilities."""
        self._authority.assert_feature("live_migration")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "probe"], capture_output=True, text=True, check=True)
        try:
            return json.loads(res.stdout)
        except Exception:
            return {"raw": res.stdout.strip()}

    def run_demo(self) -> Dict[str, Any]:
        """Execute active live TCP socket migration demonstration with sequential state preservation."""
        self._authority.assert_feature("live_migration")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "demo"], capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def benchmark(self, sessions: int = 10000) -> Dict[str, Any]:
        """Benchmark socket state serialization and decode throughput in sessions/second."""
        self._authority.assert_feature("live_migration")
        bin_path = self._get_bin_path()
        cmd = [bin_path, "bench", "--sessions", str(sessions)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

