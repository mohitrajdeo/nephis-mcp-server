import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const serverPath = path.resolve(__dirname, "../dist/index.js");

interface RpcCallResult {
  latency_ms: number;
  result: any;
  error?: any;
}

async function runAutonomousEvaluation() {
  console.error("=== STARTING AUTONOMOUS AI AGENT MCP TOOL EVALUATION ===");

  const child = spawn("node", [serverPath], {
    stdio: ["pipe", "pipe", "inherit"],
    env: { ...process.env },
  });

  let requestId = 1;
  const pendingRequests = new Map<number, (res: any) => void>();
  let buffer = "";

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
        // ignore non-json
      }
    }
  });

  function callRpc(method: string, params: any): Promise<RpcCallResult> {
    const id = requestId++;
    const t0 = performance.now();
    return new Promise((resolve) => {
      pendingRequests.set(id, (res: any) => {
        const t1 = performance.now();
        resolve({
          latency_ms: +(t1 - t0).toFixed(3),
          result: res.result,
          error: res.error,
        });
      });
      const msg = JSON.stringify({ jsonrpc: "2.0", id, method, params });
      child.stdin?.write(msg + "\n");
    });
  }

  // 0. Handshake
  const init = await callRpc("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "ananke-autonomous-evaluator", version: "3.0.0" },
  });
  child.stdin?.write(JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized", params: {} }) + "\n");

  const results: Record<string, any> = {};

  // 1. TOOL AVAILABILITY TEST
  // 1a. thanaton_list_sandboxes
  const sandboxesRes = await callRpc("tools/call", {
    name: "thanaton_list_sandboxes",
    arguments: {},
  });
  results["1a_thanaton_list_sandboxes"] = {
    latency_ms: sandboxesRes.latency_ms,
    data: JSON.parse(sandboxesRes.result.content[0].text),
  };

  // 1b. mnemon_list_tenants
  const tenantsRes = await callRpc("tools/call", {
    name: "mnemon_list_tenants",
    arguments: {},
  });
  results["1b_mnemon_list_tenants"] = {
    latency_ms: tenantsRes.latency_ms,
    data: JSON.parse(tenantsRes.result.content[0].text),
  };

  // 2. SPECULATIVE DATABASE BRANCH TEST
  // 2a. Spawn temporary branch ai_agent_sandbox_test
  const branchRes = await callRpc("tools/call", {
    name: "mnemon_create_branch",
    arguments: {
      tenant_id: "prod-primary",
      new_branch: "ai_agent_sandbox_test",
      parent_branch: "main",
    },
  });
  results["2a_mnemon_create_branch"] = {
    latency_ms: branchRes.latency_ms,
    data: JSON.parse(branchRes.result.content[0].text),
  };

  // 2b. CREATE TABLE ai_audit (id serial primary key, agent_name text)
  const createTableRes = await callRpc("tools/call", {
    name: "mnemon_execute_sql",
    arguments: {
      tenant_id: "ai_agent_sandbox_test",
      query: "CREATE TABLE ai_audit (id serial primary key, agent_name text);",
    },
  });
  results["2b_create_table"] = {
    latency_ms: createTableRes.latency_ms,
    data: JSON.parse(createTableRes.result.content[0].text),
  };

  // 2c. Insert 5 records into ai_audit
  const insertRes = await callRpc("tools/call", {
    name: "mnemon_execute_sql",
    arguments: {
      tenant_id: "ai_agent_sandbox_test",
      query: "INSERT INTO ai_audit (agent_name) VALUES ('agent-1'), ('agent-2'), ('agent-3'), ('agent-4'), ('agent-5');",
    },
  });
  results["2c_insert_5_records"] = {
    latency_ms: insertRes.latency_ms,
    data: JSON.parse(insertRes.result.content[0].text),
  };

  // 2d. Query the records back
  const queryRes = await callRpc("tools/call", {
    name: "mnemon_execute_sql",
    arguments: {
      tenant_id: "ai_agent_sandbox_test",
      query: "SELECT id, agent_name FROM ai_audit;",
    },
  });
  results["2d_query_records_before_reset"] = {
    latency_ms: queryRes.latency_ms,
    data: JSON.parse(queryRes.result.content[0].text),
  };

  // 2e. mnemon_reset_branch to restore branch to clean parent state
  const resetRes = await callRpc("tools/call", {
    name: "mnemon_reset_branch",
    arguments: {
      tenant_id: "prod-primary",
      branch_id: "ai_agent_sandbox_test",
    },
  });
  results["2e_mnemon_reset_branch"] = {
    latency_ms: resetRes.latency_ms,
    data: JSON.parse(resetRes.result.content[0].text),
  };

  // 2f. Query after reset to confirm records vanished
  const verifyRes = await callRpc("tools/call", {
    name: "mnemon_execute_sql",
    arguments: {
      tenant_id: "ai_agent_sandbox_test",
      query: "SELECT id, agent_name FROM ai_audit;",
    },
  });
  results["2f_query_records_after_reset"] = {
    latency_ms: verifyRes.latency_ms,
    data: JSON.parse(verifyRes.result.content[0].text),
  };

  // 3. CODE EVALUATION & PREFLIGHT SAFETY
  // 3a. Intentional infinite loop: while True: pass
  const preflightRes = await callRpc("tools/call", {
    name: "eschaton_preflight_check",
    arguments: {
      language: "python",
      code: "while True: pass",
    },
  });
  results["3a_preflight_infinite_loop"] = {
    latency_ms: preflightRes.latency_ms,
    data: JSON.parse(preflightRes.result.content[0].text),
  };

  // 3b. Valid Python data science formula: [x**2 for x in range(100)]
  const runCodeRes = await callRpc("tools/call", {
    name: "thanaton_run_code",
    arguments: {
      language: "python",
      code: "[x**2 for x in range(100)]",
    },
  });
  results["3b_python_datascience_run"] = {
    latency_ms: runCodeRes.latency_ms,
    data: JSON.parse(runCodeRes.result.content[0].text),
  };

  child.kill();

  // Print final clean report in stdout
  process.stdout.write(JSON.stringify(results, null, 2) + "\n");
}

runAutonomousEvaluation().catch((err) => {
  console.error("Evaluation error:", err);
  process.exit(1);
});
