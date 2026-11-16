import test from "node:test";
import assert from "node:assert";
import { MnemonClient, MnemonError } from "../src/mnemon.js";

test("MnemonClient initialization and connection string", () => {
  const client = new MnemonClient({
    apiUrl: "http://localhost:9090",
    apiKey: "nephis_live_test_ts",
    proxyHost: "db.nephis.theeducode.com",
    proxyPort: 5432,
  });

  assert.strictEqual(
    client.getConnectionString("tenant_alpha"),
    "postgresql://postgres:secret@db.nephis.theeducode.com:5432/tenant_alpha?sslmode=require"
  );
});

test("MnemonError attributes", () => {
  const err = new MnemonError("Resource not found", 404, '{"error":"not_found"}');
  assert.strictEqual(err.name, "MnemonError");
  assert.strictEqual(err.statusCode, 404);
  assert.strictEqual(err.responseBody, '{"error":"not_found"}');
});

