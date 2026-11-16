"""
Ananke Pre-OOM Flight Recorder & Kernel Diagnostics (Powered by Tombstone)
Captures process state, open file descriptors, and memory breakdown before kernel kill -9.
"""

import subprocess
import shutil
import os
from typing import Dict, Any, Optional
from .license import LicenseAuthority


class DiagnosticsManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "tombstone.exe" if os.name == "nt" else "tombstone"
        p = shutil.which(bin_name) or shutil.which("tombstone")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "07_pre_oom_flight_recorder", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def inspect(self, tombstone_file: str) -> Dict[str, Any]:
        """Parse and display pre-OOM crash autopsy report."""
        self._authority.assert_feature("flight_recorder")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "inspect", tombstone_file], capture_output=True, text=True)
        return {
            "exit_code": res.returncode,
            "autopsy": res.stdout.strip(),
            "stderr": res.stderr.strip()
        }

    def start_recorder(self, cgroup_path: str, threshold_pct: int = 80, output_path: str = "/tmp/tombstone.json") -> subprocess.Popen:
        """Launch background cgroups v2 memory.events flight recorder."""
        self._authority.assert_feature("flight_recorder")
        bin_path = self._get_bin_path()
        cmd = [
            bin_path, "record",
            "--cgroup", cgroup_path,
            "--threshold", str(threshold_pct),
            "--output", output_path
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

