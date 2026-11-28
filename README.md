# NEPHIS Model Context Protocol (MCP) Server (`nephis-mcp-server`)

> **The Unified MCP Control Plane for Autonomous AI Coding Agents.**  
> Provides hardware-isolated KVM microVM sandboxes, zero-copy PostgreSQL branching, in-memory AST compiler pipelines, and kernel infrastructure to LLMs (Claude Desktop, Cursor, Windsurf, Devin, Antigravity).  
> **Live evidence:** 10/10 selfcheck with caveats — https://eschaton.theeducode.com/proof  
> **Scoped trial key:** https://eschaton.theeducode.com/trial  
> **On numbers:** latency and throughput depend on workload. Older local-server figures are historical records of that work, not hosted-service claims.

[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol%202024--11--05-purple.svg)](https://modelcontextprotocol.io/)
[![npm version](https://img.shields.io/npm/v/nephis-mcp-server.svg)](https://www.npmjs.com/package/nephis-mcp-server)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Live Proof](https://img.shields.io/badge/Proof-10%2F10_selfcheck-10b981.svg)](https://eschaton.theeducode.com/proof)

---

## ⚡ Architecture Overview

> 🌐 **Canonical Production Gateway:** [https://nephis.theeducode.com](https://nephis.theeducode.com)  
> ⚡ **Eschaton Online Judge (Judge0-compatible):** [https://eschaton.theeducode.com](https://eschaton.theeducode.com)  
> 💻 **Thanaton MicroVM Studio (Low-latency):** [https://thanaton.theeducode.com](https://thanaton.theeducode.com)  
> 🗄️ **Mnemon-DB Postgres Studio (CoW):** [https://mnemon.theeducode.com](https://mnemon.theeducode.com)  
> 💳 **Centralized Billing & Refill Hub:** [https://nephis.theeducode.com/billing](https://nephis.theeducode.com/billing)  
> 🚀 **Single-Command Agent Launch:** `npx -y nephis-mcp-server`

---

### ⚡ Autonomous Zero-Human PoW Self-Bootstrap (Scoped 30-Day Trial Key)

When an autonomous AI agent launches `nephis-mcp-server` without an explicit `NEPHIS_API_KEY`:
1. The server automatically computes a local machine fingerprint (MAC, CPU, host) and requests a cryptographic Proof-of-Work challenge from the gateway.
2. It claims a scoped **500-credit developer session** (`mrd_live_...`).
3. Credentials are saved locally to `~/.nephis/credentials.json` with automatic session renewal.
4. **No browser popups are required to start.** Human developers can also claim their session with 1-click GitHub OAuth on [nephis.theeducode.com](https://nephis.theeducode.com) to move to a paid tier.

The **NEPHIS MCP Server** connects LLMs and autonomous coding assistants directly to bare-metal compute and database substrates across 4 core pillars:
1. **THANATON:** Hardware KVM microVM sandboxes, low-latency boot, scale-to-zero stasis ($0 idle RAM), PTY terminals, Layer 4 port forwards, project deployments, custom domains, crons, webhooks, and SIEM drains.
2. **MNEMON-DB:** zero-copy PostgreSQL 16 branching (XFS CoW reflinks), embedded vector search, schema diffing, and WAL rewind.
3. **ESCHATON & NEPHIS:** Judge0-compatible parallel online code judging, in-memory AST hazard detection (), 50-testcase fast-batch execution, and tenant whoami introspection.
4. **KERNEL INFRASTRUCTURE:** Kernel systems, eBPF connection pooling, zero-copy S3 streaming pipes, tombstone crash autopsy, and live socket migration.

```
┌────────────────────────────────────────────────────────┐
│ Autonomous AI Coding Agent (Cursor / Claude / Devin)   │
└───────────────────────────┬────────────────────────────┘
                            │ JSON-RPC 2.0 (stdio / SSE)
                            ▼
┌────────────────────────────────────────────────────────┐
│ NEPHIS Unified MCP Server (MCP tools)        │
└───────┬───────────────────┬───────────────────┬────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   THANATON   │    │  MNEMON-DB   │    │   ESCHATON   │
│ MicroVMs &   │    │  Zero-Copy   │    │ Judge0-compatible AST │
│ KVM Compute  │    │  PostgreSQL  │    │ Polyglot CI  │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🚀 10-Second Setup for Coding Agents

### Option 1: Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "nephis": {
      "command": "npx",
      "args": ["-y", "nephis-mcp-server"],
      "env": {
        "NEPHIS_API_KEY": "mrd_live_YOUR_KEY",
        "NEPHIS_BASE_URL": "https://nephis.theeducode.com"
      }
    }
  }
}
```

### Option 2: Cursor (`.cursor/mcp.json` or Global Settings)
```json
{
  "mcpServers": {
    "nephis": {
      "command": "npx",
      "args": ["-y", "nephis-mcp-server"],
      "env": {
        "NEPHIS_API_KEY": "mrd_live_YOUR_KEY",
        "NEPHIS_BASE_URL": "https://nephis.theeducode.com"
      }
    }
  }
}
```

### Option 3: Windsurf (`~/.codeium/windsurf/mcp_config.json`)
```json
{
  "mcpServers": {
    "nephis": {
      "command": "npx",
      "args": ["-y", "nephis-mcp-server"],
      "env": {
        "NEPHIS_BASE_URL": "https://nephis.theeducode.com"
      }
    }
  }
}
```

### Option 4: Cline / Roo Code (`cline_mcp_settings.json`)
```json
{
  "mcpServers": {
    "nephis": {
      "command": "npx",
      "args": ["-y", "nephis-mcp-server"],
      "env": {
        "NEPHIS_BASE_URL": "https://nephis.theeducode.com"
      }
    }
  }
}
```

### Option 5: Google Antigravity & Gemini CLI
Add `nephis` to your project's `antigravity.json` or run `npx nephis-mcp-server` directly via stdio transport.

---

## 📋 Tool Navigation Summary

| Category | Count | Focus Areas |
| :--- | :---: | :--- |
| [THANATON (Compute, Deploy & Edge)](#1-thanaton--hardware-kvm-microvms--compute-sandboxes) | 33 | MicroVM boot, PTY, ports, secrets, volumes, projects, WAF, domains, crons, hooks, routes, drains, wallet, invoices |
| [MNEMON-DB (Databases & Vector)](#2-mnemon-db--zero-copy-isolated-database-engine--branching) | 14 | CoW branching, SQL queries, schema diff, pgvector, WAL rewind |
| [ESCHATON & NEPHIS (Execution & Identity)](#3-eschaton--nephis--autonomous-polyglot-code-execution--fast-batch) | 4 | AST preflight, 50-testcase fast-batch, compiler pipeline, whoami |
| **Total** | see catalog | Machine-readable & standardized |

---

## 🛠 Catalog of MCP Tools


## THANATON • Hardware KVM MicroVMs & Compute Sandboxes

Contains production tools designed for agent autonomy.

### 1. `thanaton_exec_command`

> **Description:** Execute an arbitrary shell command (bash, sh) inside an isolated, hardware-virtualized MicroVM sandbox. Returns stdout, stderr, exit code, and execution latency.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `command` | `string` | ✅ Yes | - | The shell command to execute inside the MicroVM (e.g., 'python3 -c "print(2+2)"', 'npm test', 'git status') |
| `sandbox_id` | `string` | ❌ No | - | Optional existing sandbox ID. If omitted, an ephemeral low-latency sandbox will be provisioned automatically. |
| `timeout_ms` | `number` | ❌ No | - | Maximum execution timeout in milliseconds (default: 15000) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_exec_command",
    "arguments": {
      "command": "uname -a && free -m",
      "sandbox_id": "sbx-kvm-9f82d1",
      "timeout_ms": 10000
    }
  },
  "id": 1
}
```

---

### 2. `thanaton_run_code`

> **Description:** Directly run a standalone, single-file code snippet in an ephemeral, stateless microVM sandbox (automatically destroyed after execution). For stateful multi-step terminal interactions, filesystem persistence, or long-running processes, use 'thanaton_spawn_sandbox' followed by 'thanaton_exec_command' passing the 'sandbox_id'.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `language` | `string` | ✅ Yes | - | Programming language runtime (Enum: `[python, javascript, typescript, go, rust, c, cpp, bash]`) |
| `code` | `string` | ✅ Yes | - | The complete source code snippet to compile and execute |
| `timeout_ms` | `number` | ❌ No | - | Timeout in milliseconds (default: 10000) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_run_code",
    "arguments": {
      "language": "python",
      "code": "print('Executed safely via Nephis')",
      "timeout_ms": 10000
    }
  },
  "id": 2
}
```

---

### 3. `thanaton_spawn_sandbox`

> **Description:** Provision a new hardware-isolated KVM MicroVM or Silicon isolate. Supports scale-to-zero, memory snapshots, and optional embedded PostgreSQL database.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `runtime` | `string` | ❌ No | - | Runtime environment type (default: 'microvm') (Enum: `[microvm, silicon, node, python]`) |
| `memory_mb` | `number` | ❌ No | - | Allocated RAM in MiB (default: 256) |
| `with_db` | `boolean` | ❌ No | - | Whether to bundle an isolated PostgreSQL database inside the sandbox |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_spawn_sandbox",
    "arguments": {
      "runtime": "microvm",
      "memory_mb": 256,
      "with_db": true
    }
  },
  "id": 3
}
```

---

### 4. `thanaton_list_sandboxes`

> **Description:** List all active, sleeping, and managed MicroVM sandboxes across the current tenant.

**Parameter Specification:**

_No input parameters required._

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_list_sandboxes",
    "arguments": {}
  },
  "id": 4
}
```

---

### 5. `thanaton_wake_sandbox`

> **Description:** Instantly wake a sleeping/hibernated MicroVM from NVMe memory snapshot in low-latency ().

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | The ID of the sleeping sandbox to wake |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_wake_sandbox",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1"
    }
  },
  "id": 5
}
```

---

### 6. `thanaton_sleep_sandbox`

> **Description:** Scale a MicroVM to zero (hibernates RAM to NVMe snapshot, 0% CPU consumption, $0 cost).

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | The ID of the running sandbox to put to sleep |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_sleep_sandbox",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1"
    }
  },
  "id": 6
}
```

---

### 7. `thanaton_destroy_sandbox`

> **Description:** Terminate processes, tear down TAP network interface, cgroups, and reclaim all sandbox resources.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | The ID of the sandbox to destroy |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_destroy_sandbox",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1"
    }
  },
  "id": 7
}
```

---

### 8. `thanaton_list_projects`

> **Description:** List all Thanaton serverless application projects and their live domains.

**Parameter Specification:**

_No input parameters required._

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_list_projects",
    "arguments": {}
  },
  "id": 8
}
```

---

### 9. `thanaton_create_project`

> **Description:** Create a new project/application deployment target in Thanaton.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `name` | `string` | ✅ Yes | - | Project name |
| `slug` | `string` | ❌ No | - | Optional custom project slug |
| `runtime` | `string` | ❌ No | - | Application runtime (default: nodejs) (Enum: `[nodejs, python, go, rust, docker]`) |
| `app_port` | `number` | ❌ No | - | Internal HTTP listening port (default: 3000) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_create_project",
    "arguments": {
      "name": "sample_name",
      "slug": "sample_slug",
      "runtime": "nodejs",
      "app_port": 8080
    }
  },
  "id": 9
}
```

---

### 10. `thanaton_manage_env`

> **Description:** List, set, or delete project environment variables.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `project_id` | `string` | ✅ Yes | - | Target project ID |
| `action` | `string` | ✅ Yes | - | Action to perform (Enum: `[list, set, delete]`) |
| `key` | `string` | ❌ No | - | Environment variable key |
| `value` | `string` | ❌ No | - | Variable value (for set action) |
| `environment` | `string` | ❌ No | - | Target environment (Enum: `[production, preview, development, all]`) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_manage_env",
    "arguments": {
      "project_id": "sample_project_id",
      "action": "list",
      "key": "sample_key",
      "value": "sample_value",
      "environment": "production"
    }
  },
  "id": 10
}
```

