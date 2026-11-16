"""
Ananke Ephemeral NVMe Caching Engine (Powered by nvmesh)
Zero-Cost Local NVMe Block-Layer Read-Cache & EBS IOPS Eliminator.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class NVMeCacheManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "nvmesh-windows-amd64.exe" if os.name == "nt" else "nvmesh"
        p = shutil.which(bin_name) or shutil.which("nvmesh")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "10_ephemeral_nvme_caching_shim", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def calculate_finops(self, volume_type: str = "gp3", provisioned_iops: int = 25000, hit_rate: float = 0.85) -> Dict[str, Any]:
        """Calculate EBS provisioned IOPS cost reduction using local NVMe cache."""
        self._authority.assert_feature("nvme_cache")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [
                bin_path, "finops",
                "--volume-type", volume_type,
                "--provisioned-iops", str(provisioned_iops),
                "--cache-hit-rate", str(hit_rate),
                "--json"
            ],
            capture_output=True, text=True, check=True
        )
        return json.loads(res.stdout.strip())

    def benchmark(self, ops: int = 5000, concurrency: int = 4, read_ratio: float = 0.90) -> Dict[str, Any]:
        """Run multi-threaded NVMe block cache benchmark."""
        self._authority.assert_feature("nvme_cache")
        bin_path = self._get_bin_path()
        tmp_dir = os.environ.get("TEMP", "/tmp")
        b_file = os.path.join(tmp_dir, "nvmesh_py_back.dat")
        c_file = os.path.join(tmp_dir, "nvmesh_py_cache.dat")

        try:
            res = subprocess.run(
                [
                    bin_path, "bench",
                    "--backing", b_file,
                    "--cache", c_file,
                    "--ops", str(ops),
                    "--concurrency", str(concurrency),
                    "--read-ratio", str(read_ratio),
                    "--json"
                ],
                capture_output=True, text=True, check=True
            )
            return json.loads(res.stdout.strip())
        finally:
            if os.path.exists(b_file):
                try: os.remove(b_file)
                except Exception: pass
            if os.path.exists(c_file):
                try: os.remove(c_file)
                except Exception: pass

