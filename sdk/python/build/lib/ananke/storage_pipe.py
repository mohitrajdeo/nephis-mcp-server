"""
Ananke Zero-Copy S3 Streaming Pipe (Powered by S3pipe)
Streams multi-gigabyte files directly between kernel I/O buffers and cloud object storage without local disk scratch.
"""

import subprocess
import shutil
import os
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class StoragePipeManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "s3pipe.exe" if os.name == "nt" else "s3pipe"
        p = shutil.which(bin_name) or shutil.which("s3pipe")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "13_zero_copy_s3_streaming_pipe", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def benchmark(self, size_mb: int = 50, part_size_mb: int = 8, concurrency: int = 4) -> Dict[str, Any]:
        """Execute physical zero-copy streaming benchmark measuring MB/s and resident RAM bounds."""
        self._authority.assert_feature("pipe_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "bench",
            "--size-mb", str(size_mb),
            "--part-size-mb", str(part_size_mb),
            "--concurrency", str(concurrency)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def upload_stream(self, bucket: str, key: str, part_size_mb: int = 8, mock: bool = False) -> subprocess.Popen:
        """Create a streaming upload pipe where stdin writes stream directly to S3 multipart upload."""
        self._authority.assert_feature("pipe_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "upload",
            "--bucket", bucket,
            "--key", key,
            "--part-size-mb", str(part_size_mb)
        ]
        if mock:
            cmd.append("--mock")
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

