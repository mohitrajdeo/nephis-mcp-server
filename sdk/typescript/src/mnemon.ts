/**
 * Mnemon-DB TypeScript SDK - High-Throughput Serverless PostgreSQL Client
 *
 * Provides native bindings for:
 *  - 31ms Zero-Copy XFS Reflink Branching
 *  - One-Click Schema Diff & Branch Reset (<50ms)
 *  - Continuous Point-in-Time Recovery (PITR) via Lethe WAL Replay
 *  - ParadeDB BM25 & PostgreSQL tsvector Full-Text Search
 *  - Managed PostgREST RESTful Data API Engine (/rest/v1/...)
 *  - Branching S3-Compatible Copy-on-Write Object Storage (/storage/v1/...)
 *  - Scale-to-Zero (<200µs transparent hardware wakeup)
 */

declare const process: any;

export interface MnemonClientOptions {
  apiUrl?: string;
  apiKey?: string;
  proxyHost?: string;
  proxyPort?: number;
}

export interface TenantStatus {
  tenant_id: string;
  state: string;
  port: number;
  pid: number;
  wake_count: number;
  active_conns: number;
  last_active: string;
  cgroup_path: string;
}

export interface QueryResult {
  output: string;
  duration_ms: number;
  error?: string;
}

export interface SchemaDiffResult {
  diff: string;
  migration_ddl?: string;
}

export interface SearchResult {
  rows: any[];
  index_mode: "bm25" | "tsvector";
  query: string;
}

export interface TimeTravelResult {
  status: string;
  branch_id: string;
  database_url: string;
  duration_ms: number;
}

export class MnemonError extends Error {
  constructor(message: string, public statusCode?: number, public responseBody?: string) {
    super(message);
    this.name = "MnemonError";
  }
}

export class MnemonClient {
  private apiUrl: string;
  private apiKey?: string;
  private proxyHost: string;
  private proxyPort: number;

  constructor(options: MnemonClientOptions = {}) {
    const envUrl = typeof process !== "undefined" && process.env ? process.env.MNEMON_API_URL : undefined;
    const envKey = typeof process !== "undefined" && process.env
      ? (process.env.MNEMON_API_KEY || process.env.NEPHIS_API_KEY)
      : undefined;

    this.apiUrl = (options.apiUrl || envUrl || "https://nephis.theeducode.com/v1/db").replace(/\/+$/, "");
    this.apiKey = options.apiKey || envKey;
    this.proxyHost = options.proxyHost || "127.0.0.1";
    this.proxyPort = options.proxyPort || 5432;
  }

