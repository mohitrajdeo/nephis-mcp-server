/**
 * Thanaton & Ananke TypeScript SDK - Core Type Definitions
 */

export interface ClientOptions {
  /** Thanaton Control Plane Base URL (defaults to https://nephis.theeducode.com) */
  baseUrl?: string;
  /** Optional API Bearer Token for cloud/multi-tenant deployments */
  apiKey?: string;
  /** Global HTTP Request Timeout in ms (default: 30000) */
  timeoutMs?: number;
}

export type SandboxRuntime = "microvm" | "silicon" | "node" | "python";

export type SandboxState = "running" | "sleeping" | "frozen" | "stopped" | "unknown";

export interface CreateSandboxOptions {
  /** Sandbox runtime engine: 'microvm' (KVM/Firecracker), 'silicon' (Isolate), 'node', 'python' */
  runtime?: SandboxRuntime;
  /** Execution isolation mode: 'sandbox' (Standard unprivileged) or 'vm' (Firecracker KVM microVM) */
  executionMode?: "sandbox" | "vm";
  /** Whether to bundle an embedded PostgreSQL instance in the sandbox */
  withDb?: boolean;
  /** Memory allocated to the sandbox in MiB (e.g. 128, 256, 512, 1024, 2048) */
  memoryMb?: number;
  /** CPU limit percentage (100 = 1 full core) */
  cpuQuotaPct?: number;
  /** Optional Tenant / Organization identifier */
  tenantId?: string;
  /** Cold boot timeout in milliseconds */
  timeoutMs?: number;
}

export interface CreateProjectOptions {
  name: string;
  slug?: string;
  runtime?: "nodejs" | "python" | "go" | "rust" | "docker";
  executionMode?: "sandbox" | "vm";
  appPort?: number;
}

export interface ProjectMetadata {
  id: string;
  name: string;
  slug: string;
  runtime: string;
  execution_mode: "sandbox" | "vm";
  app_port: number;
  full_domain: string;
  preview_domain: string;
  state?: string;
  created_at?: string;
}

export interface DeployCodeOptions {
  projectSlug: string;
  code?: string;
  filename?: string;
  runtime?: "nodejs" | "python";
  executionMode?: "sandbox" | "vm";
  environment?: "production" | "staging";
  branch?: string;
}

export interface DeployResult {
  success: boolean;
  status: string;
  assigned_port?: number;
  primary_url?: string;
  custom_url?: string;
}

export interface SandboxMetadata {
  id: string;
  tenant_id: string;
  runtime: string;
  box_id?: number;
  pid?: number;
  has_db: boolean;
  db_port?: number;
  db_url?: string;
  cgroup_path?: string;
  state: SandboxState;
  created_at: string;
  last_active_at: string;
  boot_duration_ms: number;
}

export interface ExecOptions {
  /** Execution timeout in milliseconds (default: 15000) */
  timeoutMs?: number;
  /** Environment variables to pass into the guest process */
  env?: Record<string, string>;
  /** Working directory inside the guest filesystem */
  cwd?: string;
}

export interface ExecResult {
  /** Standard output */
  stdout: string;
  /** Standard error */
  stderr: string;
  /** Process exit code (0 for success) */
  exitCode: number;
  /** True if exitCode === 0 */
  ok: boolean;
  /** Execution duration in milliseconds */
  durationMs: number;
}

export interface RunCodeOptions {
  /** Complete source code block */
  code: string;
  /** Language runtime */
  language: "python" | "javascript" | "typescript" | "go" | "rust" | "c" | "cpp" | "bash";
  /** Execution timeout in milliseconds */
  timeoutMs?: number;
}

export type NephisTier = "community" | "pro" | "enterprise";

export interface LicenseStatus {
  tier: NephisTier;
  tenant_id: string;
  is_valid: boolean;
  expires_at?: number | null;
}

export interface WebhookDispatchOptions {
  url: string;
  payload: string;
  secret?: string;
  retries?: number;
}

export interface FinOpsScanOptions {
  regions?: string;
  dryRun?: boolean;
}

export interface StoragePipeBenchOptions {
  sizeMb?: number;
  partSizeMb?: number;
  concurrency?: number;
}

