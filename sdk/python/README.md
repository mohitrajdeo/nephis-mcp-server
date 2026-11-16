# NEPHIS Python SDK (`nephis` / `thanaton`)

> **Official Python SDK for the NEPHIS Systems Fabric & Sovereign Substrates.**  
> Sub-6ms Hardware-Isolated MicroVM Sandboxes, 30ms Zero-Copy PostgreSQL Branching, and Sub-38ms Bare-Metal Code Execution for Autonomous AI Agents.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0%20(urllib%20std)-green)](thanaton/client.py)
[![PyPI version](https://img.shields.io/badge/PyPI-nephis-orange.svg)](https://pypi.org/project/nephis/)

---

## ⚡ Architecture & Substrates

* **Canonical Gateway:** `https://nephis.theeducode.com`
* **Zero Human Signup:** `curl -s -X POST https://nephis.theeducode.com/v1/claim` (500 free execution credits granted instantly)
* **Zero Third-Party Dependencies:** Built on pure Python standard library (`urllib.request`, `json`, `os`, `sys`). Zero bloat, zero dependency conflicts.

```
┌────────────────────────────────────────────────────────┐
│ Autonomous AI Coding Agent / Python Application        │
└───────────────────────────┬────────────────────────────┘
                            │ Python SDK (REST / Unix Socket)
                            ▼
┌────────────────────────────────────────────────────────┐
│ NEPHIS Gateway (https://nephis.theeducode.com)         │
└───────┬───────────────────┬───────────────────┬────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   THANATON   │    │  MNEMON-DB   │    │   ESCHATON   │
│ KVM MicroVMs │    │  Zero-Copy   │    │ Sub-38ms AST │
│ 4.82ms Boot  │    │  PostgreSQL  │    │ Polyglot CI  │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 📦 Installation

```bash
pip install nephis
```

Or install locally from source:
```bash
git clone https://github.com/mohitrajdeo/testing-judge0-vm.git
cd testing-judge0-vm/sdk/python
pip install -e .
```

---

## 🚀 Quickstart

### 1. Unified Master Client (`Nephis`)
```python
from nephis import Nephis

# Initialize with API key (or set NEPHIS_API_KEY environment variable)
client = Nephis(api_key="mrd_live_YOUR_KEY", base_url="https://nephis.theeducode.com")

# 1. Evaluate code in sub-38ms across 50 testcases with AST preflight protection
run = client.execute(
    language="python",
    code="print(sum(i for i in range(1000000)))"
)
print(run.stdout)          # "499999500000"
print(f"Latency: {run.duration_ms}ms")  # 38.2ms

# 2. Boot a hardware-isolated Linux MicroVM sandbox in 4.82ms
sandbox = client.sandboxes.create(memory_mb=256, runtime="microvm")
res = sandbox.exec("uname -a && cat /etc/os-release")
print(res.stdout)
sandbox.destroy()

# 3. Branch an ephemeral PostgreSQL 16 database in 30ms (0 bytes initial storage)
branch = client.db.branch(parent="main", name="agent-migration-preview")
rows = branch.query("SELECT 1 AS status, NOW() AS ts;")
print(rows)
branch.destroy()
```

---

### 2. MicroVM Sandbox Management (`thanaton.Client`)
```python
import thanaton

client = thanaton.Client(
    base_url="https://nephis.theeducode.com",
    api_key="mrd_live_YOUR_KEY"
)

# 1. Ephemeral standalone code run (microVM auto-destroyed after execution)
result = client.run_code(
    code="import math; print(math.sqrt(1764))",
    language="python"
)
print(result.stdout)       # "42.0"
print(f"Execution time: {result.duration_ms}ms")

# 2. Context manager with embedded PostgreSQL 16
with client.sandboxes.create(runtime="microvm", memory_mb=512, with_db=True) as sbx:
    print(f"Spawned MicroVM: {sbx.id} (Booted in {sbx.boot_duration_ms:.2f}ms)")
    print(f"Embedded Postgres URL: {sbx.db_url}")

    # Run bash commands with full root capabilities
    out = sbx.exec("pip install -q requests")
    print(out.stdout)

    # Run queries directly against the bundled database
    sbx.sql("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);")
    sbx.sql("INSERT INTO users (name) VALUES ('Alice'), ('Bob');")
    data = sbx.sql("SELECT * FROM users;")
    print("Database Rows:", data)

    # Scale to zero stasis: hibernates RAM to NVMe (0% CPU, $0 idle RAM cost)
    sbx.sleep()
    print("State:", sbx.state)  # "sleeping"

    # Instant wake (<6ms)
    sbx.wake()
    print("State:", sbx.state)  # "running"
```

---

### 3. Serverless PostgreSQL 16 Zero-Copy Branching (`MnemonClient`)
```python
from nephis import MnemonClient

client = MnemonClient(
    api_url="https://nephis.theeducode.com",
    api_key="mrd_live_YOUR_KEY"
)

# 1. Fork production database in 30ms via XFS reflink CoW (0 bytes initial storage)
branch = client.branch_database(
    tenant_id="org_prod",
    new_branch="experiment_v2",
    parent_branch="main"
)
print("Branch DB Connection String:", branch["connection_string"])

# 2. Run DDL schema changes or queries
client.execute_sql(
    tenant_id="org_prod",
    branch="experiment_v2",
    sql="ALTER TABLE users ADD COLUMN embedding vector(3);"
)

# 3. Inspect schema diff between branch and main
diff = client.schema_diff("org_prod", "experiment_v2")
print("Migration DDL:", diff.get("migration_ddl"))

# 4. Instant rollback (<50ms) back to parent state
client.reset_branch("org_prod", "experiment_v2")

# 5. Point-in-Time Recovery (PITR) to exact historical timestamp
pitr = client.time_travel(
    tenant_id="org_prod",
    new_branch="audit_snapshot",
    target_time="2026-11-15T10:00:00Z"
)
print("PITR DB URL:", pitr["connection_string"])

# 6. Product Quantization (PQ) on pgvector embeddings (75-95% memory reduction)
quant = client.quantize_vectors(
    tenant_id="org_prod",
    table="documents",
    column="embedding",
    quantization_type="PQ"
)
print("Vector Index Reduction:", quant)

# 7. Zero-Downtime Import from Neon / Supabase via continuous CDC cutover
migration = client.import_database(
    tenant_id="org_prod",
    source_url="postgres://user:pass@ep-cool.neon.tech/neondb?sslmode=require"
)
print("Migration Status:", migration)
```

---

### 4. Standalone Polyglot Code Judging & Parallel Evaluation (`EschatonClient`)

For applications that need high-throughput code execution, competitive programming evaluation, or Big-O complexity profiling without spawning full KVM microVMs:

```python
from eschaton import EschatonClient

judge = EschatonClient(
    base_url="https://compiler.theeducode.com",
    api_key="mrd_live_YOUR_KEY"  # Or set ESCHATON_API_KEY environment variable
)

# 1. Sub-38ms execution across 10 evaluation suites (Omni / Apex / Void)
res = judge.execute_suite(
    source_code="print('Hello from Eschaton!')",
    language_id=71,  # Python 3
    suite="Omni"
)
print(res["stdout"])  # "Hello from Eschaton!"
print(f"Latency: {res['time']}s")

# 2. 50-test parallel fanout in a single request (Apex engine)
batch = judge.batch_execute(
    source_code="""
import sys
for line in sys.stdin:
    print(int(line.strip()) * 2)
""",
    language_id=71,
    testcases=[
        {"input": "10\\n", "expected_output": "20\\n"},
        {"input": "25\\n", "expected_output": "50\\n"},
    ]
)
print(f"Batch Passed: {batch['passed']}/{batch['total']}")

# 3. Deterministic hardware instruction counting & Big-O complexity profiling
profile = judge.complexity_profile(
    source_code="""
def bubble_sort(arr):
    for i in range(len(arr)):
        for j in range(len(arr)-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
""",
    language_id=71,
    input_sizes=[10, 50, 100, 200]
)
print("Complexity Class:", profile.get("complexity_class"))  # O(N^2)

# 4. Ephemeral SQL database sandbox grading (PostgreSQL / MySQL)
db_eval = judge.dbms_eval(
    query="SELECT name, score FROM students WHERE score >= 90 ORDER BY score DESC;",
    schema_sql="""
CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(50), score INT);
INSERT INTO students VALUES (1, 'Alice', 95), (2, 'Bob', 82), (3, 'Charlie', 91);
""",
    dialect="postgres"
)
print("Query Results:", db_eval.get("rows"))
```

---

## ⚡ Transparent Credit Economics Rate Card

| Operation | Engine | Credit Cost | Cost in USD ($0.0002/CR) | Substrate Guarantee |
| :--- | :--- | :---: | :---: | :--- |
| `execute(code)` | Eschaton | **1.0 Credit** | $0.00020 | Sub-38ms bare-metal microkernel |
| `fast_batch(tests)` | Eschaton | **1.0 CR / test** | $0.00020 / test | Up to 50 parallel testcases |
| `sandboxes.create()` | Thanaton | **5.0 Credits** | $0.00100 | 4.82ms KVM cold boot |
| `sandbox.exec()` | Thanaton | **1.0 Credit** | $0.00020 | Interactive PTY shell command |
| `sandbox.sleep() / wake()` | Thanaton | **0.0 Credits** | **$0.00000** | Free scale-to-zero stasis ($0 idle RAM) |
| `db.branch()` | Mnemon | **2.0 Credits** | $0.00040 | 30ms XFS Reflink CoW fork |
| `db.query()` | Mnemon | **1.0 Credit** | $0.00020 | Direct PostgreSQL 16 execution |
| `db.quantize()` | Mnemon | **3.0 Credits** | $0.00060 | pgvector HNSW-PQ vector quantization |
| `db.import()` | Mnemon | **10.0 Credits** | $0.00200 | Zero-downtime Neon/Supabase live cutover |
| `db.reconcile()` | Mnemon | **1.0 Credit** | $0.00020 | 3-way schema conflict reconciliation |
| `claim()` | Gateway | **0.0 Credits** | **FREE** | Hashcash PoW bootstrap (+500 trial credits) |

---

## 🤖 AI Agent Framework Integrations

### CrewAI
```python
from crewai.tools import tool
from nephis import Nephis

client = Nephis(api_key="mrd_live_YOUR_KEY")

@tool("Nephis Hardware Code Executor")
def execute_untrusted_code(code: str, language: str = "python") -> str:
    """Execute untrusted code safely in sub-38ms with AST preflight sanitization."""
    result = client.execute(language=language, code=code)
    if result.exit_code == 0:
        return result.stdout
    return f"Execution Error (Exit {result.exit_code}):\n{result.stderr}"
```

### LangChain
```python
from langchain_core.tools import tool
from nephis import Nephis

client = Nephis(api_key="mrd_live_YOUR_KEY")

@tool
def nephis_code_sandbox(code: str) -> str:
    """Runs code in an isolated bare-metal microVM with zero host infection risk."""
    res = client.execute(language="python", code=code)
    return res.stdout or res.stderr
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NEPHIS_API_KEY` | Unified API Bearer Token | `""` (Use `POST /v1/claim` for 500 free credits) |
| `NEPHIS_BASE_URL` | Canonical Production Gateway | `https://nephis.theeducode.com` |
| `THANATON_API_URL` | Thanaton MicroVM Engine URL | `https://nephis.theeducode.com` |
| `MNEMON_MGMT_URL` | Mnemon-DB Management Endpoint | `https://nephis.theeducode.com` |

---

## 👤 Creator & Engineering Attribution

* **Creator & Principal Systems Architect:** Mohit Raj Deo
* **Portfolio & Personal Site:** [https://mohitrajdeo.in](https://mohitrajdeo.in)
* **GitHub:** [https://github.com/mohitrajdeo](https://github.com/mohitrajdeo)
* **LinkedIn:** [https://www.linkedin.com/in/mohitrajdeo/](https://www.linkedin.com/in/mohitrajdeo/)
* **Contact:** [mohit@mohitrajdeo.in](mailto:mohit@mohitrajdeo.in)
* **Organization:** NEPHIS
