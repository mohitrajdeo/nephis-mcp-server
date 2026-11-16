import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { ThanatonClient, Sandbox, EschatonClient } from "../dist/index.js";

describe("Thanaton TypeScript SDK", () => {
  let mockServer: http.Server;
  let serverPort: number;
  let receivedRequests: { method: string; path: string; body?: any }[] = [];

  before(async () => {
    // Start local mock Thanaton Daemon
    mockServer = http.createServer((req, res) => {
      let data = "";
      req.on("data", (chunk) => {
        data += chunk;
      });
      req.on("end", () => {
        const parsedBody = data ? JSON.parse(data) : undefined;
        receivedRequests.push({
          method: req.method || "GET",
          path: req.url || "/",
          body: parsedBody,
        });

        res.setHeader("Content-Type", "application/json");

        // Routing
        if (req.url === "/v1/sandboxes" && req.method === "POST") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              id: "sbx_test_123",
              tenant_id: parsedBody?.tenant_id || "default",
              runtime: parsedBody?.runtime || "microvm",
              state: "running",
              has_db: parsedBody?.with_db || false,
              db_url: parsedBody?.with_db ? "postgresql://postgres:thanaton@172.16.2.2:5432/sbx_test_123" : null,
              boot_duration_ms: 5.82,
              created_at: new Date().toISOString(),
              last_active_at: new Date().toISOString(),
            })
          );
          return;
        }

        if (req.url === "/v1/sandboxes/sbx_test_123" && req.method === "GET") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              id: "sbx_test_123",
              tenant_id: "default",
              runtime: "microvm",
              state: "running",
              has_db: true,
              boot_duration_ms: 5.82,
              created_at: new Date().toISOString(),
              last_active_at: new Date().toISOString(),
            })
          );
          return;
        }

        if (req.url === "/v1/sandboxes/sbx_test_123/exec" && req.method === "POST") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              stdout: `Output of ${parsedBody?.command}\n`,
              stderr: "",
              exit_code: 0,
              duration_ms: 12.5,
            })
          );
          return;
        }

        if (req.url === "/_thanaton/tenants/sbx_test_123/sleep" && req.method === "POST") {
          res.writeHead(200);
          res.end(JSON.stringify({ status: "sleeping", ram_rss_bytes: 0 }));
          return;
        }

        if (req.url === "/_thanaton/tenants/sbx_test_123/wake" && req.method === "POST") {
          res.writeHead(200);
          res.end(JSON.stringify({ status: "running", wake_duration_ms: 1.84 }));
          return;
        }

        if (req.url === "/v1/sandboxes/sbx_test_123" && req.method === "DELETE") {
          res.writeHead(200);
          res.end(JSON.stringify({ status: "destroyed" }));
          return;
        }

        if (req.url === "/v1/sandboxes/sbx_test_123/pty" && req.method === "GET") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              sandbox_id: "sbx_test_123",
              pty_endpoint: "wss://nephis.theeducode.com/v1/sandboxes/sbx_test_123/pty",
              terminal: "xterm-256color",
              status: "ready",
            })
          );
          return;
        }

        if (req.url === "/v1/sandboxes/sbx_test_123/ports" && req.method === "POST") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              sandbox_id: "sbx_test_123",
              service_name: parsedBody?.service_name || "postgres",
              guest_port: parsedBody?.guest_port || 5432,
              host_port: 15432,
              connection_string: "nephis.theeducode.com:15432",
              status: "FORWARDING",
              created_at: new Date().toISOString(),
            })
          );
          return;
        }

        if (req.url === "/v1/sandboxes/sbx_test_123/ports" && req.method === "GET") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              ports: [
                {
                  sandbox_id: "sbx_test_123",
                  service_name: "postgres",
                  guest_port: 5432,
                  host_port: 15432,
                  connection_string: "nephis.theeducode.com:15432",
                  status: "FORWARDING",
                  created_at: new Date().toISOString(),
                },
              ],
            })
          );
          return;
        }

        if (req.url === "/v1/sandboxes/sbx_test_123/ports/15432" && req.method === "DELETE") {
          res.writeHead(200);
          res.end(JSON.stringify({ status: "RELEASED", host_port: 15432 }));
          return;
        }

        if (req.url === "/v1/speculate/race" && req.method === "POST") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              problem_id: parsedBody?.problem_id || "test_problem",
              winner_candidate_id: "cand_2",
              total_candidates: (parsedBody?.candidates || []).length,
              race_duration_ms: 42.5,
              strategy: "FASTEST_PASSING",
              results: [
                {
                  candidate_id: "cand_1",
                  status: "FAILED",
                  exit_code: 1,
                  stdout: "",
                  stderr: "AssertionError",
                  duration_ms: 35.0,
                },
                {
                  candidate_id: "cand_2",
                  status: "WINNER",
                  exit_code: 0,
                  stdout: "All tests passed",
                  stderr: "",
                  duration_ms: 42.5,
                },
              ],
            })
          );
          return;
        }

        if (req.url === "/v1/sandboxes/wal/rewind" && req.method === "POST") {
          res.writeHead(200);
          res.end(
            JSON.stringify({
              status: "REWOUND",
              sandbox_id: parsedBody?.sandbox_id,
              project_id: parsedBody?.project_id,
              branch_id: "wal_rewind_branch_1",
              target_time: parsedBody?.target_time,
              target_lsn: parsedBody?.target_lsn,
              connection_string: "postgresql://postgres:thanaton@nephis.theeducode.com:5432/wal_rewind_branch_1",
              rewind_latency_ms: 31.4,
              message: "Point-in-time recovery completed in 31.4ms",
            })
          );
          return;
        }

        if (req.url === "/v1/execute" && req.method === "POST") {
          const suite = parsedBody?.suite || "Omni";
          if (suite === "Complexity") {
            res.writeHead(200);
            res.end(
              JSON.stringify({
                Results: [
                  {
                    test_case_id: 1,
                    time: 0.042,
                    memory: 15400,
                    stdout: "O(N) confirmed",
                    stderr: "",
                    passed: true,
                    status_id: 3,
                    instructions_executed: 18450,
                  },
                ],
                Error: "",
              })
            );
            return;
          }
          if (suite === "Sanitizer") {
            res.writeHead(200);
            res.end(
              JSON.stringify({
                Results: [
                  {
                    test_case_id: 1,
                    time: 0.015,
                    memory: 12400,
                    stdout: "Clean",
                    stderr: "",
                    passed: true,
                    status_id: 3,
                    memory_leaks: false,
                  },
                ],
                Error: "",
              })
            );
            return;
          }
          if (suite === "DBMS") {
            res.writeHead(200);
            res.end(
              JSON.stringify({
                Results: [
                  {
                    test_case_id: 1,
                    time: 0.008,
                    memory: 8400,
                    stdout: "1|Alice\n2|Bob",
                    stderr: "",
                    passed: true,
                    status_id: 3,
                    schema_applied: true,
                  },
                ],
                Error: "",
              })
            );
            return;
          }
          if (suite === "FileIO") {
            res.writeHead(200);
            res.end(
              JSON.stringify({
                Results: [
                  {
                    test_case_id: 1,
                    time: 0.012,
                    memory: 10200,
                    stdout: "SUCCESS",
                    stderr: "",
                    passed: true,
                    status_id: 3,
                    file_matched: true,
                  },
                ],
                Error: "",
              })
            );
            return;
          }
          if (suite === "SpecialJudge") {
            res.writeHead(200);
            res.end(
              JSON.stringify({
                Results: [
                  {
                    test_case_id: 1,
                    time: 0.021,
                    memory: 14200,
                    stdout: "2.5000000000",
                    stderr: "",
                    passed: true,
                    status_id: 3,
                    checker_verdict: "ACCEPTED (eps < 1e-6)",
                  },
                ],
                Error: "",
              })
            );
            return;
          }

          // Default / Omni / Void
          res.writeHead(200);
          res.end(
            JSON.stringify({
              Results: [
                {
                  test_case_id: 1,
                  time: 0.018,
                  memory: 11200,
                  stdout: "Hello from Eschaton",
                  stderr: "",
                  passed: true,
                  status_id: 3,
                },
              ],
              Error: "",
            })
          );
          return;
        }

        res.writeHead(404);
        res.end(JSON.stringify({ error: "not found" }));
      });
    });

    await new Promise<void>((resolve) => {
      mockServer.listen(0, "127.0.0.1", () => {
        const addr = mockServer.address() as any;
        serverPort = addr.port;
        resolve();
      });
    });
  });

  after(() => {
    mockServer.close();
  });

  it("should initialize client with default and custom options", () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}`, apiKey: "thanaton_sec_xyz" });
    assert.equal(client.baseUrl, `http://127.0.0.1:${serverPort}`);
    assert.equal(client.apiKey, "thanaton_sec_xyz");
  });

  it("should provision a sandbox and return typed Sandbox instance", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const sbx = await client.sandboxes.create({
      runtime: "microvm",
      memoryMb: 512,
      withDb: true,
    });

    assert.ok(sbx instanceof Sandbox);
    assert.equal(sbx.id, "sbx_test_123");
    assert.equal(sbx.runtime, "microvm");
    assert.equal(sbx.hasDb, true);
    assert.ok(sbx.dbUrl?.includes("postgresql://"));
    assert.equal(sbx.state, "running");
  });

  it("should execute shell commands inside sandbox", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const sbx = await client.sandboxes.get("sbx_test_123");
    const result = await sbx.exec("echo 'hello world'");

    assert.equal(result.ok, true);
    assert.equal(result.exitCode, 0);
    assert.ok(result.stdout.includes("echo 'hello world'"));
  });

  it("should support scale-to-zero (sleep) and instant wake", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const sbx = await client.sandboxes.get("sbx_test_123");

    await sbx.sleep();
    assert.equal(sbx.state, "sleeping");

    await sbx.wake();
    assert.equal(sbx.state, "running");
  });

  it("should retrieve PTY connection metadata", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const sbx = await client.sandboxes.get("sbx_test_123");
    const pty = await sbx.ptyInfo();

    assert.equal(pty.sandbox_id, "sbx_test_123");
    assert.ok(pty.pty_endpoint.startsWith("wss://"));
    assert.equal(pty.status, "ready");
  });

  it("should manage Layer 4 TCP port forwardings", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const sbx = await client.sandboxes.get("sbx_test_123");

    const forward = await sbx.exposePort(5432, "tcp", "postgres");
    assert.equal(forward.sandbox_id, "sbx_test_123");
    assert.equal(forward.guest_port, 5432);
    assert.equal(forward.host_port, 15432);
    assert.equal(forward.status, "FORWARDING");

    const ports = await sbx.listPorts();
    assert.equal(ports.length, 1);
    assert.equal(ports[0].host_port, 15432);

    await sbx.closePort(15432);
  });

  it("should race speculative candidate patches and identify winner", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const candidates = [
      { id: "cand_1", command: "pytest tests/broken" },
      { id: "cand_2", command: "pytest tests/passing" },
    ];

    const race = await client.race(candidates, "race_test_123");
    assert.equal(race.problem_id, "race_test_123");
    assert.equal(race.winner_candidate_id, "cand_2");
    assert.equal(race.total_candidates, 2);
    assert.equal(race.results.length, 2);
    assert.equal(race.results[1].status, "WINNER");
  });

  it("should rewind database to historical point in time via WAL rewind", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.rewindDatabase({
      sandboxId: "sbx_test_123",
      targetTime: "2026-11-15T01:00:00Z",
    });

    assert.equal(res.status, "REWOUND");
    assert.equal(res.branch_id, "wal_rewind_branch_1");
    assert.ok(res.connection_string.includes("postgresql://"));
    assert.ok(res.rewind_latency_ms < 50);
  });

  it("should execute code against Eschaton multi-suite engine", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.executeSuite({
      sourceCode: "print('Hello from Eschaton')",
      languageId: 71,
      suite: "Omni",
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
    assert.ok(res.Results[0].stdout.includes("Hello from Eschaton"));
  });

  it("should profile algorithmic complexity via Valgrind lackey", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.complexityProfile({
      sourceCode: "int main() { return 0; }",
      languageId: 202,
      stdin: "100",
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
    assert.equal(res.Results[0].instructions_executed, 18450);
  });

  it("should run memory safety checks via AddressSanitizer (ASan)", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.sanitizeCheck({
      sourceCode: "int main() { return 0; }",
      languageId: 202,
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
    assert.equal(res.Results[0].memory_leaks, false);
  });

  it("should evaluate SQL queries with ephemeral schema in DBMS suite", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.dbmsEval({
      sourceCode: "SELECT * FROM users;",
      schemaSql: "CREATE TABLE users(id INT, name TEXT); INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');",
      database: "sqlite",
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
    assert.equal(res.Results[0].schema_applied, true);
    assert.ok(res.Results[0].stdout.includes("Alice"));
  });

  it("should evaluate FileIO sandboxed execution with custom files", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.fileioEval({
      sourceCode: "f = open('output.txt', 'w'); f.write('SUCCESS'); f.close()",
      inputFilename: "input.txt",
      inputContent: "DATA",
      outputFilename: "output.txt",
      expectedOutput: "SUCCESS",
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
    assert.equal(res.Results[0].file_matched, true);
  });

  it("should evaluate custom checker binary in SpecialJudge suite", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.specialJudge({
      sourceCode: "int main() { printf(\"2.5000000000\\n\"); }",
      checkerCode: "int main() { return 0; }",
      stdin: "5.0",
      expectedOutput: "2.5",
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
    assert.ok(res.Results[0].checker_verdict?.includes("ACCEPTED"));
  });

  it("should evaluate multi-testcase batch in batchExecute", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const res = await client.batchExecute({
      sourceCode: "print(1)",
      tests: [{ stdin: "1", expected_output: "1" }],
      suite: "Omni",
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
  });

  it("should execute code using standalone EschatonClient", async () => {
    const eschaton = new EschatonClient({ baseUrl: `http://127.0.0.1:${serverPort}`, apiKey: "esk_standalone_test" });
    const res = await eschaton.execute({
      sourceCode: "print('from standalone eschaton client')",
      languageId: 71,
    });

    assert.equal(res.Results.length, 1);
    assert.equal(res.Results[0].passed, true);
  });

  it("should destroy the sandbox cleanly", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    const sbx = await client.sandboxes.get("sbx_test_123");
    await sbx.destroy();
    assert.equal(sbx.state, "stopped");
  });

  it("should throw a formatted error on HTTP 404", async () => {
    const client = new ThanatonClient({ baseUrl: `http://127.0.0.1:${serverPort}` });
    await assert.rejects(
      async () => {
        await client.request("GET", "/non_existent_endpoint");
      },
      /Thanaton API error \[HTTP 404\]/
    );
  });
});
