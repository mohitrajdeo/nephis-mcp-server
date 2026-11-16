"""
Ananke Zero-Download Rootfs Streamer (Powered by Nbdstream)
Boots multi-gigabyte container rootfs images in <10ms via Linux NBD protocol v2 and COW sparse block cache.
"""

import subprocess
import shutil
import os
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class RootfsManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "nbdstream.exe" if os.name == "nt" else "nbdstream"
        p = shutil.which(bin_name) or shutil.which("nbdstream")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "15_zero_download_rootfs_streamer", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def build_manifest(self, source_path: str, output_path: str = "manifest.json", chunk_kb: int = 64) -> Dict[str, Any]:
        """Convert a container image or rootfs into a chunked block manifest."""
        self._authority.assert_feature("rootfs")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "build-manifest",
            "--source", source_path,
            "--output", output_path,
            "--chunk-kb", str(chunk_kb)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def benchmark(self, size_gb: int = 2, reads: int = 3000, concurrency: int = 15) -> Dict[str, Any]:
        """Benchmark 4KB block read IOPS and latency under random access patterns."""
        self._authority.assert_feature("rootfs")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "bench",
            "--size-gb", str(size_gb),
            "--reads", str(reads),
            "--concurrency", str(concurrency)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def start_server(self, listen: str = "127.0.0.1:10809", size_gb: int = 2, cache_mb: int = 64) -> subprocess.Popen:
        """Launch background NBD block streaming server."""
        self._authority.assert_feature("rootfs")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "serve",
            "--listen", listen,
            "--size-gb", str(size_gb),
            "--cache-mb", str(cache_mb)
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

