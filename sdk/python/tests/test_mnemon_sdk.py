import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import patch, MagicMock
from mnemon import MnemonClient, MnemonException, TenantStatus, QueryResult


def test_mnemon_init():
    client = MnemonClient(api_url="http://localhost:9090", api_key="nephis_live_test123")
    assert client.api_url == "http://localhost:9090"
    assert client.api_key == "nephis_live_test123"
    headers = client._headers()
    assert headers["Authorization"] == "Bearer nephis_live_test123"
    assert headers["X-API-Key"] == "nephis_live_test123"


@patch("requests.get")
def test_schema_diff(mock_get):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "diff": "ALTER TABLE users ADD COLUMN phone text;",
        "migration_ddl": "ALTER TABLE users ADD COLUMN phone text;",
    }
    mock_get.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    res = client.schema_diff("tenant1", "feat_branch", parent_branch="main")

    assert "ALTER TABLE" in res["diff"]
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "v1/tenants/branch/diff" in args[0]
    assert kwargs["params"]["tenant_id"] == "tenant1"
    assert kwargs["params"]["branch_id"] == "feat_branch"


@patch("requests.post")
def test_reset_branch(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"status": "ok", "duration_ms": 12.5}
    mock_post.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    res = client.reset_branch("tenant1", "feat_branch")

    assert res["status"] == "ok"
    assert res["duration_ms"] == 12.5
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "v1/tenants/branch/reset" in args[0]
    assert kwargs["json"]["tenant_id"] == "tenant1"
    assert kwargs["json"]["branch_id"] == "feat_branch"


@patch("requests.post")
def test_time_travel(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "status": "ok",
        "branch_id": "backup_point",
        "database_url": "postgresql://postgres:secret@127.0.0.1:5432/backup_point",
    }
    mock_post.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    res = client.time_travel("tenant1", "backup_point", "2026-11-13T10:00:00Z")

    assert res["branch_id"] == "backup_point"
    assert "backup_point" in res["database_url"]
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "v1/tenants/branch/time-travel" in args[0]


@patch("requests.post")
def test_search(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "rows": [{"id": 1, "title": "test"}],
        "index_mode": "bm25",
        "query": "test query",
    }
    mock_post.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    res = client.search("tenant1", "documents", "test query", columns=["id", "title"])

    assert res["index_mode"] == "bm25"
    assert len(res["rows"]) == 1
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "v1/tenants/search" in args[0]


@patch("requests.put")
def test_storage_put(mock_put):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"status": "created", "key": "avatar.png"}
    mock_put.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    res = client.storage_put("tenant1", "main", "avatar.png", b"filedata", "image/png")

    assert res["status"] == "created"
    mock_put.assert_called_once()
    args, kwargs = mock_put.call_args
    assert "storage/v1/tenant1/main/object/avatar.png" in args[0]


@patch("requests.get")
def test_storage_get(mock_get):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.content = b"filedata_contents"
    mock_get.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    content = client.storage_get("tenant1", "main", "avatar.png")

    assert content == b"filedata_contents"
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "storage/v1/tenant1/main/object/avatar.png" in args[0]


@patch("requests.get")
def test_rest_query(mock_get):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [{"id": 1, "name": "Alice"}]
    mock_get.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    rows = client.rest_query("tenant1", "users", params={"id": "eq.1"})

    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "rest/v1/tenant1/users" in args[0]


@patch("requests.post")
@patch("requests.get")
def test_lethe_cdc(mock_get, mock_post):
    # Mock CDC publish
    mock_post_resp = MagicMock()
    mock_post_resp.ok = True
    mock_post_resp.json.return_value = {"status": "published", "id": "cdc_1", "dispatched": 1}
    mock_post.return_value = mock_post_resp

    # Mock CDC stats
    mock_get_resp = MagicMock()
    mock_get_resp.ok = True
    mock_get_resp.json.return_value = {
        "project_id": "tenant1",
        "total_ingested": 10,
        "total_dispatched": 10,
        "active_subscribers": 1,
        "buffered_events": 10,
    }
    mock_get.return_value = mock_get_resp

    client = MnemonClient(api_key="test-key")
    pub = client.publish_cdc("tenant1", "orders", "INSERT", {"id": 101, "total": 99.0})
    assert pub["status"] == "published"
    assert pub["id"] == "cdc_1"

    stats = client.get_cdc_stats("tenant1")
    assert stats["total_ingested"] == 10
    assert stats["active_subscribers"] == 1