export interface PTYInfo {
  sandbox_id: string;
  pty_endpoint: string;
  terminal: string;
  status: string;
}

export interface PortForwarding {
  sandbox_id: string;
  service_name: string;
  guest_port: number;
  host_port: number;
  connection_string: string;
  status: string;
  created_at: string;
}

export interface CandidateSpec {
  id: string;
  command?: string;
  code?: string;
  language?: string;
}

export interface CandidateRaceResult {
  candidate_id: string;
  status: "WINNER" | "REAPED" | "FAILED" | "TIMEOUT";
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_ms: number;
}

export interface SpeculativeRaceResult {
  problem_id: string;
  winner_candidate_id: string | null;
  total_candidates: number;
  race_duration_ms: number;
  strategy: string;
  results: CandidateRaceResult[];
}

export interface WALRewindOptions {
  sandboxId?: string;
  projectId?: string;
  targetTime?: string;
  targetLsn?: string;
}

export interface WALRewindResult {
  status: string;
  sandbox_id?: string;
  project_id?: string;
  branch_id: string;
  target_time?: string;
  target_lsn?: string;
  connection_string: string;
  rewind_latency_ms: number;
  message: string;
}

export interface MultiverseTimeline {
  branch_id: number;
  scenario: string;
  seed: number;
  passed: boolean;
  split_brain_risk: boolean;
  duration_ms: number;
  report?: {
    total_packets: number;
    dropped_packets: number;
    delayed_packets: number;
    split_brain_risk: boolean;
  };
}

export interface MultiverseForkResult {
  total_timelines: number;
  passed_count: number;
  failed_count: number;
  fork_latency_ms: number;
  master_seed: number;
  branches: MultiverseTimeline[];
}

export interface VirtualClockStatus {
  current_ticks: number;
  drift_ns: number;
  virtual_epoch: string;
  master_seed: number;
  tick_latency_ns: number;
}

export interface TwoPhasePromoteResult {
  status: "COMMITTED" | "ABORTED";
  promoted_branch_id: string;
  pruned_branches: string[];
  commit_duration_ms: number;
  message: string;
}

export interface VolumeAttachment {
  id: string;
  sandbox_id: string;
  mount_path: string;
  size_bytes: number;
  format: string;
  persist_at_scale: boolean;
  status: string;
  created_at: string;
}

export interface DualProbeResult {
  status: string;
  probe_mode: string;
  target: string;
  liveness: boolean;
  message: string;
  status_code?: number;
}

// -------------------------------------------------------------
// Eschaton Multi-Suite Assessment & Dynamic Evaluation Types
// -------------------------------------------------------------

export interface TestCaseSpec {
  id?: number | string;
  stdin?: string;
  expected_output?: string;
  schema_sql?: string;
  files?: Record<string, string>;
  output_file?: string;
}

export interface TestCaseResult {
  test_case_id: number;
  time: number;
  memory: number;
  stdout: string;
  stderr: string;
  passed: boolean;
  status_id: number;
  [key: string]: any;
}

export type DatabaseEngine = "postgres" | "mysql" | "mariadb" | "mongodb" | "redis" | "sqlite" | "qdrant" | string;

export interface ExecuteSuiteOptions {
  sourceCode: string;
  languageId?: number;
  /**
   * Execution suite. Note: "Omni" is deprecated/degraded.
   * Prefer "Apex" (hard-isolated multi-core) or "Void" (sub-4ms in-memory microkernel).
   */
  suite?: "Apex" | "Void" | "Complexity" | "Sanitizer" | "MemoryProfile" | "FileIO" | "DBMS" | "SpecialJudge" | "Omni" | string;
  testCases?: TestCaseSpec[];
  /** Supported database engines: postgres, mysql, mariadb, mongodb, redis, sqlite, qdrant */
  database?: DatabaseEngine;
  checkerCode?: string;
  checkerLanguageId?: number;
  verbose?: boolean;
  /** Stable caller-generated key; reuse it when retrying the same request. */
  idempotencyKey?: string;
}

export interface ExecuteSuiteResult {
  Results: TestCaseResult[];
  Error?: string;
  PassedCount?: number;
  TotalCount?: number;
}

