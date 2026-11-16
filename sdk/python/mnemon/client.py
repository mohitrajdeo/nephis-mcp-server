import os
from typing import Any, Dict, List, Optional
import requests


class MnemonException(Exception):
    """Raised when a Mnemon-DB API call fails."""
    pass


class QueryResult:
    def __init__(self, output: str, duration_ms: float, error: Optional[str] = None):
        self.output = output
        self.duration_ms = duration_ms
        self.error = error

    def __repr__(self):
        return f"<QueryResult duration_ms={self.duration_ms:.2f}ms error={self.error}>"


class TenantStatus:
    def __init__(self, data: Any):
        if isinstance(data, str):
            data = {"tenant_id": data}
        elif not isinstance(data, dict):
            data = {}
        self.tenant_id: str = data.get("tenant_id") or data.get("id") or data.get("name") or ""
        self.state: str = data.get("state") or data.get("status") or "ACTIVE"
        self.port: int = data.get("port", 0)
        self.pid: int = data.get("pid", 0)
        self.wake_count: int = data.get("wake_count", 0)
        self.active_conns: int = data.get("active_conns") or data.get("active_connections") or 0
        self.last_active: str = data.get("last_active", "")
        self.cgroup_path: str = data.get("cgroup_path", "")

    def is_frozen(self) -> bool:
        return self.state in ("paused", "stopped")

    def __repr__(self):
        status = "FROZEN (0% CPU)" if self.is_frozen() else "RUNNING"
        return f"<Tenant '{self.tenant_id}' [{status}] port={self.port}>"