@patch("requests.post")
@patch("requests.get")
def test_pitr_and_snapshots(mock_get, mock_post):
    client = MnemonClient(api_key="test-key")

    # 1. Snapshot Create
    mock_post_snap = MagicMock()
    mock_post_snap.ok = True
    mock_post_snap.json.return_value = {"id": "snp_123", "snapshot_lsn": "0/16B0000"}
    mock_post.return_value = mock_post_snap

    snap = client.create_snapshot("prj_1", name="backup_1")
    assert snap["id"] == "snp_123"

    # 2. Snapshot List
    mock_get_snaps = MagicMock()
    mock_get_snaps.ok = True
    mock_get_snaps.json.return_value = {"snapshots": [{"id": "snp_123"}]}
    mock_get.return_value = mock_get_snaps

    snaps = client.list_snapshots("prj_1")
    assert len(snaps) == 1
    assert snaps[0]["id"] == "snp_123"

    # 3. PITR Timelines
    mock_get_timeline = MagicMock()
    mock_get_timeline.ok = True
    mock_get_timeline.json.return_value = {"timeline": {"timeline_id": 1, "retention_days": 7}}
    mock_get.return_value = mock_get_timeline

    tl = client.get_pitr_timelines("prj_1")
    assert tl["timeline"]["retention_days"] == 7

    # 4. PITR Restore
    mock_post_restore = MagicMock()
    mock_post_restore.ok = True
    mock_post_restore.json.return_value = {"status": "restored", "recovered_branch_id": "br_rec_1"}
    mock_post.return_value = mock_post_restore

    rec = client.restore_pitr("prj_1", "pitr_branch", 0x16B0000)
    assert rec["status"] == "restored"
    assert rec["recovered_branch_id"] == "br_rec_1"


@patch("requests.post")
@patch("requests.get")
def test_mnemon_admin_and_scaling(mock_get, mock_post):
    client = MnemonClient(api_url="http://localhost:9090", api_key="nephis_live_admin")

    # 1. configure_scaling
    mock_post_scale = MagicMock()
    mock_post_scale.ok = True
    mock_post_scale.json.return_value = {"status": "configured", "min_acu": 1, "max_acu": 4}
    mock_post.return_value = mock_post_scale
    res = client.configure_scaling("prj_1", min_acu=1, max_acu=4)
    assert res["status"] == "configured"

    # 2. kill_query
    mock_post_kill = MagicMock()
    mock_post_kill.ok = True
    mock_post_kill.json.return_value = {"killed": 1, "pid": 1234}
    mock_post.return_value = mock_post_kill
    res = client.kill_query(pid=1234)
    assert res["killed"] == 1

    # 3. reap_branches
    mock_post_reap = MagicMock()
    mock_post_reap.ok = True
    mock_post_reap.json.return_value = {"reaped": 5, "reclaimed_bytes": 10485760}
    mock_post.return_value = mock_post_reap
    res = client.reap_branches(max_age_hours=12)
    assert res["reaped"] == 5

    # 4. quarantine_tenant
    mock_post_quar = MagicMock()
    mock_post_quar.ok = True
    mock_post_quar.json.return_value = {"status": "quarantined", "tenant_id": "prj_bad"}
    mock_post.return_value = mock_post_quar
    res = client.quarantine_tenant("prj_bad")
    assert res["status"] == "quarantined"

    # 5. IP allowlist
    mock_get_ip = MagicMock()
    mock_get_ip.ok = True
    mock_get_ip.json.return_value = {"cidrs": ["10.0.0.0/8"]}
    mock_get.return_value = mock_get_ip
    res = client.get_ip_allowlist("prj_1")
    assert "10.0.0.0/8" in res["cidrs"]



