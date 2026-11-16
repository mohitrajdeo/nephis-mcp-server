"""
Ananke Ephemeral DNS Engine (Powered by Xdpdns)
Sub-microsecond in-memory authoritative DNS server for dynamic wildcard staging routing.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class DNSManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "xdpdns.exe" if os.name == "nt" else "xdpdns"
        p = shutil.which(bin_name) or shutil.which("xdpdns")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "17_kernel_bypass_submicrosecond_dns", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def probe(self) -> Dict[str, Any]:
        """Inspect host interface XDP driver status and kernel bypass capabilities."""
        self._authority.assert_feature("dns_basic")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "probe"], capture_output=True, text=True, check=True)
        try:
            return json.loads(res.stdout)
        except Exception:
            return {"raw": res.stdout.strip()}

    def benchmark(self, queries: int = 20000, concurrency: int = 20, target: Optional[str] = None) -> Dict[str, Any]:
        """Run continuous high-throughput UDP DNS query benchmark measuring QPS and latency."""
        self._authority.assert_feature("dns_basic")
        bin_path = self._get_bin_path()
        cmd = [bin_path, "bench", "--queries", str(queries), "--concurrency", str(concurrency)]
        if target:
            cmd.extend(["--target", target])
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def start_server(self, listen: str = "127.0.0.1:1053", wildcard: str = "preview.ananke.run", default_ip: str = "10.0.0.1") -> subprocess.Popen:
        """Launch authoritative UDP DNS resolver daemon."""
        self._authority.assert_feature("dns_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "serve",
            "--listen", listen,
            "--wildcard", wildcard,
            "--default-ip", default_ip
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

