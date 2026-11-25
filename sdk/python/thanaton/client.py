"""Thanaton HTTP Client using standard library urllib (zero external dependencies)."""

import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

try:
    _DEFAULT_SSL_CTX = ssl._create_unverified_context()
except Exception:
    _DEFAULT_SSL_CTX = ssl.create_default_context()
    _DEFAULT_SSL_CTX.check_hostname = False
    _DEFAULT_SSL_CTX.verify_mode = ssl.CERT_NONE

from .exceptions import (
    APIError,
    EgressPolicyViolationError,
    EschatonFuelExhaustedError,
    EscalationRequiredException,
    SQLError,
    SSRFSecurityViolationError,
    SandboxNotFoundError,
    ThanatonCapacityError,
    ThanatonConnectionError,
    ThanatonRateLimitError,
    ThanatonTimeoutError,
)
from .sandbox import ExecResult, Sandbox


class SandboxManager:
    """Manages creation, retrieval, and listing of Thanaton sandboxes."""

    def __init__(self, client: "Client"):
        self._client = client

    def create(
        self,
        runtime: str = "microvm",
        with_db: bool = False,
        memory_mb: int = 256,
        cpu_quota_pct: int = 100,
        tenant_id: Optional[str] = None
    ) -> Sandbox:
        """Provision a new isolated sandbox instance."""
        payload = {
            "runtime": runtime,
            "with_db": with_db,
            "memory_mb": memory_mb,
            "cpu_quota_pct": cpu_quota_pct,
            "tenant_id": tenant_id or "default"
        }
        data = self._client._request("POST", "/v1/sandboxes", body=payload)
        return Sandbox(self._client, data)

    def get(self, sandbox_id: str) -> Sandbox:
        """Retrieve an existing sandbox by ID."""
        data = self._client._request("GET", f"/v1/sandboxes/{sandbox_id}")
        return Sandbox(self._client, data)

    def list(self) -> List[Sandbox]:
        """List all active, frozen, or managed sandboxes."""
        data = self._client._request("GET", "/v1/sandboxes")
        if isinstance(data, dict):
            raw_items = data.get("sandboxes") or data.get("projects") or data.get("items") or []
            items = raw_items if isinstance(raw_items, list) else []
        elif isinstance(data, list):
            items = data
        else:
            items = []
        return [Sandbox(self._client, item) for item in items if isinstance(item, dict)]

    def destroy(self, sandbox_id: str) -> Dict[str, Any]:
        """Destroy a sandbox by ID."""
        return self._client._request("DELETE", f"/v1/sandboxes/{sandbox_id}")

    def wake_coalesced(self, tenant_id: str, sandbox_id: Optional[str] = None) -> Dict[str, Any]:
        """Trigger or coalesce a wake request with 2-phase admission to prevent thundering herds."""
        payload = {"tenant_id": tenant_id, "sandbox_id": sandbox_id or ""}
        return self._client._request("POST", "/api/v1/sandboxes/wake-coalesce", body=payload)

    def get_coalesce_stats(self) -> Dict[str, Any]:
        """Retrieve host metrics on coalesced wake bursts and prevented thundering herds."""
        return self._client._request("GET", "/api/v1/sandboxes/wake-coalesce/stats")


