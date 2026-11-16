"""
Ananke Gray-Failure Network Simulator (Powered by graynet)
Deterministic Distributed Split-Brain & Asymmetric Network Partitioner.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class GrayNetManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "graynet-windows-amd64.exe" if os.name == "nt" else "graynet"
        p = shutil.which(bin_name) or shutil.which("graynet")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "14_gray_failure_network_simulator", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def simulate(
        self,
        scenario: str = "asymmetric-drop",
        seed: int = 1337,
        drop_rate: float = 0.30,
        steps: int = 20,
        node_a: str = "node-1",
        node_b: str = "node-2"
    ) -> Dict[str, Any]:
        """Run deterministic discrete-step network failure simulation."""
        self._authority.assert_feature("net_chaos")
        bin_path = self._get_bin_path()
        res = subprocess.run(
            [
                bin_path, "simulate",
                "--scenario", scenario,
                "--seed", str(seed),
                "--drop-rate", str(drop_rate),
                "--steps", str(steps),
                "--node-a", node_a,
                "--node-b", node_b,
                "--json"
            ],
            capture_output=True, text=True, check=True
        )
        return json.loads(res.stdout.strip())

    def probe(self) -> Dict[str, Any]:
        """Probe host network stack isolation and driver capabilities."""
        self._authority.assert_feature("net_chaos")
        bin_path = self._get_bin_path()
        res = subprocess.run([bin_path, "probe", "--json"], capture_output=True, text=True, check=True)
        return json.loads(res.stdout.strip())

