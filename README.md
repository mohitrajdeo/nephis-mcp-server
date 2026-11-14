# NEPHIS MCP Server (`nephis-mcp-server`)

> **Model Context Protocol (MCP) Server for NEPHIS**  
> Sub-6ms KVM MicroVM Sandboxes, Zero-Copy Database Branching, and Execution Fabric for AI Coding Agents.

[![MCP Registry](https://img.shields.io/badge/MCP-Protocol%202024--11--05-purple.svg)](https://modelcontextprotocol.io/)
[![npm version](https://img.shields.io/npm/v/nephis-mcp-server.svg)](https://www.npmjs.com/package/nephis-mcp-server)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## ⚡ Architecture Overview

> **Canonical Production Gateway:** [https://nephis.theeducode.com](https://nephis.theeducode.com)  
> **Instant Self-Serve API Keys (10k Free Runs):** [https://nephis.theeducode.com/keys](https://nephis.theeducode.com/keys)  
> **Commercial Pricing Table:** [https://nephis.theeducode.com/pricing.html](https://nephis.theeducode.com/pricing.html)  
> **Quickstart Command:** `npx -y nephis-mcp-server`

The **NEPHIS MCP Server** connects LLMs and autonomous coding assistants (**Claude Desktop**, **Cursor**, **Windsurf**, and **Cline**) directly to NEPHIS's bare-metal MicroVM engine and the wider NEPHIS Systems Fabric:
- **Eschaton**: 74k RPS bare-metal online judge with 38ms parallel testcase fan-out.
- **Thanaton**: Sub-12ms hardware KVM microVMs with 10.4 GB/s Sabre restore and $0 idle RAM cost.
- **Mnemon-DB**: 31ms zero-copy PostgreSQL 16 + pgvector branching with 2.26 GB/s FastCDC.
- **Aletheia**: 1.09µs fuel-metered in-memory symbolic verifier (100% Free Apache 2.0).
- **Hyperion, Acheron, Lethe, Kronos**: On-premises kernel schedulers, zero-tax networks, CDC Parquet streaming, and deterministic hypervisors.

```
┌─────────────────────────────────┐
│ AI Coding Agent                 │
│ (Claude / Cursor / Windsurf)    │
└────────────────┬────────────────┘
                 │
                 │ JSON-RPC 2.0 (stdio / SSE)
                 ▼
┌─────────────────────────────────┐
│ Thanaton MCP Server             │
│ (@thanaton/mcp-server)          │
└────────────────┬────────────────┘
                 │
                 │ REST Control Plane (Port 8080 / mTLS)
                 ▼
┌─────────────────────────────────┐
│ Project Thanaton Engine (KVM)   │
│ ├── Firecracker MicroVMs        │ ──► Sub-6ms boot (<2ms with UFFD)
│ ├── Cgroups v2 Jailer           │ ──► Hardened hardware sandbox
│ ├── SSRF Firewall (iptables)    │ ──► Blocks 169.254.169.254 metadata
│ └── Scale-to-Zero Snapshotting  │ ──► Drops RAM to 0 MB when idle
└─────────────────────────────────┘
```

---

## 🛠️ Complete MCP Tool Catalog

The server exposes **7 production tools** over standard MCP JSON-RPC:

### 1. `thanaton_exec_command`
Executes an arbitrary bash or shell command inside an isolated MicroVM sandbox.

- **Parameters:**
  - `command` *(string, required)*: Shell command to execute (e.g. `npm test`, `git status`, `python3 script.py`).
  - `sandbox_id` *(string, optional)*: Target sandbox ID. If omitted, an ephemeral sandbox is created automatically.
  - `timeout_ms` *(number, optional)*: Maximum execution timeout in ms (default: `15000`).
- **Response Format:**
  ```json
  {
    "sandbox_id": "sbx_a1b2c3",
    "command": "python3 -c 'print(42)'",
    "stdout": "42\n",
    "stderr": "",
    "exit_code": 0,
    "duration_ms": 11.2
  }
  ```

---

### 2. `thanaton_run_code`
Directly compiles and runs standalone code snippets with Base64 encoding to prevent parameter injection or shell quoting failures.

- **Parameters:**
  - `language` *(string, required)*: One of `"python"`, `"javascript"`, `"typescript"`, `"go"`, `"rust"`, `"c"`, `"cpp"`, `"bash"`.
  - `code` *(string, required)*: The source code snippet to compile and execute.
  - `timeout_ms` *(number, optional)*: Execution timeout in ms (default: `10000`).
- **Response Format:**
  ```json
  {
    "language": "python",
    "stdout": "Result: 144\n",
    "stderr": "",
    "exit_code": 0,
    "execution_time_ms": 9.4
  }
  ```

---

### 3. `thanaton_spawn_sandbox`
Provisions a new hardware-isolated KVM MicroVM with customizable RAM, vCPU quota, and optional embedded PostgreSQL database.

- **Parameters:**
  - `runtime` *(string, optional)*: `"microvm"` (default) or `"silicon"`.
  - `memory_mb` *(number, optional)*: RAM allocation in MiB (default: `256`, max: `4096`).
  - `with_db` *(boolean, optional)*: Whether to bundle an embedded PostgreSQL instance (default: `false`).
- **Response Format:**
  ```json
  {
    "status": "success",
    "sandbox_id": "sbx_f8a92e",
    "runtime": "microvm",
    "state": "running",
    "boot_duration_ms": 5.82,
    "db_url": "postgresql://postgres:thanaton@172.16.2.2:5432/sbx_f8a92e"
  }
  ```

---

### 4. `thanaton_list_sandboxes`
Lists all active, sleeping, and managed MicroVM sandboxes across the current organization.

---

### 5. `thanaton_wake_sandbox`
Instantly wakes a hibernated MicroVM from an NVMe memory snapshot in sub-6ms (<2ms with Userfaultfd).

- **Parameters:**
  - `sandbox_id` *(string, required)*: ID of the sleeping sandbox to wake.

---

### 6. `thanaton_sleep_sandbox`
Scales a MicroVM to zero. Guest RAM is flushed to an NVMe golden memory snapshot; CPU usage drops to 0.00% and RAM allocation drops to 0 MB ($0 idle cost).

- **Parameters:**
  - `sandbox_id` *(string, required)*: ID of the sandbox to hibernate.

---

### 7. `thanaton_destroy_sandbox`
Terminates guest processes, deletes TAP network interfaces, unlinks cgroups, and frees all resources.

- **Parameters:**
  - `sandbox_id` *(string, required)*: ID of the sandbox to delete.

---

## 🚀 Client Configuration Guides

### 1. Claude Desktop Setup
Open your Claude configuration file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the `thanaton` server:

```json
{
  "mcpServers": {
    "thanaton": {
      "command": "node",
      "args": ["d:/MOHIT/testing-judge0-vm/mcp-server/dist/index.js"],
      "env": {
        "THANATON_API_URL": "http://127.0.0.1:8080",
        "THANATON_API_KEY": ""
      }
    }
  }
}
```

*Or run directly via NPX:*
```json
{
  "mcpServers": {
    "thanaton": {
      "command": "npx",
      "args": ["-y", "@thanaton/mcp-server"]
    }
  }
}
```

---

### 2. Cursor IDE Setup
In your workspace root, create or edit `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "thanaton": {
      "command": "node",
      "args": ["d:/MOHIT/testing-judge0-vm/mcp-server/dist/index.js"],
      "env": {
        "THANATON_API_URL": "http://127.0.0.1:8080"
      }
    }
  }
}
```

---

### 3. Cline / Roo-Code Setup
In VS Code `settings.json` under `cline.mcpServers`:

```json
{
  "cline.mcpServers": {
    "thanaton": {
      "command": "node",
      "args": ["d:/MOHIT/testing-judge0-vm/mcp-server/dist/index.js"]
    }
  }
}
```

---

### 4. Windsurf (Cascade) Setup
In `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "thanaton": {
      "command": "node",
      "args": ["d:/MOHIT/testing-judge0-vm/mcp-server/dist/index.js"]
    }
  }
}
```

---

## 🔒 Security & Sandboxing Guarantees

1. **Hardware KVM Boundary:** Every command runs inside a guest Linux kernel. Host memory and filesystem are completely inaccessible from the guest.
2. **SSRF & Cloud Metadata Firewall:** The network namespace blocks all egress to `169.254.169.254` (cloud metadata service) and link-local ranges, preventing IAM token theft.
3. **Pure Stdio Guard:** All internal logging is piped to `stderr`, guaranteeing standard output remains strictly formatted for JSON-RPC 2.0 frames.
4. **Base64 Code Escaping:** Scripts are Base64 encoded before execution, preventing shell injection or command substitution exploits.

---

## 🤖 Recommended System Prompt for AI Coding Agents

To ensure Claude or Cursor always uses Thanaton for running code, add this to your custom instructions:

```markdown
You have access to the Thanaton MCP Server tools (`thanaton_exec_command`, `thanaton_run_code`, `thanaton_spawn_sandbox`). 
Whenever executing untrusted code, testing bash scripts, running unit tests, or querying databases:
1. ALWAYS use `thanaton_run_code` or `thanaton_exec_command` instead of running directly on the local machine.
2. For multi-step tasks requiring dependencies or database state, spawn a dedicated sandbox using `thanaton_spawn_sandbox`.
3. Put dormant sandboxes to sleep with `thanaton_sleep_sandbox` to preserve resources.
```

---

## 📄 License

Apache-2.0 © Thanaton Architecture Team
