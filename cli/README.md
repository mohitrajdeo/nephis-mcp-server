# NEPHIS Unified CLI Manual & Command Reference (`nephisctl`)

> **Master Reference Manual for Autonomous AI Coding Agents & Human Developers.**  
> Native CLI tools for **Thanaton** (Hardware MicroVMs), **Eschaton** (low-latency Polyglot Judge), **Mnemon-DB** (Zero-Copy Postgres), and **Nephis** (Unified Gateway).

[![CLI Version](https://img.shields.io/badge/CLI-v2.4.0-blue.svg)](https://nephis.theeducode.com)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-brightgreen.svg)](#-3-step-quickstart-for-autonomous-ai-agents)
[![Status](https://img.shields.io/badge/Status-Production%20Live-brightgreen.svg)](https://nephis.theeducode.com)

---

## 📖 Linux-Standard In-Terminal `man` Manuals & Argument Help

Every CLI tool now adheres to strict Linux / POSIX manual conventions with built-in terminal manuals, explicit argument tables, default values, and copy-pasteable examples for AI coding agents:

* **In-Terminal Built-in Manuals (Runs everywhere without external `groff`):**
  ```bash
  thanaton man [command]        # e.g. thanaton man deploy, thanaton man up, thanaton man exec
  mnemon man [command]          # e.g. mnemon man branch, mnemon man sql, mnemon man cdc
  eschatonctl man [command]      # e.g. eschatonctl man run, eschatonctl man exec
  ```
* **POSIX System Man Pages (`man 1 ...`):**
  Standard troff/groff manual files located in `man/man1/thanaton.1`, `man/man1/mnemon.1`, and `man/man1/eschatonctl.1`.
* **Exhaustive AI Agent & Parameter Specification:**
  See the full parameter matrices and JSON schemas in [docs/cli_and_mcp_manual/AGENT_CLI_AND_MCP_MANUAL.md](../../docs/cli_and_mcp_manual/AGENT_CLI_AND_MCP_MANUAL.md).

---

## 🤖 3-Step Quickstart for Autonomous AI Agents

Follow these 3 exact steps to execute any code, deploy any container, or branch any PostgreSQL database:

### Step 1: Set Your API Key
Set your API key as an environment variable (or run `nephisctl login` to auto-claim 500 free credits via Hashcash PoW):

```powershell
# Windows PowerShell
$env:NEPHIS_API_KEY = "mrd_live_YOUR_KEY"

# Windows CMD
set NEPHIS_API_KEY=mrd_live_YOUR_KEY
```
```bash
# Linux / macOS Bash
export NEPHIS_API_KEY="mrd_live_YOUR_KEY"
```

> 💡 **Don't have a key?** Claim 500 free credits instantly with zero humans in the loop:  
> Run `python sdk/cli/nephisctl login` (solves Hashcash PoW challenge in <80ms) or visit [https://nephis.theeducode.com/claim](https://nephis.theeducode.com/claim).

---

### Step 2: Verify Your Identity & Credits
Confirm your credentials and check remaining compute credits:

```powershell
python sdk/cli/nephisctl whoami
```

**Expected Console Output:**
```
==================================================================
         NEPHIS UNIFIED IDENTITY & ACCOUNT QUOTAS
==================================================================
API Endpoint:      https://nephis.theeducode.com
Active Key Prefix: mrd_live_378cd1e
Tenant ID:         b7de0a5a-3e48-41eb-afc2-f62d5d4483b1
Organization:      org_mohitrajdeo
Account Tier:      FREE
Credits Remaining: 195 credits
Active Status:     ACTIVE
Expires In:        30 days
Rate Limit:        10 req/s
==================================================================
```

---

### Step 3: Run Your Task (Copy-Paste Recipes)

#### 🚀 Recipe A: Run Code Instantly (Judge0-compatible Polyglot Execution)
Execute scripts or inline code snippets across Python, JavaScript, TypeScript, Go, Rust, C++, Java:

```powershell
# Inline code string
python sdk/cli/nephisctl run "print('Hello from Nephis!')" --language python

# Run local file
python sdk/cli/nephisctl run solution.py

# With STDIN input
python sdk/cli/nephisctl run solution.cpp --stdin "10 20\n"
```

#### 💻 Recipe B: Boot a MicroVM Sandbox & Run Shell Commands
Launch an isolated hardware KVM Linux sandbox in <6ms:

```powershell
# 1. Boot a sandbox
python sdk/cli/thanaton up --runtime microvm --memory-mb 512

# 2. Execute bash command inside sandbox
python sdk/cli/thanaton exec sbx-101 -- uname -a

# 3. List active sandboxes
python sdk/cli/thanaton ps

# 4. Hibernate to scale-to-zero ($0 idle cost)
python sdk/cli/thanaton sleep sbx-101

# 5. Wake up in <6ms
python sdk/cli/thanaton wake sbx-101
```

#### 🗄️ Recipe C: Serverless PostgreSQL 16 Branching & Querying
Fork an isolated database branch in and run SQL:

```powershell
# 1. Check database identity & tier
python sdk/cli/mnemon whoami

# 2. Create instant zero-copy branch
python sdk/cli/mnemon branch prod_org feature_preview --parent main

# 3. Execute SQL query
python sdk/cli/mnemon sql prod_org "SELECT * FROM users LIMIT 5;"

# 4. Show schema differences
python sdk/cli/mnemon diff prod_org --branch feature_preview

# 5. Reset branch back to parent snapshot in <50ms
python sdk/cli/mnemon reset prod_org feature_preview
```

#### 🌐 Recipe D: Deploy a Full-Stack Web Application to Thanaton
Deploy any directory containing Node.js, Python FastAPI, or Go to Thanaton:

```powershell
# Deploy to Production root with automated SSL domain
python sdk/cli/thanaton deploy ./my-web-app --name "my-app" --port 5000 --prod

# Deploy to Staging Preview
python sdk/cli/thanaton deploy ./my-web-app --name "my-app" --port 5000 --preview
```

---

## ⚡ Architecture & CLI Suite Hierarchy

The NEPHIS CLI suite is organized into 4 cohesive tools:

```
                          ┌──────────────────────────┐
                          │ nephisctl (Unified CLI)  │
                          └─────────────┬────────────┘
         ┌──────────────────────┬───────┴──────────────┬──────────────────────┐
         ▼                      ▼                      ▼                      ▼
  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
  │   THANATON   │       │   ESCHATON   │       │  MNEMON-DB   │       │   SOVEREIGN  │
  │   MicroVM    │       │   Polyglot   │       │  Zero-Copy   │       │    FABRIC    │
  │   Compute    │       │ Online Judge │       │  PostgreSQL  │       │ Kernel Moats │
  └──────────────┘       └──────────────┘       └──────────────┘       └──────────────┘
```

| Command | Engine | Canonical Cloud URL | Primary Role |
| :--- | :--- | :--- | :--- |
| `nephisctl` | **Nephis Unified** | `https://nephis.theeducode.com` | Master control plane, account identity, credits, and universal routing |
| `thanaton` | **Thanaton MicroVM** | `https://thanaton.theeducode.com` | Hardware KVM sandboxes, web app deployments, scaling, custom domains |
| `mnemon` | **Mnemon-DB** | `https://mnemon.theeducode.com` | Serverless PostgreSQL 16, CoW branching, schema diffing, CDC |
| `eschatonctl` | **Eschaton Judge** | `https://eschaton.theeducode.com` | High-throughput polyglot compiler execution and 50-test fast-batching |

---

## 🔑 Single Source of Truth: Environment Variables

All tools respect a single, unified environment variable standard:

| Variable | Description | Default Fallback |
| :--- | :--- | :--- |
| `NEPHIS_API_KEY` | **Universal API Key** (works across all 4 CLIs) | `~/.nephis/credentials.json` |
| `NEPHIS_BASE_URL` | Nephis Gateway URL | `https://nephis.theeducode.com` |
| `THANATON_URL` | Thanaton Control Plane URL | `https://thanaton.theeducode.com` |
| `MNEMON_MGMT_URL` | Mnemon Management API URL | `https://mnemon.theeducode.com/api` |
| `ESCHATON_GATEWAY_URL`| Eschaton Judge Gateway URL | `https://eschaton.theeducode.com` |

---

## 🧭 Complete Command Reference

### 1. `nephisctl` Core Commands

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `nephisctl whoami` | Inspect active account identity, organization, tier, and quotas | `python sdk/cli/nephisctl whoami` |
| `nephisctl balance` | Quick check of remaining credits and expiration | `python sdk/cli/nephisctl balance` |
| `nephisctl login [key]` | Save API key or claim 500 free credits via Hashcash PoW | `python sdk/cli/nephisctl login` |
| `nephisctl status` | Check live operational health across all cloud engines | `python sdk/cli/nephisctl status` |
| `nephisctl run <code/file>` | Run standalone code in low-latency (Python, JS, Go, Rust, C++) | `python sdk/cli/nephisctl run "print('hi')"` |
| `nephisctl fast-batch` | Run up to 50 concurrent testcases in memory | `python sdk/cli/nephisctl fast-batch -f sol.py --tests-file tests.json` |
| `nephisctl up` | Provision a new microVM sandbox | `python sdk/cli/nephisctl up --runtime microvm --memory-mb 512` |
| `nephisctl exec <id> -- <cmd>`| Run command inside sandbox | `python sdk/cli/nephisctl exec sbx-101 -- ls -la` |
| `nephisctl sql <id> "<query>"`| Run SQL query on embedded database | `python sdk/cli/nephisctl sql sbx-101 "SELECT 1"` |
| `nephisctl ps` | List active microVM sandboxes | `python sdk/cli/nephisctl ps` |
| `nephisctl freeze <id>` | Freeze microVM to 0.00% vCPU stasis | `python sdk/cli/nephisctl freeze sbx-101` |
| `nephisctl resume <id>` | Resume frozen microVM in <6ms | `python sdk/cli/nephisctl resume sbx-101` |
| `nephisctl rm <id>` | Destroy microVM sandbox | `python sdk/cli/nephisctl rm sbx-101` |

---

### 2. `thanaton` MicroVM & Deployment Commands

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `thanaton whoami` | Display Thanaton identity, tier, and project quotas | `python sdk/cli/thanaton whoami` |
| `thanaton balance` | Display compute credits and wallet status | `python sdk/cli/thanaton balance` |
| `thanaton deploy <dir>` | Deploy web app to Thanaton Fabric | `python sdk/cli/thanaton deploy ./app --name "app" --port 3000` |
| `thanaton up` | Boot microVM sandbox | `python sdk/cli/thanaton up --memory-mb 512` |
| `thanaton exec <id> -- <cmd>`| Execute command inside microVM | `python sdk/cli/thanaton exec sbx-101 -- pytest` |
| `thanaton ps` | List active and sleeping sandboxes | `python sdk/cli/thanaton ps` |
| `thanaton sleep <id>` | Scale sandbox to zero | `python sdk/cli/thanaton sleep sbx-101` |
| `thanaton wake <id>` | Wake sandbox in <6ms | `python sdk/cli/thanaton wake sbx-101` |
| `thanaton rm <id>` | Terminate sandbox | `python sdk/cli/thanaton rm sbx-101` |
| `thanaton projects list` | List deployed web projects | `python sdk/cli/thanaton projects list` |
| `thanaton domains add <proj>`| Attach custom domain with SSL | `python sdk/cli/thanaton domains add my-proj api.example.com` |

---

### 3. `mnemon` PostgreSQL Commands

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `mnemon whoami` | Display database tenant identity and limits | `python sdk/cli/mnemon whoami` |
| `mnemon list` | List all database tenants | `python sdk/cli/mnemon list` |
| `mnemon create <name>` | Provision a new PostgreSQL 16 tenant | `python sdk/cli/mnemon create my_db` |
| `mnemon branch <db> <name>`| Instant zero-copy database fork | `python sdk/cli/mnemon branch my_db preview_branch` |
| `mnemon branches <db>` | List all branches across cluster | `python sdk/cli/mnemon branches my_db` |
| `mnemon sql <db> "<query>"`| Execute SQL query on database | `python sdk/cli/mnemon sql my_db "SELECT 1;"` |
| `mnemon diff <db> --branch <b>`| Schema DDL diff between branch and parent | `python sdk/cli/mnemon diff my_db --branch preview_branch` |
| `mnemon reset <db> <branch>`| Reset branch to parent snapshot in <50ms | `python sdk/cli/mnemon reset my_db preview_branch` |
| `mnemon quantize <set|stats> <db>`| HNSW-PQ vector quantization & disk indexing | `python sdk/cli/mnemon quantize set my_db --table docs --type PQ` |
| `mnemon import <start|cutover> <db>`| Zero-downtime database import from Neon/Supabase | `python sdk/cli/mnemon import start my_db --source-url "postgres://..."` |
| `mnemon reconcile <db> <branch>`| 3-way schema reconciliation before merge | `python sdk/cli/mnemon reconcile my_db preview_branch` |
| `mnemon advisor <db>` | Slow query telemetry, cache & index advisor | `python sdk/cli/mnemon advisor my_db --top 5` |
| `mnemon lineage <db>` | Visual DAG tree of branch ancestry and LSNs | `python sdk/cli/mnemon lineage my_db --format tree` |
| `mnemon pitr <timelines|restore> <db>`| Point-In-Time Recovery via WAL replay | `python sdk/cli/mnemon pitr restore my_db --target-lsn "0/16B38D8"` |
| `mnemon snapshot <create|restore>`| Manage point-in-time cluster snapshots | `python sdk/cli/mnemon snapshot create my_db` |
| `mnemon search <db> "<query>"`| ParadeDB BM25 + pgvector hybrid full-text search | `python sdk/cli/mnemon search my_db "agent memory" --hybrid` |
| `mnemon scale <get|set> <db>` | Aurora ACU scaling limits & suspend timeouts | `python sdk/cli/mnemon scale set my_db --min-acu 0.5 --max-acu 16` |
| `mnemon pooler <status|tune> <db>`| Dynamic PgBouncer connection pooler settings | `python sdk/cli/mnemon pooler tune my_db --max-connections 1000` |
| `mnemon ext <list|enable> <db>`| Enable/disable PostgreSQL extensions | `python sdk/cli/mnemon ext enable my_db --name vector` |
| `mnemon freeze <db>` | Suspend database to 0.0% CPU | `python sdk/cli/mnemon freeze my_db` |
| `mnemon resume <db>` | Wake database in <200µs | `python sdk/cli/mnemon resume my_db` |

---

### 4. `eschatonctl` Online Judge Commands

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `eschatonctl account` | Inspect remaining execution credits & tier | `python scripts/eschatonctl.py account` |
| `eschatonctl run <file>` | Submit local code file to judge (<4ms) | `python scripts/eschatonctl.py run solution.cpp` |
| `eschatonctl exec "<code...>"`| Submit inline code snippet to judge | `python scripts/eschatonctl.py exec "print(42)"` |
| `eschatonctl batch <file> <tests>`| Run up to 50 test cases concurrently in low-latency | `python scripts/eschatonctl.py batch sol.cpp tests.json` |
| `eschatonctl complexity <file>`| Instruction counting & empirical Big-O analyzer | `python scripts/eschatonctl.py complexity solution.cpp` |
| `eschatonctl sanitize <file>` | ASan + UBSan memory safety & leak detection | `python scripts/eschatonctl.py sanitize buffer_test.c` |
| `eschatonctl dbms "<sql>"` | Ephemeral in-memory SQL database sandbox | `python scripts/eschatonctl.py dbms "SELECT 1;" --engine postgres` |
| `eschatonctl fileio <file>` | Filesystem sandbox evaluation with named files | `python scripts/eschatonctl.py fileio sol.py --input-file "in.txt:10"` |
| `eschatonctl special-judge <f> <chk>`| Custom validator / checker program evaluation | `python scripts/eschatonctl.py special-judge sol.cpp chk.py` |
| `eschatonctl languages` | List 60+ supported compiler runtimes | `python scripts/eschatonctl.py languages` |
| `eschatonctl status` | Check health across 3 execution tiers | `python scripts/eschatonctl.py status` |
| `eschatonctl man [cmd]` | Built-in terminal Linux manuals | `python scripts/eschatonctl.py man batch` |

---

## ⚡ CLI Command Credit Cost & Rate Card

| CLI Command | Engine | Credit Cost | USD Cost ($0.0002/CR) | Execution Guarantee |
| :--- | :--- | :---: | :---: | :---: |
| `thanaton deploy <dir>` | Thanaton | **5.0 Credits** | $0.00100 | 4.82ms KVM cold boot |
| `thanaton exec <id> -- <cmd>` | Thanaton | **1.0 Credit** | $0.00020 | &lt; 8ms PTY shell command |
| `thanaton sleep / wake` | Thanaton | **0.0 Credits** | $0.00000 | Free scale-to-zero ($0 idle RAM) |
| `thanaton logs <id>` | Thanaton | **0.0 Credits** | $0.00000 | Free real-time stdout/stderr stream |
| `mnemon branch <db> <name>`| Mnemon-DB | **2.0 Credits** | $0.00040 | Reflink CoW fork |
| `mnemon sql <db> "<query>"`| Mnemon-DB | **1.0 Credit** | $0.00020 | &lt; 5ms direct PostgreSQL query |
| `mnemon diff <db> --branch`| Mnemon-DB | **1.0 Credit** | $0.00020 | Schema DDL diff generation |
| `mnemon reset <db> <branch>`| Mnemon-DB | **1.0 Credit** | $0.00020 | &lt; 35ms snapshot reset |
| `mnemon quantize <set\|stats>`| Mnemon-DB | **3.0 Credits** | $0.00060 | pgvector HNSW-PQ index build |
| `mnemon import <start\|cutover>`| Mnemon-DB | **10.0 Credits** | $0.00200 | Zero-downtime Neon/Supabase CDC migration |
| `mnemon reconcile <db> <br>`| Mnemon-DB | **1.0 Credit** | $0.00020 | 3-way schema reconciliation AST |
| `mnemon advisor <db>` | Mnemon-DB | **0.0 Credits** | $0.00000 | Free diagnostic telemetry & slow queries |
| `mnemon lineage <db>` | Mnemon-DB | **0.0 Credits** | $0.00000 | Free visual DAG lineage inspection |
| `mnemon pitr <timelines\|restore>`| Mnemon-DB | **2.0 Credits** | $0.00040 | Sub-35ms LSN rollback & WAL replay |
| `mnemon snapshot <create>` | Mnemon-DB | **2.0 Credits** | $0.00040 | Point-in-time database cluster snapshot |
| `mnemon search <db> "<query>"`| Mnemon-DB | **1.0 Credit** | $0.00020 | ParadeDB BM25 hybrid full-text search |
| `mnemon branches / tables / ext`| Mnemon-DB | **0.0 Credits** | $0.00000 | Free metadata catalog lookup |
| `eschatonctl run <file>` | Eschaton | **1.0 Credit** | $0.00020 | Sub-4ms microkernel code execution |
| `eschatonctl batch <file> <tests>`| Eschaton | **1.0 CR / test**| $0.00020 / test | Up to 50 parallel tests in &lt;low-latency |
| `eschatonctl complexity <file>`| Eschaton | **2.0 Credits** | $0.00040 | Instruction counting & Big-O analyzer |
| `eschatonctl sanitize <file>`| Eschaton | **2.0 Credits** | $0.00040 | ASan + UBSan memory safety & leaks |
| `eschatonctl dbms "<sql>"` | Eschaton | **2.0 Credits** | $0.00040 | In-memory ephemeral SQL database sandbox |
| `eschatonctl fileio <file>` | Eschaton | **1.0 Credit** | $0.00020 | Named file evaluation sandbox |
| `eschatonctl special-judge` | Eschaton | **2.0 Credits** | $0.00040 | Custom testlib validator execution |
| `nephisctl fast-batch` | Eschaton | **1.0 CR / test**| $0.00020 / test | Up to 50 parallel tests in &lt;40ms |
| `nephisctl whoami` | Core | **0.0 Credits** | $0.00000 | Instant quota introspection |

> 🤖 **Machine-Readable Flag (`--json`):**  
> Append `--json` to any command (e.g. `thanaton deploy ./app --json` or `mnemon branch prod feat --json`) to receive clean, unescaped JSON output directly into your agent's parser!

---

## 👤 Engineering Attribution & Contact

* **Creator & Principal Systems Architect:** Mohit Raj Deo
* **Portfolio & Personal Site:** [https://mohitrajdeo.in](https://mohitrajdeo.in)
* **GitHub:** [https://github.com/mohitrajdeo](https://github.com/mohitrajdeo)
* **LinkedIn:** [https://www.linkedin.com/in/mohitrajdeo/](https://www.linkedin.com/in/mohitrajdeo/)
* **Contact & Inquiries:** [mohit@mohitrajdeo.in](mailto:mohit@mohitrajdeo.in)
* **Organization:** NEPHIS