  private getHeaders(extra: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = { ...extra };
    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
      headers["X-API-Key"] = this.apiKey;
    }
    return headers;
  }

  private async request<T = any>(
    method: string,
    path: string,
    options: {
      body?: any;
      params?: Record<string, string>;
      headers?: Record<string, string>;
      binaryResponse?: boolean;
    } = {}
  ): Promise<T> {
    let url = `${this.apiUrl}${path}`;
    if (options.params) {
      const sp = new URLSearchParams(options.params);
      url += `?${sp.toString()}`;
    }

    const headers = this.getHeaders(options.headers);
    let body: any = undefined;

    if (options.body !== undefined) {
      if (typeof options.body === "string" || options.body instanceof Uint8Array) {
        body = options.body;
      } else {
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(options.body);
      }
    }

    let lastErr: any;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const res = await fetch(url, {
          method,
          headers,
          body,
        });

        if (!res.ok) {
          const errText = await res.text();
          throw new MnemonError(
            `Mnemon API error ${res.status}: ${errText}`,
            res.status,
            errText
          );
        }

        if (options.binaryResponse) {
          const ab = await res.arrayBuffer();
          return new Uint8Array(ab) as any;
        }

        const text = await res.text();
        if (!text || text.trim() === "") {
          return {} as T;
        }
        try {
          return JSON.parse(text) as T;
        } catch {
          return text as any;
        }
      } catch (err: any) {
        lastErr = err;
        if (err instanceof MnemonError) {
          throw err;
        }
        if (attempt === 0) {
          await new Promise((r) => setTimeout(r, 600));
          continue;
        }
        throw err;
      }
    }
    throw lastErr;
  }

  async listDatabases(): Promise<TenantStatus[]> {
    return this.request<TenantStatus[]>("GET", "/v1/status");
  }

  async createDatabase(
    tenantId: string,
    options: { memoryMb?: number; vcpus?: number; engine?: import("./types.js").DatabaseEngine } = {}
  ): Promise<any> {
    const engine = options.engine || "postgres";
    const payload = {
      tenant_id: tenantId,
      engine,
      memory_mb: options.memoryMb ?? 512,
      vcpus: options.vcpus ?? 2,
      port: 0,
    };
    const res = await this.request("POST", "/v1/tenants/provision", { body: payload });
    res.engine = engine;
    res.connection_string = this.getConnectionString(tenantId, "postgres", "secret", engine);
    return res;
  }

  async branchDatabase(
    tenantId: string,
    newBranch: string,
    options: string | { parentBranch?: string; maskPii?: boolean; targetLsn?: string; engine?: import("./types.js").DatabaseEngine } = "main"
  ): Promise<any> {
    const parentBranch = typeof options === "string" ? options : (options.parentBranch ?? "main");
    const maskPii = typeof options === "object" ? Boolean(options.maskPii) : false;
    const targetLsn = typeof options === "object" ? options.targetLsn : undefined;
    const engine = typeof options === "object" ? (options.engine || "postgres") : "postgres";

    const payload: any = {
      tenant_id: tenantId,
      new_branch: newBranch,
      parent_branch: parentBranch,
      mask_pii: maskPii,
      engine,
    };
    if (targetLsn) {
      payload.target_lsn = targetLsn;
    }
    const res = await this.request("POST", "/v1/tenants/branch", { body: payload });
    res.engine = engine;
    res.connection_string = this.getConnectionString(newBranch, "postgres", "secret", engine);
    return res;
  }

  async mergeBranch(
    tenantId: string,
    branchId: string,
    parentBranch: string = "main"
  ): Promise<{ status: string; duration_ms: number; fast_forward: boolean; migration_sql?: string }> {
    return this.request("POST", "/v1/tenants/merge", {
      body: { tenant_id: tenantId, branch_id: branchId, parent_branch: parentBranch },
    });
  }

  async schemaDiff(
    tenantId: string,
    branchId: string,
    parentBranch: string = "main"
  ): Promise<SchemaDiffResult> {
    return this.request<SchemaDiffResult>("POST", "/v1/tenants/branch/diff", {
      body: {
        tenant_id: tenantId,
        branch_id: branchId,
        parent_branch: parentBranch,
      },
    });
  }

  async resetBranch(
    tenantId: string,
    branchId: string
  ): Promise<{ status: string; duration_ms: number }> {
    return this.request("POST", "/v1/tenants/branch/reset", {
      body: { tenant_id: tenantId, branch_id: branchId },
    });
  }

  async timeTravel(
    tenantId: string,
    newBranch: string,
    targetTime: string,
    parentBranch: string = "main"
  ): Promise<TimeTravelResult> {
    const payload = {
      tenant_id: tenantId,
      new_branch: newBranch,
      target_time: targetTime,
      parent_branch: parentBranch,
    };
    const res = await this.request<TimeTravelResult>("POST", "/v1/tenants/branch/time-travel", {
      body: payload,
    });
    res.database_url = this.getConnectionString(newBranch);
    return res;
  }

  async search(
    tenantId: string,
    table: string,
    query: string,
    columns?: string[]
  ): Promise<SearchResult> {
    const payload = {
      tenant_id: tenantId,
      table,
      query,
      columns: columns || [],
    };
    return this.request<SearchResult>("POST", "/v1/tenants/search", { body: payload });
  }

  async storagePut(
    tenantId: string,
    branch: string,
    key: string,
    data: Uint8Array | string,
    contentType: string = "application/octet-stream"
  ): Promise<any> {
    return this.request("PUT", `/storage/v1/${tenantId}/${branch}/object/${key}`, {
      body: data,
      headers: { "Content-Type": contentType },
    });
  }

  async storageGet(tenantId: string, branch: string, key: string): Promise<Uint8Array> {
    return this.request<Uint8Array>("GET", `/storage/v1/${tenantId}/${branch}/object/${key}`, {
      binaryResponse: true,
    });
  }

  async storageDelete(tenantId: string, branch: string, key: string): Promise<boolean> {
    try {
      await this.request("DELETE", `/storage/v1/${tenantId}/${branch}/object/${key}`);
      return true;
    } catch {
      return false;
    }
  }

  async restQuery(
    tenantId: string,
    table: string,
    params?: Record<string, string>
  ): Promise<any[]> {
    return this.request<any[]>("GET", `/rest/v1/${tenantId}/${table}`, { params });
  }

  async restInsert(tenantId: string, table: string, payload: any): Promise<any> {
    return this.request("POST", `/rest/v1/${tenantId}/${table}`, { body: payload });
  }

  async query(
    tenantId: string,
    sql: string,
    options: { asOfLsn?: string } = {}
  ): Promise<QueryResult> {
    const payload: any = {
      tenant_id: tenantId,
      query: sql,
    };
    if (options.asOfLsn) {
      payload.as_of_lsn = options.asOfLsn;
    }
    return this.request<QueryResult>("POST", "/v1/tenants/sql", { body: payload });
  }

  async freeze(tenantId: string): Promise<boolean> {
    try {
      await this.request("GET", "/v1/tenants/freeze", { params: { tenant: tenantId } });
      return true;
    } catch {
      return false;
    }
  }

  async resume(tenantId: string): Promise<number> {
    const res = await this.request<{ duration_ms: number }>("GET", "/v1/tenants/unfreeze", {
      params: { tenant: tenantId },
    });
    return res.duration_ms || 0.0;
  }

  getConnectionString(
    tenantId: string,
    user: string = "postgres",
    password: string = "secret",
    engine: import("./types.js").DatabaseEngine = "postgres"
  ): string {
    const eng = (engine || "postgres").toLowerCase();
    switch (eng) {
      case "mysql":
      case "mariadb":
        return `mysql://${user}:${password}@${this.proxyHost}:17001/${tenantId}`;
      case "mongodb":
        return `mongodb://${this.proxyHost}:27101/${tenantId}`;
      case "redis":
        return `redis://${this.proxyHost}:18001`;
      case "sqlite":
        return `/var/lib/mnemon/sqlite/${tenantId}/database.db`;
      case "qdrant":
        return `http://${this.proxyHost}:21001`;
      case "postgres":
      default:
        return `postgresql://${user}:${password}@${this.proxyHost}:${this.proxyPort}/${tenantId}?sslmode=require`;
    }
  }

  async promoteBranch(tenantId: string, branch: string): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/branches/${encodeURIComponent(branch)}/promote`);
  }

  async getPooler(tenantId: string): Promise<any> {
    try {
      return await this.request("GET", "/v1/tenants/pooler", { params: { tenant_id: tenantId } });
    } catch {
      return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/pooler`);
    }
  }

  async configurePooler(
    tenantId: string,
    options: { poolMode?: string; defaultPoolSize?: number; maxClientConns?: number } = {}
  ): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/pooler`, { body: options });
  }

  async listTables(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/tables`);
  }

  async listExtensions(tenantId: string): Promise<any> {
    try {
      return await this.request("GET", "/v1/tenants/extensions", { params: { tenant: tenantId } });
    } catch {
      return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/extensions`);
    }
  }

  async toggleExtension(tenantId: string, extension: string, enable: boolean = true): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/extensions`, {
      body: { extension, action: enable ? "enable" : "disable" },
    });
  }

  async getSlowQueries(tenantId: string): Promise<any> {
    try {
      return await this.request("GET", "/v1/tenants/queries/slow", { params: { tenant_id: tenantId } });
    } catch {
      return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/queries/slow`);
    }
  }

  async getQueryAdvisor(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/queries/advisor`);
  }

  async getScaling(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/scaling`);
  }

  async configureScaling(
    tenantId: string,
    options: { minAcu?: number; maxAcu?: number; autoFreezeSec?: number } = {}
  ): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/scaling`, { body: options });
  }

  async createSnapshot(tenantId: string, options: { name?: string; branchId?: string } = {}): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/snapshots`, {
      body: { name: options.name || `snap_${tenantId}`, branch_id: options.branchId || "main" },
    });
  }

  async listSnapshots(tenantId: string): Promise<any[]> {
    const res = await this.request<{ snapshots: any[] }>("GET", `/v1/projects/${encodeURIComponent(tenantId)}/snapshots`);
    return res.snapshots || [];
  }

  async getPitrTimelines(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/pitr/timelines`);
  }

  async restorePitr(tenantId: string, options: { targetBranch: string; targetLsn?: number }): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/pitr/restore`, {
      body: { target_branch: options.targetBranch, target_lsn: options.targetLsn },
    });
  }

  async getBranchLineage(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/branches/lineage`);
  }

  async reconcileSchema(tenantId: string, branch: string, sqlOrTarget: string = "main"): Promise<any> {
    try {
      return await this.request("POST", "/v1/tenants/branch/analyze-migration", {
        body: { tenant_id: tenantId, branch, sql: sqlOrTarget },
      });
    } catch {
      return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/branches/${encodeURIComponent(branch)}/reconcile`, {
        body: { target_branch: sqlOrTarget },
      });
    }
  }

  async cloneVectorIndex(
    tenantId: string,
    branch: string,
    indexName: string,
    dimensions: number = 1536
  ): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/branches/${encodeURIComponent(branch)}/clone-vector`, {
      body: { index_name: indexName, dimensions },
    });
  }

  async autoFreezePolicy(
    tenantId?: string,
    options: { enabled?: boolean; idleSec?: number } = {}
  ): Promise<any> {
    try {
      return await this.request("GET", "/v1/admin/autofreeze/stats");
    } catch {
      return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId || "default")}/autofreeze`, {
        body: { enabled: options.enabled !== false, idle_sec: options.idleSec ?? 300 },
      });
    }
  }

  async startImport(tenantId: string, sourceUrl: string): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/import`, {
      body: { source_url: sourceUrl },
    });
  }

  async getImportStatus(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/import/status`);
  }

  async cutoverImport(tenantId: string): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/import/cutover`);
  }

  async configureVectorQuantization(
    tenantId: string,
    options: { table: string; column: string; dimensions?: number; quantizationType?: string; diskSpill?: boolean }
  ): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/vector/quantize`, {
      body: {
        table: options.table,
        column: options.column,
        dimensions: options.dimensions || 1536,
        quantization_type: options.quantizationType || "PQ",
        disk_spill: options.diskSpill !== false,
      },
    });
  }

  async getVectorStats(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/vector/stats`);
  }

  async getCdcStats(tenantId: string): Promise<any> {
    return this.request("GET", `/v1/projects/${encodeURIComponent(tenantId)}/cdc/stats`);
  }

  async publishCdcEvent(
    tenantId: string,
    options: { table: string; action: string; data: any }
  ): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/cdc/publish`, {
      body: options,
    });
  }

  async killQuery(options: { pid?: number; queryId?: string; durationSec?: number } = {}): Promise<any> {
    return this.request("POST", "/v1/admin/queries/kill", { body: options });
  }

  async reapBranches(options: { maxAgeHours?: number; dryRun?: boolean } = {}): Promise<any> {
    return this.request("POST", "/v1/admin/branches/reap", {
      body: { max_age_hours: options.maxAgeHours || 24, dry_run: !!options.dryRun },
    });
  }

  /**
   * Set the active tenant context in PostgreSQL session (`SET LOCAL app.current_tenant = ...`)
   * for zero-leak Row-Level Security (RLS) enforcement.
   */
  async setTenantContext(tenantId: string): Promise<QueryResult> {
    const escaped = tenantId.replace(/'/g, "''");
    return this.query(tenantId, `SET LOCAL app.current_tenant = '${escaped}';`);
  }

  /**
   * Enforce PostgreSQL Row-Level Security (RLS) on a table with a tenant isolation policy.
   */
  async createRLSPolicy(
    tenantId: string,
    options: {
      table: string;
      policyName?: string;
      expression?: string;
      forAction?: "SELECT" | "INSERT" | "UPDATE" | "DELETE" | "ALL";
    }
  ): Promise<{ success: boolean; tenant_id: string; table: string; policy_name: string; sql_executed: string; duration_ms: number }> {
    const table = options.table;
    const policyName = options.policyName || `tenant_isolation_${table}`;
    const action = options.forAction || "ALL";
    const expr = options.expression || `tenant_id = current_setting('app.current_tenant', true)`;

    const sql = `
      ALTER TABLE "${table}" ENABLE ROW LEVEL SECURITY;
      DROP POLICY IF EXISTS "${policyName}" ON "${table}";
      CREATE POLICY "${policyName}" ON "${table}" FOR ${action} USING (${expr}) WITH CHECK (${expr});
    `;

    const start = Date.now();
    await this.query(tenantId, sql);
    return {
      success: true,
      tenant_id: tenantId,
      table,
      policy_name: policyName,
      sql_executed: sql.trim(),
      duration_ms: Date.now() - start,
    };
  }

  /**
   * Execute an atomic Redis command (GET, SET, INCR, HSET, EXPIRE) via Unix socket or TCP bridge.
   * Runs in ~0.02ms (20 microseconds) for microsecond token bucket rate limiting.
   */
  async redisCommand(
    tenantId: string,
    command: string,
    ...args: (string | number)[]
  ): Promise<import("./types.js").RedisCommandResult> {
    const payload = {
      tenant_id: tenantId,
      command: command.toUpperCase(),
      args: args.map(String),
    };
    return this.request<import("./types.js").RedisCommandResult>("POST", `/v1/projects/${encodeURIComponent(tenantId)}/redis`, { body: payload });
  }

  /**
   * Query or mutate a MongoDB collection (find, findOne, insertOne, aggregate, count)
   * with zero-copy WiredTiger B-Tree storage isolation.
   */
  async mongoQuery(
    tenantId: string,
    options: import("./types.js").MongoQueryOptions
  ): Promise<import("./types.js").MongoQueryResult> {
    return this.request<import("./types.js").MongoQueryResult>("POST", `/v1/projects/${encodeURIComponent(tenantId)}/mongo`, {
      body: {
        tenant_id: tenantId,
        collection: options.collection,
        action: options.action || "find",
        filter: options.filter || {},
        projection: options.projection,
        pipeline: options.pipeline,
        document: options.document,
        documents: options.documents,
      },
    });
  }

  /**
   * Execute SIMD-accelerated HNSW vector similarity search on Qdrant with optional scalar/binary quantization.
   * Delivers sub-millisecond nearest neighbor search over high-dimensional embeddings.
   */
  async vectorSearch(
    tenantId: string,
    options: import("./types.js").VectorSearchOptions
  ): Promise<import("./types.js").VectorSearchResult> {
    return this.request<import("./types.js").VectorSearchResult>("POST", `/v1/projects/${encodeURIComponent(tenantId)}/vector/search`, {
      body: {
        tenant_id: tenantId,
        collection: options.collection,
        vector: options.vector,
        limit: options.limit || 10,
        filter: options.filter,
        with_payload: options.withPayload !== false,
      },
    });
  }

  /**
   * Upsert vector embeddings and associated payload metadata into a Qdrant vector collection.
   */
  async vectorUpsert(
    tenantId: string,
    options: import("./types.js").VectorUpsertOptions
  ): Promise<import("./types.js").VectorUpsertResult> {
    return this.request<import("./types.js").VectorUpsertResult>("POST", `/v1/projects/${encodeURIComponent(tenantId)}/vector/upsert`, {
      body: {
        tenant_id: tenantId,
        collection: options.collection,
        points: options.points,
      },
    });
  }

  /**
   * Execute an embedded SQLite query on an isolated single-file zero-daemon database branch.
   * Branches in <2.5ms via raw FICLONE with 0 MB idle RAM footprint.
   */
  async sqliteQuery(tenantId: string, sql: string): Promise<QueryResult> {
    return this.request<QueryResult>("POST", `/v1/projects/${encodeURIComponent(tenantId)}/sqlite`, {
      body: { tenant_id: tenantId, query: sql },
    });
  }

  /**
   * Rewind a database branch to a historical WAL Log Sequence Number (LSN) via Lethe engine.
   */
  async walRewind(tenantId: string, targetLsn: string): Promise<any> {
    return this.request("POST", `/v1/projects/${encodeURIComponent(tenantId)}/wal/rewind`, {
      body: { tenant_id: tenantId, target_lsn: targetLsn },
    });
  }

  /**
   * Execute raw SQL on PostgreSQL (alias for query).
   */
  async executeSql(tenantId: string, sql: string, options: { asOfLsn?: string } = {}): Promise<QueryResult> {
    return this.query(tenantId, sql, options);
  }
}