export interface ComplexityProfileOptions {
  sourceCode: string;
  languageId?: number;
  stdin?: string;
}

export interface ComplexityProfileResult {
  Results: Array<{
    test_case_id: number;
    time: number;
    memory: number;
    stdout: string;
    stderr: string;
    passed: boolean;
    status_id: number;
    instructions_executed?: number;
    read_accesses?: number;
    write_accesses?: number;
    complexity_class?: string;
  }>;
  Error?: string;
}

export interface SanitizeCheckOptions {
  sourceCode: string;
  languageId?: number;
  stdin?: string;
}

export interface SanitizeCheckResult {
  Results: Array<{
    test_case_id: number;
    time: number;
    memory: number;
    stdout: string;
    stderr: string;
    passed: boolean;
    status_id: number;
    asan_report?: string;
    memory_leaks?: boolean;
    use_after_free?: boolean;
    buffer_overflow?: boolean;
  }>;
  Error?: string;
}

export interface DBMSEvalOptions {
  sourceCode: string;
  schemaSql: string;
  /** Supported database engines: postgres, mysql, mariadb, mongodb, redis, sqlite, qdrant */
  database?: DatabaseEngine;
  expectedOutput?: string;
  stdin?: string;
}

export interface DBMSEvalResult {
  Results: Array<{
    test_case_id: number;
    time: number;
    memory: number;
    stdout: string;
    stderr: string;
    passed: boolean;
    status_id: number;
    schema_applied?: boolean;
    tuples_affected?: number;
  }>;
  Error?: string;
}

export interface FileIOEvalOptions {
  sourceCode: string;
  inputFilename?: string;
  inputContent?: string;
  outputFilename?: string;
  expectedOutput?: string;
  languageId?: number;
}

export interface FileIOEvalResult {
  Results: Array<{
    test_case_id: number;
    time: number;
    memory: number;
    stdout: string;
    stderr: string;
    passed: boolean;
    status_id: number;
    file_matched?: boolean;
  }>;
  Error?: string;
}

export interface SpecialJudgeOptions {
  sourceCode: string;
  checkerCode: string;
  languageId?: number;
  checkerLanguageId?: number;
  stdin?: string;
  expectedOutput?: string;
}

export interface SpecialJudgeResult {
  Results: Array<{
    test_case_id: number;
    time: number;
    memory: number;
    stdout: string;
    stderr: string;
    passed: boolean;
    status_id: number;
    checker_verdict?: string;
  }>;
  Error?: string;
}

export interface BatchExecuteOptions {
  sourceCode: string;
  tests: TestCaseSpec[];
  /** Execution suite: defaults to "Apex". "Omni" is deprecated. */
  suite?: "Apex" | "Void" | "Omni" | string;
  languageId?: number;
  idempotencyKey?: string;
}

export interface BatchExecuteResult {
  Results: TestCaseResult[];
  Error?: string;
}

// -------------------------------------------------------------
// Live Socket & MicroVM Migration Types (Acheron / sockmig)
// -------------------------------------------------------------

export interface LiveMigrateOptions {
  /** Target node IP or hostname to migrate the process/socket to */
  targetNode: string;
  /** Source node IP or hostname (defaults to local / current node) */
  sourceNode?: string;
  /** Process ID of the guest or workload to migrate */
  pid: number;
  /** Specific socket file descriptor to checkpoint and hand over (optional) */
  socketFd?: number;
  /** Dry-run inspection without cutting over active connections */
  dryRun?: boolean;
}

export interface LiveMigrateResult {
  success: boolean;
  status: string;
  duration_ms: number;
  source_node: string;
  target_node: string;
  pid: number;
  socket_fd?: number;
  bytes_transferred?: number;
  error?: string;
}

// -------------------------------------------------------------
// Unified BaaS Multi-Tenant Auth & RLS Policy Types
// -------------------------------------------------------------

export type UnifiedKeyType = "publishable" | "secret" | "tenant_token";

export interface TenantAuthContext {
  tenantId: string;
  apiKey?: string;
  role?: "anon" | "authenticated" | "service_role";
  publishableKey?: string;
  secretKey?: string;
}

