"""
Ananke Internal PKI & ACME CA (Powered by acmeca)
Turnkey Zero-Config Internal Root/Intermediate Certificate Authority.
"""

import subprocess
import shutil
import os
import json
import tempfile
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class PKIManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "acmeca-windows-amd64.exe" if os.name == "nt" else "acmeca"
        p = shutil.which(bin_name) or shutil.which("acmeca")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "04_turnkey_internal_pki_acme", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def issue_certificate(self, domain: str, ca_dir: Optional[str] = None, days: int = 90) -> Dict[str, Any]:
        """Issue an internal TLS certificate directly signed by the Intermediate CA."""
        self._authority.assert_feature("pki_basic")
        bin_path = self._get_bin_path()
        if not ca_dir:
            ca_dir = os.path.join(tempfile.gettempdir(), "ca_data")
        res = subprocess.run(
            [bin_path, "issue", "--domains", domain, "--data-dir", ca_dir, "--days", str(days)],
            capture_output=True, text=True, check=True
        )
        return {"output": res.stdout.strip()}

    def revoke_certificate(self, serial: str, ca_dir: Optional[str] = None) -> Dict[str, Any]:
        """Revoke a certificate by serial number."""
        self._authority.assert_feature("pki_basic")
        bin_path = self._get_bin_path()
        if not ca_dir:
            ca_dir = os.path.join(tempfile.gettempdir(), "ca_data")
        res = subprocess.run(
            [bin_path, "revoke", "--serial", serial, "--data-dir", ca_dir],
            capture_output=True, text=True, check=True
        )
        return {"output": res.stdout.strip()}
