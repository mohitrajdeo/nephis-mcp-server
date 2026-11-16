"""
Ananke CDC Engine (Powered by Walquet)
Zero-JVM PostgreSQL WAL to Parquet/S3 Replication Manager.
"""

import subprocess
import shutil
import os
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class CDCManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        # Check PATH or local product_ideas path
        bin_name = "walquet.exe" if os.name == "nt" else "walquet"
        p = shutil.which(bin_name) or shutil.which("walquet")
        if p:
            return p
        
        # Local workspace fallbacks
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "01_debezium_without_kafka", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def inspect_parquet(self, file_path: str) -> Dict[str, Any]:
        """Inspect schema, row count, and sample record of a Walquet Parquet file."""
        self._authority.assert_feature("cdc_basic")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "inspect", file_path], capture_output=True, text=True, check=True)
        return {"output": res.stdout.strip()}

    def benchmark(self, records: int = 10000, batch_size: int = 2000) -> Dict[str, Any]:
        """Run in-memory WAL Parquet encoding throughput benchmark."""
        self._authority.assert_feature("cdc_basic")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [bin_path, "benchmark", "--records", str(records), "--batch-size", str(batch_size)],
            capture_output=True, text=True, check=True
        )
        return {"output": res.stdout.strip()}

    def start_stream(self, db_url: str, output_dir: str, slot: str = "walquet_slot", pub: str = "walquet_pub", batch_size: int = 5000) -> subprocess.Popen:
        """Launch background WAL replication streaming daemon."""
        self._authority.assert_feature("cdc_basic")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "run",
            "--db-url", db_url,
            "--output-dir", output_dir,
            "--slot", slot,
            "--publication", pub,
            "--batch-size", str(batch_size)
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

