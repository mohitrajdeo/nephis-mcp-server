"""
Comprehensive test suite for the Nephis Series unified SDK & authority engine.
"""

import unittest
import sys
import os
from pathlib import Path

# Insert local nephis package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import nephis
from nephis.license import LicenseAuthority, LicenseToken, LicenseError


from unittest.mock import patch, MagicMock

class TestAnankeSeriesSDK(unittest.TestCase):
    def setUp(self):
        # Hermetically isolate environment from external env vars
        self.old_env = os.environ.pop("NEPHIS_LICENSE_KEY", None)
        # Generate an Enterprise test license
        self.enterprise_token = LicenseToken(tenant_id="test-enterprise-corp", tier="enterprise", expires_in_days=30).generate()
        self.community_client = nephis.Client()
        self.enterprise_client = nephis.Client(license_key=self.enterprise_token)

    def tearDown(self):
        if self.old_env:
            os.environ["NEPHIS_LICENSE_KEY"] = self.old_env

    def test_license_authority_community(self):
        auth = self.community_client.authority
        self.assertEqual(auth.tier, "community")
        self.assertTrue(auth.is_feature_allowed("cdc_basic"))
        self.assertTrue(auth.is_feature_allowed("pool_basic"))
        self.assertFalse(auth.is_feature_allowed("live_migration"))

        # Gated call should raise LicenseError
        with self.assertRaises(LicenseError):
            auth.assert_feature("live_migration")

    def test_license_authority_enterprise(self):
        auth = self.enterprise_client.authority
        self.assertEqual(auth.tier, "enterprise")
        self.assertTrue(auth.is_feature_allowed("live_migration"))
        self.assertTrue(auth.is_feature_allowed("finops"))
        self.assertTrue(auth.is_feature_allowed("chaos"))

    def test_license_tampering_detection(self):
        tampered_token = self.enterprise_token[:-5] + "aaaaa"
        with self.assertRaises(LicenseError):
            LicenseToken.verify(tampered_token)

    def test_client_managers_presence(self):
        cl = self.enterprise_client
        self.assertIsNotNone(cl.cdc)
        self.assertIsNotNone(cl.webhooks)
        self.assertIsNotNone(cl.finops)
        self.assertIsNotNone(cl.diagnostics)
        self.assertIsNotNone(cl.chaos)
        self.assertIsNotNone(cl.pool)
        self.assertIsNotNone(cl.storage_pipe)
        self.assertIsNotNone(cl.rootfs)
        self.assertIsNotNone(cl.dns)
        self.assertIsNotNone(cl.migration)

    @patch("subprocess.run")
    def test_storage_pipe_benchmark(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="100% SHA-256 Bit-Perfect Match", stderr="")
        res = self.enterprise_client.storage_pipe.benchmark(size_mb=10, part_size_mb=5, concurrency=2)
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("100% SHA-256 Bit-Perfect Match", res["stdout"])

    @patch("subprocess.run")
    def test_pool_probe(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='{"engine_mode": "mock_pool", "status": "READY"}', stderr="")
        probe = self.enterprise_client.pool.probe()
        self.assertIn("engine_mode", probe)

    @patch("subprocess.run")
    def test_dns_probe(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='{"engine_mode": "mock_xdp", "status": "READY"}', stderr="")
        probe = self.enterprise_client.dns.probe()
        self.assertIn("engine_mode", probe)

    @patch("subprocess.run")
    def test_migration_benchmark(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="100% Bit-Perfect Encode/Decode", stderr="")
        res = self.enterprise_client.migration.benchmark(sessions=1000)
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("100% Bit-Perfect Encode/Decode", res["stdout"])

    def test_speculative_branch_race_and_wal_rewind(self):
        candidates = [
            {"id": "c1", "patch": "fix syntax"},
            {"id": "c2", "patch": "fix logic"}
        ]
        res = self.enterprise_client.race(candidates=candidates)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["winner_id"], "c1")
        self.assertEqual(len(res["branches"]), 2)

        rewind_res = self.enterprise_client.rewind_database(target_lsn="16/B374D848", tenant_id="tenant-test")
        self.assertIn(rewind_res["status"], ("rewound", "RECOVERED"))
        self.assertEqual(rewind_res["tenant_id"], "tenant-test")
        self.assertIn("postgres", rewind_res["db_url"])

    def test_sandbox_pty_and_l4_port_forwarding(self):
        sbx_data = {
            "id": "sbx-test-01",
            "runtime": "python",
            "state": "running",
            "has_db": True,
            "db_port": 5432,
            "created_at": "2026-11-15T00:00:00Z"
        }
        sbx = nephis.sandbox.Sandbox(self.enterprise_client, sbx_data)
        pty = sbx.pty_info()
        self.assertIn(pty["status"], ("ready", "connected"))
        self.assertEqual(pty["terminal"], "xterm-256color")

        exp = sbx.expose_port(5432, service_name="postgres")
        self.assertEqual(exp["status"], "forwarded")
        self.assertEqual(exp["guest_port"], 5432)

        ports = sbx.list_ports()
        self.assertIsInstance(ports, list)

        close = sbx.close_port(exp["host_port"])
        self.assertEqual(close["status"], "closed")


if __name__ == "__main__":
    unittest.main()