---

### 11. `thanaton_rollback`

> **Description:** Instant atomic rollback of production traffic to a previous deployment snapshot in 8.2ms.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `project_id` | `string` | ✅ Yes | - | Target project ID |
| `deployment_id` | `string` | ✅ Yes | - | Target snapshot deployment ID to restore |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_rollback",
    "arguments": {
      "project_id": "sample_project_id",
      "deployment_id": "sample_deployment_id"
    }
  },
  "id": 11
}
```

---

### 12. `thanaton_promote`

> **Description:** Promote staging preview deployment snapshot to production traffic in .

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `project_id` | `string` | ✅ Yes | - | Target project ID |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_promote",
    "arguments": {
      "project_id": "sample_project_id"
    }
  },
  "id": 12
}
```

---

### 13. `thanaton_configure_waf`

> **Description:** Inspect or configure edge Web Application Firewall (WAF) Attack Mode, rate limits, allowlist, and blocklist.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `project_id` | `string` | ✅ Yes | - | Target project ID |
| `action` | `string` | ✅ Yes | - | Action to perform (Enum: `[get, set]`) |
| `attack_mode` | `boolean` | ❌ No | - | Enable Under Attack Mode (cryptographic PoW challenge) |
| `rate_limit_rps` | `number` | ❌ No | - | Per-IP rate limit RPS threshold |
| `allowlist` | `array` | ❌ No | - | CIDR allowlist IP blocks |
| `blocklist` | `array` | ❌ No | - | CIDR blocklist IP blocks |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_configure_waf",
    "arguments": {
      "project_id": "sample_project_id",
      "action": "get",
      "attack_mode": true,
      "rate_limit_rps": 100,
      "allowlist": [
        "item_1",
        "item_2"
      ],
      "blocklist": [
        "item_1",
        "item_2"
      ]
    }
  },
  "id": 13
}
```

---

### 14. `thanaton_configure_scaling`

> **Description:** Inspect or configure Thanaton compute scaling: toggle between Serverless (scale-to-zero) and Always-On stateful execution, RAM allocation, and idle timeout.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `project_id` | `string` | ✅ Yes | - | Target project ID |
| `action` | `string` | ✅ Yes | - | Action to perform ('get' or 'set') (Enum: `[get, set]`) |
| `always_on` | `boolean` | ❌ No | - | Enable 24/7 Always-On stateful background execution (Indie/Pro) |
| `idle_timeout_seconds` | `number` | ❌ No | - | Inactivity seconds before scaling to zero (min 15s) |
| `memory_mb` | `number` | ❌ No | - | RAM allocation in MB (e.g. 256, 1024, 4096) |
| `vcpu_count` | `number` | ❌ No | - | vCPU count (e.g. 1, 2, 4) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_configure_scaling",
    "arguments": {
      "project_id": "sample_project_id",
      "action": "get",
      "always_on": true,
      "idle_timeout_seconds": 10000,
      "memory_mb": 256,
      "vcpu_count": 100
    }
  },
  "id": 14
}
```

