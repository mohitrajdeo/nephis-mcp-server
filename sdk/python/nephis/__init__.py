"""
NEPHIS Cloud Systems SDK: High-Performance Isolated Compute & Database Substrate.
Provides native bindings for microVM sandboxing, deterministic storage, and speculative execution.
"""

import os
from typing import Optional, Dict, Any, List

from thanaton.client import Client as ThanatonClient, Sandbox as ThanatonSandbox
from thanaton.exceptions import (
    ThanatonError,
    ThanatonConnectionError,
    APIError,
    ExecutionTimeoutError,
    SandboxNotFoundError,
    SQLError,
    EscalationRequiredException,
)

from nephis.auth import (
    resolve_base_url,
    resolve_api_key,
    load_stored_credentials,
    save_credentials,
)

__version__ = "1.0.4"

class AdminManager:
    """Cluster administration & emergency security killswitch manager."""
    def __init__(self, client: 'NephisClient'):
        self.client = client

    def quarantine(self, tenant_id: str, reason: str = "Emergency security isolation trigger", freeze_sandboxes: bool = True) -> Dict[str, Any]:
        return self.client._request("POST", "/api/v1/admin/tenants/quarantine", body={
            "tenant_id": tenant_id,
            "reason": reason,
            "operator": "nephis-python-sdk",
            "freeze_sandbox": freeze_sandboxes,
        })

    def unquarantine(self, tenant_id: str) -> Dict[str, Any]:
        return self.client._request("POST", "/api/v1/admin/tenants/unquarantine", body={"tenant_id": tenant_id})

    def list_quarantined(self) -> List[str]:
        result = self.client._request("GET", "/api/v1/admin/tenants/quarantined")
        tenants = result.get("quarantined_tenants", []) if isinstance(result, dict) else []
        return [str(item) for item in tenants]

    def list_nodes(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("The provider API does not expose a node inventory endpoint.")


class SpecBoxManager:
    """Green Paper 10 (ATC '25 SpecBox): Token-Stream Interception Sandbox Pre-warming."""
    def __init__(self, client: 'NephisClient'):
        self.client = client

    def warm(self, language: str = "python", memory_mb: int = 128, tenant_id: str = "tenant-default") -> Dict[str, Any]:
        raise NotImplementedError("The provider API does not expose a SpecBox warm endpoint.")


class OZZManager:
    """Green Paper 11 (SOSP '24 OZZ Best Paper): In-Vivo PMU Permutation Fuzzing for Concurrency Races."""
    def __init__(self, client: 'NephisClient'):
        self.client = client

    def fuzz(self, target_command: str = "go test -race ./...", iterations: int = 50, thread_count: int = 4) -> Dict[str, Any]:
        raise NotImplementedError("The provider API does not expose an OZZ fuzz endpoint.")


class LazyLogManager:
    """Green Paper 12 (SOSP '24 LazyLog Best Paper): Decoupled WAL Ingest Ring Buffer."""
    def __init__(self, client: 'NephisClient'):
        self.client = client

    def append(self, tenant_id: str, record_type: str = "WAL_RECORD_TX_COMMIT", payload: str = "") -> Dict[str, Any]:
        raise NotImplementedError("The provider API does not expose a LazyLog append endpoint.")


class AnvilManager:
    """Green Paper 13 (OSDI '24 Anvil Best Paper): Formally Bounded Ranked Controller Liveness."""
    def __init__(self, client: 'NephisClient'):
        self.client = client

    def verify(self, controller_name: str = "nephis-sandbox-reconciler", initial_rank: int = 8) -> Dict[str, Any]:
        raise NotImplementedError("The provider API does not expose an Anvil verification endpoint.")


class ResearchManager:
    """Research Paper Verification Manager for 13 Commodity Green Systems Papers."""
    def __init__(self, client: 'NephisClient'):
        self.client = client

    def verify(self) -> Dict[str, Any]:
        raise NotImplementedError("The provider API does not expose a research verification endpoint.")


class NephisClient(ThanatonClient):
    """NEPHIS Cloud Platform Client with multi-dock support and alias bridges."""
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: float = 30.0):
        resolved_base_url = resolve_base_url(base_url)
        resolved_api_key = resolve_api_key(api_key, base_url=resolved_base_url)
        super().__init__(base_url=resolved_base_url, api_key=resolved_api_key, timeout=timeout)
        self.admin = AdminManager(self)
        self.specbox = SpecBoxManager(self)
        self.ozz = OZZManager(self)
        self.lazylog = LazyLogManager(self)
        self.anvil = AnvilManager(self)
        self.research = ResearchManager(self)

    def fast_batch(self, language_id: int, source_code: str, tests: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Executes up to 50 testcases through the metered /v1/execute endpoint.
        Returns the server's raw result and propagates API or billing errors.
        """
        if not 1 <= len(tests) <= 50:
            raise ValueError("tests must contain between 1 and 50 test cases")
        tests_slice = tests[:50]
        return self.eschaton.batch_execute(
            source_code=source_code,
            tests=tests_slice,
            language_id=language_id,
        )


# Canonical NEPHIS aliases
Client = NephisClient
NephisError = ThanatonError
NephisConnectionError = ThanatonConnectionError
NephisAPIError = APIError

# Try optional sub-engine imports for unified convenience
try:
    from mnemon import MnemonClient, TenantStatus, QueryResult, MnemonException
except ImportError:
    pass

try:
    from eschaton import EschatonClient, EschatonError
except ImportError:
    pass

__all__ = [
    "NephisClient",
    "Client",
    "ThanatonClient",
    "ThanatonSandbox",
    "EschatonClient",
    "EschatonError",
    "NephisError",
    "NephisConnectionError",
    "NephisAPIError",
    "AdminManager",
    "SpecBoxManager",
    "OZZManager",
    "LazyLogManager",
    "AnvilManager",
    "ResearchManager",
    "resolve_base_url",
    "resolve_api_key",
    "load_stored_credentials",
    "save_credentials",
    "__version__",
]
