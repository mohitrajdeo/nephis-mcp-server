/**
 * @nephis/sdk & nephis - Official TypeScript & Node.js SDK
 * Sub-6ms KVM MicroVM Sandboxes, Zero-Copy Database Branching, and Execution Fabric for AI Coding Agents.
 */

export {
  ThanatonClient,
  ThanatonClient as AnankeClient,
  ThanatonClient as CielClient,
  ThanatonClient as NephisClient,
  ThanatonClient as Nephis,
  SandboxManager,
  CDCManager,
  WebhookManager,
  FinOpsManager,
  DiagnosticsManager,
  ChaosManager,
  PoolManager,
  StoragePipeManager,
  RootfsManager,
  DNSManager,
  LiveMigrationManager,
} from "./client.js";

export { Sandbox } from "./sandbox.js";

export {
  ThanatonError,
  ThanatonError as CielError,
  ThanatonError as NephisError,
  ThanatonConnectionError as CielConnectionError,
  ThanatonConnectionError as NephisConnectionError,
  ThanatonAPIError as CielAPIError,
  ThanatonAPIError as NephisAPIError,
  ThanatonAPIError,
  ThanatonTimeoutError,
  ThanatonRateLimitError,
  ThanatonCapacityError,
  EschatonFuelExhaustedError,
  ThanatonConnectionError,
  EscalationRequiredError,
} from "./errors.js";

export {
  LicenseToken,
  LicenseAuthority,
  LicenseError,
  TIERS,
  DEFAULT_LICENSE_SECRET,
} from "./license.js";

export {
  MnemonClient,
  MnemonError,
} from "./mnemon.js";

export {
  EschatonClient,
  EschatonError,
} from "./eschaton.js";

export type {
  EschatonClientOptions,
} from "./eschaton.js";

export type {
  MnemonClientOptions,
  TenantStatus,
  QueryResult,
  SchemaDiffResult,
  SearchResult,
  TimeTravelResult,
} from "./mnemon.js";

export type {
  ClientOptions,
  CreateSandboxOptions,
  ExecOptions,
  ExecResult,
  RunCodeOptions,
  SandboxMetadata,
  SandboxRuntime,
  SandboxState,
  AnankeTier,
  LicenseStatus,
  WebhookDispatchOptions,
  FinOpsScanOptions,
  StoragePipeBenchOptions,
  PTYInfo,
  PortForwarding,
  CandidateSpec,
  CandidateRaceResult,
  SpeculativeRaceResult,
  WALRewindOptions,
  WALRewindResult,
  TestCaseSpec,
  TestCaseResult,
  ExecuteSuiteOptions,
  ExecuteSuiteResult,
  ComplexityProfileOptions,
  ComplexityProfileResult,
  SanitizeCheckOptions,
  SanitizeCheckResult,
  DBMSEvalOptions,
  DBMSEvalResult,
  FileIOEvalOptions,
  FileIOEvalResult,
  SpecialJudgeOptions,
  SpecialJudgeResult,
  BatchExecuteOptions,
  BatchExecuteResult,
} from "./types.js";

export type {
  TierEntitlements,
  LicenseClaims,
  GenerateLicenseOptions,
} from "./license.js";

export { ThanatonClient as default } from "./client.js";