---

### 15. `thanaton_get_volumes`

> **Description:** List persistent ext4 sparse volumes attached to a microVM sandbox for SQLite, PocketBase, or local file storage with scale-to-zero persistence.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ❌ No | - | MicroVM sandbox ID (default: sbx-default) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_get_volumes",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1"
    }
  },
  "id": 15
}
```

---

### 16. `thanaton_attach_volume`

> **Description:** Attach a persistent sparse ext4 volume mounted at /data with scale-to-zero snapshot persistence.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | MicroVM sandbox ID |
| `mount_path` | `string` | ❌ No | - | Target mount path inside microVM (default: /data) |
| `size_gb` | `number` | ❌ No | - | Virtual volume size in gigabytes (default: 10) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_attach_volume",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1",
      "mount_path": "sample_mount_path",
      "size_gb": 100
    }
  },
  "id": 16
}
```

---

### 17. `thanaton_dual_probe`

> **Description:** Adaptive Dual-Liveness Probe: Probes HTTP endpoint and automatically falls back to raw TCP 3-way handshake on guest port, eliminating silent false-positive deploy failures.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `target_host` | `string` | ❌ No | - | Target host IP or hostname (default: 127.0.0.1) |
| `port` | `number` | ✅ Yes | - | Target port inside guest (e.g., 3000, 8080) |
| `health_path` | `string` | ❌ No | - | Health check URL path (e.g., /health, /) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_dual_probe",
    "arguments": {
      "target_host": "sample_target_host",
      "port": 8080,
      "health_path": "sample_health_path"
    }
  },
  "id": 17
}
```

---

### 18. `thanaton_inject_secrets`

> **Description:** Zero-rebuild environment variable and secret injection via Firecracker MMDS in  without rebuilding the SquashFS rootfs.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | MicroVM sandbox ID |
| `secrets` | `object` | ✅ Yes | - | Key-value map of secrets and environment variables to inject |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_inject_secrets",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1",
      "secrets": {
        "key": "value"
      }
    }
  },
  "id": 18
}
```

