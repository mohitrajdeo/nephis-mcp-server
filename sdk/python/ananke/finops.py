"""
Ananke FinOps & Cloud Resource Optimizer (Powered by ZombiePrune)
Deterministic AWS zombie resource pruner detecting detached EBS, unattached EIPs, and idle NATs.
"""

import subprocess
import shutil
import os
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class FinOpsManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "zombieprune.exe" if os.name == "nt" else "zombieprune"
        p = shutil.which(bin_name) or shutil.which("zombieprune")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "05_aws_zombie_resource_pruner", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def scan(self, regions: str = "us-east-1", dry_run: bool = True, mock: bool = True) -> Dict[str, Any]:
        """Scan AWS infrastructure for orphaned resources and estimated monthly savings."""
        self._authority.assert_feature("finops")
        bin_path = self._get_bin_path()
        cmd = [bin_path, "scan", "-json"]
        if mock or dry_run:
            cmd.append("-mock")
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "report": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def prune(self, regions: str = "us-east-1", confirm: bool = False) -> Dict[str, Any]:
        """Prune unattached, unprotected zombie resources across specified regions."""
        self._authority.assert_feature("finops")
        bin_path = self._get_bin_path()
        cmd = [bin_path, "prune", "--regions", regions]
        if confirm:
            cmd.append("--confirm-prune-i-know-what-i-am-doing")
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

