import unittest
from unittest.mock import patch

from nephis import NephisClient


class NephisManagerTests(unittest.TestCase):
    def setUp(self):
        self.client = NephisClient(base_url="https://nephis.invalid", api_key="test-key")

    def test_admin_quarantine_uses_authenticated_provider_route(self):
        with patch.object(self.client, "_request", return_value={"status": "quarantined"}) as request:
            result = self.client.admin.quarantine("tenant-1", reason="test", freeze_sandboxes=False)
        self.assertEqual(result["status"], "quarantined")
        request.assert_called_once_with(
            "POST",
            "/api/v1/admin/tenants/quarantine",
            body={
                "tenant_id": "tenant-1",
                "reason": "test",
                "operator": "nephis-python-sdk",
                "freeze_sandbox": False,
            },
        )

    def test_list_quarantined_reads_provider_result(self):
        with patch.object(
            self.client,
            "_request",
            return_value={"quarantined_tenants": ["tenant-1", "tenant-2"]},
        ):
            self.assertEqual(self.client.admin.list_quarantined(), ["tenant-1", "tenant-2"])

    def test_unimplemented_managers_do_not_claim_synthetic_success(self):
        operations = (
            lambda: self.client.admin.list_nodes(),
            lambda: self.client.specbox.warm(),
            lambda: self.client.ozz.fuzz(),
            lambda: self.client.lazylog.append("tenant-1"),
            lambda: self.client.anvil.verify(),
            lambda: self.client.research.verify(),
        )
        for operation in operations:
            with self.subTest(operation=operation):
                with self.assertRaises(NotImplementedError):
                    operation()


if __name__ == "__main__":
    unittest.main()
