"""
Ananke Shared-Memory Compiler Pre-Parser (Powered by shmparse)
Sub-50ms AST Header Pre-Tokenization & Acceleration Bridge.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class SHMCompilerManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "shmparse-windows-amd64.exe" if os.name == "nt" else "shmparse"
        p = shutil.which(bin_name) or shutil.which("shmparse")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "18_shared_memory_compiler_preparser", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def warm_headers(self, headers: str = "bits/stdc++.h,iostream,vector,algorithm") -> Dict[str, Any]:
        """Pre-tokenize and pin standard library headers to /dev/shm."""
        self._authority.assert_feature("shm_preparser")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [bin_path, "warm", "--headers", headers, "--json"],
            capture_output=True, text=True, check=True
        )
        return json.loads(res.stdout.strip())

    def benchmark(self, iterations: int = 25) -> Dict[str, Any]:
        """Benchmark cold disk I/O vs /dev/shm shared memory compilation speedup."""
        self._authority.assert_feature("shm_preparser")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [bin_path, "bench", "--iterations", str(iterations), "--json"],
            capture_output=True, text=True, check=True
        )
        return json.loads(res.stdout.strip())

