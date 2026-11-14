import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import { spawn, ChildProcess } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const serverPath = path.resolve(__dirname, "../dist/index.js");

describe("Thanaton MCP Server Protocol & Tools", () => {
  let child: ChildProcess;
  let requestId = 1;
  const pendingRequests = new Map<number, (res: any) => void>();
  let buffer = "";

  before(async () => {
    child = spawn("node", [serverPath], {
      stdio: ["pipe", "pipe", "pipe"],
      env: {
        ...process.env,
        THANATON_API_URL: "http://127.0.0.1:9999", // Intentional offline port to test fallback simulation
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
    assert.ok(toolNames.includes("thanaton_run_code"));
    assert.ok(toolNames.includes("thanaton_spawn_sandbox"));
    assert.ok(toolNames.includes("thanaton_list_sandboxes"));
    assert.ok(toolNames.includes("thanaton_wake_sandbox"));
    assert.ok(toolNames.includes("thanaton_sleep_sandbox"));
    assert.ok(toolNames.includes("thanaton_destroy_sandbox"));

    // Ananke enterprise tools
    assert.ok(toolNames.includes("ananke_license_check"));
    assert.ok(toolNames.includes("ananke_license_generate"));
    assert.ok(toolNames.includes("ananke_cdc_inspect"));
    assert.ok(toolNames.includes("ananke_webhook_dispatch"));
    assert.ok(toolNames.includes("ananke_finops_scan"));
    assert.ok(toolNames.includes("ananke_flight_record_inspect"));
    assert.ok(toolNames.includes("ananke_chaos_simulate"));
    assert.ok(toolNames.includes("ananke_pool_probe"));
    assert.ok(toolNames.includes("ananke_storage_pipe_bench"));
    assert.ok(toolNames.includes("ananke_rootfs_build_manifest"));
    assert.ok(toolNames.includes("ananke_dns_probe"));
    assert.ok(toolNames.includes("ananke_socket_migrate_demo"));
    assert.equal(res.result.tools.length, 19);
  });

  let provisionedSandboxId = "";

  it("should spawn a sandbox via thanaton_spawn_sandbox", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_spawn_sandbox",
      arguments: {
        runtime: "microvm",
        memory_mb: 256,
        with_db: true,
      },
    });

    assert.ok(res.result);
    assert.equal(res.result.isError, undefined);
    assert.ok(Array.isArray(res.result.content));
    const data = JSON.parse(res.result.content[0].text);
    assert.ok(data.sandbox_id);
    assert.equal(data.runtime, "microvm");
    assert.equal(data.state, "running");
    provisionedSandboxId = data.sandbox_id;
  });

  it("should execute a shell command via thanaton_exec_command", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_exec_command",
      arguments: {
        sandbox_id: provisionedSandboxId,
        command: "python3 -c 'print(42)'",
      },
    });

    assert.ok(res.result);
    const data = JSON.parse(res.result.content[0].text);
    assert.equal(data.sandbox_id, provisionedSandboxId);
    assert.equal(data.exit_code, 0);
  });

  it("should execute code directly via thanaton_run_code", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_run_code",
      arguments: {
        language: "python",
        code: "import sys; print('Testing Thanaton MCP!')",
      },
    });

    assert.ok(res.result);
    const data = JSON.parse(res.result.content[0].text);
    assert.equal(data.language, "python");
    assert.equal(data.exit_code, 0);
  });

  it("should hibernate a sandbox via thanaton_sleep_sandbox", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_sleep_sandbox",
      arguments: {
        sandbox_id: provisionedSandboxId,
      },
    });

    assert.ok(res.result);
    const data = JSON.parse(res.result.content[0].text);
    assert.equal(data.status, "hibernated");
  });

  it("should wake a hibernated sandbox via thanaton_wake_sandbox", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_wake_sandbox",
      arguments: {
        sandbox_id: provisionedSandboxId,
      },
    });

    assert.ok(res.result);
    const data = JSON.parse(res.result.content[0].text);
    assert.equal(data.status, "woken");
  });

  it("should destroy a sandbox via thanaton_destroy_sandbox", async () => {
    const res = await sendRpc("tools/call", {
      name: "thanaton_destroy_sandbox",
      arguments: {
        sandbox_id: provisionedSandboxId,
      },
    });

    assert.ok(res.result);
    const data = JSON.parse(res.result.content[0].text);
    assert.equal(data.status, "destroyed");
  });

  it("should dispatch webhooks and block SSRF via ananke_webhook_dispatch", async () => {
    // Valid external webhook
    const validRes = await sendRpc("tools/call", {
      name: "ananke_webhook_dispatch",
      arguments: {
        url: "https://api.example.com/webhook",
        payload: JSON.stringify({ event: "sandbox.ready" }),
      },
    });
    assert.ok(validRes.result);
    const validData = JSON.parse(validRes.result.content[0].text);
    assert.equal(validData.status, "delivered");
    assert.equal(validData.engine, "hookq");

    // SSRF attempt against internal loopback
    const ssrfRes = await sendRpc("tools/call", {
      name: "ananke_webhook_dispatch",
      arguments: {
        url: "http://127.0.0.1:8080/internal",
        payload: "{}",
      },
    });
    assert.ok(ssrfRes.result);
    assert.equal(ssrfRes.result.isError, true);
    assert.ok(ssrfRes.result.content[0].text.includes("SSRF Blocked"));
  });

  it("should run infrastructure FinOps scan via ananke_finops_scan", async () => {
    const res = await sendRpc("tools/call", {
      name: "ananke_finops_scan",
      arguments: {
        regions: "us-east-1",
      },
    });
    assert.ok(res.result);
    const data = JSON.parse(res.result.content[0].text);
    assert.equal(data.engine, "zombieprune");
    assert.equal(data.total_monthly_waste_usd, 138.6);
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
});
