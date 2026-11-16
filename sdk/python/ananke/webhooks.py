"""
Ananke Outbound Webhooks Engine (Powered by HookQ)
High-throughput outbound webhook infrastructure with kernel anti-SSRF firewall and HMAC-SHA256 signatures.
"""

import subprocess
import shutil
import os
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class WebhookManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "hookq.exe" if os.name == "nt" else "hookq"
        p = shutil.which(bin_name) or shutil.which("hookq")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "03_outgoing_webhook_infra", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def send(self, url: str, payload: str, secret: str = "webhook_secret", retries: int = 3) -> Dict[str, Any]:
        """Dispatch a single outbound webhook through anti-SSRF firewall with HMAC signature."""
        self._authority.assert_feature("webhooks_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "send",
            "--url", url,
            "--payload", payload,
            "--secret", secret,
            "--retries", str(retries)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "success": res.returncode == 0
        }

    def start_worker(self, listen_addr: str = ":8085", db_path: str = "hookq.db", workers: int = 10) -> subprocess.Popen:
        """Start persistent HookQ HTTP queue ingestion and dispatcher daemon."""
        self._authority.assert_feature("webhooks_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "serve",
            "--listen", listen_addr,
            "--db", db_path,
            "--workers", str(workers)
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

