/**
 * Thanaton TypeScript SDK - Sandbox Representation
 *
 * Provides lifecycle management, secure command execution, code execution,
 * and embedded PostgreSQL querying for hardware-isolated MicroVMs.
 */

import type { ThanatonClient } from "./client.js";

declare const Buffer: any;
import type {
  ExecOptions,
  ExecResult,
  RunCodeOptions,
  SandboxMetadata,
  SandboxState,
  PTYInfo,
  PortForwarding,
  VolumeAttachment,
  DualProbeResult,
} from "./types.js";

/**
 * Represents a dedicated, hardware-isolated execution sandbox (Firecracker MicroVM or Silicon Isolate).
 *
 * @example
 * ```typescript
 * const sbx = await client.sandboxes.create({ runtime: "microvm", memoryMb: 512 });
 * const res = await sbx.exec("echo 'hello world'");
 * console.log(res.stdout);
 * await sbx.destroy();
 * ```
 */
export class Sandbox {
  /** Unique sandbox identifier (e.g., 'sbx_a1b2c3d4') */
  public id: string;
  /** Organization or tenant ID associated with this sandbox */
  public tenantId: string;
  /** Underlying virtualization runtime ('microvm', 'silicon', 'node', 'python') */
  public runtime: string;
  /** Current lifecycle state of the sandbox ('running', 'sleeping', 'frozen', 'stopped') */
  public state: SandboxState;
  /** Indicates whether an embedded PostgreSQL database is running in this sandbox */
  public hasDb: boolean;
  /** Host-mapped TCP port for connecting to PostgreSQL (if hasDb is true) */
  public dbPort?: number;
  /** Fully qualified PostgreSQL connection URL (e.g. postgresql://postgres:thanaton@...) */
  public dbUrl?: string;
  /** Time taken to cold boot or hydrate the sandbox from snapshot, in milliseconds */
  public bootDurationMs: number;
  /** ISO timestamp when the sandbox was provisioned */
  public createdAt: string;
  /** ISO timestamp of last recorded activity */
  public lastActiveAt: string;

  private client: ThanatonClient;

  constructor(client: ThanatonClient, meta: SandboxMetadata) {
    this.client = client;
    this.id = meta.id;
    this.tenantId = meta.tenant_id;
    this.runtime = meta.runtime;
    this.state = meta.state;
    this.hasDb = meta.has_db;
    this.dbPort = meta.db_port;
    this.dbUrl = meta.db_url;
    this.bootDurationMs = meta.boot_duration_ms;
    this.createdAt = meta.created_at;
    this.lastActiveAt = meta.last_active_at;
  }

  /**
   * Execute an arbitrary shell command inside this isolated MicroVM.
   *
   * @param command - Shell command string (e.g., 'npm test', 'ls -la', 'python3 train.py')
   * @param options - Optional timeout, environment variables, and working directory
   * @returns Promise resolving to stdout, stderr, exit code, and execution duration
   *
   * @example
   * ```typescript
   * const res = await sandbox.exec("git status", { timeoutMs: 10000 });
   * if (res.ok) {
   *   console.log(res.stdout);
   * }
   * ```
   */
  async exec(command: string, options: ExecOptions = {}): Promise<ExecResult> {
    const payload = {
      command,
      timeout_ms: options.timeoutMs ?? 15000,
      env: options.env,
      cwd: options.cwd,
    };

    const res = await this.client.request<any>("POST", `/v1/sandboxes/${this.id}/exec`, payload);
    const exitCode = typeof res.exit_code === "number" ? res.exit_code : 0;

    return {
      stdout: res.stdout || "",
      stderr: res.stderr || "",
      exitCode,
      ok: exitCode === 0,
      durationMs: Number(res.duration_ms || 0),
    };
  }