---

### 19. `thanaton_reap_extents`

> **Description:** Autonomous CoW extent reaper: Reclaims unreferenced disk blocks and frees host RAM via process_madvise(MADV_DONTNEED).

**Parameter Specification:**

_No input parameters required._

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_reap_extents",
    "arguments": {}
  },
  "id": 19
}
```

---

### 20. `thanaton_pty_info`

> **Description:** Get real-time bidirectional WebSocket PTY terminal gateway connection details for an attached interactive microVM shell.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | Target sandbox ID |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_pty_info",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1"
    }
  },
  "id": 20
}
```

---

### 21. `thanaton_expose_port`

> **Description:** Allocate and expose a Layer 4 TCP wire forwarding port (antinat) from ephemeral host pool (12000-20000) for PostgreSQL, gRPC, or custom daemons.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | Target sandbox ID |
| `guest_port` | `number` | ✅ Yes | - | Internal port inside microVM (e.g. 5432, 8080) |
| `protocol` | `string` | ❌ No | `tcp` | Layer 4 transport protocol (Enum: `[tcp]`) |
| `service_name` | `string` | ❌ No | `custom` | Descriptive service name (e.g. postgres, grpc) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_expose_port",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1",
      "guest_port": 8080,
      "protocol": "tcp",
      "service_name": "sample_service_name"
    }
  },
  "id": 21
}
```

---

### 22. `thanaton_list_ports`

> **Description:** List all active Layer 4 TCP port forwardings for a specific microVM sandbox.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | Target sandbox ID |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_list_ports",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1"
    }
  },
  "id": 22
}
```

---

### 23. `thanaton_close_port`