class MnemonClient:
    """Official Python SDK for Mnemon-DB Multi-Tenant Serverless PostgreSQL Platform.

    Supports:
      - 31ms Zero-Copy XFS Reflink Branching
      - One-Click Schema Diff & Branch Reset (<50ms)
      - Continuous Point-in-Time Recovery (PITR) via Mnemon WAL Replay
      - ParadeDB BM25 & PostgreSQL tsvector Full-Text Search
      - Managed PostgREST RESTful Data API Engine (/rest/v1/...)
      - Branching S3-Compatible Copy-on-Write Object Storage (/storage/v1/...)
      - Scale-to-Zero (<200µs transparent hardware wakeup)
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        proxy_host: str = "127.0.0.1",
        proxy_port: int = 5432,
    ):
        self.api_url = (api_url or os.getenv("MNEMON_API_URL") or "https://mnemon.theeducode.com/api").rstrip("/")
        self.api_key = api_key or os.getenv("MNEMON_API_KEY") or os.getenv("NEPHIS_API_KEY")
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": "Mnemon-SDK/2.0.0 (Windows NT 10.0; Win64; x64) Nephis/Unified",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        if extra:
            headers.update(extra)
        return headers

    def list_databases(self) -> List[TenantStatus]:
        """List all managed tenant database instances and their runtime states."""
        resp = requests.get(f"{self.api_url}/v1/projects", headers=self._headers(), timeout=10)
        if not resp.ok:
            resp = requests.get(f"{self.api_url}/api/v1/projects", headers=self._headers(), timeout=10)
        if not resp.ok:
            resp = requests.get(f"{self.api_url}/v1/status", headers=self._headers(), timeout=10)
        if not resp.ok:
            raise MnemonException(f"Failed to list databases: {resp.text}")
        data = resp.json()
        if isinstance(data, dict):
            raw_items = data.get("projects") or data.get("tenants") or data.get("items") or []
            items = raw_items if isinstance(raw_items, list) else [data]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        return [TenantStatus(item) for item in items if isinstance(item, (dict, str))]

    def create_database(self, tenant_id: str, memory_mb: int = 512, vcpus: int = 2) -> Dict[str, Any]:
        """Provision a new serverless PostgreSQL database tenant on pure silicon."""
        payload = {
            "tenant_id": tenant_id,
            "memory_mb": memory_mb,
            "vcpus": vcpus,
            "port": 0,
        }
        resp = requests.post(
            f"{self.api_url}/v1/tenants/provision",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if not resp.ok:
            raise MnemonException(f"Provision failed: {resp.text}")
        data = resp.json()
        data["connection_string"] = self.get_connection_string(tenant_id)
        return data

    def branch_database(self, tenant_id: str, new_branch: str, parent_branch: str = "main") -> Dict[str, Any]:
        """Create an instant block-level Copy-on-Write (CoW) database branch in <50ms."""
        payload = {
            "tenant_id": tenant_id,
            "new_branch": new_branch,
            "parent_branch": parent_branch,
        }
        resp = requests.post(
            f"{self.api_url}/v1/tenants/branch",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if not resp.ok:
            raise MnemonException(f"Branching failed: {resp.text}")
        data = resp.json()
        data["connection_string"] = self.get_connection_string(new_branch)
        return data

    def schema_diff(self, tenant_id: str, branch_id: str, parent_branch: str = "main") -> Dict[str, Any]:
        """Calculate schema diff and generate migration DDL between a branch and its parent."""
        params = {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "parent_branch": parent_branch,
        }
        resp = requests.get(
            f"{self.api_url}/v1/tenants/branch/diff",
            params=params,
            headers=self._headers(),
            timeout=30,
        )
        if not resp.ok:
            raise MnemonException(f"Schema diff failed: {resp.text}")
        return resp.json()

    def reset_branch(self, tenant_id: str, branch_id: str) -> Dict[str, Any]:
        """One-click instant branch reset back to parent branch state (<50ms)."""
        payload = {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
        }
        resp = requests.post(
            f"{self.api_url}/v1/tenants/branch/reset",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if not resp.ok:
            raise MnemonException(f"Branch reset failed: {resp.text}")
        return resp.json()

    def time_travel(
        self, tenant_id: str, new_branch: str, target_time: str, parent_branch: str = "main"
    ) -> Dict[str, Any]:
        """Continuous Point-in-Time Recovery: spawn a new branch from a historical timestamp via Mnemon WAL replay."""
        payload = {
            "tenant_id": tenant_id,
            "new_branch": new_branch,
            "target_time": target_time,
            "parent_branch": parent_branch,
        }
        resp = requests.post(
            f"{self.api_url}/v1/tenants/branch/time-travel",
            json=payload,
            headers=self._headers(),
            timeout=60,
        )
        if not resp.ok:
            raise MnemonException(f"Time travel branch creation failed: {resp.text}")
        data = resp.json()
        data["connection_string"] = self.get_connection_string(new_branch)
        return data

    def search(
        self, tenant_id: str, table: str, query: str, columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute full-text BM25 search (ParadeDB pg_search) with automatic tsvector GIN fallback."""
        payload = {
            "tenant_id": tenant_id,
            "table": table,
            "query": query,
            "columns": columns or [],
        }
        resp = requests.post(
            f"{self.api_url}/v1/tenants/search",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if not resp.ok:
            raise MnemonException(f"Search query failed: {resp.text}")
        return resp.json()

    def storage_put(
        self, tenant_id: str, branch: str, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """Write an object to branch-isolated S3 Copy-on-Write storage."""
        headers = self._headers({"Content-Type": content_type})
        url = f"{self.api_url}/storage/v1/{tenant_id}/{branch}/object/{key}"
        resp = requests.put(url, data=data, headers=headers, timeout=60)
        if not resp.ok:
            raise MnemonException(f"Storage upload failed: {resp.text}")
        return resp.json()

    def storage_get(self, tenant_id: str, branch: str, key: str) -> bytes:
        """Read an object from branch-isolated S3 Copy-on-Write storage (reads CoW parent if unmutated)."""
        url = f"{self.api_url}/storage/v1/{tenant_id}/{branch}/object/{key}"
        resp = requests.get(url, headers=self._headers(), timeout=60)
        if not resp.ok:
            raise MnemonException(f"Storage download failed: {resp.text}")
        return resp.content

    def storage_delete(self, tenant_id: str, branch: str, key: str) -> bool:
        """Delete an object from branch-isolated S3 Copy-on-Write storage."""
        url = f"{self.api_url}/storage/v1/{tenant_id}/{branch}/object/{key}"
        resp = requests.delete(url, headers=self._headers(), timeout=30)
        return resp.ok

    def rest_query(
        self, tenant_id: str, table: str, params: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Query rows via managed PostgREST RESTful Data API engine."""
        url = f"{self.api_url}/rest/v1/{tenant_id}/{table}"
        resp = requests.get(url, params=params, headers=self._headers(), timeout=30)
        if not resp.ok:
            raise MnemonException(f"PostgREST query failed: {resp.text}")
        return resp.json()

    def rest_insert(self, tenant_id: str, table: str, payload: Any) -> Any:
        """Insert rows via managed PostgREST RESTful Data API engine."""
        url = f"{self.api_url}/rest/v1/{tenant_id}/{table}"
        headers = self._headers({"Content-Type": "application/json"})
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if not resp.ok:
            raise MnemonException(f"PostgREST insert failed: {resp.text}")
        return resp.json()

    def query(self, tenant_id: str, sql: str) -> QueryResult:
        """Execute arbitrary SQL statement against a tenant database with automatic transparent unfreeze."""
        payload = {
            "tenant_id": tenant_id,
            "query": sql,
        }
        resp = requests.post(
            f"{self.api_url}/v1/tenants/sql",
            json=payload,
            headers=self._headers(),
            timeout=60,
        )
        data = resp.json()
        return QueryResult(
            output=data.get("output", ""),
            duration_ms=data.get("duration_ms", 0.0),
            error=data.get("error"),
        )

    def freeze(self, tenant_id: str) -> bool:
        """Manually freeze a tenant to 0.0% CPU idle state via Cgroups v2."""
        resp = requests.get(f"{self.api_url}/v1/tenants/freeze?tenant={tenant_id}", headers=self._headers(), timeout=10)
        return resp.ok

    def resume(self, tenant_id: str) -> float:
        """Unfreeze a tenant in <0.5ms pure silicon wakeup. Returns wake duration in ms."""
        resp = requests.get(f"{self.api_url}/v1/tenants/unfreeze?tenant={tenant_id}", headers=self._headers(), timeout=10)
        if not resp.ok:
            raise MnemonException(f"Resume failed: {resp.text}")
        return resp.json().get("duration_ms", 0.0)

    def promote_branch(self, tenant_id: str, branch_id: str) -> Dict[str, Any]:
        """Promote a preview branch to the primary production root with zero downtime."""
        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/branches/{branch_id}/promote",
            headers=self._headers(),
            timeout=30,
        )
        if not resp.ok:
            raise MnemonException(f"Branch promotion failed: {resp.text}")
        return resp.json()

    def get_pooler(self, tenant_id: str) -> Dict[str, Any]:
        """Inspect PgBouncer connection pooler state and mode."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/pooler", headers=self._headers(), timeout=10)
        if not resp.ok:
            raise MnemonException(f"Failed to get pooler: {resp.text}")
        return resp.json()

    def configure_pooler(self, tenant_id: str, pool_mode: str = "transaction", max_pool_size: int = 10) -> Dict[str, Any]:
        """Dynamically tune PgBouncer connection pooler parameters."""
        payload = {"pool_mode": pool_mode, "max_pool_size": max_pool_size}
        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/pooler",
            json=payload,
            headers=self._headers(),
            timeout=10,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to configure pooler: {resp.text}")
        return resp.json()

    def list_tables(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Introspect tables and columns for the database cluster."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/tables", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to list tables: {resp.text}")
        data = resp.json()
        return data.get("tables", []) if isinstance(data, dict) else data

    def list_extensions(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List available and enabled PostgreSQL extensions (vector, pg_search, postgis)."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/extensions", headers=self._headers(), timeout=10)
        if not resp.ok:
            raise MnemonException(f"Failed to list extensions: {resp.text}")
        data = resp.json()
        return data.get("extensions", []) if isinstance(data, dict) else data

    def toggle_extension(self, tenant_id: str, name: str, action: str = "enable") -> Dict[str, Any]:
        """Enable or disable a PostgreSQL extension."""
        payload = {"name": name, "action": action}
        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/extensions",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to toggle extension '{name}': {resp.text}")
        return resp.json()

    def get_slow_queries(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Fetch slow query execution diagnostics and cache hit rates."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/queries/slow", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to get slow queries: {resp.text}")
        data = resp.json()
        return data.get("slow_queries", []) if isinstance(data, dict) else data

    def get_scaling(self, tenant_id: str) -> Dict[str, Any]:
        """Fetch current Aurora Serverless v2 ACU capacity allocation and scale-to-zero state."""
        resp = requests.get(
            f"{self.api_url}/v1/projects/{tenant_id}/scaling",
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to fetch scaling configuration: {resp.text}")
        return resp.json()

    def configure_scaling(
        self,
        tenant_id: str,
        min_acu: float = 0.0,
        max_acu: float = 16.0,
        scale_to_zero_enabled: Optional[bool] = None,
        idle_suspend_seconds: int = 300,
        tier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Configure Aurora Serverless v2 ACU capacity limits and scale-to-zero idle timeout."""
        payload: Dict[str, Any] = {
            "min_acu": min_acu,
            "max_acu": max_acu,
            "idle_suspend_seconds": idle_suspend_seconds,
        }
        if scale_to_zero_enabled is not None:
            payload["scale_to_zero_enabled"] = scale_to_zero_enabled
        if tier is not None:
            payload["tier"] = tier

        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/scaling",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to configure scaling: {resp.text}")
        return resp.json()

    def configure_ip_allowlist(
        self, tenant_id: str, enabled: bool = True, cidr_rules: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Configure CIDR IP firewall allowlist rules."""
        payload = {"enabled": enabled, "cidr_rules": cidr_rules or []}
        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/ip-allowlist",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to configure IP allowlist: {resp.text}")
        return resp.json()

    def list_webhooks(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List active CDC event webhooks."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/webhooks", headers=self._headers(), timeout=10)
        if not resp.ok:
            raise MnemonException(f"Failed to list webhooks: {resp.text}")
        data = resp.json()
        return data.get("webhooks", []) if isinstance(data, dict) else data

    def create_webhook(
        self, tenant_id: str, table_name: str, events: List[str], target_url: str, secret: str = ""
    ) -> Dict[str, Any]:
        """Subscribe to Change Data Capture (CDC) events on a table."""
        payload = {"table_name": table_name, "events": events, "target_url": target_url, "secret": secret}
        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/webhooks",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to create webhook: {resp.text}")
        return resp.json()

    def get_cdc_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Fetch live Mnemon CDC buffer and throughput performance statistics."""
        resp = requests.get(
            f"{self.api_url}/v1/projects/{tenant_id}/cdc/stats",
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to fetch CDC stats: {resp.text}")
        return resp.json()

    def publish_cdc(
        self,
        tenant_id: str,
        table: str,
        action: str,
        record: Dict[str, Any],
        old_record: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Publish a database row mutation directly to Mnemon CDC stream."""
        payload = {
            "table": table,
            "action": action.upper(),
            "record": record,
            "old_record": old_record,
        }
        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/cdc/publish",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to publish CDC event: {resp.text}")
        return resp.json()

    def publish_cdc_event(
        self,
        tenant_id: str,
        table: str,
        action: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Alias for publish_cdc providing 1:1 parameter parity with MCP mnemon_cdc_publish and TypeScript SDK."""
        return self.publish_cdc(tenant_id=tenant_id, table=table, action=action, record=data)

    def stream_cdc(
        self,
        tenant_id: str,
        table: str = "*",
        action: str = "*",
        replay_since: Optional[int] = None,
    ):
        """Yield real-time database mutations as a continuous SSE generator."""
        params = {"table": table, "action": action}
        if replay_since is not None:
            params["replay_since"] = str(replay_since)
        resp = requests.get(
            f"{self.api_url}/v1/projects/{tenant_id}/cdc/stream",
            params=params,
            headers={"Accept": "text/event-stream", **self._headers()},
            stream=True,
            timeout=None,
        )
        if not resp.ok:
            raise MnemonException(f"Failed to connect to CDC stream: {resp.text}")
        for line in resp.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data:"):
                    raw_data = decoded[5:].strip()
                    try:
                        yield json.loads(raw_data)
                    except Exception:
                        yield {"raw": raw_data}

    def get_connection_string(self, tenant_id: str, user: str = "postgres", password: str = "secret") -> str:
        """Return standard PostgreSQL connection URI for SQLAlchemy, Prisma, Drizzle, etc."""
        return f"postgresql://{user}:{password}@{self.proxy_host}:{self.proxy_port}/{tenant_id}?sslmode=require"

    def create_snapshot(self, tenant_id: str, name: Optional[str] = None, branch_id: str = "main") -> Dict[str, Any]:
        """Create a point-in-time snapshot of a database cluster branch."""
        payload = {"name": name or f"snap_{tenant_id}", "branch_id": branch_id}
        resp = requests.post(f"{self.api_url}/v1/projects/{tenant_id}/snapshots", json=payload, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to create snapshot: {resp.text}")
        return resp.json()

    def list_snapshots(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List all snapshots taken on a database cluster."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/snapshots", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to list snapshots: {resp.text}")
        return resp.json().get("snapshots", [])

    def get_pitr_timelines(self, tenant_id: str) -> Dict[str, Any]:
        """Retrieve available WAL archiving timelines and PITR restoration windows."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/pitr/timelines", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to fetch PITR timelines: {resp.text}")
        return resp.json()

    def restore_pitr(self, tenant_id: str, target_branch: str, target_lsn: Optional[int] = None) -> Dict[str, Any]:
        """Execute Point-In-Time Recovery (PITR) to a target LSN on a fresh branch."""
        payload = {"target_branch": target_branch}
        if target_lsn is not None:
            payload["target_lsn"] = target_lsn
        resp = requests.post(f"{self.api_url}/v1/projects/{tenant_id}/pitr/restore", json=payload, headers=self._headers(), timeout=30)
        if not resp.ok:
            raise MnemonException(f"Failed to restore PITR branch: {resp.text}")
        return resp.json()

    def get_branch_lineage(self, tenant_id: str) -> Dict[str, Any]:
        """Display visual DAG tree and ancestry of database branches."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/branches/lineage", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to fetch branch lineage: {resp.text}")
        return resp.json()

    def reconcile_schema(self, tenant_id: str, branch: str, target_branch: str = "main") -> Dict[str, Any]:
        """Perform 3-way schema reconciliation before merging branch into target."""
        payload = {"target_branch": target_branch}
        resp = requests.post(
            f"{self.api_url}/v1/projects/{tenant_id}/branches/{branch}/reconcile",
            json=payload,
            headers=self._headers(),
            timeout=30
        )
        if not resp.ok:
            raise MnemonException(f"Failed to reconcile schema: {resp.text}")
        return resp.json()

    def get_query_advisor(self, tenant_id: str) -> Dict[str, Any]:
        """Inspect slow queries, circuit breaker status, and FinOps index recommendations."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/queries/advisor", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to fetch query advisor: {resp.text}")
        return resp.json()

    def start_import(self, tenant_id: str, source_url: str) -> Dict[str, Any]:
        """Initiate zero-downtime database import from Neon or Supabase."""
        payload = {"source_url": source_url}
        resp = requests.post(f"{self.api_url}/v1/projects/{tenant_id}/import", json=payload, headers=self._headers(), timeout=30)
        if not resp.ok:
            raise MnemonException(f"Failed to initiate import: {resp.text}")
        return resp.json()

    def get_import_status(self, tenant_id: str) -> Dict[str, Any]:
        """Query current progress and replication lag of active database import."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/import/status", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to fetch import status: {resp.text}")
        return resp.json()

    def cutover_import(self, tenant_id: str) -> Dict[str, Any]:
        """Complete zero-downtime cutover and route read/write traffic to Mnemon-DB."""
        resp = requests.post(f"{self.api_url}/v1/projects/{tenant_id}/import/cutover", headers=self._headers(), timeout=30)
        if not resp.ok:
            raise MnemonException(f"Failed to execute cutover: {resp.text}")
        return resp.json()

    def configure_vector_quantization(
        self,
        tenant_id: str,
        table: str,
        column: str,
        dimensions: int = 1536,
        quantization_type: str = "PQ",
        disk_spill: bool = True
    ) -> Dict[str, Any]:
        """Configure pgvector + HNSW-PQ vector quantization with disk-spill indexing."""
        payload = {
            "table": table,
            "column": column,
            "dimensions": dimensions,
            "quantization_type": quantization_type,
            "disk_spill": disk_spill
        }
        resp = requests.post(f"{self.api_url}/v1/projects/{tenant_id}/vector/quantize", json=payload, headers=self._headers(), timeout=30)
        if not resp.ok:
            raise MnemonException(f"Failed to configure vector quantization: {resp.text}")
        return resp.json()

    def get_vector_quantization_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Fetch memory savings and vector indexing stats across cluster."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/vector/stats", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to fetch vector quantization stats: {resp.text}")
        return resp.json()

    def configure_scaling(
        self,
        tenant_id: str,
        min_acu: float = 0.5,
        max_acu: float = 8.0,
        auto_freeze_sec: int = 300,
    ) -> Dict[str, Any]:
        """Configure Aurora Serverless v2 ACU auto-scaling boundaries and idle stasis."""
        payload = {"min_acu": min_acu, "max_acu": max_acu, "auto_freeze_sec": auto_freeze_sec}
        resp = requests.post(f"{self.api_url}/v1/projects/{tenant_id}/scaling", json=payload, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to configure scaling: {resp.text}")
        return resp.json()

    def kill_query(
        self,
        pid: Optional[int] = None,
        query_id: Optional[str] = None,
        duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Emergency termination of a rogue or long-running query by PID or duration."""
        payload: Dict[str, Any] = {}
        if pid is not None:
            payload["pid"] = pid
        if query_id:
            payload["query_id"] = query_id
        if duration_sec is not None:
            payload["duration_sec"] = duration_sec
        resp = requests.post(f"{self.api_url}/v1/admin/queries/kill", json=payload, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to terminate query: {resp.text}")
        return resp.json()

    def reap_branches(self, max_age_hours: int = 24, dry_run: bool = False) -> Dict[str, Any]:
        """Prune and reclaim storage extents from orphaned ephemeral branches."""
        payload = {"max_age_hours": max_age_hours, "dry_run": dry_run}
        resp = requests.post(f"{self.api_url}/v1/admin/branches/reap", json=payload, headers=self._headers(), timeout=30)
        if not resp.ok:
            raise MnemonException(f"Failed to reap branches: {resp.text}")
        return resp.json()

    def quarantine_tenant(self, tenant_id: str, reason: str = "Emergency Security Quarantine", freeze_sandboxes: bool = True) -> Dict[str, Any]:
        """Isolate a tenant database cluster and revoke active tokens."""
        payload = {"reason": reason, "freeze_sandboxes": freeze_sandboxes}
        resp = requests.post(f"{self.api_url}/v1/admin/tenants/{tenant_id}/quarantine", json=payload, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to quarantine tenant: {resp.text}")
        return resp.json()

    def unquarantine_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Release a tenant database cluster from quarantine."""
        resp = requests.post(f"{self.api_url}/v1/admin/tenants/{tenant_id}/unquarantine", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to unquarantine tenant: {resp.text}")
        return resp.json()

    def get_ip_allowlist(self, tenant_id: str) -> Dict[str, Any]:
        """Fetch network CIDR security allowlist for a database cluster."""
        resp = requests.get(f"{self.api_url}/v1/projects/{tenant_id}/ip-allowlist", headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to fetch IP allowlist: {resp.text}")
        return resp.json()

    def update_ip_allowlist(self, tenant_id: str, cidrs: List[str]) -> Dict[str, Any]:
        """Update network CIDR security allowlist for a database cluster."""
        payload = {"cidrs": cidrs}
        resp = requests.post(f"{self.api_url}/v1/projects/{tenant_id}/ip-allowlist", json=payload, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise MnemonException(f"Failed to update IP allowlist: {resp.text}")
        return resp.json()
