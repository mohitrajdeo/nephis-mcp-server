"""
Ananke Out-of-Band Memory Reclaimer (Powered by memreclaim)
process_madvise Heap Reclaimer & Host Density Optimizer.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class MemoryReclaimManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "memreclaim-windows-amd64.exe" if os.name == "nt" else "memreclaim"
        p = shutil.which(bin_name) or shutil.which("memreclaim")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "12_out_of_band_memory_reclaimer", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def scan_host(self, min_rss_mb: int = 20) -> Dict[str, Any]:
        """Scan host container memory maps for inactive reclaimable pages."""
        self._authority.assert_feature("mem_reclaim")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [bin_path, "scan", "--min-rss-mb", str(min_rss_mb), "--json"],
            capture_output=True, text=True, check=True
        )
        return json.loads(res.stdout.strip())

    def benchmark(self, alloc_mb: int = 128) -> Dict[str, Any]:
        """Run self-reclamation heap memory reduction benchmark."""
        self._authority.assert_feature("mem_reclaim")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [bin_path, "bench", "--alloc-mb", str(alloc_mb), "--json"],
            capture_output=True, text=True, check=True
        )
        return json.loads(res.stdout.strip())

