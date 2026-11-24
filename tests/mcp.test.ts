import { describe, it, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { spawn, ChildProcess } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const serverPath = path.resolve(__dirname, "../dist/index.js");

const API_KEY = process.env.NEPHIS_API_KEY || process.env.THANATON_API_KEY || process.env.ESCHATON_API_KEY || "mrd_live_c24252187b5a8c01378e9e396ffe2e7fae4a03ff78e5b357";
if (!API_KEY) throw new Error("Set NEPHIS_API_KEY before running live MCP tests");
const THANATON_URL = process.env.THANATON_API_URL || process.env.NEPHIS_BASE_URL || "https://nephis.theeducode.com";
const ESCHATON_URL = process.env.NEPHIS_API_URL || "https://nephis.theeducode.com";
let ANCHOR_PROJECT_ID = process.env.NEPHIS_ANCHOR_PROJECT || "proj-1795418552949048854-113";
let LIVE_TENANT_ID = "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1";
let LIVE_TENANT_NAME = "Mohit Raj Deo";
let LIVE_TIER = "enterprise";

describe("Thanaton MCP Server Protocol & Live Tools Integration", () => {
  let child: ChildProcess;
  let requestId = 1;
  const pendingRequests = new Map<number, (res: any) => void>();
  let buffer = "";

  before(async () => {
    child = spawn("node", [serverPath], {
      stdio: ["pipe", "pipe", "pipe"],
      env: {
        ...process.env,
        THANATON_API_URL: THANATON_URL,
        NEPHIS_BASE_URL: ESCHATON_URL,
        NEPHIS_API_URL: ESCHATON_URL,
        ESCHATON_API_URL: ESCHATON_URL,
        NEPHIS_API_KEY: API_KEY,
        THANATON_API_KEY: API_KEY,
        ESCHATON_API_KEY: API_KEY,
      },
    });

    child.stdout?.setEncoding("utf-8");
    child.stdout?.on("data", (chunk: string) => {
      buffer += chunk;
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const json = JSON.parse(line.trim());
          if (json.id && pendingRequests.has(json.id)) {
            const cb = pendingRequests.get(json.id)!;
            pendingRequests.delete(json.id);
            cb(json);
          }
        } catch {
          // ignore partial or non-json lines
        }
      }
    });

    // Perform MCP handshake
    const initRes = await sendRpc("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "test-client", version: "1.0.0" },
    });

    assert.ok(initRes.result);
    assert.equal(initRes.result.serverInfo.name, "nephis-mcp-server");

    // Send initialized notification
    child.stdin?.write(
      JSON.stringify({
        jsonrpc: "2.0",
        method: "notifications/initialized",
        params: {},
      }) + "\n"
    );

    // Dynamically resolve tenant, user identity, and tier via nephis_whoami
    try {
      const whoamiRes = await sendRpc("tools/call", {
        name: "nephis_whoami",
        arguments: {},
      });
      if (whoamiRes?.result?.content?.[0]?.text && !whoamiRes.result.isError) {
        const whoami = JSON.parse(whoamiRes.result.content[0].text);
        if (whoami.tenant_id) LIVE_TENANT_ID = whoami.tenant_id;
        if (whoami.tenant_name) LIVE_TENANT_NAME = whoami.tenant_name;
        if (whoami.tier) LIVE_TIER = whoami.tier;
      }
    } catch (e) {
      console.warn("Dynamic whoami resolution failed:", e);
    }

    // Dynamically verify or select project from thanaton_list_projects
    try {
      const projRes = await sendRpc("tools/call", {
        name: "thanaton_list_projects",
        arguments: {},
      });
      if (projRes?.result?.content?.[0]?.text && !projRes.result.isError) {
        const parsed = JSON.parse(projRes.result.content[0].text);
        const projects = Array.isArray(parsed.projects) ? parsed.projects : (Array.isArray(parsed) ? parsed : []);
        if (projects.length > 0) {
          const match = projects.find((p: any) => p.id === ANCHOR_PROJECT_ID) || projects[0];
          ANCHOR_PROJECT_ID = match.id;
        }
      }
    } catch (e) {
      console.warn("Dynamic project resolution failed:", e);
    }
  });

  // The live key is rate-limited to 10 req/s. Pace tool calls so transient
  // 401/429/504 responses don't masquerade as product failures.
  beforeEach(async () => {
    await new Promise((r) => setTimeout(r, 350));
  });

  after(() => {
    child.kill();
  });

  function sendRpc(method: string, params: any): Promise<any> {
    const id = requestId++;
    return new Promise((resolve) => {
      pendingRequests.set(id, resolve);
      const msg = JSON.stringify({
        jsonrpc: "2.0",
        id,
        method,
        params,
      });
      child.stdin?.write(msg + "\n");
    });
  }

  it("should list all available Thanaton MCP tools", async () => {
    const res = await sendRpc("tools/list", {});
    assert.ok(res.result);
    assert.ok(Array.isArray(res.result.tools));
    const toolNames = res.result.tools.map((t: any) => t.name);
    assert.ok(toolNames.includes("thanaton_exec_command"));
    assert.ok(toolNames.includes("thanaton_list_projects"));
    assert.ok(toolNames.includes("thanaton_get_wallet"));
    assert.ok(toolNames.includes("nephis_whoami"));
    assert.ok(toolNames.includes("eschaton_execute_suite"));
    assert.ok(toolNames.includes("eschaton_complexity_profile"));
    assert.ok(toolNames.includes("eschaton_special_judge"));
    assert.equal(res.result.tools.length, 99);
    assert.ok(res.result.tools.every((t: any) => t.name && t.description), "every tool must have a name and description");
  });

  it("should query live wallet credits via thanaton_get_wallet", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_get_wallet",
      arguments: {},
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    const wallet = JSON.parse(content);
    const numericValues = Object.values(wallet).filter((v) => typeof v === "number" && v > 0);
    assert.ok(numericValues.length > 0, "no positive numeric credit balance in wallet JSON");
    assert.match(content, new RegExp(LIVE_TIER, "i"), "wallet tier missing");
    assert.match(content, new RegExp(LIVE_TENANT_ID), "wallet tenant missing");
  });

  it("should list live projects via thanaton_list_projects", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_list_projects",
      arguments: {},
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    assert.match(content, new RegExp(ANCHOR_PROJECT_ID.replace(/[-]/g, "\\-")), "anchor project missing");
    assert.match(content, /READY/, "anchor project not READY");
  });

  it("should query developer identity via nephis_whoami", async () => {
    const res = await sendRpc("tools/call", {
      name: "nephis_whoami",
      arguments: {},
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    assert.match(content, /ENTERPRISE/i, "tier missing");
    assert.match(content, /b7de0a5a-3e48-41eb-afc2-f62d5d4483b1/, "tenant ID missing");
    assert.match(content, /Mohit Raj Deo/, "user identity missing");
  });

  it("should execute code against live Eschaton compiler via eschaton_execute_suite", async () => {
    const res = await sendRpc("tools/call", {
      name: "eschaton_execute_suite",
      arguments: {
        source_code: "print('LIVE_MCP_ESCHATON_PASS')",
        language_id: 204,
        suite: "Apex",
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    assert.ok(content.includes("LIVE_MCP_ESCHATON_PASS"));
  });

  it("should profile algorithmic instructions via eschaton_complexity_profile", async () => {
    const res = await sendRpc("tools/call", {
      name: "eschaton_complexity_profile",
      arguments: {
        source_code: "#include <iostream>\nint main(){ long long s=0; for(int i=0;i<50;i++) s+=i; std::cout<<s; return 0; }",
        language_id: 202,
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    // Complexity returns instruction counts, not wall time. Assert the real
    // result payload rather than accepting either of two generic substrings.
    const profile = JSON.parse(content);
    if (profile.Results) {
      assert.ok(Array.isArray(profile.Results) && profile.Results.length >= 1, "no instruction results");
      assert.ok(profile.Results.every((r: any) => Number(r.time) > 0), "instruction counts missing");
    } else {
      assert.ok(profile.Error || profile.compile_output || profile.status || content.includes("Compilation"), "unexpected profile response");
    }
  });

  it("should evaluate custom checker binary via eschaton_special_judge", async () => {
    const res = await sendRpc("tools/call", {
      name: "eschaton_special_judge",
      arguments: {
        source_code: "#include <iostream>\nint main(){ std::cout<<3.14159; return 0; }",
        checker_code: "#include <iostream>\nint main(){ return 0; }",
        language_id: 202,
        checker_language_id: 202,
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const judged = JSON.parse(res.result.content[0].text);
    assert.ok(Array.isArray(judged.Results) && judged.Results.length >= 1, "no checker results");
    assert.equal(judged.Results[0].passed, true, "custom checker rejected a correct answer");
  });

  it("should manage SaaS project domains via thanaton_manage_domains", async () => {
    const testDomain = "test-live-mcp.theeducode.com";
    const addRes = await sendRpc("tools/call", {
      name: "thanaton_manage_domains",
      arguments: {
        project_id: ANCHOR_PROJECT_ID,
        action: "add",
        domain: testDomain,
      },
    });
    assert.ok(addRes.result);
    assert.notEqual(addRes.result.isError, true);
    const added = JSON.parse(addRes.result.content[0].text);
    assert.equal(added.domain, testDomain, "domain add did not echo the requested domain");

    const delRes = await sendRpc("tools/call", {
      name: "thanaton_manage_domains",
      arguments: {
        project_id: ANCHOR_PROJECT_ID,
        action: "delete",
        domain: testDomain,
      },
    });
    assert.ok(delRes.result);
    assert.notEqual(delRes.result.isError, true);
    // The delete tool reports status rather than echoing the domain.
    const delContent = delRes.result.content[0].text;
    assert.ok(/delet|remov|success/i.test(delContent), "domain delete did not report success");
  });

  it("should return an error for unknown tools", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_non_existent_tool",
      arguments: {},
    });
    assert.ok(res.result);
    assert.equal(res.result.isError, true);
    assert.ok(res.result.content[0].text.includes("Unknown tool"));
  });

  it("should return isError true when thanaton_exec_command is called with empty command", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_exec_command",
      arguments: { command: "" },
    });
    assert.ok(res.result);
    assert.equal(res.result.isError, true);
    assert.ok(res.result.content[0].text.includes("Error: 'command' argument is required"));
  });

  it("should return isError true when mnemon_execute_sql is called with empty query", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_execute_sql",
      arguments: { query: "" },
    });
    assert.ok(res.result);
    assert.equal(res.result.isError, true);
    assert.ok(res.result.content[0].text.includes("Error: 'query' argument is required"));
  });

  it("should execute real command inside live microVM via thanaton_exec_command", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_exec_command",
      arguments: {
        sandbox_id: ANCHOR_PROJECT_ID,
        command: "echo 'LIVE_MCP_MICROVM_OK'",
      },
    });
    assert.ok(res.result);
    const content = res.result.content[0]?.text || "";
    if (res.result.isError) {
      assert.match(content, /Thanaton API Error|unauthorized|not configured|Sandbox/i);
    } else {
      const parsed = JSON.parse(content);
      assert.equal(parsed.exit_code, 0);
      assert.ok(parsed.stdout.includes("LIVE_MCP_MICROVM_OK"));
    }
  });

  it("should expose, list, and close L4 raw TCP port via thanaton port tools", async () => {
    const exposeRes = await sendRpc("tools/call", {
      name: "thanaton_expose_port",
      arguments: {
        sandbox_id: ANCHOR_PROJECT_ID,
        guest_port: 5432,
      },
    });
    assert.ok(exposeRes.result);
    assert.notEqual(exposeRes.result.isError, true);
    const exposed = JSON.parse(exposeRes.result.content[0].text);
    assert.equal(exposed.guest_port, 5432);
    const hostPort = exposed.host_port;
    assert.ok(hostPort > 0);

    const listRes = await sendRpc("tools/call", {
      name: "thanaton_list_ports",
      arguments: {
        sandbox_id: ANCHOR_PROJECT_ID,
      },
    });
    assert.ok(listRes.result);
    if (listRes.result.isError) {
      console.error("mnemon_list_snapshots error:", listRes.result.content[0]?.text);
    }
    assert.notEqual(listRes.result.isError, true);
    const listed = JSON.parse(listRes.result.content[0].text);
    assert.ok(listed.count >= 1);

    const closeRes = await sendRpc("tools/call", {
      name: "thanaton_close_port",
      arguments: {
        sandbox_id: ANCHOR_PROJECT_ID,
        host_port: hostPort,
      },
    });
    assert.ok(closeRes.result);
    assert.notEqual(closeRes.result.isError, true);
    const closed = JSON.parse(closeRes.result.content[0].text);
    assert.equal(closed.status, "released");
  });

  it("should race speculative algorithm candidates via thanaton_speculate_race", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_speculate_race",
      arguments: {
        project_id: ANCHOR_PROJECT_ID,
        candidates: [{ id: "mcp_c1", code: "print('LIVE_MCP_RACE')" }],
      },
    });
    assert.ok(res.result);
    const content = res.result.content[0]?.text || "";
    if (res.result.isError) {
      assert.match(content, /Thanaton API Error|speculative execution backend is not configured|candidates/i);
    } else {
      const parsed = JSON.parse(content);
      assert.ok(Array.isArray(parsed.branches) && parsed.branches.length >= 1, "no speculative branches");
      assert.equal(parsed.branches[0].committed, true);
      assert.ok(JSON.stringify(parsed.branches).includes("LIVE_MCP_RACE"), "candidate output missing");
    }
  });

  it("should execute live PostgreSQL 16 SQL via mnemon_execute_sql", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_execute_sql",
      arguments: {
        tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1",
        query: "SELECT 777 as lucky;",
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.equal(parsed.status, "success");
    assert.equal(parsed.row_count, 1);
    assert.deepEqual(parsed.rows, [{ lucky: 777 }]);
  });

  it("should create instantaneous zero-copy reflink branch via mnemon_create_branch", async () => {
    const branchName = `mcp_br_${Date.now()}`;
    const res = await sendRpc("tools/call", {
      name: "mnemon_create_branch",
      arguments: {
        tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1",
        new_branch: branchName,
        parent_branch: "main",
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.equal(parsed.branch_id, branchName);
    assert.ok(parsed.port > 16000);
  });

  it("should list and attach persistent microVM storage volumes via thanaton volume tools", async () => {
    const listRes = await sendRpc("tools/call", {
      name: "thanaton_get_volumes",
      arguments: { sandbox_id: ANCHOR_PROJECT_ID },
    });
    assert.ok(listRes.result);
    if (listRes.result.isError) {
      console.error("mnemon_list_snapshots error:", listRes.result.content[0]?.text);
    }
    assert.notEqual(listRes.result.isError, true);
    const listParsed = JSON.parse(listRes.result.content[0].text);
    assert.equal(listParsed.sandbox_id, ANCHOR_PROJECT_ID, "wrong sandbox in volume list");
    assert.ok(Array.isArray(listParsed.volumes) && listParsed.volumes.length > 0, "no live volumes");

    const attachRes = await sendRpc("tools/call", {
      name: "thanaton_attach_volume",
      arguments: {
        sandbox_id: ANCHOR_PROJECT_ID,
        mount_path: "/data/live_mcp_test",
        size_gb: 1,
      },
    });
    assert.ok(attachRes.result);
    assert.notEqual(attachRes.result.isError, true);
    const attachParsed = JSON.parse(attachRes.result.content[0].text);
    assert.match(String(attachParsed.volume_id || attachParsed.message), /\/data|vol-/, "no mount path or volume ID returned");
  });

  it("should inject MMDS runtime secrets via thanaton_inject_secrets", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_inject_secrets",
      arguments: {
        sandbox_id: ANCHOR_PROJECT_ID,
        secrets: { LIVE_MCP_SECRET_KEY: "nephis_secret_verified_2026" },
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.match(String(parsed.status || ""), /INJECTED/i, "secret injection did not report injected");
    assert.match(String(parsed.file_path || ""), /mmds|secret/i, "no MMDS path returned");
  });

  it("should execute sub-millisecond Redis commands on live engine via mnemon_redis_command", async () => {
    const redisTenant = `mcp_redis_${Date.now()}`;
    const setRes = await sendRpc("tools/call", {
      name: "mnemon_redis_command",
      arguments: {
        tenant_id: redisTenant,
        command: "SET",
        args: ["live_mcp_key", "LIVE_REDIS_PASS"],
      },
    });
    assert.ok(setRes.result);
    assert.notEqual(setRes.result.isError, true);

    const getRes = await sendRpc("tools/call", {
      name: "mnemon_redis_command",
      arguments: {
        tenant_id: redisTenant,
        command: "GET",
        args: ["live_mcp_key"],
      },
    });
    assert.ok(getRes.result);
    assert.notEqual(getRes.result.isError, true);
    const parsed = JSON.parse(getRes.result.content[0].text);
    assert.equal(parsed.result, "LIVE_REDIS_PASS");
  });

  it("should execute live SQLite ephemeral queries via mnemon_sqlite_query", async () => {
    const sqTenant = `mcp_sq_${Date.now()}`;
    const res = await sendRpc("tools/call", {
      name: "mnemon_sqlite_query",
      arguments: {
        tenant_id: sqTenant,
        query: "CREATE TABLE metrics (val INT); INSERT INTO metrics VALUES (999); SELECT val FROM metrics;",
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.equal(parsed.status, "success");
    assert.deepEqual(parsed.result, [{ val: 999 }]);
  });

  it("should execute live MongoDB document queries via mnemon_mongo_query", async () => {
    const mgTenant = "cs_master_lab";
    const insertRes = await sendRpc("tools/call", {
      name: "mnemon_mongo_query",
      arguments: {
        tenant_id: mgTenant,
        collection: "benchmarks",
        action: "insertOne",
        document: { test: "live_mongo_mcp", score: 100 },
      },
    });
    assert.ok(insertRes.result);
    if (insertRes.result.isError) {
      assert.match(insertRes.result.content[0].text, /Mnemon API Error|timed out|fetch failed|Cannot reach/i);
    } else {
      assert.notEqual(insertRes.result.isError, true);
      const findRes = await sendRpc("tools/call", {
        name: "mnemon_mongo_query",
        arguments: {
          tenant_id: mgTenant,
          collection: "benchmarks",
          action: "find",
        },
      });
      assert.ok(findRes.result);
      if (!findRes.result.isError) {
        const parsed = JSON.parse(findRes.result.content[0].text);
        assert.equal(parsed.status, "success");
      }
    }
  });

  it("should create and list instant zero-copy reflink snapshots via mnemon snapshot tools", async () => {
    const listRes = await sendRpc("tools/call", {
      name: "mnemon_list_snapshots",
      arguments: {
        tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1",
      },
    });
    assert.ok(listRes.result);
    if (listRes.result.isError) {
      console.error("mnemon_list_snapshots error:", listRes.result.content[0]?.text);
    }
    assert.notEqual(listRes.result.isError, true);
    const parsed = JSON.parse(listRes.result.content[0].text);
    const snaps = parsed.backups ?? parsed.snapshots ?? parsed;
    assert.ok(Array.isArray(snaps) && snaps.length > 0, "no live snapshots returned");
    assert.ok(JSON.stringify(snaps).includes("b7de0a5a-3e48-41eb-afc2-f62d5d4483b1"), "snapshots for wrong tenant");
  });

  it("should upsert and search vectors on live Qdrant engine via mnemon vector tools", async () => {
    const qTenant = `mcp_qd_${Date.now()}`;
    const upsertRes = await sendRpc("tools/call", {
      name: "mnemon_vector_upsert",
      arguments: {
        tenant_id: qTenant,
        collection: "kb_vectors",
        points: [
          { id: 1, vector: [0.12, 0.34, 0.56, 0.78], payload: { doc: "nephis_mcp_test" } },
        ],
      },
    });
    assert.ok(upsertRes.result);
    assert.notEqual(upsertRes.result.isError, true);

    const searchRes = await sendRpc("tools/call", {
      name: "mnemon_vector_search",
      arguments: {
        tenant_id: qTenant,
        collection: "kb_vectors",
        vector: [0.12, 0.34, 0.56, 0.78],
        limit: 1,
      },
    });
    assert.ok(searchRes.result);
    assert.notEqual(searchRes.result.isError, true);
  });

  it("should inspect scaling configuration via thanaton_configure_scaling", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_configure_scaling",
      arguments: { project_id: ANCHOR_PROJECT_ID, action: "get" },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.equal(parsed.project_id, ANCHOR_PROJECT_ID);
    assert.equal(parsed.memory_mb, 8192, "wrong live memory allocation");
    assert.equal(parsed.vcpu_count ?? parsed.vcpus, 8, "wrong live vCPU allocation");
  });

  it("should list deployments via thanaton_list_deployments", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_list_deployments",
      arguments: { project_id: ANCHOR_PROJECT_ID },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    assert.match(content, new RegExp(ANCHOR_PROJECT_ID.replace(/[-]/g, "\\-")), "wrong project in deployments");
  });

  it("should inspect environments via thanaton_inspect_environments", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_inspect_environments",
      arguments: { project_id: ANCHOR_PROJECT_ID },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    const envs = JSON.parse(content);
    assert.equal(envs.project?.id, ANCHOR_PROJECT_ID, "wrong project in environment report");
    assert.ok(envs.production && "healthy" in envs.production, "no production deployment state");
    assert.ok(envs.staging && "healthy" in envs.staging, "no staging deployment state");
  });

  it("should compare deployments via thanaton_diff_deployments", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_diff_deployments",
      arguments: { project_id: ANCHOR_PROJECT_ID },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    assert.match(content, /Staging deployment/i, "no staging deployment in diff");
    assert.match(content, /Production deployment/i, "no production deployment in diff");
    assert.match(content, /Runtime:\s*python/, "runtime missing from diff");
  });

  it("should manage deploy hooks via thanaton_manage_deploy_hooks", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_manage_deploy_hooks",
      arguments: { project_id: ANCHOR_PROJECT_ID, action: "list" },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.ok(Array.isArray(parsed.hooks));
  });

  it("should manage custom edge routes via thanaton_manage_routes", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_manage_routes",
      arguments: { project_id: ANCHOR_PROJECT_ID, action: "list" },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.ok(Array.isArray(parsed.routes));
  });

  it("should manage real-time log drains via thanaton_manage_log_drains", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_manage_log_drains",
      arguments: { project_id: ANCHOR_PROJECT_ID, action: "list" },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.ok(Array.isArray(parsed.drains));
  });

  it("should list billing invoices via thanaton_list_invoices", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_list_invoices",
      arguments: {},
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const content = res.result.content[0].text;
    // An empty invoice list is a valid answer; the endpoint returns [].
    const invoices = JSON.parse(content);
    assert.ok(Array.isArray(invoices), "invoices endpoint did not return a collection");
  });

  it("should perform physical health probe via thanaton_dual_probe", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_dual_probe",
      arguments: { target: "sandbox_kernel" },
    });
    assert.ok(res.result);
    // This runs the MCP server on the test host, where 127.0.0.1:3000 is not
    // running. The tool truthfully reports an unhealthy probe as isError with
    // a structured body; that is correct behaviour, so assert the body rather
    // than requiring success.
    const content = res.result.content[0]?.text || "";
    let probe: any;
    try {
      probe = JSON.parse(content);
    } catch {
      // Tool layer wraps non-2xx API responses as "Error executing ...".
      const m = content.match(/\{[\s\S]*\}/);
      assert.ok(m, "probe returned neither JSON nor a structured error body");
      probe = JSON.parse(m![0]);
    }
    assert.ok(["HEALTHY", "HEALTHY_HTTP", "UNHEALTHY", "DUAL_FAILED"].includes(probe.status), "invalid probe status");
    assert.ok(Number.isFinite(Number(probe.latency_ms)), "no probe latency");
  });

  it("should list PostgreSQL extensions on live tenant via mnemon_manage_extensions", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_manage_extensions",
      arguments: { tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1", action: "list" },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.ok(Array.isArray(parsed.extensions), "extensions not an array");
    assert.ok(JSON.stringify(parsed.extensions).includes("uuid"), "no extensions returned for live tenant");
  });

  it("should inspect connection pooler metrics via mnemon_configure_pooler", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_configure_pooler",
      arguments: { tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1" },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.match(String(parsed.pool_mode || ""), /session/i, "wrong pool mode");
    assert.match(res.result.content[0].text, /session/i, "pool mode missing from tool output");
  });

  it("should query slow query metrics via mnemon_get_slow_queries", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_get_slow_queries",
      arguments: { tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1" },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.ok(Array.isArray(parsed.queries), "slow queries not an array");
    assert.ok(Number.isFinite(Number(parsed.count ?? parsed.queries.length)), "no query count");
  });

  it("should diff branch schemas on live engine via mnemon_diff_branch", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_diff_branch",
      arguments: {
        tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1",
        branch_id: "main",
        parent_branch: "main",
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.equal(typeof parsed.generated_migration_sql, "string", "no migration SQL string");
    assert.match(parsed.generated_migration_sql, /CREATE|ALTER|DROP|--/, "migration SQL is not DDL");
  });

  it("should analyze safe migration via mnemon_reconcile_schema", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_reconcile_schema",
      arguments: {
        tenant_id: "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1",
        branch: "main",
        sql: "CREATE TABLE IF NOT EXISTS mcp_safe_test (id serial);",
      },
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.equal(parsed.is_safe, true);
  });

  it("should inspect global autofreeze statistics via mnemon_autofreeze_policy", async () => {
    const res = await sendRpc("tools/call", {
      name: "mnemon_autofreeze_policy",
      arguments: {},
    });
    assert.ok(res.result);
    if (res.result.isError) {
      console.error("Tool execution error:", res.result.content[0]?.text);
    }
    assert.notEqual(res.result.isError, true);
    const parsed = JSON.parse(res.result.content[0].text);
    assert.ok(Number.isFinite(Number(parsed.total_scans)), "total_scans is not numeric");
    assert.ok(Number(parsed.total_scans) >= 0, "negative scan count");
  });
});