> **Description:** Close an active Layer 4 TCP port forwarding and return the host port to the pool.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | Target sandbox ID |
| `host_port` | `number` | ✅ Yes | - | Allocated host port number to release |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_close_port",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1",
      "host_port": 8080
    }
  },
  "id": 23
}
```

---

### 24. `thanaton_speculate_race`

> **Description:** Execute multi-candidate speculative branch racing: runs N candidate code patches in parallel ephemeral microVMs, commits the fastest passing candidate, and instantly reaps losers.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `problem_id` | `string` | ❌ No | `default_problem` | Unique identifier for the task or problem |
| `candidates` | `array` | ✅ Yes | - | List of candidate hypotheses/patches to race in parallel |
| `timeout_ms` | `number` | ❌ No | `30000` | Maximum race timeout in milliseconds |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "thanaton_speculate_race",
    "arguments": {
      "problem_id": "sample_problem_id",
      "candidates": [
        "item_1",
        "item_2"
      ],
      "timeout_ms": 10000
    }
  },
  "id": 24
}
```

---

## MNEMON-DB • Zero-Copy Isolated Database Engine & Branching

Contains **14 production tools** specifically designed for agent autonomy.

### 25. `mnemon_list_tenants`

> **Description:** List active PostgreSQL database tenants, clusters, and copy-on-write branches with replication and fork telemetry.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ❌ No | - | Optional tenant filter |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_list_tenants",
    "arguments": {
      "tenant_id": "org_production"
    }
  },
  "id": 25
}
```

---

### 26. `mnemon_create_branch`

> **Description:** Fork an instant copy-on-write PostgreSQL database branch in  at an exact WAL LSN without storage duplication.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant/cluster identifier |
| `new_branch` | `string` | ✅ Yes | - | Name for the new branch (e.g. 'feature-migration') |
| `parent_branch` | `string` | ❌ No | - | Parent branch name (default: 'main') |
| `mask_pii` | `boolean` | ❌ No | `false` | Mask sensitive PII fields (emails, names, phones) with deterministic SHA-256 hashes |
| `target_lsn` | `number` | ❌ No | - | Optional WAL LSN for point-in-time fork |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_create_branch",
    "arguments": {
      "tenant_id": "org_production",
      "new_branch": "preview_experiment_branch",
      "parent_branch": "preview_experiment_branch",
      "target_lsn": 100
    }
  },
  "id": 26
}
```

---

### 27. `mnemon_promote_branch`

> **Description:** Promote a preview/ephemeral database branch to primary production root with atomic zero-downtime pointer swap.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `branch_id` | `string` | ✅ Yes | - | Branch ID to promote to primary root |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_promote_branch",
    "arguments": {
      "tenant_id": "org_production",
      "branch_id": "preview_experiment_branch"
    }
  },
  "id": 27
}
```

---

### 28. `mnemon_reset_branch`

> **Description:** Reset an ephemeral database branch back to its parent snapshot in <50ms, wiping all test mutations.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `branch_id` | `string` | ✅ Yes | - | Branch ID to reset |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_reset_branch",
    "arguments": {
      "tenant_id": "org_production",
      "branch_id": "preview_experiment_branch"
    }
  },
  "id": 28
}
```

---

### 29. `mnemon_diff_branch`

> **Description:** Inspect SQL DDL schema diff and migration script between a branch and its parent.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `branch_id` | `string` | ✅ Yes | - | Branch ID to diff |
| `parent_branch` | `string` | ❌ No | - | Parent branch (default: 'main') |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_diff_branch",
    "arguments": {
      "tenant_id": "org_production",
      "branch_id": "preview_experiment_branch",
      "parent_branch": "preview_experiment_branch"
    }
  },
  "id": 29
}
```

---

### 30. `mnemon_execute_sql`

> **Description:** Execute raw SQL query directly on a tenant database cluster or branch.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `query` | `string` | ✅ Yes | - | SQL query statement to execute |
| `as_of_lsn` | `string` | ❌ No | - | Optional historical WAL LSN for inline point-in-time time-travel query |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_execute_sql",
    "arguments": {
      "tenant_id": "org_production",
      "query": "sample_query"
    }
  },
  "id": 30
}
```

---

### 31. `mnemon_get_schema`

> **Description:** Introspect database schema tables, column types, and primary key constraints.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_get_schema",
    "arguments": {
      "tenant_id": "org_production"
    }
  },
  "id": 31
}
```

---

### 32. `mnemon_configure_scaling`

> **Description:** Configure Aurora Serverless v2 / Neon ACU scaling limits (min ACU, max ACU, scale-to-zero timeout).

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `min_acu` | `number` | ❌ No | - | Minimum ACU capacity (e.g. 0.0 for scale-to-zero) |
| `max_acu` | `number` | ❌ No | - | Maximum ACU capacity (e.g. 16.0 or 128.0) |
| `idle_timeout_sec` | `number` | ❌ No | - | Inactivity seconds before scaling to zero (default: 300) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_configure_scaling",
    "arguments": {
      "tenant_id": "org_production",
      "min_acu": 100,
      "max_acu": 100,
      "idle_timeout_sec": 10000
    }
  },
  "id": 32
}
```

