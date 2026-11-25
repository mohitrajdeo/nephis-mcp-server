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


@patch("requests.post")
def test_schema_diff(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "diff": "ALTER TABLE users ADD COLUMN phone text;",
        "migration_ddl": "ALTER TABLE users ADD COLUMN phone text;",
    }
    mock_post.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    res = client.schema_diff("tenant1", "feat_branch", parent_branch="main")

    assert "ALTER TABLE" in res["diff"]
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "v1/projects/tenant1/branches/feat_branch/diff" in args[0]
    assert kwargs["json"] == {}


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
    assert "v1/projects/tenant1/branches/feat_branch/reset" in args[0]
    assert kwargs["json"] == {}


@patch("requests.post")
def test_time_travel(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "status": "ok",
        "branch_name": "backup_point",
    }
    mock_post.return_value = mock_resp

    client = MnemonClient(api_key="test-key")
    res = client.time_travel("tenant1", "backup_point", "2026-11-13T10:00:00Z")

    assert res["branch_name"] == "backup_point"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "v1/projects/tenant1/branches/time-travel" in args[0]
    assert kwargs["json"] == {"branch_name": "backup_point", "target_time": "2026-11-13T10:00:00Z"}


def test_search_fails_explicitly_without_provider_endpoint():
    client = MnemonClient(api_key="test-key")
    with pytest.raises(NotImplementedError):
        client.search("tenant1", "documents", "test query", columns=["id", "title"])


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
    client = MnemonClient(api_url="http://localhost:9090", api_key="test-admin")

    # 1. configure_scaling
    mock_post_scale = MagicMock()
    mock_post_scale.ok = True
    mock_post_scale.json.return_value = {"status": "configured", "min_acu": 1, "max_acu": 4}
    mock_post.return_value = mock_post_scale
    res = client.configure_scaling("prj_1", min_acu=1, max_acu=4)
    assert res["status"] == "configured"
    assert mock_post.call_args.kwargs["json"]["idle_suspend_seconds"] == 300
    assert "auto_freeze_sec" not in mock_post.call_args.kwargs["json"]

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
    mock_get_ip.json.return_value = {"ip_allowlist": {"allowed_ips": ["10.0.0.0/8"]}}
    mock_get.return_value = mock_get_ip
    res = client.get_ip_allowlist("prj_1")
    assert "10.0.0.0/8" in res["ip_allowlist"]["allowed_ips"]


@patch("requests.post")
def test_branch_database_uses_supported_project_route(mock_post):
    client = MnemonClient(api_url="http://localhost:9090", api_key="test-key")
    mock_post.return_value.ok = True
    mock_post.return_value.json.return_value = {
        "id": "br_prj_1_feat",
        "name": "feat",
        "target_lsn": 23803712,
    }
    res_branch = client.branch_database(
        tenant_id="prj_1",
        new_branch="feat",
        target_lsn="0/16B3740",
    )
    assert res_branch["name"] == "feat"
    mock_post.assert_called_with(
        "http://localhost:9090/v1/projects/prj_1/branches",
        json={"name": "feat", "parent_branch": "main", "target_lsn": 23803712},
        headers=client._headers(),
        timeout=30,
    )

    with pytest.raises(NotImplementedError):
        client.branch_database(tenant_id="prj_1", new_branch="pii", mask_pii=True)
    with pytest.raises(NotImplementedError):
        client.merge_branch(tenant_id="prj_1", branch_id="feat")


@patch("requests.post")
def test_query_uses_project_scoped_sql_route_and_rejects_fake_time_travel(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"rows": [{"answer": 1}], "duration_ms": 2.0}
    mock_post.return_value = mock_resp
    client = MnemonClient(api_url="http://localhost:9090", api_key="test-key")
    result = client.query("prj_1", "SELECT 1")
    assert result.output == '[{"answer":1}]'
    assert result.duration_ms == 2.0
    args, kwargs = mock_post.call_args
    assert args[0] == "http://localhost:9090/v1/projects/prj_1/sql"
    assert kwargs["json"] == {"query": "SELECT 1"}
    with pytest.raises(NotImplementedError):
        client.query("prj_1", "SELECT 1", as_of_lsn="0/1")


@patch("requests.post")
def test_create_database_uses_project_route_without_invented_connection_string(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"id": "mn_prj_tenant_a_tenant_a", "tenant_id": "tenant_a"}
    mock_post.return_value = mock_resp
    client = MnemonClient(api_url="http://localhost:9090", api_key="test-key")
    result = client.create_database("tenant_a")
    assert "connection_string" not in result
    args, kwargs = mock_post.call_args
    assert args[0] == "http://localhost:9090/v1/projects"
    assert kwargs["json"] == {"name": "tenant_a", "tenant_id": "tenant_a", "region": "us-east-1"}


