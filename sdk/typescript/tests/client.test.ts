import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ThanatonClient, EschatonClient } from "../dist/index.js";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const API_KEY = process.env.NEPHIS_API_KEY || "mrd_live_63bb486dd0718806c08fb3ec9428cbd9dc8e7e88e20073f1";
const THANATON_URL = process.env.NEPHIS_BASE_URL || process.env.THANATON_API_URL || "https://nephis.theeducode.com";
const ESCHATON_URL = process.env.NEPHIS_API_URL || "https://nephis.theeducode.com";
const ANCHOR_PROJECT_ID = process.env.NEPHIS_ANCHOR_PROJECT || "3eb8d9e9-819f-47b1-89b3-5157b88570a8";

describe("Thanaton TypeScript SDK - Real Production Integration Tests", () => {
  const client = new ThanatonClient({ baseUrl: THANATON_URL, apiKey: API_KEY });

  it("should initialize client with default and custom options", () => {
    assert.equal(client.baseUrl, THANATON_URL);
    assert.equal(client.apiKey, API_KEY);
  });

  it("should list projects from Thanaton live control plane", async () => {
    const projects = await client.listProjects();
    assert.ok(Array.isArray(projects));
    assert.ok(projects.length > 0);
    const anchor = projects.find((p: any) => p.id === ANCHOR_PROJECT_ID);
    assert.ok(anchor, `Anchor project ${ANCHOR_PROJECT_ID} must exist`);
  });

  it("should retrieve billing wallet and real credits balance", async () => {
    const wallet = await client.getWallet();
    assert.equal(wallet.tier, "enterprise");
    assert.ok(wallet.credits_balance > 0);
    assert.equal(wallet.allow_custom_domains, true);
  });

  it("should manage SaaS project domains and crons", async () => {
    const testDomain = "test-live-verify-ts.theeducode.com";
    const domainRes = await client.addDomain(ANCHOR_PROJECT_ID, testDomain);
    assert.equal(domainRes.status, "success");
    await client.deleteDomain(ANCHOR_PROJECT_ID, testDomain);

    const cronRes = await client.addCron(ANCHOR_PROJECT_ID, "0 * * * *", "/api/ping");
    assert.equal(cronRes.status, "success");
    if (cronRes.id) {
      await client.deleteCron(ANCHOR_PROJECT_ID, cronRes.id);
    }
  });

  it("should execute code against Eschaton multi-suite engine", async () => {
    const res = await client.executeSuite({
      sourceCode: "print('Hello from Live Eschaton TS SDK')",
      languageId: 204,
      suite: "Omni",
    });

    assert.ok(res.Results && res.Results.length >= 1);
    assert.equal(res.Results[0].passed, true);
    assert.ok(res.Results[0].stdout.includes("Hello from Live Eschaton TS SDK"));
  });

  it("should profile algorithmic complexity via Valgrind lackey", async () => {
    const res = await client.complexityProfile({
      sourceCode: "int main() { return 0; }",
      languageId: 202,
      stdin: "100",
    });

    assert.ok(res.Results && res.Results.length >= 1);
    assert.equal(res.Results[0].passed, true);
    const instr = res.Results[0].instructions_executed || res.Results[0].time;
    assert.ok(Number(instr) > 1000);
  });

  it("should run memory safety checks via AddressSanitizer (ASan)", async () => {
    const res = await client.sanitizeCheck({
      sourceCode: "int main() { return 0; }",
      languageId: 202,
    });

    assert.ok(res.Results && res.Results.length >= 1);
    assert.ok(res.Results[0].passed === true || res.Results[0].stderr?.includes("ASan"));
  });

  it("should evaluate SQL queries with ephemeral schema in DBMS suite", async () => {
    const res = await client.dbmsEval({
      sourceCode: "SELECT * FROM users WHERE id = 1;",
      schemaSql: "CREATE TABLE users(id INT, name TEXT); INSERT INTO users VALUES (1, 'Alice');",
      database: "sqlite",
    });

    assert.ok(res.Results && res.Results.length >= 1);
    assert.equal(res.Results[0].passed, true);
    assert.ok(res.Results[0].stdout.includes("Alice"));
  });

  it("should evaluate FileIO sandboxed execution with custom files", async () => {
    const res = await client.fileioEval({
      sourceCode: "with open('in.txt') as f:\n    val = f.read().strip()\nwith open('out.txt', 'w') as f:\n    f.write(f'MATCHED_{val}')",
      inputFilename: "in.txt",
      inputContent: "TS_DATA_2026",
      outputFilename: "out.txt",
      expectedOutput: "MATCHED_TS_DATA_2026",
      languageId: 204,
    });

    assert.ok(res.Results && res.Results.length >= 1);
    assert.equal(res.Results[0].passed, true);
  });

  it("should evaluate custom checker binary in SpecialJudge suite", async () => {
    const res = await client.specialJudge({
      sourceCode: "#include <iostream>\nint main(){ std::cout << 3.14159; return 0; }",
      checkerCode: "#include <iostream>\nint main(){ return 0; }",
      languageId: 202,
      checkerLanguageId: 202,
    });

    assert.ok(res.Results && res.Results.length >= 1);
    assert.equal(res.Results[0].passed, true);
  });

  it("should evaluate multi-testcase batch in batchExecute", async () => {
    const res = await client.batchExecute({
      sourceCode: "import sys\nfor line in sys.stdin:\n    l = line.strip()\n    if l:\n        print(int(l) ** 2)",
      tests: [
        { id: 1, stdin: "4\n", expected_output: "16\n" },
        { id: 2, stdin: "9\n", expected_output: "81\n" },
      ],
      languageId: 204,
    });

    assert.equal(res.Results.length, 2);
    assert.ok(res.Results.every((r: any) => r.passed));
  });

  it("should execute code using standalone EschatonClient", async () => {
    const eschaton = new EschatonClient({ baseUrl: ESCHATON_URL, apiKey: API_KEY });
    const res = await eschaton.execute({
      sourceCode: "print('from standalone eschaton client')",
      languageId: 204,
    });

    assert.ok(res.Results && res.Results.length >= 1);
    assert.equal(res.Results[0].passed, true);
    assert.ok(res.Results[0].stdout.includes("from standalone eschaton client"));
  });

  it("should execute command inside live Thanaton Firecracker KVM microVM", async () => {
    const res: any = await client.request("POST", "/v1/sandboxes/run", {
      command: "echo 'NEPHIS_TS_MICROVM_HARDWARE_OK'",
    });
    assert.equal(res.engine, "thanaton-kvm");
    assert.equal(res.exit_code, 0);
    assert.ok(res.stdout.includes("NEPHIS_TS_MICROVM_HARDWARE_OK"));
    assert.ok(res.wall_time_ms < 100);
  });

  it("should expose, list, and release L4 raw TCP port on microVM", async () => {
    const exposed: any = await client.request("POST", `/v1/sandboxes/${ANCHOR_PROJECT_ID}/ports`, {
      guest_port: 5432,
    });
    assert.equal(exposed.guest_port, 5432);
    const hostPort = exposed.host_port;
    assert.ok(hostPort > 0);

    const listed: any = await client.request("GET", `/v1/sandboxes/${ANCHOR_PROJECT_ID}/ports`);
    assert.ok(listed.count >= 1);

    const released: any = await client.request("DELETE", `/v1/sandboxes/${ANCHOR_PROJECT_ID}/ports/${hostPort}`);
    assert.equal(released.status, "released");
  });

  it("should race multi-candidate speculative algorithmic branches", async () => {
    const race: any = await client.request("POST", "/api/v1/speculate/race", {
      project_id: ANCHOR_PROJECT_ID,
      candidates: [{ id: "ts_can_1", code: "console.log('TS_FAST')" }],
    });
    assert.ok(race.branches && race.branches.length >= 1);
    assert.equal(race.branches[0].committed, true);
  });

  it("should execute live PostgreSQL 16 SQL and zero-copy reflink branch in Mnemon", async () => {
    const tenantId = `ts_eval_${Date.now()}`;
    const mnemonDirect = "https://nephis.theeducode.com/v1/db";
    const reqHeaders = {
      "Content-Type": "application/json",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      "X-API-Key": API_KEY,
      Authorization: `Bearer ${API_KEY}`,
    };
    // Provision fresh tenant
    await fetch(`${mnemonDirect}/v1/tenants/provision`, {
      method: "POST",
      headers: reqHeaders,
      body: JSON.stringify({ tenant_id: tenantId, memory_mb: 256, vcpus: 1 }),
    });

    const sqlRes = await fetch(`${mnemonDirect}/v1/tenants/sql`, {
      method: "POST",
      headers: reqHeaders,
      body: JSON.stringify({ tenant_id: tenantId, query: "SELECT 99 as value;" }),
    });
    const sqlData: any = await sqlRes.json();
    assert.equal(sqlData.status, "success");
    assert.equal(sqlData.row_count, 1);
    assert.deepEqual(sqlData.rows, [{ value: 99 }]);

    const branchName = `ts_br_${Date.now()}`;
    const brRes = await fetch(`${mnemonDirect}/v1/tenants/branch`, {
      method: "POST",
      headers: reqHeaders,
      body: JSON.stringify({ tenant_id: tenantId, new_branch: branchName, parent_branch: "main" }),
    });
    const brData: any = await brRes.json();
    assert.equal(brData.branch_id, branchName);
    assert.ok(brData.port > 16000);
  });

  it("should manage persistent storage volumes on live microVM", async () => {
    const listRes: any = await client.request("GET", `/api/v1/sandboxes/volumes?sandbox_id=${ANCHOR_PROJECT_ID}`);
    assert.equal(listRes.sandbox_id, ANCHOR_PROJECT_ID);

    const attachRes: any = await client.request("POST", "/api/v1/sandboxes/volumes", {
      sandbox_id: ANCHOR_PROJECT_ID,
      mount_path: "/data/ts_live_test",
      size_gb: 5,
    });
    assert.ok(attachRes.message || attachRes.volume_id);
  });

  it("should inject runtime secrets into live microVM", async () => {
    const secRes: any = await client.request("POST", "/api/v1/sandboxes/secrets/inject", {
      sandbox_id: ANCHOR_PROJECT_ID,
      secrets: { TS_SDK_SECRET: "live_verified_2026" },
    });
    assert.ok(secRes.file_path || /injected/i.test(secRes.status || "") || secRes.message);
  });

  it("should execute live commands on multi-engine Redis and MongoDB substrates", async () => {
    const ts = Date.now();
    const redisTenant = `ts_rd_${ts}`;
    const mnemonHost = "https://nephis.theeducode.com/v1/db";
    const headers = {
      "Content-Type": "application/json",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      Authorization: `Bearer ${API_KEY}`,
      "X-API-Key": API_KEY,
    };

    // Redis execution on persistent tenant
    await fetch(`${mnemonHost}/v1/redis/tenants/query`, {
      method: "POST",
      headers,
      body: JSON.stringify({ tenant_id: "redis_master_lab", command: ["SET", "ts_token", "TS_REDIS_PASS"] }),
    });
    const rdGet = await fetch(`${mnemonHost}/v1/redis/tenants/query`, {
      method: "POST",
      headers,
      body: JSON.stringify({ tenant_id: "redis_master_lab", command: ["GET", "ts_token"] }),
    });
    const rdData: any = await rdGet.json();
    assert.equal(rdData.result, "TS_REDIS_PASS");

    // Mongo query on persistent tenant
    const mgQuery = await fetch(`${mnemonHost}/v1/mongodb/tenants/query`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        tenant_id: "cs_master_lab",
        query: "db.ts_bench.insertOne({language: 'TypeScript', status: 'verified'})",
      }),
    });
    const mgData: any = await mgQuery.json();
    assert.equal(mgData.status, "success");
  });

  it("should inspect and configure autoscaling parameters via client.getScaling", async () => {
    const scaling = await client.getScaling(ANCHOR_PROJECT_ID);
    assert.ok(scaling);
    assert.ok(typeof scaling === "object");
  });

  it("should list deployments for project via client.listDeployments", async () => {
    const res = await client.listDeployments(ANCHOR_PROJECT_ID);
    assert.ok(res);
  });

  it("should inspect dual-slot environments via client.inspectEnvironments", async () => {
    const envs = await client.inspectEnvironments(ANCHOR_PROJECT_ID);
    assert.ok(envs);
  });

  it("should compare deployments and DB schema via client.diffDeployments", async () => {
    const diff = await client.diffDeployments(ANCHOR_PROJECT_ID);
    assert.ok(diff);
  });

  it("should create, list, and delete deploy hooks via client", async () => {
    const hook = await client.createDeployHook(ANCHOR_PROJECT_ID, "ts_test_hook", "main");
    assert.ok(hook);
    const hooks = await client.listDeployHooks(ANCHOR_PROJECT_ID);
    assert.ok(hooks);
    const hookId = hook.id || hook.hook_id || (Array.isArray(hooks) && hooks[0]?.id) || (hooks.hooks && hooks.hooks[0]?.id);
    if (hookId) {
      await client.deleteDeployHook(ANCHOR_PROJECT_ID, hookId);
    }
  });

  it("should add, list, and delete custom edge routes via client", async () => {
    const route = await client.addRoute(ANCHOR_PROJECT_ID, {
      source: "/ts-api-test",
      destination: "https://httpbin.org/get",
      type: "rewrite",
    });
    assert.ok(route);
    const routes = await client.listRoutes(ANCHOR_PROJECT_ID);
    assert.ok(routes);
    const routeId = route.id || route.route_id || (Array.isArray(routes) && routes[0]?.id) || (routes.routes && routes.routes[0]?.id);
    if (routeId) {
      await client.deleteRoute(ANCHOR_PROJECT_ID, routeId);
    }
  });

  it("should add, list, and delete log drains via client", async () => {
    const drain = await client.addLogDrain(ANCHOR_PROJECT_ID, "https://example.com/ts-drain", "webhook");
    assert.ok(drain);
    const drains = await client.listLogDrains(ANCHOR_PROJECT_ID);
    assert.ok(drains);
    const drainId = drain.id || drain.drain_id || (Array.isArray(drains) && drains[0]?.id) || (drains.drains && drains.drains[0]?.id);
    if (drainId) {
      await client.deleteLogDrain(ANCHOR_PROJECT_ID, drainId);
    }
  });

  it("should list billing invoices via client.listInvoices", async () => {
    const invoices = await client.listInvoices();
    assert.ok(invoices);
  });

  it("should perform physical health probe via client.dualProbe", async () => {
    const probe = await client.dualProbe("all");
    assert.ok(probe);
    assert.ok(probe.status === "HEALTHY" || probe.status === "HEALTHY_HTTP");
  });

  it("should list extensions, pooler, and slow queries via MnemonClient", async () => {
    const { MnemonClient } = await import("../dist/mnemon.js");
    const mnemon = new MnemonClient({ apiUrl: "https://nephis.theeducode.com/v1/db", apiKey: API_KEY });
    const tenantId = "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1";

    const ext = await mnemon.listExtensions(tenantId);
    assert.ok(ext);

    const pool = await mnemon.getPooler(tenantId);
    assert.ok(pool);

    const slow = await mnemon.getSlowQueries(tenantId);
    assert.ok(slow);
  });

  it("should diff branch schemas and analyze safe migration via MnemonClient", async () => {
    const { MnemonClient } = await import("../dist/mnemon.js");
    const mnemon = new MnemonClient({ apiUrl: "https://nephis.theeducode.com/v1/db", apiKey: API_KEY });
    const tenantId = "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1";

    const diff = await mnemon.schemaDiff(tenantId, "main", "main");
    assert.ok(diff);

    const migration = await mnemon.reconcileSchema(tenantId, "main", "CREATE TABLE IF NOT EXISTS ts_probe (id int);");
    assert.ok(migration);
  });

  it("should inspect global autofreeze stats via MnemonClient", async () => {
    const { MnemonClient } = await import("../dist/mnemon.js");
    const mnemon = new MnemonClient({ apiUrl: "https://nephis.theeducode.com/v1/db", apiKey: API_KEY });

    const stats = await mnemon.autoFreezePolicy();
    assert.ok(stats);
  });

  it("should throw a formatted error on HTTP 404", async () => {
    await assert.rejects(
      async () => {
        await client.request("GET", "/api/v1/non_existent_endpoint_for_test_404");
      },
      (err: any) => err.message.includes("404") || err.name.includes("APIError") || err.name.includes("ConnectionError")
    );
  });
});