  /**
   * Directly run a standalone source code snippet inside the sandbox.
   * Encodes the script in Base64 to prevent shell quoting bugs or parameter injection.
   *
   * @param options - Source code string, language runtime, and execution timeout
   * @returns Promise resolving to execution results
   *
   * @example
   * ```typescript
   * const res = await sandbox.runCode({
   *   language: "python",
   *   code: "import math; print(math.sqrt(144))",
   * });
   * console.log(res.stdout); // 12.0
   * ```
   */
  async runCode(options: RunCodeOptions): Promise<ExecResult> {
    const { code, language, timeoutMs = 15000 } = options;
    const b64 = Buffer.from(code, "utf-8").toString("base64");

    let cmd: string;
    switch (language.toLowerCase()) {
      case "python":
        cmd = `python3 -c "import base64; exec(base64.b64decode('${b64}').decode('utf-8'))"`;
        break;
      case "javascript":
      case "node":
        cmd = `node -e "eval(Buffer.from('${b64}', 'base64').toString('utf-8'))"`;
        break;
      case "typescript":
        cmd = `npx -y tsx -e "eval(Buffer.from('${b64}', 'base64').toString('utf-8'))"`;
        break;
      case "bash":
      case "sh":
        cmd = `echo '${b64}' | base64 -d | bash`;
        break;
      default:
        cmd = `python3 -c "import base64; exec(base64.b64decode('${b64}').decode('utf-8'))"`;
    }

    return this.exec(cmd, { timeoutMs });
  }

  /**
   * Execute a raw SQL query against the sandbox's embedded PostgreSQL instance.
   *
   * @param query - Raw SQL query to execute (DDL, DML, or SELECT)
   * @returns Array of resulting database rows represented as JavaScript objects
   * @throws Error if the sandbox was created without withDb: true
   *
   * @example
   * ```typescript
   * const rows = await sandbox.sql("SELECT tablename FROM pg_tables WHERE schemaname = 'public';");
   * console.log(rows);
   * ```
   */
  async sql(query: string): Promise<Record<string, any>[]> {
    if (!this.hasDb) {
      throw new Error(`Sandbox '${this.id}' was provisioned without an embedded database. Create with { withDb: true }.`);
    }

    const res = await this.client.request<{ rows: Record<string, any>[] }>(
      "POST",
      `/v1/sandboxes/${this.id}/sql`,
      { query }
    );
    return res.rows || [];
  }

  /**
   * Freeze the sandbox via Linux cgroups v2 (`cgroup.freeze = 1`).
   * Pauses all guest threads instantly, reducing host CPU consumption to exactly 0.00%.
   */
  async freeze(): Promise<void> {
    await this.client.request("POST", `/v1/sandboxes/${this.id}/freeze`);
    this.state = "frozen";
  }

  /**
   * Resume/unfreeze the sandbox in sub-millisecond latency via cgroups v2 (`cgroup.freeze = 0`).
   */
  async unfreeze(): Promise<void> {
    await this.client.request("POST", `/v1/sandboxes/${this.id}/unfreeze`);
    this.state = "running";
  }

  /**
   * Scale the MicroVM to zero. Hibernates guest RAM into an NVMe golden memory snapshot.
   * Host RAM utilization drops to 0 MB ($0 idling cost).
   */
  async sleep(): Promise<void> {
    await this.client.request("POST", `/_thanaton/tenants/${this.id}/sleep`);
    this.state = "sleeping";
  }

  /**
   * Instantly wake the MicroVM from its NVMe memory snapshot in sub-6ms (<2ms with UFFD lazy-paging).
   * Restores exact register and RAM state prior to hibernation.
   */
  async wake(): Promise<void> {
    await this.client.request("POST", `/_thanaton/tenants/${this.id}/wake`);
    this.state = "running";
  }

  /**
   * Fetch and synchronize the latest state, IP, and timestamps from the Thanaton daemon.
   */
  async refresh(): Promise<Sandbox> {
    const meta = await this.client.request<SandboxMetadata>("GET", `/v1/sandboxes/${this.id}`);
    this.state = meta.state;
    this.lastActiveAt = meta.last_active_at;
    return this;
  }

  /**
   * Retrieve WebSocket PTY gateway connection details for real-time interactive terminal access.
   */
  async ptyInfo(): Promise<PTYInfo> {
    return this.client.request<PTYInfo>("GET", `/v1/sandboxes/${this.id}/pty`);
  }