class VolumeManager:
    """Manages persistent ext4 NVMe block volumes for microVMs (SQLite & PocketBase)."""

    def __init__(self, client: "Client"):
        self._client = client

    def list(self, sandbox_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active and attached persistent volumes."""
        path = "/api/v1/sandboxes/volumes"
        if sandbox_id:
            path += f"?sandbox_id={sandbox_id}"
        res = self._client._request("GET", path)
        return res.get("volumes", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])

    def attach(self, sandbox_id: str, mount_path: str = "/data", size_gb: int = 10) -> Dict[str, Any]:
        """Attach a persistent sparse ext4 volume mounted at /data."""
        payload = {"sandbox_id": sandbox_id, "mount_path": mount_path, "size_gb": size_gb}
        return self._client._request("POST", "/api/v1/sandboxes/volumes", body=payload)

    def freeze(self, sandbox_id: str, volume_id: str) -> Dict[str, Any]:
        """Safely freeze the filesystem (fsfreeze -f) before scale-to-zero stasis."""
        payload = {"sandbox_id": sandbox_id, "volume_id": volume_id}
        return self._client._request("POST", "/api/v1/sandboxes/volumes/freeze", body=payload)

    def thaw(self, sandbox_id: str, volume_id: str) -> Dict[str, Any]:
        """Thaw the filesystem (fsfreeze -u) upon cold wake."""
        payload = {"sandbox_id": sandbox_id, "volume_id": volume_id}
        return self._client._request("POST", "/api/v1/sandboxes/volumes/thaw", body=payload)


class SecretsManager:
    """Manages instant zero-rebuild environment variable injection via Firecracker MMDS."""

    def __init__(self, client: "Client"):
        self._client = client

    def inject(self, sandbox_id: str, secrets: Dict[str, str]) -> Dict[str, Any]:
        """Stream secrets directly to Firecracker MMDS in <50µs with 0ms rebuild latency."""
        payload = {"sandbox_id": sandbox_id, "secrets": secrets}
        return self._client._request("POST", "/api/v1/sandboxes/secrets/inject", body=payload)

    def get(self, sandbox_id: str) -> Dict[str, Any]:
        """Read active MMDS metadata for a sandbox."""
        return self._client._request("GET", f"/api/v1/sandboxes/secrets?sandbox_id={sandbox_id}")


class ProjectManager:
    """Manages Thanaton projects, deployments, and edge settings."""

    def __init__(self, client: "Client"):
        self._client = client

    def list(self) -> List[Dict[str, Any]]:
        res = self._client._request("GET", "/api/v1/projects")
        if isinstance(res, dict) and "projects" in res:
            return res["projects"] or []
        return res if isinstance(res, list) else []

    def create(
        self,
        name: str,
        slug: Optional[str] = None,
        runtime: str = "nodejs",
        app_port: int = 3000,
        execution_mode: str = "sandbox",
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "slug": slug or "",
            "runtime": runtime,
            "app_port": app_port,
            "execution_mode": execution_mode,
        }
        return self._client._request("POST", "/api/v1/projects", body=payload)

    def deploy(
        self,
        slug: str,
        code: Optional[str] = None,
        filename: Optional[str] = None,
        runtime: str = "python",
        execution_mode: str = "sandbox",
        environment: str = "production",
        branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "code": code or "",
            "filename": filename or ("server.js" if runtime in ("node", "nodejs") else "app.py"),
            "runtime": runtime,
            "execution_mode": execution_mode,
            "environment": environment,
            "branch": branch,
            "demo": not bool(code),
        }
        return self._client._request("POST", f"/api/v1/projects/{slug}/deploy", body=payload)

    def list_deployments(self, project_id: str) -> Dict[str, Any]:
        """List deployment history for a Thanaton project with staging/production slots."""
        return self._client._request("GET", f"/api/v1/projects/deployments?project_id={project_id}")

    def deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Inspect status, build duration, bundle size, and worker node of a specific deployment."""
        return self._client._request("GET", f"/api/v1/deployments/status?id={deployment_id}")

    def set_preview(self, project_id: str, deployment_id: str) -> Dict[str, Any]:
        """Pin a deployment snapshot to the Staging Preview slot with synchronized zero-copy Mnemon database branch."""
        return self._client._request("POST", "/api/v1/projects/set-preview", body={"project_id": project_id, "deployment_id": deployment_id})

    def get_metrics(self, project_id: str) -> Dict[str, Any]:
        """Fetch live operational analytics for a Thanaton project (latency, status codes, requests/min)."""
        return self._client._request("GET", f"/api/v1/analytics/overview?project_id={project_id}")

    def get_telemetry(self, sandbox_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch real-time hardware telemetry for a Thanaton microVM sandbox (CPU, RSS, network rx/tx, disk I/O)."""
        query = f"?sandbox_id={sandbox_id}" if sandbox_id else ""
        return self._client._request("GET", f"/api/v1/user/sandboxes/telemetry{query}")

    def get_cluster_metrics(self) -> Dict[str, Any]:
        """Fetch physical cluster host telemetry (CPU, RAM used/total, active sandboxes, PPS)."""
        return self._client._request("GET", "/api/v1/admin/live-metrics")

    def rollback(self, project_id: str, deployment_id: Optional[str] = None, atomic: bool = True) -> Dict[str, Any]:
        """Roll back production traffic. Defaults to atomic 2PC sub-millisecond rollback."""
        if atomic:
            return self.rollback_atomic(project_id, target_deployment_id=deployment_id)
        payload = {"project_id": project_id, "deployment_id": deployment_id or ""}
        return self._client._request("POST", "/api/v1/projects/rollback", body=payload)

    def promote(self, project_id: str, atomic: bool = True, skip_health_gate: bool = False) -> Dict[str, Any]:
        """Promote staging preview snapshot to production traffic. Defaults to atomic 2PC with health gate and watchdog."""
        if atomic:
            return self.promote_atomic(project_id, skip_health_gate=skip_health_gate)
        payload = {"project_id": project_id}
        return self._client._request("POST", "/api/v1/projects/promote", body=payload)

    def promote_atomic(self, project_id: str, skip_health_gate: bool = False) -> Dict[str, Any]:
        """Perform an atomic 2PC promotion of staging preview snapshot to production traffic with 5-stage health verification."""
        payload = {"project_id": project_id, "skip_health_gate": skip_health_gate}
        return self._client._request("POST", "/api/v1/projects/promote-atomic", body=payload)

    def rollback_atomic(self, project_id: str, target_deployment_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform an atomic rollback of production traffic to a previous healthy deployment snapshot."""
        payload = {"project_id": project_id, "target_deployment_id": target_deployment_id or ""}
        return self._client._request("POST", "/api/v1/projects/rollback-atomic", body=payload)

    def environments(self, project_id: str) -> Dict[str, Any]:
        """Inspect dual-slot environment state (Staging preview slot vs Production live slot) with Mnemon DB branches."""
        return self._client._request("GET", f"/api/v1/projects/environments?project_id={project_id}")

    def diff(self, project_id: str, from_tag: Optional[str] = None, to_tag: Optional[str] = None) -> Dict[str, Any]:
        """Inspect Git commit log, physical unified code diff, and Mnemon zero-copy schema diff between snapshots."""
        url = f"/api/v1/projects/diff?project_id={project_id}"
        if from_tag:
            url += f"&from={from_tag}"
        if to_tag:
            url += f"&to={to_tag}"
        return self._client._request("GET", url)

    def deploy_blue_green(self, project_id: str, version_tag: str = "v2") -> Dict[str, Any]:
        """Perform an atomic blue/green deployment swap with dual-probe health and zero dropped requests."""
        payload = {"project_id": project_id, "version_tag": version_tag}
        return self._client._request("POST", "/api/v1/projects/blue-green/deploy", body=payload)

    def env_list(self, project_id: str) -> List[Dict[str, Any]]:
        res = self._client._request("GET", f"/api/v1/projects/env?project_id={project_id}")
        return res.get("env_vars", []) if isinstance(res, dict) else []

    def env_set(self, project_id: str, key: str, value: str, environment: str = "all") -> Dict[str, Any]:
        payload = {"project_id": project_id, "key": key, "value": value, "environment": environment}
        return self._client._request("POST", "/api/v1/projects/env", body=payload)

    def env_delete(self, project_id: str, key: str) -> Dict[str, Any]:
        return self._client._request("DELETE", f"/api/v1/projects/env?project_id={project_id}&key={key}")

    def domains_list(self, project_id: str) -> List[Dict[str, Any]]:
        res = self._client._request("GET", f"/api/v1/projects/domains?project_id={project_id}")
        return res.get("domains", []) if isinstance(res, dict) else []

    def domains_add(self, project_id: str, domain: str) -> Dict[str, Any]:
        payload = {"project_id": project_id, "domain": domain}
        return self._client._request("POST", "/api/v1/projects/domains", body=payload)

    def domains_delete(self, project_id: str, domain: str) -> Dict[str, Any]:
        return self._client._request("DELETE", f"/api/v1/projects/domains?project_id={project_id}&domain={domain}")

    def crons_list(self, project_id: str) -> List[Dict[str, Any]]:
        res = self._client._request("GET", f"/api/v1/projects/crons?project_id={project_id}")
        return res.get("crons", []) if isinstance(res, dict) else []

    def crons_add(self, project_id: str, path: str, schedule: str) -> Dict[str, Any]:
        payload = {"project_id": project_id, "path": path, "schedule": schedule}
        return self._client._request("POST", "/api/v1/projects/crons", body=payload)

    def crons_delete(self, project_id: str, cron_id: str) -> Dict[str, Any]:
        return self._client._request("DELETE", f"/api/v1/projects/crons?project_id={project_id}&cron_id={cron_id}")

    def deploy_hooks_list(self, project_id: str) -> List[Dict[str, Any]]:
        res = self._client._request("GET", f"/api/v1/projects/deploy-hooks?project_id={project_id}")
        return res.get("deploy_hooks", []) if isinstance(res, dict) else []

    def deploy_hooks_create(self, project_id: str, name: str, branch: str = "main") -> Dict[str, Any]:
        payload = {"project_id": project_id, "name": name, "branch": branch}
        return self._client._request("POST", "/api/v1/projects/deploy-hooks", body=payload)

    def deploy_hooks_delete(self, project_id: str, hook_id: str) -> Dict[str, Any]:
        return self._client._request("DELETE", f"/api/v1/projects/deploy-hooks?project_id={project_id}&hook_id={hook_id}")

    def waf_get(self, project_id: str) -> Dict[str, Any]:
        return self._client._request("GET", f"/api/v1/projects/waf?project_id={project_id}")

    def waf_set(
        self,
        project_id: str,
        attack_mode: bool = False,
        rate_limit_rps: int = 1000,
        allowlist: Optional[List[str]] = None,
        blocklist: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "project_id": project_id,
            "attack_mode": attack_mode,
            "rate_limit_rps": rate_limit_rps,
            "allowlist": allowlist or [],
            "blocklist": blocklist or [],
        }
        return self._client._request("POST", "/api/v1/projects/waf", body=payload)

    def log_drains_list(self, project_id: str) -> List[Dict[str, Any]]:
        res = self._client._request("GET", f"/api/v1/projects/log-drains?project_id={project_id}")
        return res.get("log_drains", []) if isinstance(res, dict) else []

    def log_drains_add(
        self,
        project_id: str,
        name: str,
        drain_type: str,
        url: str,
        api_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "project_id": project_id,
            "name": name,
            "type": drain_type,
            "url": url,
            "api_token": api_token or "",
        }
        return self._client._request("POST", "/api/v1/projects/log-drains", body=payload)

    def log_drains_delete(self, project_id: str, drain_id: str) -> Dict[str, Any]:
        return self._client._request("DELETE", f"/api/v1/projects/log-drains?project_id={project_id}&drain_id={drain_id}")

    def scaling_get(self, project_id: str) -> Dict[str, Any]:
        """Fetch project compute scaling, execution mode (Serverless vs Always-On), and resource allocations."""
        return self._client._request("GET", f"/api/v1/projects/scaling?project_id={project_id}")

    def scaling_update(
        self,
        project_id: str,
        always_on: Optional[bool] = None,
        idle_timeout_seconds: Optional[int] = None,
        memory_mb: Optional[int] = None,
        vcpu_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update compute scaling, toggle between Serverless (scale-to-zero) and Always-On (stateful daemon)."""
        payload: Dict[str, Any] = {"project_id": project_id}
        if always_on is not None:
            payload["always_on"] = always_on
        if idle_timeout_seconds is not None:
            payload["idle_timeout_seconds"] = idle_timeout_seconds
        if memory_mb is not None:
            payload["memory_mb"] = memory_mb
        if vcpu_count is not None:
            payload["vcpu_count"] = vcpu_count
        return self._client._request("POST", "/api/v1/projects/scaling", body=payload)


class BillingManager:
    """Manages developer wallet balance, Stripe checkout sessions, and invoice history."""

    def __init__(self, client: "Client"):
        self._client = client

    def get_wallet(self) -> Dict[str, Any]:
        """Fetch current developer wallet balance ($ USD and credits), tier, and limits."""
        return self._client._request("GET", "/api/v1/billing/wallet")

    def topup(self, amount_usd: float = 10.00) -> Dict[str, Any]:
        """Create a Stripe checkout session for a supported one-time credit pack."""
        if amount_usd not in (5, 10, 20, 25, 50):
            raise ValueError("amount_usd must be one of the supported credit packs: 5, 10, 20, 25, or 50")
        return self._client._request("POST", "/api/v1/billing/topup", body={"amount_usd": amount_usd})

    def get_plans(self) -> List[Dict[str, Any]]:
        """List all subscription tiers and one-time credit refill packs."""
        return self._client._request("GET", "/api/v1/billing/plans")

    def checkout(
        self,
        plan: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a self-serve Stripe checkout session."""
        payload: Dict[str, Any] = {"plan": plan}
        if success_url:
            payload["success_url"] = success_url
        if cancel_url:
            payload["cancel_url"] = cancel_url
        return self._client._request("POST", "/api/v1/billing/checkout", body=payload)

    def list_invoices(self) -> List[Dict[str, Any]]:
        """Retrieve billing invoices and transaction payment history."""
        res = self._client._request("GET", "/api/v1/billing/invoices")
        return res if isinstance(res, list) else []


class Client:
    """Thanaton Control Plane Client."""

    def __init__(self, base_url: str = "https://nephis.theeducode.com", api_key: Optional[str] = None, timeout: float = 30.0, admin_secret: Optional[str] = None, api_url: Optional[str] = None):
        target_url = api_url or os.environ.get("NEPHIS_BASE_URL") or os.environ.get("THANATON_BASE_URL") or os.environ.get("THANATON_URL") or base_url
        self.base_url = target_url.rstrip("/")
        self.api_key = api_key or os.environ.get("THANATON_API_KEY") or os.environ.get("NEPHIS_API_KEY") or os.environ.get("ANANKE_API_KEY")
        self.admin_secret = admin_secret or os.environ.get("THANATON_ADMIN_SECRET")
        self.timeout = timeout
        self.sandboxes = SandboxManager(self)
        self.projects = ProjectManager(self)
        self.volumes = VolumeManager(self)
        self.secrets = SecretsManager(self)
        self.billing = BillingManager(self)

    def list_deployments(self, project_id: str) -> Dict[str, Any]:
        return self.projects.list_deployments(project_id)

    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        return self.projects.deployment_status(deployment_id)

    def set_preview(self, project_id: str, deployment_id: str) -> Dict[str, Any]:
        return self.projects.set_preview(project_id, deployment_id)

    def get_project_metrics(self, project_id: str) -> Dict[str, Any]:
        return self.projects.get_metrics(project_id)

    def get_sandbox_telemetry(self, sandbox_id: Optional[str] = None) -> Dict[str, Any]:
        return self.projects.get_telemetry(sandbox_id)

    def get_cluster_metrics(self) -> Dict[str, Any]:
        return self.projects.get_cluster_metrics()

    def inspect_environments(self, project_id: str) -> Dict[str, Any]:
        return self.projects.environments(project_id)

    def diff_deployments(self, project_id: str, from_tag: Optional[str] = None, to_tag: Optional[str] = None) -> Dict[str, Any]:
        return self.projects.diff(project_id, from_tag, to_tag)


        # Unified Mnemon Serverless PostgreSQL Substrate Access
        try:
            from mnemon.client import Client as MnemonClient
            mnemon_url = os.environ.get("MNEMON_API_URL", f"{self.base_url}/v1/db")
            proxy_h = self.base_url.split("://")[-1].split(":")[0]
            self.mnemon = MnemonClient(api_url=mnemon_url, api_key=self.api_key, proxy_host=proxy_h)
            self.db = self.mnemon
        except Exception:
            self.mnemon = None
            self.db = None

        # Dedicated Eschaton Execution Substrate Access
        try:
            from eschaton.client import EschatonClient
            self.eschaton = EschatonClient(base_url=self.base_url, api_key=self.api_key, timeout=self.timeout)
        except Exception:
            self.eschaton = None

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Thanaton-CLI/2.0"
        }
        if self.api_key:
            req_headers["Authorization"] = f"Bearer {self.api_key}"
            req_headers["X-API-Key"] = self.api_key
        if getattr(self, "admin_secret", None):
            req_headers["X-Admin-Secret"] = self.admin_secret
        if headers:
            req_headers.update(headers)

        last_error = None
        for attempt in range(3):
            req = urllib.request.Request(url, data=data, headers=req_headers, method=method)

            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=_DEFAULT_SSL_CTX) as response:
                    resp_bytes = response.read()
                    if not resp_bytes:
                        return {}
                    return json.loads(resp_bytes.decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                # In-Flight Transparent Replay Protocol (X-Nephis-Replay)
                if e.code == 503 and e.headers and e.headers.get("X-Nephis-Replay"):
                    replay_header = e.headers.get("X-Nephis-Replay")
                    replay_count = int(e.headers.get("X-Nephis-Replay-Count", "1"))
                    if replay_count <= 3:
                        target_addr = None
                        for part in replay_header.split(";"):
                            if part.strip().startswith("addr="):
                                target_addr = part.strip().split("=", 1)[1]
                        if target_addr and target_addr != self.base_url:
                            replay_client = Client(base_url=target_addr, api_key=self.api_key, timeout=self.timeout)
                            return replay_client._request(method, path, body=body)

                if e.code in (502, 503, 504) and attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue

                if e.code == 403 and "SSRF_BLOCKED" in err_body:
                    raise SSRFSecurityViolationError(message=err_body) from e
                elif e.code == 403 and ("EGRESS_BLOCKED" in err_body or "EGRESS_HOST_UNAUTHORIZED" in err_body):
                    raise EgressPolicyViolationError(message=err_body) from e
                elif e.code == 404:
                    raise SandboxNotFoundError(f"Endpoint or resource not found: {path}") from e
                elif e.code == 429:
                    retry_after = int(e.headers.get("Retry-After", 5)) if e.headers else 5
                    raise ThanatonRateLimitError(retry_after=retry_after, message=err_body) from e
                elif e.code == 503:
                    raise ThanatonCapacityError(message=err_body) from e
                elif e.code == 400 and ("fuel" in err_body.lower() or "budget" in err_body.lower()):
                    raise EschatonFuelExhaustedError(message=err_body) from e
                raise APIError(status_code=e.code, message=err_body) from e
            except urllib.error.URLError as e:
                if attempt < 2 and "timed out" not in str(e.reason).lower():
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if "timed out" in str(e.reason).lower():
                    raise ThanatonTimeoutError(f"Request timed out after {self.timeout}s: {path}") from e
                raise ThanatonConnectionError(url=url, reason=str(e.reason)) from e

    def whoami(self) -> Dict[str, Any]:
        """Display active account identity and quotas."""
        return self._request("GET", "/api/v1/auth/whoami")

    def list_golden_amis(self) -> List[Dict[str, Any]]:
        """List available pre-baked Golden AMI runtimes."""
        res = self._request("GET", "/v1/golden-amis")
        if isinstance(res, dict) and "amis" in res:
            return res["amis"]
        return res if isinstance(res, list) else []

    def create_ram_snapshot(self, sandbox_id: str, warm_packages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Capture running guest RAM state directly to /dev/shm in ~15ms."""
        payload = {"warm_packages": warm_packages or []}
        return self._request("POST", f"/v1/sandboxes/{sandbox_id}/ram-snapshot", body=payload)

    def restore_ram_snapshot(self, snapshot_id: str, sandbox_id: Optional[str] = None) -> Dict[str, Any]:
        """Restore guest memory state from RAM snapshot in 12ms."""
        target_sbx = sandbox_id or "default"
        payload = {"snapshot_id": snapshot_id}
        return self._request("POST", f"/v1/sandboxes/{target_sbx}/ram-snapshot/restore", body=payload)

    def configure_secret_shield(self, sandbox_id: str, action: str = "get") -> Dict[str, Any]:
        """Inspect or configure eBPF kernel TAP outbound secret exfiltration firewall."""
        if action == "get":
            return self._request("GET", f"/v1/sandboxes/{sandbox_id}/shield")
        return self._request("POST", f"/v1/sandboxes/{sandbox_id}/shield", body={"action": action})

    def capture_browser_display(self, sandbox_id: str, format: str = "jpeg", quality: int = 80) -> Dict[str, Any]:
        """Capture real-time screenshot or CDP stream frame from headless browser canvas."""
        return self._request("GET", f"/v1/sandboxes/{sandbox_id}/display?format={format}&quality={quality}")

    def live_migrate(
        self,
        target_node: str,
        pid: int,
        source_node: str = "localhost",
        socket_fd: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Live-migrate a running microVM or active TCP socket across nodes (AMD64 <-> ARM64)
        using Acheron Linux TCP_REPAIR with sub-105ms zero-downtime cutover."""
        payload = {
            "source_node": source_node,
            "target_node": target_node,
            "pid": pid,
            "dry_run": dry_run,
        }
        if socket_fd is not None:
            payload["socket_fd"] = socket_fd
        return self._request("POST", "/v1/sandboxes/migrate", body=payload)

    def create_checkpoint(
        self,
        sandbox_id: str,
        name: Optional[str] = None,
        snapshot_type: str = "ram",
    ) -> Dict[str, Any]:
        """Snapshot a running sandbox memory & filesystem state to persistent storage."""
        payload = {
            "name": name or f"snap_{int(time.time())}",
            "snapshot_type": snapshot_type,
        }
        return self._request("POST", f"/v1/sandboxes/{sandbox_id}/checkpoint", body=payload)

    def run_code(self, code: str, language: str = "python") -> ExecResult:
        """Helper to run code in an ephemeral sandbox and destroy it immediately."""
        sbx = self.sandboxes.create(runtime="microvm", memory_mb=256)
        try:
            return sbx.run_code(code, language=language)
        finally:
            sbx.destroy()

    def race(
        self,
        candidates: List[Dict[str, Any]],
        problem_id: str = "patch-race",
        strategy: str = "FASTEST_PASSING",
        timeout_ms: int = 15000,
    ) -> Dict[str, Any]:
        """Execute parallel multi-candidate speculative branch race across ephemeral microVMs.
        The fastest passing candidate wins and commits; losing candidate branches are instantly reaped."""
        payload = {
            "problem_id": problem_id,
            "strategy": strategy,
            "timeout_ms": timeout_ms,
            "candidates": candidates,
        }
        return self._request("POST", "/v1/speculate/race", body=payload)

    def rewind_database(
        self,
        target_lsn: str = "16/B374D848",
        tenant_id: Optional[str] = None,
        target_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fork an isolated database branch from historical PostgreSQL WAL in <35ms (point-in-time recovery)."""
        payload: Dict[str, Any] = {"target_lsn": target_lsn}
        if tenant_id:
            payload["tenant_id"] = tenant_id
        if target_time:
            payload["target_time"] = target_time
        return self._request("POST", "/v1/sandboxes/wal/rewind", body=payload)

    def upgrade_to_thanaton(
        self,
        session_or_state: Optional[Any] = None,
        runtime: str = "microvm",
        memory_mb: int = 512,
        with_db: bool = False,
        **kwargs
    ) -> Sandbox:
        """Seamlessly transitions execution from an in-memory Tier 0 session to a hardware-isolated Thanaton MicroVM,
        re-hydrating preserved session state (variables, memory) inside the new sandbox."""
        sbx = self.sandboxes.create(runtime=runtime, memory_mb=memory_mb, with_db=with_db, **kwargs)

        # Extract state from dict, EscalationRequiredException, or Session-like object
        state = {}
        if isinstance(session_or_state, dict):
            state = session_or_state
        elif hasattr(session_or_state, "serialized_state"):
            state = getattr(session_or_state, "serialized_state", {})
        elif hasattr(session_or_state, "env"):
            state = getattr(session_or_state, "env", {})

        if state:
            prelude_code = self._generate_state_hydration_code(state)
            sbx.run_code(prelude_code, language="python")

        return sbx

    @staticmethod
    def _generate_state_hydration_code(state: Dict[str, Any]) -> str:
        """Serializes session state dictionary into executable guest Python definitions."""
        lines = ["# Re-hydrated Tier 0 State from Aletheia/Eschaton Session"]
        for k, v in state.items():
            if not k.isidentifier():
                continue
            if isinstance(v, dict) and "type" in v and "value" in v:
                val = v["value"]
            else:
                val = v
            lines.append(f"{k} = {repr(val)}")
        return "\n".join(lines)

    def speculate(
        self,
        candidates: List[Any],
        test_command: str = "pytest",
        repo: Optional[str] = None,
        base_commit: Optional[str] = None,
        base_snapshot: Optional[str] = None,
        timeout_ms: int = 10000,
        strategy: str = "FASTEST_PASSING",
        auto_hot_swap: bool = False,
    ) -> Dict[str, Any]:
        """Physical-State MCTS: Evaluates candidate code patches across parallel hardware microVMs
        and CoW database branches in sub-seconds."""
        normalized_candidates = []
        for i, c in enumerate(candidates):
            if isinstance(c, str):
                normalized_candidates.append({"id": f"patch_{i+1}", "patch": c, "strategy": "default"})
            elif isinstance(c, dict):
                cand_id = c.get("id", f"patch_{i+1}")
                patch = c.get("patch", c.get("code", ""))
                strat = c.get("strategy", "default")
                normalized_candidates.append({"id": str(cand_id), "patch": patch, "strategy": strat})

        payload = {
            "repo": repo or "workspace",
            "base_commit": base_commit or "HEAD",
            "base_snapshot": base_snapshot or "db_base",
            "candidates": normalized_candidates,
            "test_command": test_command,
            "timeout_ms": timeout_ms,
            "strategy": strategy,
            "auto_hot_swap": auto_hot_swap,
        }

        return self._request("POST", "/api/v1/speculate", body=payload)

    # -------------------------------------------------------------
    # 5 Commercial Production Avenues (v2.0 Full Suite)
    # -------------------------------------------------------------

    def ci_accelerate(
        self,
        changed_symbols: Optional[List[str]] = None,
        test_suite_size: int = 500,
        enable_quarantine: bool = True,
        vm_snapshot_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Avenue 1: CI/CD Integration Test Accelerator v2.0
        Computes AST syntax delta impact slicing, quarantines flaky races under Kronos clock dilation,
        and restores pre-warmed COW microVM database testbeds."""
        payload = {
            "changed_symbols": changed_symbols or ["service.DBConnect"],
            "test_suite_size": test_suite_size,
            "enable_quarantine": enable_quarantine,
            "vm_snapshot_key": vm_snapshot_key or "snap-ci-default"
        }
        return self._request("POST", "/api/v1/ci/accelerate", body=payload)

    def db_branch(
        self,
        tenant_id: str = "tenant-enterprise-prod",
        target_lsn: str = "16/B374D848",
        mask_pii: bool = True,
        reap_ttl_hours: int = 2
    ) -> Dict[str, Any]:
        """Avenue 2: Self-Hosted On-Prem Database Branching v2.0
        Forks isolated copy-on-write database branches directly from any PostgreSQL Log Sequence Number (LSN),
        enforces in-kernel dynamic PII masking, and runs ephemeral branch auto-reaping."""
        payload = {
            "tenant_id": tenant_id,
            "target_lsn": target_lsn,
            "mask_pii": mask_pii,
            "reap_ttl_hours": reap_ttl_hours
        }
        return self._request("POST", "/api/v1/db/branch", body=payload)

    def socket_handover(
        self,
        canary_weight_pct: int = 15,
        in_flight_requests: int = 25,
        listen_sockets: int = 8
    ) -> Dict[str, Any]:
        """Avenue 3: Zero-Downtime Socket Handover & Hot-Reload Fabric v2.0
        Coordinates stateful WebSocket session re-hydration, SCM_RIGHTS file descriptor passing,
        and eBPF SO_REUSEPORT adaptive canary shifting with instant rollback."""
        payload = {
            "canary_weight_pct": canary_weight_pct,
            "in_flight_requests": in_flight_requests,
            "listen_sockets": listen_sockets
        }
        return self._request("POST", "/api/v1/socket/handover", body=payload)

    def microvm_runner(
        self,
        guest_ram_mb: int = 64,
        sandboxes_count: int = 120,
        subcore_quota_milli: int = 100
    ) -> Dict[str, Any]:
        """Avenue 4: High-Performance Serverless MicroVM Runner v2.0
        Restores guest memory from SABRE warm-pool superpages, enforces µSlice sub-core pacing
        across 120 co-located sandboxes, and streams analytical blocks via raw NVMe direct-I/O."""
        payload = {
            "guest_ram_mb": guest_ram_mb,
            "sandboxes_count": sandboxes_count,
            "subcore_quota_milli": subcore_quota_milli
        }
        return self._request("POST", "/api/v1/runner/execute", body=payload)

    def finops_optimize(
        self,
        traffic_tb: float = 10.0,
        volumes_count: int = 2
    ) -> Dict[str, Any]:
        """Avenue 5: Cloud Platform FinOps & Wire Matrix v2.0
        Bypasses AWS NAT Gateway fees via AntiNAT in-kernel masquerading, keeps traffic intra-AZ
        via AZAffinity locality routing, and active-prunes EBS gp2 storage to gp3."""
        payload = {
            "traffic_tb": traffic_tb,
            "volumes_count": volumes_count
        }
        return self._request("POST", "/api/v1/finops/optimize", body=payload)

    # -------------------------------------------------------------
    # 8 Frontier Research Breakthroughs (P0, P1, P2, P3 Full Suite)
    # -------------------------------------------------------------

    def catalyzer_fork(self, template_id: str = "tpl-python-3.12", sandbox_count: int = 120) -> Dict[str, Any]:
        """P0 Thanaton: Catalyzer Physical Frame Sharing (SOSP '24).
        Deduplicates immutable physical memory pages across microVM sandboxes for 119x memory boost."""
        payload = {"template_id": template_id, "sandbox_count": sandbox_count}
        return self._request("POST", "/api/v1/frontier/catalyzer/fork", body=payload)

    def ktls_sockmap_handover(self, conn_id: str = "sockmap-live-tls-01", target_gen: str = "gen-v2") -> Dict[str, Any]:
        """P0 Acheron: In-Kernel kTLS + eBPF SockMap Splicing (NSDI '25 / USENIX ATC '25).
        Migrates active TLS 1.3 TCP streams inside kernel with 0 dropped packets and 0 TLS renegotiation."""
        payload = {"conn_id": conn_id, "target_gen": target_gen}
        return self._request("POST", "/api/v1/frontier/ktls/handover", body=payload)

    def deltabranch_fork(self, tenant_id: str = "tenant-core-prod", branch_count: int = 20, lsn: int = 5000) -> Dict[str, Any]:
        """P1 Mnemon-DB: B-Tree Delta Trails & Warm Buffer Pool Grafting (VLDB '25 / SIGMOD '24 Neon).
        Zero-copy database branches graft parent shared buffer pools for sub-5ms forks and 0 disk I/O."""
        payload = {"tenant_id": tenant_id, "branch_count": branch_count, "lsn": lsn}
        return self._request("POST", "/api/v1/frontier/deltabranch/fork", body=payload)

    def rdt_partition_cache(self, sandbox_count: int = 120, arch: str = "auto") -> Dict[str, Any]:
        """P1 Hyperion: NUMA-Aware Intel RDT / ARM MPAM L3 Cache Partitioning (EuroSys '25 Cachier).
        Guarantees sub-0.2ms max stall latency by carving dedicated L3 cache ways and memory bandwidth."""
        payload = {"sandbox_count": sandbox_count, "arch": arch}
        return self._request("POST", "/api/v1/frontier/rdt/partition", body=payload)

    def nvme_predicate_pushdown(self, tenant_id: str = "tenant-analytics", rows: int = 500000, value: int = 42) -> Dict[str, Any]:
        """P2 Lethe: In-Storage eBPF Predicate Pushdown via io_uring_cmd (SIGMOD '25 PushdownStorage).
        Direct columnar block filtering pushes SQL WHERE evaluation into NVMe controllers (> 25 GB/s throughput)."""
        payload = {"tenant_id": tenant_id, "rows": rows, "value": value}
        return self._request("POST", "/api/v1/frontier/nvme/pushdown", body=payload)

    def specfuzz_synthesize(self, vector_count: int = 100000) -> Dict[str, Any]:
        """P2 Aletheia: Coverage-Guided Evolutionary Micro-Fuzzing with 64KB AFL Bitmap (OSDI '24 SpecFuzz).
        Synthesizes 100,000 edge-guided evolutionary test vectors in < 12ms."""
        payload = {"vector_count": vector_count}
        return self._request("POST", "/api/v1/frontier/specfuzz/synthesize", body=payload)

    def vdso_deterministic_schedule(self, sandbox_id: str = "sbx-kronos-01", seed: int = 9876543210, thread_count: int = 8) -> Dict[str, Any]:
        """P3 Kronos: VDSO Unmapping & Concurrency Thread Permuter (OSDI '24 Hermit).
        Forces all time reads through hypervisor trap table and permutes mutex sequences for 100% deterministic race reproduction."""
        payload = {"sandbox_id": sandbox_id, "seed": seed, "thread_count": thread_count}
        return self._request("POST", "/api/v1/frontier/vdso/schedule", body=payload)

    def rdma_cluster_commit(self, node_count: int = 100, tx_count: int = 10) -> Dict[str, Any]:
        """P3 Atomic 2PC Coordinator: RDMA One-Sided Cluster Coordination (OSDI '24 FaRM v3 / FastCommit).
        Executes distributed two-phase commits across 100 cloud nodes in < 10 microseconds."""
        payload = {"node_count": node_count, "tx_count": tx_count}
        return self._request("POST", "/api/v1/frontier/rdma/commit", body=payload)

    def create_snapshot(self, project_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a zero-copy NVMe volume snapshot of a microVM project."""
        payload = {"name": name} if name else {}
        return self._request("POST", f"/api/v1/projects/{project_id}/snapshots", body=payload)

    def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        """List all volume snapshots for a microVM project."""
        resp = self._request("GET", f"/api/v1/projects/{project_id}/snapshots")
        return resp.get("snapshots", [])

    def restore_snapshot(self, project_id: str, snapshot_id: str) -> Dict[str, Any]:
        """Restore a microVM project to a historical volume snapshot."""
        return self._request("POST", f"/api/v1/projects/{project_id}/snapshots/{snapshot_id}/restore")

    def get_fleet_overview(self) -> Dict[str, Any]:
        """Retrieve unified multi-engine fleet overview for admin governance."""
        return self._request("GET", "/api/v1/admin/fleet/overview")

    def execute_suite(self,
        source_code: str,
        language_id: int = 202,
        suite: str = "Apex",  # Omni is deprecated/degraded; default to Apex
        test_cases: Optional[List[Dict[str, Any]]] = None,
        database: Optional[str] = None,
        checker_code: Optional[str] = None,
        checker_language_id: Optional[int] = None,
        verbose: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute code across any of the Eschaton evaluation suites (Apex default, Void sub-4ms).
        Note: Omni suite is deprecated/degraded due to single-process pipe EOF failure on multi-cases.
        """
        payload: Dict[str, Any] = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": suite,
            "test_cases": test_cases or [{"id": 1, "stdin": "", "expected_output": ""}],
        }
        if database:
            payload["database"] = database
        if checker_code:
            payload["checker_code"] = checker_code
            payload["checker_language_id"] = checker_language_id or language_id
        if verbose is not None:
            payload["verbose"] = verbose
        return self._request("POST", "/v1/execute", body=payload)

    def complexity_profile(self,
        source_code: str,
        language_id: int = 202,
        stdin: str = "100",
    ) -> Dict[str, Any]:
        """Deterministic instruction counting & algorithmic complexity via Valgrind Lackey."""
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": "Complexity",
            "test_cases": [{"id": 1, "stdin": stdin}],
        }
        return self._request("POST", "/v1/execute", body=payload)

    def sanitize_check(self,
        source_code: str,
        language_id: int = 202,
        stdin: str = "",
    ) -> Dict[str, Any]:
        """Sub-20ms AddressSanitizer (ASan) + UBSan memory safety & leak profiling."""
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": "Sanitizer",
            "test_cases": [{"id": 1, "stdin": stdin}],
        }
        return self._request("POST", "/v1/execute", body=payload)

    def dbms_eval(self,
        source_code: str,
        schema_sql: str,
        database: str = "sqlite",
        expected_output: Optional[str] = None,
        stdin: str = "",
    ) -> Dict[str, Any]:
        """Automated SQL database grading with ephemeral schema injection across SQLite, Postgres, MySQL, Oracle."""
        tc: Dict[str, Any] = {"id": 1, "schema_sql": schema_sql, "stdin": stdin}
        if expected_output:
            tc["expected_output"] = expected_output
        payload = {
            "language_id": 204,
            "source_code": source_code,
            "suite": "DBMS",
            "database": database,
            "test_cases": [tc],
        }
        return self._request("POST", "/v1/execute", body=payload)

    def fileio_eval(self,
        source_code: str,
        input_filename: str = "input.txt",
        input_content: str = "DATA",
        output_filename: str = "output.txt",
        expected_output: Optional[str] = None,
        language_id: int = 204,
    ) -> Dict[str, Any]:
        """Isolated filesystem sandbox grading with custom input and output files."""
        tc: Dict[str, Any] = {
            "id": 1,
            "files": {input_filename: input_content},
            "output_file": output_filename,
        }
        if expected_output:
            tc["expected_output"] = expected_output
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": "FileIO",
            "test_cases": [tc],
        }
        return self._request("POST", "/v1/execute", body=payload)

    def special_judge(self,
        source_code: str,
        checker_code: str,
        language_id: int = 202,
        checker_language_id: int = 202,
        stdin: str = "5.0",
        expected_output: str = "2.5",
    ) -> Dict[str, Any]:
        """Custom competitive programming checker binary validator for floating point tolerances & permutations."""
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": "SpecialJudge",
            "checker_code": checker_code,
            "checker_language_id": checker_language_id,
            "test_cases": [{"id": 1, "stdin": stdin, "expected_output": expected_output}],
        }
        return self._request("POST", "/v1/execute", body=payload)

    def batch_execute(self,
        source_code: str,
        tests: List[Dict[str, Any]],
        suite: str = "Apex",  # Omni is deprecated/degraded; default to Apex
        language_id: int = 54,
    ) -> Dict[str, Any]:
        """High-throughput parallel or streamed batch execution across Apex (default) or Void suites."""
        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "suite": suite,
            "test_cases": tests,
        }
        return self._request("POST", "/v1/execute", body=payload)


ThanatonClient = Client
Thanaton = Client

