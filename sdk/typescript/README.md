# nephis (TypeScript / Node.js SDK)

> **Official TypeScript & Node.js SDK for the NEPHIS Systems Fabric.**  
> Low-latency Hardware-Isolated MicroVM Sandboxes, Zero-Copy PostgreSQL Branching, and Judge0-compatible Bare-Metal Code Execution for Autonomous AI Agents.

[![npm version](https://img.shields.io/npm/v/nephis.svg)](https://www.npmjs.com/package/nephis)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Type Definitions](https://img.shields.io/badge/TypeScript-Strict%20Types-blue)](src/types.ts)
[![Node Version](https://img.shields.io/badge/Node.js-18%2B-brightgreen.svg)](https://nodejs.org/)

---

## ⚡ Architecture & Features

* **Canonical Gateway:** `https://nephis.theeducode.com`
* **Zero-Friction Agent Auth:** `curl -s -X POST https://nephis.theeducode.com/v1/claim` (500 free execution credits granted in 200ms)
* **Zero Production Dependencies:** Uses Node.js 18+ native `fetch` and built-in `crypto`. Zero runtime dependency bloat.

| Feature / Metric | Standard Docker | E2B Sandbox | AWS Lambda | **NEPHIS MicroVM** |
| :--- | :---: | :---: | :---: | :---: |
| **Cold Start Latency** | 2,000ms – 10,000ms | 150ms – 400ms | 200ms – 1,500ms | ** (< 2ms with UFFD)** ⚡ |
| **Security Boundary** | Shared Linux Host Kernel | Container Sandbox | MicroVM (Firecracker) | **Hardware KVM + Cgroups v2 Jailer** 🔒 |
| **Scale-to-Zero ($0 Idle)**| ❌ Dormant RAM used | ❌ Billed per second | ✅ (Stateless only) | **✅ NVMe Memory Snapshot ($0 RAM)** 💾 |
| **Embedded PostgreSQL** | ❌ Manual setup | ❌ Extra container | ❌ None | **✅ Instant Bundled Postgres (10ms)** 🗄️ |
| **Execution Duration** | Uncapped | Capped (Timeout) | 15-minute Guillotine | **✅ UNLIMITED Background Execution** 🚀 |
| **Real Linux Kernel** | ❌ Shared namespace | ❌ Container | ❌ Restricted Lambda | **✅ Uncompressed Linux 6.1 LTS Kernel** 🐧 |

---

## 📦 Installation

```bash
npm install nephis
```

---

## 🚀 Quickstart

### 1. Ephemeral Code Execution (One-Liner)
```typescript
import { NephisClient } from "nephis";

const client = new NephisClient({
  apiKey: "mrd_live_YOUR_KEY",
  baseUrl: "https://nephis.theeducode.com"
});

const result = await client.runCode({
  language: "python",
  code: `
import math
print("Euler's number:", math.e)
  `,
});

console.log(result.stdout);                    // "Euler's number: 2.718281828459045"
console.log(`Exit Code: ${result.exitCode}`);   // 0
console.log(`Execution Latency: ${result.durationMs}ms`); // measured latency
```

---

### 2. Stateful MicroVM Sandbox with Embedded PostgreSQL 16
```typescript
import { NephisClient } from "nephis";

const client = new NephisClient();

// Provision a dedicated KVM microVM with embedded Postgres in single-digit ms
const sandbox = await client.sandboxes.create({
  runtime: "microvm",
  memoryMb: 512,
  withDb: true,
});

console.log(`Spawned Sandbox: ${sandbox.id} (Booted in ${sandbox.bootDurationMs}ms)`);
console.log(`Embedded Postgres URL: ${sandbox.dbUrl}`);

// 1. Run bash commands
const execRes = await sandbox.exec("npm init -y && npm install express");
console.log(execRes.stdout);

// 2. Run SQL queries against the isolated database
const rows = await sandbox.sql(`
  CREATE TABLE metrics (id SERIAL PRIMARY KEY, score FLOAT);
  INSERT INTO metrics (score) VALUES (0.994), (0.981);
  SELECT * FROM metrics;
`);
console.log("SQL Rows:", rows);

// 3. Scale to zero stasis: hibernates RAM to NVMe (0% CPU, $0 idle RAM cost)
await sandbox.sleep();
console.log("State:", sandbox.state); // "sleeping"

// 4. Instant wake (<6ms)
await sandbox.wake();
console.log("State:", sandbox.state); // "running"

// 5. Clean teardown
await sandbox.destroy();
```

---

### 3. Serverless PostgreSQL 16 Zero-Copy Branching (`MnemonClient`)
```typescript
import { MnemonClient } from "nephis";

const mnemon = new MnemonClient({
  apiKey: "mrd_live_YOUR_KEY",
  apiUrl: "https://nephis.theeducode.com",
});

// 1. Fork production database in via XFS reflink CoW
const branch = await mnemon.createBranch({
  tenantId: "org_prod",
  newBranch: "agent_preview_branch",
  parentBranch: "main",
});
console.log("Branch Connection String:", branch.connectionString);

// 2. Run DDL schema migration
await mnemon.executeSql({
  tenantId: "org_prod",
  branch: "agent_preview_branch",
  sql: "ALTER TABLE users ADD COLUMN embedding vector(3);",
});

// 3. Inspect schema diff between branch and main
const diff = await mnemon.getSchemaDiff("org_prod", "agent_preview_branch");
console.log("Migration DDL:", diff.migrationDdl);

// 4. Reset branch back to parent snapshot (<50ms)
await mnemon.resetBranch("org_prod", "agent_preview_branch");

// 5. Product Quantization (PQ) on pgvector embeddings (75-95% memory reduction)
const quant = await mnemon.quantizeVectors({
  tenantId: "org_prod",
  table: "documents",
  column: "embedding",
  quantizationType: "PQ",
});
console.log("Vector Quantization Result:", quant);

// 6. Zero-Downtime Database Migration from Neon/Supabase
const migration = await mnemon.importDatabase({
  tenantId: "org_prod",
  sourceUrl: "postgres://user:pass@ep-cool.neon.tech/neondb?sslmode=require",
});
console.log("Migration Status:", migration);
```

---

## ⚡ Transparent Credit Economics Rate Card

| Operation | Engine | Credit Cost | Cost in USD ($0.0002/CR) | Substrate Guarantee |
| :--- | :--- | :---: | :---: | :--- |
| `client.runCode()` | Eschaton | **1.0 Credit** | $0.00020 | Judge0-compatible bare-metal microkernel |
| `client.fastBatch()` | Eschaton | **1.0 CR / test** | $0.00020 / test | Up to 50 parallel testcases |
| `client.sandboxes.create()` | Thanaton | **5.0 Credits** | $0.00100 | 4.82ms KVM cold boot |
| `sandbox.exec()` | Thanaton | **1.0 Credit** | $0.00020 | Interactive PTY shell command |
| `sandbox.sleep() / wake()` | Thanaton | **0.0 Credits** | **$0.00000** | Free scale-to-zero stasis ($0 idle RAM) |
| `mnemon.createBranch()` | Mnemon | **2.0 Credits** | $0.00040 | XFS Reflink CoW fork |
| `mnemon.executeSql()` | Mnemon | **1.0 Credit** | $0.00020 | Direct PostgreSQL 16 execution |
| `mnemon.quantizeVectors()` | Mnemon | **3.0 Credits** | $0.00060 | pgvector HNSW-PQ vector quantization |
| `mnemon.importDatabase()` | Mnemon | **10.0 Credits** | $0.00200 | Zero-downtime Neon/Supabase live cutover |
| `mnemon.reconcileSchema()` | Mnemon | **1.0 Credit** | $0.00020 | 3-way schema conflict reconciliation |
| `claim()` | Gateway | **0.0 Credits** | **FREE** | Hashcash PoW bootstrap (+500 trial credits) |
```

---

### 4. Standalone Code Execution & Parallel Judging (`EschatonClient`)

For applications that need lightweight, high-throughput code execution or competitive programming grading without spinning up full KVM microVMs:

```typescript
import { EschatonClient } from "nephis";

const judge = new EschatonClient({
  baseUrl: "https://compiler.theeducode.com",
  apiKey: "mrd_live_YOUR_KEY", // Or set ESCHATON_API_KEY environment variable
});

// 1. Single execution across 10 evaluation suites (Omni / Apex / Void)
const res = await judge.executeSuite({
  sourceCode: "console.log('Hello from Eschaton TypeScript SDK!');",
  languageId: 63, // JavaScript (Node.js)
  suite: "Omni",
});
console.log(res.stdout); // "Hello from Eschaton TypeScript SDK!"
console.log(`Latency: ${res.time}s`);

// 2. 50-test parallel batch fanout in a single request (Apex engine)
const batch = await judge.batchExecute({
  sourceCode: `
    const fs = require('fs');
    const input = fs.readFileSync(0, 'utf-8').trim();
    console.log(Number(input) * 2);
  `,
  languageId: 63,
  testcases: [
    { input: "10\\n", expected_output: "20\\n" },
    { input: "25\\n", expected_output: "50\\n" },
  ],
});
console.log(`Batch Passed: ${batch.passed}/${batch.total}`);

// 3. Algorithmic complexity profiling (deterministic hardware instruction counting)
const profile = await judge.complexityProfile({
  sourceCode: `
    const n = parseInt(require('fs').readFileSync(0, 'utf-8'));
    let sum = 0;
    for (let i = 0; i < n; i++) sum += i;
    console.log(sum);
  `,
  languageId: 63,
  inputSizes: [100, 500, 1000],
});
console.log("Complexity Class:", profile.complexity_class); // O(N)

// 4. Ephemeral SQL database sandbox grading (PostgreSQL / MySQL)
const dbEval = await judge.dbmsEval({
  query: "SELECT name, score FROM students WHERE score >= 90 ORDER BY score DESC;",
  schemaSql: `
    CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(50), score INT);
    INSERT INTO students VALUES (1, 'Alice', 95), (2, 'Bob', 82), (3, 'Charlie', 91);
  `,
  dialect: "postgres",
});
console.log("Database Rows:", dbEval.rows);
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
