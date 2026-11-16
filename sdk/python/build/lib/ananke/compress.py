"""
Ananke Cross-AZ Traffic Compressor (Powered by azcomp)
Wire-Level LZ4/Snappy TCP Stream Compressor & AWS Egress FinOps Optimizer.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class CompressManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "azcomp-windows-amd64.exe" if os.name == "nt" else "azcomp"
        p = shutil.which(bin_name) or shutil.which("azcomp")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "06_cross_az_traffic_compressor", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def benchmark(self, algo: str = "snappy", size_mb: int = 50) -> Dict[str, Any]:
        """Run wire compression throughput benchmark."""
        self._authority.assert_feature("compress_basic")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [bin_path, "bench", "--algo", algo, "--size-mb", str(size_mb)],
            capture_output=True, text=True, check=True
        )
        return {"output": res.stdout.strip()}

    def calculate_finops_savings(self, monthly_gb: float = 100000.0, compression_ratio: float = 0.80) -> Dict[str, Any]:
        """Calculate AWS Cross-AZ $0.01/GB transfer bill reduction."""
        self._authority.assert_feature("compress_basic")
        baseline_cost = monthly_gb * 0.01
        compressed_gb = monthly_gb * (1.0 - compression_ratio)
        optimized_cost = compressed_gb * 0.01
        monthly_savings = baseline_cost - optimized_cost

        return {
            "baseline_traffic_gb": monthly_gb,
            "compression_ratio_percent": compression_ratio * 100.0,
            "compressed_wire_traffic_gb": compressed_gb,
            "baseline_monthly_cost_usd": baseline_cost,
            "optimized_monthly_cost_usd": optimized_cost,
            "monthly_savings_usd": monthly_savings,
            "annual_savings_usd": monthly_savings * 12.0
        }

