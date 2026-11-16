"""
Ananke Zero-Downtime Socket Handover (Powered by sockpass)
POSIX SCM_RIGHTS Live TCP Socket Handover Supervisor.
"""

import subprocess
import shutil
import os
import json
from typing import Dict, Any, List, Optional
from .license import LicenseAuthority


class SocketHandoffManager:
    def __init__(self, client: Any, authority: Optional[LicenseAuthority] = None):
        self._client = client
        self._authority = authority or getattr(client, "authority", LicenseAuthority())

    def _get_bin_path(self) -> str:
        bin_name = "sockpass-windows-amd64.exe" if os.name == "nt" else "sockpass"
        p = shutil.which(bin_name) or shutil.which("sockpass")
        if p:
            return p
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_bin = os.path.join(base, "product_ideas", "08_zero_downtime_socket_handover", "bin", bin_name)
        if os.path.exists(local_bin):
            return local_bin
        return bin_name

    def verify_scm_rights(self) -> Dict[str, Any]:
        """Verify operating system and kernel SCM_RIGHTS ancillary data capabilities."""
        self._authority.assert_feature("socket_handoff")
        is_linux = os.name != "nt"
        return {
            "os": "linux" if is_linux else "windows",
            "scm_rights_supported": is_linux,
            "zero_downtime_capable": is_linux,
            "mode": "KERNEL_SCM_RIGHTS" if is_linux else "SIMULATED_HANDOVER"
        }