---

### 33. `mnemon_configure_pooler`

> **Description:** Inspect or configure PgBouncer connection pooling mode and max connection limits.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `pool_mode` | `string` | ❌ No | - | Pooling mode (Enum: `[transaction, session]`) |
| `max_pool_size` | `number` | ❌ No | - | Maximum pooled backend connections |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_configure_pooler",
    "arguments": {
      "tenant_id": "org_production",
      "pool_mode": "transaction",
      "max_pool_size": 100
    }
  },
  "id": 33
}
```

---

### 34. `mnemon_manage_extensions`

> **Description:** Manage 1-click PostgreSQL extensions (vector, pg_search, postgis, uuid-ossp).

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `action` | `string` | ✅ Yes | - | Action to perform (Enum: `[list, enable, disable]`) |
| `name` | `string` | ❌ No | - | Extension name (for enable/disable) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_manage_extensions",
    "arguments": {
      "tenant_id": "org_production",
      "action": "list",
      "name": "sample_name"
    }
  },
  "id": 34
}
```

---

### 35. `mnemon_get_slow_queries`

> **Description:** Inspect slow query execution diagnostics, call frequencies, and buffer cache hit rates.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_get_slow_queries",
    "arguments": {
      "tenant_id": "org_production"
    }
  },
  "id": 35
}
```

---

### 36. `mnemon_clone_vector`

> **Description:** Sub-35ms pgvector HNSW index clone: Duplicates vector index graphs across branches using XFS/Btrfs zero-copy reflink extents.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `project_id` | `string` | ✅ Yes | - | Mnemon project / tenant ID |
| `branch` | `string` | ✅ Yes | - | Branch name to clone index from |
| `index_name` | `string` | ✅ Yes | - | pgvector HNSW index name |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_clone_vector",
    "arguments": {
      "project_id": "sample_project_id",
      "branch": "preview_experiment_branch",
      "index_name": "sample_index_name"
    }
  },
  "id": 36
}
```

---

### 37. `mnemon_autofreeze_policy`

> **Description:** Configure automatic zero-CPU instance freezing via cgroups v2 (cgroup.freeze) while keeping PostgreSQL shared buffer pool in RAM.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `project_id` | `string` | ✅ Yes | - | Mnemon project / tenant ID |
| `idle_timeout_seconds` | `number` | ❌ No | - | Inactivity seconds before auto-freezing (default: 30) |
| `preserve_buffer_pool` | `boolean` | ❌ No | - | Preserve shared buffers in RAM (default: true) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_autofreeze_policy",
    "arguments": {
      "project_id": "sample_project_id",
      "idle_timeout_seconds": 10000,
      "preserve_buffer_pool": true
    }
  },
  "id": 37
}
```

---

### 38. `mnemon_wal_rewind`

> **Description:**  Point-in-Time Recovery & WAL rewind: forks an isolated zero-copy CoW PostgreSQL branch from an arbitrary historical timestamp or LSN.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ❌ No | - | Optional sandbox ID to rewind |
| `project_id` | `string` | ❌ No | - | Optional project ID |
| `target_time` | `string` | ❌ No | - | Target ISO-8601 UTC timestamp to rewind to |
| `target_lsn` | `string` | ❌ No | - | Target PostgreSQL WAL LSN position |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "mnemon_wal_rewind",
    "arguments": {
      "sandbox_id": "sbx-kvm-9f82d1",
      "project_id": "sample_project_id",
      "target_time": "sample_target_time",
      "target_lsn": "sample_target_lsn"
    }
  },
  "id": 38
}
```

---

## ESCHATON & NEPHIS • Autonomous Polyglot Code Execution & Fast-Batch

Contains **3 production tools** specifically designed for agent autonomy.

### 39. `eschaton_preflight_check`

> **Description:** In-memory AST syntax and hazard detection (): Detects infinite loops, fork bombs, and banned syscalls before microVM dispatch.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `code` | `string` | ✅ Yes | - | Source code to analyze |
| `language` | `string` | ✅ Yes | - | Programming language (python, javascript, c, cpp, bash, go) |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "eschaton_preflight_check",
    "arguments": {
      "code": "print('Executed safely via Nephis')",
      "language": "sample_language"
    }
  },
  "id": 39
}
```

---

### 40. `nephis_fast_batch`

> **Description:** 50-Testcase Parallel Fast-Batch: Dispatches up to 50 testcases in a single HTTP request to evaluate concurrently in low-latency parallel memory.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `language_id` | `number` | ❌ No | `54` | Language ID (e.g. 54 for Python, 63 for JavaScript, 71 for Python 3) |
| `source_code` | `string` | ✅ Yes | - | Source code to evaluate against tests |
| `tests` | `array` | ❌ No | - | List of up to 50 testcases with stdin and expected_output |
| `submissions` | `array` | ❌ No | - | Alternative batch submissions format for backward compatibility |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "nephis_fast_batch",
    "arguments": {
      "language_id": 100,
      "source_code": "print('Executed safely via Nephis')",
      "tests": [
        "item_1",
        "item_2"
      ],
      "submissions": [
        "item_1",
        "item_2"
      ]
    }
  },
  "id": 40
}
```

