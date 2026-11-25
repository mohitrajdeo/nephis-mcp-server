"""Automated real live integration tests for Thanaton Python SDK."""

import sys
import unittest
from pathlib import Path

tests_dir = Path(__file__).resolve().parent
sdk_dir = tests_dir.parent
sys.path.insert(0, str(sdk_dir))
sys.path.insert(0, str(tests_dir))

import thanaton
from thanaton.exceptions import APIError, SandboxNotFoundError, ThanatonConnectionError, ThanatonError
from live_config import THANATON_URL, ANCHOR_PROJECT_ID, get_live_api_key


class TestThanatonSDK(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_key = get_live_api_key()
        cls.client = thanaton.Client(base_url=THANATON_URL, api_key=cls.api_key)
        cls.anchor_id = ANCHOR_PROJECT_ID

    def test_client_initialization(self):
        self.assertTrue(self.client.base_url.startswith("https://"))
        self.assertTrue(self.client.api_key.startswith("mrd_live_"))

    def test_projects_listing(self):
        projects = self.client.projects.list()
        self.assertGreater(len(projects), 0)
        p_ids = [p["id"] for p in projects]
        self.assertIn(self.anchor_id, p_ids)

    def test_billing_wallet(self):
        wallet = self.client.billing.get_wallet()
        self.assertEqual(wallet["tier"], "enterprise")
        self.assertGreater(wallet["credits_balance"], 0)
        self.assertTrue(wallet["allow_custom_domains"])

    def test_execute_suite(self):
        res = self.client.execute_suite(
            source_code="print('LIVE_THANATON_PY_PASS')",
            language_id=204,
            suite="Omni"
        )
        self.assertGreaterEqual(len(res["Results"]), 1)
        self.assertTrue(res["Results"][0]["passed"])
        self.assertIn("LIVE_THANATON_PY_PASS", res["Results"][0]["stdout"])

    def test_complexity_profile(self):
        res = self.client.complexity_profile(
            source_code="#include <iostream>\nint main(){ long long sum=0; for(int i=0;i<100;i++) sum+=i; std::cout<<sum; return 0; }",
            language_id=202,
            stdin="100"
        )
        self.assertGreaterEqual(len(res["Results"]), 1)
        self.assertTrue(res["Results"][0]["passed"])
        instructions = res["Results"][0].get("instructions_executed") or res["Results"][0].get("time")
        self.assertGreater(int(instructions), 1000)

    def test_special_judge(self):
        res = self.client.special_judge(
            source_code="#include <iostream>\nint main(){ std::cout << 3.14159; return 0; }",
            checker_code="#include <iostream>\nint main(){ return 0; }",
            checker_language_id=202
        )
        self.assertGreaterEqual(len(res["Results"]), 1)
        self.assertTrue(res["Results"][0]["passed"])

    def test_batch_execute(self):
        res = self.client.batch_execute(
            source_code="import sys\nfor line in sys.stdin:\n    line = line.strip()\n    if line:\n        print(int(line) ** 2)",
            tests=[
                {"id": 1, "stdin": "4\n", "expected_output": "16\n"},
                {"id": 2, "stdin": "9\n", "expected_output": "81\n"}
            ],
            language_id=204
        )
        self.assertEqual(len(res["Results"]), 2)
        self.assertTrue(all(r["passed"] for r in res["Results"]))

    def test_live_microvm_hardware_execution(self):
        """Execute real command inside ring-0 Thanaton Firecracker KVM microVM."""
        res = self.client._request(
            "POST",
            "/v1/sandboxes/run",
            body={"command": "echo 'NEPHIS_MICROVM_HARDWARE_OK'"}
        )
        self.assertEqual(res.get("engine"), "thanaton-kvm")
        self.assertEqual(res.get("exit_code"), 0)
        self.assertIn("NEPHIS_MICROVM_HARDWARE_OK", res.get("stdout", ""))
        self.assertLess(res.get("wall_time_ms", 999), 100)

    def test_live_speculative_candidate_race(self):
        """Race multi-candidate speculative algorithmic branches in parallel."""
        res = self.client._request(
            "POST",
            "/api/v1/speculate/race",
            body={
                "project_id": self.anchor_id,
                "candidates": [{"id": "c1", "code": "print('FAST_BRANCH')"}]
            }
        )
        self.assertIn("branches", res)
        self.assertTrue(len(res["branches"]) >= 1)
        self.assertTrue(res["branches"][0].get("committed", False))

    def test_live_wal_timeline_rewind(self):
        """Point-in-time recovery and WAL rewind on microVM timeline branch."""
        res = self.client._request(
            "POST",
            "/v1/sandboxes/wal/rewind",
            body={"project_id": self.anchor_id, "target_lsn": "0/150000"}
        )
        self.assertIn("branch_id", res)
        self.assertIn("current_lsn", res)

    def test_live_l4_port_forwarding(self):
        """Dynamic L4 raw TCP port forwarding and release."""
        # 1. Expose guest port 5432
        exposed = self.client._request(
            "POST",
            f"/v1/sandboxes/{self.anchor_id}/ports",
            body={"guest_port": 5432}
        )
        self.assertEqual(exposed.get("guest_port"), 5432)
        host_port = exposed.get("host_port")
        self.assertIsNotNone(host_port)

        # 2. List ports
        listed = self.client._request("GET", f"/v1/sandboxes/{self.anchor_id}/ports")
        self.assertGreaterEqual(listed.get("count", 0), 1)

        # 3. Clean release
        released = self.client._request("DELETE", f"/v1/sandboxes/{self.anchor_id}/ports/{host_port}")
        self.assertEqual(released.get("status"), "released")

    def test_live_project_waf_and_scaling(self):
        """Query real WAF policy, autoscaling bounds, and deploy hooks."""
        waf = self.client._request("GET", f"/api/v1/projects/waf?project_id={self.anchor_id}")
        self.assertIn("waf", waf)
        self.assertIn("rate_limit_rps", waf["waf"])

        scaling = self.client._request("GET", f"/api/v1/projects/scaling?project_id={self.anchor_id}")
        self.assertIn("memory_mb", scaling)
        self.assertIn("vcpu_count", scaling)

    def test_live_persistent_volumes(self):
        """List and attach persistent storage volumes on live microVM."""
        vols = self.client._request("GET", f"/api/v1/sandboxes/volumes?sandbox_id={self.anchor_id}")
        self.assertIn("sandbox_id", vols)
        self.assertEqual(vols["sandbox_id"], self.anchor_id)

        attach = self.client._request(
            "POST",
            "/api/v1/sandboxes/volumes",
            body={"sandbox_id": self.anchor_id, "mount_path": "/data/py_live_test", "size_gb": 5}
        )
        self.assertTrue("message" in attach or "volume_id" in attach)

    def test_live_secrets_injection(self):
        """Inject MMDS runtime secrets into live microVM."""
        res = self.client._request(
            "POST",
            "/api/v1/sandboxes/secrets/inject",
            body={"sandbox_id": self.anchor_id, "secrets": {"PY_SDK_LIVE": "1"}}
        )
        self.assertTrue("file_path" in res or "injected" in str(res.get("status", "")).lower())

    def test_exceptions_hierarchy(self):
        self.assertTrue(issubclass(APIError, ThanatonError))
        self.assertTrue(issubclass(SandboxNotFoundError, ThanatonError))

    def test_connection_error_diagnostic(self):
        unreachable_client = thanaton.Client(base_url="http://127.0.0.1:59999")
        with self.assertRaises(thanaton.ThanatonConnectionError) as ctx:
            unreachable_client.sandboxes.list()
        err_msg = str(ctx.exception)
        self.assertIn("Cannot connect to Thanaton Daemon", err_msg)
        self.assertIn("Set base_url='https://nephis.theeducode.com'", err_msg)

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


if __name__ == "__main__":
    unittest.main()