export interface RLSPolicyOptions {
  tenantId: string;
  table: string;
  policyName?: string;
  expression?: string;
  forAction?: "SELECT" | "INSERT" | "UPDATE" | "DELETE" | "ALL";
}

export interface RLSPolicyResult {
  success: boolean;
  tenant_id: string;
  table: string;
  policy_name: string;
  sql_executed: string;
  duration_ms: number;
}

export interface CheckpointOptions {
  sandboxId: string;
  name?: string;
  snapshotType?: "ram" | "disk" | "full";
}

export interface CheckpointResult {
  snapshot_id: string;
  sandbox_id: string;
  name: string;
  size_bytes: number;
  duration_ms: number;
  created_at: string;
}

// -------------------------------------------------------------
// Mnemon 6-Engine Multi-Database Substrate Types
// (PostgreSQL, MySQL/MariaDB, MongoDB, Redis, SQLite, Qdrant)
// -------------------------------------------------------------

export interface CreateDatabaseOptions {
  engine?: DatabaseEngine;
  memoryMb?: number;
  vcpus?: number;
  parentBranch?: string;
}

export interface RedisCommandOptions {
  tenantId: string;
  command: string;
  args?: (string | number)[];
}

export interface RedisCommandResult {
  status: string;
  tenant_id: string;
  command: string;
  result: any;
  duration_ms: number;
}

export interface MongoQueryOptions {
  tenantId: string;
  collection: string;
  action?: "find" | "findOne" | "insertOne" | "insertMany" | "aggregate" | "count";
  filter?: Record<string, any>;
  projection?: Record<string, any>;
  pipeline?: any[];
  document?: Record<string, any>;
  documents?: Record<string, any>[];
}

export interface MongoQueryResult {
  status: string;
  tenant_id: string;
  collection: string;
  documents?: any[];
  inserted_id?: string;
  count?: number;
  duration_ms: number;
}

export interface VectorSearchOptions {
  tenantId: string;
  collection: string;
  vector: number[];
  limit?: number;
  filter?: Record<string, any>;
  withPayload?: boolean;
}

export interface VectorSearchResult {
  status: string;
  tenant_id: string;
  collection: string;
  points: Array<{
    id: string | number;
    score: number;
    payload?: Record<string, any>;
  }>;
  duration_ms: number;
}

export interface VectorUpsertOptions {
  tenantId: string;
  collection: string;
  points: Array<{
    id: string | number;
    vector: number[];
    payload?: Record<string, any>;
  }>;
}

export interface VectorUpsertResult {
  status: string;
  tenant_id: string;
  collection: string;
  upserted_count: number;
  duration_ms: number;
}






export interface DeploymentItem {
  id: string;
  project_id: string;
  environment: "production" | "staging";
  branch?: string;
  commit_hash?: string;
  status: "BUILDING" | "READY" | "FAILED" | "ROLLBACK";
  build_duration_ms?: number;
  bundle_size_bytes?: number;
  worker_node?: string;
  created_at: string;
}

export interface DeploymentsListResult {
  project_id: string;
  count: number;
  deployments: DeploymentItem[];
}

export interface DeploymentStatusResult {
  id: string;
  status: string;
  build_ms: number;
  size_bytes: number;
  node: string;
}

export interface SetPreviewOptions {
  projectId: string;
  deploymentId: string;
}

export interface ProjectMetricsResult {
  project_id: string;
  tenant: string;
  requests_per_minute: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  http_2xx_count: number;
  http_4xx_count: number;
  http_5xx_count: number;
  bandwidth_bytes: number;
  active_connections: number;
}

export interface SandboxTelemetryResult {
  sandbox_id: string;
  tenant_id: string;
  status: string;
  timings?: {
    stage_us: number;
    boot_us: number;
    exec_us: number;
  };
  cpu_percent?: number;
  rss_bytes?: number;
  network_rx_bytes?: number;
  network_tx_bytes?: number;
  disk_io_bytes?: number;
}

export interface ClusterMetricsResult {
  host_cpu_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  swap_used_mb: number;
  pps: number;
  active_sandboxes: number;
  engine_score: number;
}
