"""
Ananke Deterministic Chaos Hypervisor (Powered by Chronofault)
Seed-driven discrete pseudo-time hypervisor for distributed Raft consensus and network fault injection.
"""

import subprocess
import shutil
import os
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class ChaosManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "chronofault.exe" if os.name == "nt" else "chronofault"
        p = shutil.which(bin_name) or shutil.which("chronofault")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "09_deterministic_chaos_hypervisor", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def run_simulation(self, seed: int = 1337, drop_rate: float = 0.10, dup_rate: float = 0.05, steps: int = 30) -> Dict[str, Any]:
        """Execute deterministic network chaos simulation with Raft consensus election."""
        self._authority.assert_feature("chaos")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "run",
            "--seed", str(seed),
            "--drop-rate", str(drop_rate),
            "--dup-rate", str(dup_rate),
            "--steps", str(steps)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def replay(self, seed: int = 1337) -> Dict[str, Any]:
        """Verify 100% bit-identical decision replay from a historical chaos seed."""
        self._authority.assert_feature("chaos")
        bin_path = self._get_bin_path()
        cmd = [bin_path, "replay", "--seed", str(seed)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

