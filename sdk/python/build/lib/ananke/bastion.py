"""
Ananke Ephemeral DB Bastion (Powered by db-bastion)
Zero-Trust Ephemeral Wire-Level PostgreSQL Proxy & Audit Engine.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class BastionManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "db-bastion-windows-amd64.exe" if os.name == "nt" else "db-bastion"
        p = shutil.which(bin_name) or shutil.which("db-bastion")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "02_ephemeral_db_ssh_gateway", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def generate_token(self, tenant_id: str, username: str, duration_sec: int = 900) -> Dict[str, Any]:
        """Generate a cryptographically signed ephemeral access token."""
        self._authority.assert_feature("bastion_basic")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [bin_path, "token", "--tenant", tenant_id, "--user", username, "--duration", f"{duration_sec}s"],
            capture_output=True, text=True, check=True
        )
        return {"output": res.stdout.strip()}

    def inspect_audit(self, audit_file_path: str) -> List[Dict[str, Any]]:
        """Parse and return structured JSON audit entries from an append-only bastion log."""
        self._authority.assert_feature("bastion_basic")
        if not os.path.exists(audit_file_path):
            return []
        entries = []
        with open(audit_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
        return entries