  /**
   * Expose a guest TCP port via Layer 4 TCP port forwarding (antinat).
   *
   * @param guestPort - Guest port inside the microVM (e.g. 5432, 8080, 50051)
   * @param protocol - Transport protocol (default: 'tcp')
   * @param serviceName - Optional descriptive service name (e.g. 'postgres', 'grpc')
   */
  async exposePort(
    guestPort: number,
    protocol: string = "tcp",
    serviceName: string = "custom"
  ): Promise<PortForwarding> {
    const payload = {
      guest_port: guestPort,
      protocol,
      service_name: serviceName,
    };
    return this.client.request<PortForwarding>("POST", `/v1/sandboxes/${this.id}/ports`, payload);
  }

  /**
   * List all currently active Layer 4 TCP port forwardings for this sandbox.
   */
  async listPorts(): Promise<PortForwarding[]> {
    const res = await this.client.request<{ ports: PortForwarding[] }>(
      "GET",
      `/v1/sandboxes/${this.id}/ports`
    );
    return res.ports || [];
  }

  /**
   * Close and release an allocated Layer 4 TCP port forwarding.
   *
   * @param hostPort - Host port number to release
   */
  async closePort(hostPort: number): Promise<void> {
    await this.client.request("DELETE", `/v1/sandboxes/${this.id}/ports/${hostPort}`);
  }

  /**
   * List persistent ext4 volumes attached to this sandbox (/data).
   */
  async getVolumes(): Promise<VolumeAttachment[]> {
    const res = await this.client.request<{ volumes: VolumeAttachment[] }>(
      "GET",
      `/api/v1/sandboxes/volumes?sandbox_id=${encodeURIComponent(this.id)}`
    );
    return res.volumes || [];
  }

  /**
   * Attach a persistent sparse ext4 volume mounted at /data for SQLite/PocketBase scale-to-zero.
   */
  async attachVolume(options: { mountPath?: string; sizeGb?: number } = {}): Promise<VolumeAttachment> {
    const res = await this.client.request<{ volume: VolumeAttachment }>(
      "POST",
      "/api/v1/sandboxes/volumes",
      {
        sandbox_id: this.id,
        mount_path: options.mountPath || "/data",
        size_gb: options.sizeGb || 10,
      }
    );
    return res.volume;
  }

  /**
   * Hot-inject environment secrets into Firecracker MMDS in <50µs without rebuilding rootfs.
   */
  async injectSecrets(secrets: Record<string, string>): Promise<{ status: string; injection_time_us: number }> {
    return this.client.request<{ status: string; injection_time_us: number }>(
      "POST",
      "/api/v1/sandboxes/secrets/inject",
      {
        sandbox_id: this.id,
        secrets,
      }
    );
  }

  /**
   * Run adaptive dual-liveness probe (HTTP with raw TCP 3-way handshake fallback).
   */
  async probe(port: number = 3000, healthPath: string = "/health"): Promise<DualProbeResult> {
    return this.client.request<DualProbeResult>(
      "POST",
      "/api/v1/sandboxes/dual-probe",
      {
        target_host: "127.0.0.1",
        port,
        health_path: healthPath,
      }
    );
  }

  /**
   * Capture running guest RAM state directly to high-speed /dev/shm in ~15ms.
   */
  async createRAMSnapshot(warmPackages: string[] = []): Promise<any> {
    return this.client.createRAMSnapshot(this.id, warmPackages);
  }

  /**
   * Restore this sandbox from a pre-warmed RAM snapshot in 12ms.
   */
  async restoreRAMSnapshot(snapshotId: string): Promise<any> {
    return this.client.restoreRAMSnapshot(snapshotId, this.id);
  }

  /**
   * Inspect or configure eBPF kernel TAP outbound secret exfiltration firewall.
   */
  async configureSecretShield(action: "get" | "enable" | "disable" = "get"): Promise<any> {
    return this.client.configureSecretShield(this.id, { action });
  }

  /**
   * Capture real-time screenshot or CDP stream frame from headless browser canvas.
   */
  async captureBrowserDisplay(options: { format?: "jpeg" | "png" | "webp"; quality?: number } = {}): Promise<any> {
    return this.client.captureBrowserDisplay(this.id, options);
  }

  /**
   * Gracefully terminate guest processes, clean up database tables, delete TAP network interfaces,
   * unmount cgroups, and permanently reclaim sandbox resources.
   */
  async destroy(): Promise<void> {
    await this.client.request("DELETE", `/v1/sandboxes/${this.id}`);
    this.state = "stopped";
  }
}
