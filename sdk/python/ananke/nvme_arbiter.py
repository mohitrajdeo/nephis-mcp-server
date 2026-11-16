"""
Ananke Dynamic NVMe I/O Fair-Share Arbiter (Powered by ioarbiter)
Multi-Tenant SSD QoS Protection & Runaway Cgroup Clamping Engine.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class IOArbiterManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "ioarbiter-windows-amd64.exe" if os.name == "nt" else "ioarbiter"
        p = shutil.which(bin_name) or shutil.which("ioarbiter")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "16_dynamic_nvme_io_fair_share_arbiter", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def observe(self) -> List[Dict[str, Any]]:
        """Sample host block devices and NVMe drive queue depths."""
        self._authority.assert_feature("io_arbiter")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "observe", "--json"], capture_output=True, text=True, check=True)
        return json.loads(res.stdout.strip())

    def benchmark(self, enforce: bool = True) -> Dict[str, Any]:
        """Run multi-tenant noisy neighbor contention simulation."""
        self._authority.assert_feature("io_arbiter")
        bin_path = self._get_bin_path()
        cmd = [bin_path, "bench", "--json"]
        if enforce:
            cmd.append("--enforce")
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout.strip())

