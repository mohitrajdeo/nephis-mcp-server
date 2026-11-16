/**
 * Thanaton & Ananke TypeScript SDK - Core Type Definitions
 */

export interface ClientOptions {
  /** Thanaton/Ananke Control Plane Base URL (defaults to http://127.0.0.1:8080) */
  baseUrl?: string;
  /** Optional API Bearer Token for cloud/multi-tenant deployments */
  apiKey?: string;
  /** Optional Cryptographic Ananke License Token (ank_lic_...) */
  licenseKey?: string;
  /** Global HTTP Request Timeout in ms (default: 30000) */
  timeoutMs?: number;
}

export type SandboxRuntime = "microvm" | "silicon" | "node" | "python";

export type SandboxState = "running" | "sleeping" | "frozen" | "stopped" | "unknown";

export interface CreateSandboxOptions {
  /** Sandbox runtime engine: 'microvm' (KVM/Firecracker), 'silicon' (Isolate), 'node', 'python' */
  runtime?: SandboxRuntime;
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

export type AnankeTier = "community" | "pro" | "enterprise";

export interface LicenseStatus {
  tier: AnankeTier;
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

export interface ExecuteSuiteOptions {
  sourceCode: string;
  languageId?: number;
  suite?: "Omni" | "Apex" | "Void" | "Complexity" | "Sanitizer" | "MemoryProfile" | "FileIO" | "DBMS" | "SpecialJudge" | string;
  testCases?: TestCaseSpec[];
  database?: "sqlite" | "postgres" | "mysql" | "oracle" | string;
  checkerCode?: string;
  checkerLanguageId?: number;
  verbose?: boolean;
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
  database?: "sqlite" | "postgres" | "mysql" | "oracle" | string;
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
  suite?: "Omni" | "Apex" | "Void" | string;
  languageId?: number;
}

export interface BatchExecuteResult {
  Results: TestCaseResult[];
  Error?: string;
}