def test_live_tenant_database_listing():
    from live_config import MNEMON_URL, get_live_api_key
    client = MnemonClient(api_url=MNEMON_URL, api_key=get_live_api_key())
    dbs = client.list_databases()
    assert isinstance(dbs, list)


def test_live_sqlite_query_and_execution():
    from live_config import MNEMON_URL, get_live_api_key
    client = MnemonClient(api_url=MNEMON_URL, api_key=get_live_api_key())
    client.sqlite_provision("test_live_py")
    res = client.sqlite_query("test_live_py", "SELECT 42 as answer;")
    assert res["status"] == "success"
    assert res["result"] == [{"answer": 42}]
    assert res["duration_ms"] > 0


def test_live_postgresql_sql_execution():
    import urllib.request, json, ssl
    from live_config import NEPHIS_URL, get_live_api_key, _DEFAULT_SSL_CTX
    api_key = get_live_api_key()
    url = f"{NEPHIS_URL}/v1/db/v1/tenants/sql"
    req = urllib.request.Request(
        url,
        data=json.dumps({"tenant_id": "live_db", "query": "SELECT 1 as num;"}).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "X-API-Key": api_key,
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        res = json.loads(resp.read().decode())
        assert res.get("status") == "success"
        assert res.get("row_count") == 1
        assert res.get("rows") == [{"num": 1}]
        assert res.get("duration_ms") > 0


def test_live_zero_copy_reflink_branching():
    import urllib.request, json, ssl, time
    from live_config import NEPHIS_URL, get_live_api_key, _DEFAULT_SSL_CTX
    api_key = get_live_api_key()
    branch_name = f"test_br_{int(time.time())}"
    url = f"{NEPHIS_URL}/v1/db/v1/tenants/branch"
    req = urllib.request.Request(
        url,
        data=json.dumps({"tenant_id": "live_db", "new_branch": branch_name, "parent_branch": "main"}).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "X-API-Key": api_key,
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        res = json.loads(resp.read().decode())
        assert res.get("branch_id") == branch_name
        assert res.get("port") > 16000
        assert res.get("parent_branch_id") in ["main", None]


def test_live_redis_execution():
    import urllib.request, json, time
    from live_config import get_live_api_key, _DEFAULT_SSL_CTX
    api_key = get_live_api_key()
    tenant = f"py_rd_{int(time.time())}"
    base = "https://mnemon.theeducode.com"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "X-API-Key": api_key,
        "Authorization": f"Bearer {api_key}"
    }

    # 1. Provision Redis tenant
    prov_req = urllib.request.Request(f"{base}/v1/redis/tenants", data=json.dumps({"tenant_id": tenant, "max_memory_mb": 16}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(prov_req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        prov = json.loads(resp.read().decode())
        assert prov.get("status") in ["created", "success"]

    # 2. SET command
    set_req = urllib.request.Request(f"{base}/v1/redis/tenants/query", data=json.dumps({"tenant_id": tenant, "command": ["SET", "py_live_token", "LIVE_PY_REDIS_PASS"]}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(set_req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        res_set = json.loads(resp.read().decode())
        assert res_set.get("status") == "success"

    # 3. GET command
    get_req = urllib.request.Request(f"{base}/v1/redis/tenants/query", data=json.dumps({"tenant_id": tenant, "command": ["GET", "py_live_token"]}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(get_req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        res_get = json.loads(resp.read().decode())
        assert res_get.get("status") == "success"
        assert res_get.get("result") == "LIVE_PY_REDIS_PASS"


def test_live_mongodb_execution():
    import urllib.request, json, time
    from live_config import get_live_api_key, _DEFAULT_SSL_CTX
    api_key = get_live_api_key()
    tenant = f"py_mg_{int(time.time())}"
    base = "https://mnemon.theeducode.com"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "X-API-Key": api_key,
        "Authorization": f"Bearer {api_key}"
    }

    # 1. Provision Mongo tenant
    prov_req = urllib.request.Request(f"{base}/v1/mongodb/tenants", data=json.dumps({"tenant_id": tenant, "memory_max_mb": 64}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(prov_req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        prov = json.loads(resp.read().decode())
        assert prov.get("status") in ["created", "success"]

    # 2. Insert document
    ins_req = urllib.request.Request(f"{base}/v1/mongodb/tenants/query", data=json.dumps({"tenant_id": tenant, "query": "db.py_bench.insertOne({framework: 'pytest', status: 'pass'})"}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(ins_req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        ins = json.loads(resp.read().decode())
        assert ins.get("status") == "success"

    # 3. Find document
    find_req = urllib.request.Request(f"{base}/v1/mongodb/tenants/query", data=json.dumps({"tenant_id": tenant, "query": "db.py_bench.find().toArray()"}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(find_req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
        find = json.loads(resp.read().decode())
        assert find.get("status") == "success"
        assert len(find.get("result", [])) >= 1