---

### 41. `eschaton_fast_batch`

> **Description:** Parallel early-exit batch matrix execution: Runs test matrices across submissions concurrently with sub-millisecond short-circuiting on failure.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `language_id` | `number` | ❌ No | `54` |  |
| `source_code` | `string` | ❌ No | - |  |
| `tests` | `array` | ❌ No | - |  |
| `submissions` | `array` | ❌ No | - | List of code submissions to evaluate |

**Sample JSON-RPC Invocation:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "eschaton_fast_batch",
    "arguments": {
      "language_id": 100,
      "source_code": "print('Executed safely via Nephis')",
      "tests": [
        "item_1",
        "item_2"
      ],
      "submissions": [
        "item_1",
        "item_2"
      ]
    }
  },
  "id": 41
}
```

---

### 42. `mnemon_merge_branch`

> **Description:** Fast-forward merge schema migrations from a branch back to parent trunk in <200ms. Verifies non-divergence and applies migrations without table locks or cluster restarts.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `tenant_id` | `string` | ✅ Yes | - | Database tenant identifier |
| `branch_id` | `string` | ✅ Yes | - | Branch identifier to merge |
| `parent_branch` | `string` | ❌ No | `"main"` | Target parent branch |

---

### 43. `thanaton_list_golden_amis`

> **Description:** List available pre-baked Golden AMI runtimes (`node22`, `python312`, `golang122`, `nextjs`) with pre-installed language toolchains and common packages. Eliminates cold package installation delays.

---

### 44. `thanaton_create_ram_snapshot`

> **Description:** Capture running guest RAM state directly to high-speed POSIX shared memory (`/dev/shm`) in ~14.5ms. Allows sub-12ms speculative branch spawning without hypervisor determinism overhead.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | Target sandbox ID |
| `warm_packages` | `array` | ❌ No | `[]` | List of pre-imported packages to register in memory snapshot |

---

### 45. `thanaton_restore_ram_snapshot`

> **Description:** Restore a guest microVM memory state from a pre-warmed RAM snapshot in 11.8ms.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `snapshot_id` | `string` | ✅ Yes | - | Snapshot ID to restore |
| `sandbox_id` | `string` | ❌ No | `"default"` | Target sandbox ID to hydrate |

---

### 46. `thanaton_secret_shield_status`

> **Description:** Inspect or configure the eBPF kernel TAP outbound secret exfiltration firewall. Drops unauthorized credential leaks (OpenAI, Anthropic, AWS, JWT) in kernel space.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | Target sandbox ID |
| `action` | `string` | ❌ No | `"get"` | Action to perform (`get`, `enable`, `disable`) |

---

### 47. `thanaton_capture_browser_display`

> **Description:** Capture real-time screenshot or CDP stream frame from a guest headless browser canvas via virtual framebuffer (`/dev/fb0`) or Chrome DevTools Protocol.

**Parameter Specification:**

| Parameter | Type | Required | Default | Details & Constraints |
| :--- | :--- | :---: | :---: | :--- |
| `sandbox_id` | `string` | ✅ Yes | - | Target sandbox ID |
| `format` | `string` | ❌ No | `"jpeg"` | Image format (`jpeg`, `png`, `webp`) |
| `quality` | `number` | ❌ No | `80` | Compression quality (1-100) |

## 💻 Developer SDKs & Native Command-Line Tools (CLI)

Beyond the Model Context Protocol (MCP) JSON-RPC transport, NEPHIS provides first-class native command-line interfaces and client SDKs for automated terminal scripting, CI/CD test automation, and full-stack application development.

### 1. Thanaton MicroVM CLI (`thanaton`)
Available as a zero-dependency CLI wrapper (`sdk/cli/thanaton.bat` on Windows or `thanaton` on Linux):

```bash
# Provision a low-latency hardware KVM MicroVM (512MB RAM, attached Postgres DB)
thanaton up --runtime microvm --memory-mb 512 --db

# Execute arbitrary bash / terminal commands inside the isolated sandbox
thanaton exec sbx-kvm-9f82d1 -- npm test

# Query pre-baked Golden AMI runtimes (node22, python312, golang122, nextjs)
thanaton goldenami

# Capture running guest RAM state directly to /dev/shm in ~14ms
thanaton ramsnap create sbx-kvm-9f82d1 --warm-packages next,react

# Enable eBPF kernel TAP outbound secret exfiltration firewall
thanaton shield sbx-kvm-9f82d1 enable

# Capture live headless browser canvas frame (screenshot)
thanaton display sbx-kvm-9f82d1 --out screenshot.jpg

# Put sandbox into compressed stasis (Scale-to-Zero, $0 RAM burn)
thanaton sleep sbx-kvm-9f82d1

# Instant hardware cold-wake from stasis (low-latency)
thanaton wake sbx-kvm-9f82d1

# Expose a local MicroVM port for live browser preview (e.g. Next.js on port 3000)
thanaton ports expose sbx-kvm-9f82d1 --port 3000
```

### 2. Mnemon-DB Serverless PostgreSQL CLI (`mnemon`)
Available as a native CLI tool (`sdk/cli/mnemon.bat` on Windows or `mnemon` on Linux):

```bash
# Instant zero-copy snapshot branch creation via Linux XFS reflink blocks (<)
mnemon branch prod-db staging --parent main

# Fork a sanitized branch with automated PII masking (emails, names, phones)
mnemon branch prod-db safe-eval --parent main --mask-pii

# Execute raw SQL directly against the branch (supports inline AS OF LSN time-travel)
mnemon sql prod-db "SELECT * FROM balances WHERE id = 1;" --as-of-lsn 0/16B3740

# Fast-forward merge schema migrations from a branch back to parent trunk in <200ms
mnemon merge prod-db feat-auth-migration --parent main

# Structural schema and data delta comparison between branches
mnemon diff prod-db --branch staging --target main

# Point-in-Time WAL rewind to an exact PostgreSQL Log Sequence Number (LSN)
mnemon pitr restore prod-db --target-lsn 0/16B38D8

# Promote verified staging branch to production zero-downtime
mnemon promote prod-db staging --target main
```

### 3. Eschaton Code Execution CLI (`eschatonctl`)
High-throughput compiler and parallel testcase runner (`scripts/eschatonctl.py`):

```bash
# Single execution with instant in-memory microkernel (<3.4ms)
eschatonctl run solution.cpp --lang 54 --stdin input.txt

# Run 50 parallel testcases simultaneously in measured latency (Apex Fan-Out)
eschatonctl batch --source solution.cpp --testcases ./tests/ --parallel 50

# Ultra-fast (12µs) in-memory AST hazard detection (fork bombs, infinite loops)
eschatonctl preflight untrusted_script.py
```

### 4. Official Python SDK (`nephis-sdk`)

```python
from nephis import NephisClient

# Authenticate with your API key or rely on auto-bootstrapped credentials
client = NephisClient(api_key="mrd_live_...")

# 1. Thanaton: Spawn a low-latency MicroVM
sandbox = client.thanaton.spawn(runtime="microvm", memory_mb=512)
result = sandbox.exec("python3 -c 'print(42)'")
print(result.stdout)  # 42
sandbox.sleep()  # Scale-to-zero stasis ($0 ongoing cost)

# 2. Mnemon-DB: Zero-copy PostgreSQL 16 branch
branch = client.mnemon.create_branch("ai-agent-staging", parent="main")
db_rows = branch.query("SELECT id, email FROM tenants LIMIT 5;")

# 3. Eschaton: Judge0-compatible batch code execution
run = client.eschaton.execute(
    language_id=54,  # C++
    source_code='#include <iostream>\nint main() { std::cout << "Done"; return 0; }'
)
print(f"Executed in {run.time}s with memory {run.memory}KB")
```

### 5. Official Node.js / TypeScript SDK (`@nephis/sdk`)

```typescript
import { NephisClient } from '@nephis/sdk';

const nephis = new NephisClient({
  apiKey: process.env.NEPHIS_API_KEY,
  baseUrl: 'https://nephis.theeducode.com',
});

// Launch an isolated microVM and execute command
const sbx = await nephis.thanaton.spawnSandbox({ runtime: 'microvm', memoryMb: 1024 });
const exec = await nephis.thanaton.execCommand(sbx.id, 'uname -a');
console.log('Sandbox Kernel:', exec.stdout);

// Create zero-copy database branch
const branch = await nephis.mnemon.createBranch({
  branchName: 'pr-142',
  parentBranch: 'main'
});
console.log('Branch Ready:', branch.connection_string);
```

## 👤 Creator & Engineering Attribution

* **Creator & Principal Systems Architect:** Mohit Raj Deo
* **Portfolio & Personal Site:** [https://mohitrajdeo.in](https://mohitrajdeo.in)
* **GitHub:** [https://github.com/mohitrajdeo](https://github.com/mohitrajdeo)
* **LinkedIn:** [https://www.linkedin.com/in/mohitrajdeo/](https://www.linkedin.com/in/mohitrajdeo/)
* **Contact:** [mohit@mohitrajdeo.in](mailto:mohit@mohitrajdeo.in)
* **Organization:** NEPHIS / Eduniketan Private Limited
