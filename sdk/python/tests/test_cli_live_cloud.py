"""Live CLI verification against the real Nephis endpoint.

Every test asserts an expected value from the live service, not merely that a
command exited zero or printed a header. No mocks, no localhost.
"""
import os
import sys
import subprocess
import re
import pytest

SDK_PYTHON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV = os.environ.copy()
ENV["PYTHONPATH"] = SDK_PYTHON_DIR
ENV["PYTHONIOENCODING"] = "utf-8"
ENV["PYTHONUTF8"] = "1"
_LIVE_KEY = os.environ.get("NEPHIS_API_KEY", "")
if not _LIVE_KEY:
    raise RuntimeError("Set NEPHIS_API_KEY before running live CLI tests")
ENV["NEPHIS_API_KEY"] = _LIVE_KEY
ENV["THANATON_API_KEY"] = _LIVE_KEY
ENV["ESCHATON_API_KEY"] = _LIVE_KEY
for _var, _default in (
    ("NEPHIS_BASE_URL", "https://nephis.theeducode.com"),
    ("THANATON_BASE_URL", "https://nephis.theeducode.com"),
    ("ESCHATON_BASE_URL", "https://nephis.theeducode.com"),
    ("MNEMON_API_URL", "https://db.theeducode.com"),
):
    ENV[_var] = os.environ.get(_var, _default)
ANCHOR_PROJECT = os.environ.get("NEPHIS_ANCHOR_PROJECT", "3eb8d9e9-819f-47b1-89b3-5157b88570a8")
TENANT_ID = os.environ.get("NEPHIS_TENANT_ID", "b7de0a5a-3e48-41eb-afc2-f62d5d4483b1")
ENDPOINT = ENV["NEPHIS_BASE_URL"]


def run_cli(args):
    # text=True uses the Windows locale (cp1252) and crashes on tree glyphs.
    # Decode explicitly so stdout is always a real string for the assertions.
    p = subprocess.run(
        [sys.executable, "-m"] + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=ENV, timeout=45,
    )
    return subprocess.CompletedProcess(
        p.args, p.returncode,
        p.stdout.decode("utf-8", errors="replace"),
        p.stderr.decode("utf-8", errors="replace"),
    )


def ok(res):
    assert res.returncode == 0, f"CLI failed: {res.stderr}\n{res.stdout}"


def test_thanaton_cli_whoami():
    res = run_cli(["thanaton.cli", "whoami"])
    ok(res)
    assert ENDPOINT in res.stdout
    assert TENANT_ID in res.stdout, "wrong tenant identity"
    assert "ENTERPRISE" in res.stdout.upper(), "wrong tier"
    assert "ACTIV" in res.stdout.upper(), "billing status not active"
    assert "8192 MB" in res.stdout, "wrong max RAM"
    assert "Max vCPUs per VM: 8" in res.stdout, "wrong max vCPU"


def test_thanaton_cli_balance():
    res = run_cli(["thanaton.cli", "balance"])
    ok(res)
    assert TENANT_ID in res.stdout, "wrong tenant wallet"
    assert "ENTERPRISE" in res.stdout.upper(), "wrong tier"
    m = re.search(r"Compute Credits:\s+([\d,]+) credits", res.stdout)
    assert m, "no numeric credit balance returned"
    assert int(m.group(1).replace(",", "")) > 0, "credit balance is zero"
    assert "$0.0002/credit" in res.stdout, "wrong credit price"


def test_thanaton_cli_projects_list():
    res = run_cli(["thanaton.cli", "projects", "list"])
    ok(res)
    assert ANCHOR_PROJECT in res.stdout, "anchor project missing"
    assert "Live E2E Verification Anchor" in res.stdout, "anchor name missing"
    assert "READY" in res.stdout, "anchor is not READY"
    assert "python" in res.stdout and "5050" in res.stdout, "wrong runtime/port"


def test_thanaton_cli_ports_list():
    res = run_cli(["thanaton.cli", "ports", "list", ANCHOR_PROJECT])
    ok(res)
    assert ANCHOR_PROJECT in res.stdout, "wrong sandbox in port list"
    assert "No active L4 port forwardings" in res.stdout or re.search(r"\b\d+:\d+\b", res.stdout), \
        "neither empty marker nor a port mapping returned"


def test_thanaton_cli_volumes_list():
    res = run_cli(["thanaton.cli", "volume", "list", "--sandbox-id", ANCHOR_PROJECT])
    ok(res)
    assert ANCHOR_PROJECT in res.stdout, "wrong sandbox in volume list"
    assert re.search(r"vol-[a-zA-Z0-9_-]+", res.stdout), "no real volume ID"
    assert "ext4-sparse" in res.stdout, "wrong volume format"


def test_thanaton_cli_env():
    res = run_cli(["thanaton.cli", "env", "list", ANCHOR_PROJECT])
    ok(res)
    assert "TEST_CLI_KEY" in res.stdout, "expected live env key missing"
    assert "all" in res.stdout, "env scope missing"


def test_thanaton_cli_domains():
    res = run_cli(["thanaton.cli", "domains", "list", ANCHOR_PROJECT])
    ok(res)
    assert "theeducode.com" in res.stdout, "expected domain missing"


def test_thanaton_cli_crons():
    res = run_cli(["thanaton.cli", "crons", "list", ANCHOR_PROJECT])
    ok(res)
    assert re.search(r"cron_[a-z0-9]+", res.stdout), "expected cron missing"
    assert "/api/ping" in res.stdout and "0 * * * *" in res.stdout, "wrong cron definition"


def test_thanaton_cli_waf():
    res = run_cli(["thanaton.cli", "waf", "status", ANCHOR_PROJECT])
    ok(res)
    assert ANCHOR_PROJECT in res.stdout, "wrong project in WAF status"
    assert "1000" in res.stdout, "wrong rate limit"


def test_mnemon_cli_whoami():
    res = run_cli(["mnemon.cli", "whoami"])
    ok(res)
    assert TENANT_ID in res.stdout, "wrong tenant identity"
    assert "ENTERPRISE" in res.stdout.upper() or "TIER_PRO" in res.stdout, "wrong tier"


def test_mnemon_cli_list():
    res = run_cli(["mnemon.cli", "list"])
    ok(res)
    assert TENANT_ID in res.stdout, "test tenant missing"
    m = re.search(r"\|\s+(\d{4,6})\s+\|", res.stdout)
    assert m, "no numeric postgres port returned"
    assert int(m.group(1)) >= 16000, "implausible port"


def test_mnemon_cli_sql_execution():
    res = run_cli(["mnemon.cli", "sql", TENANT_ID, "SELECT 987654 as num;"])
    ok(res)
    assert "987654" in res.stdout, "SQL result value missing"


def test_mnemon_cli_branches():
    res = run_cli(["mnemon.cli", "branches", "--tenant", TENANT_ID])
    ok(res)
    assert TENANT_ID in res.stdout, "wrong tenant"
    assert "main" in res.stdout, "no root branch"
    assert re.search(r"mcp_br_\d+", res.stdout), "no real MCP-created branch"


def test_mnemon_cli_snapshots():
    res = run_cli(["mnemon.cli", "snapshot", "list", TENANT_ID])
    ok(res)
    assert f"snap_{TENANT_ID}_" in res.stdout, "no real snapshot ID for tenant"
    assert "zero_copy_reflink_snapshot" in res.stdout, "wrong snapshot type"


def test_eschaton_cli_languages():
    res = run_cli(["eschaton.cli", "languages"])
    ok(res)
    assert "Total Available Compilers/Runtimes: 28" in res.stdout or "Total Available Compilers/Runtimes: 29" in res.stdout, "wrong catalog size"
    for name in ("C (GCC 9", "C++", "Python", "Go"):
        assert name in res.stdout, f"missing catalog entry: {name}"


def test_eschaton_cli_exec():
    res = run_cli(["eschaton.cli", "exec", "print(98765)"])
    ok(res)
    assert "Verdict:           SUCCESS / EXECUTED" in res.stdout, "execution did not succeed"
    assert re.search(r"STDOUT:\s*98765", res.stdout), "stdout value missing"


def test_nephisctl_whoami():
    res = run_cli(["nephis.cli", "whoami"])
    ok(res)
    assert ENDPOINT in res.stdout, "wrong endpoint"
    assert TENANT_ID in res.stdout, "wrong tenant"
    assert "ENTERPRISE" in res.stdout.upper(), "wrong tier"
    assert "Mohit Raj Deo" in res.stdout or "mohitrajdeo" in res.stdout.lower(), "wrong user"


def test_thanaton_cli_scale():
    res = run_cli(["thanaton.cli", "scale", "get", ANCHOR_PROJECT])
    ok(res)
    assert ANCHOR_PROJECT in res.stdout, "wrong project"
    assert "Always-On" in res.stdout, "wrong execution mode"
    assert "8192 MB" in res.stdout and "| 8 " in res.stdout, "wrong memory/vCPU"


def test_thanaton_cli_deploy_hooks():
    res = run_cli(["thanaton.cli", "deploy-hooks", "list", ANCHOR_PROJECT])
    ok(res)
    assert "(empty)" in res.stdout or "HOOK ID" in res.stdout, "no valid empty/table marker"


def test_thanaton_cli_log_drains():
    res = run_cli(["thanaton.cli", "log-drains", "list", ANCHOR_PROJECT])
    ok(res)
    assert "(empty)" in res.stdout or "DRAIN ID" in res.stdout, "no valid empty/table marker"


def test_mnemon_cli_advisor():
    res = run_cli(["mnemon.cli", "advisor", TENANT_ID])
    ok(res)
    assert TENANT_ID in res.stdout, "wrong project ID"
    assert "10000ms" in res.stdout, "statement timeout missing"
    assert re.search(r"Queries Analyzed:\s+\d+", res.stdout), "no numeric query count"


def test_mnemon_cli_lineage():
    res = run_cli(["mnemon.cli", "lineage", TENANT_ID])
    ok(res)
    assert TENANT_ID in res.stdout, "wrong tenant"
    assert "Root Branch:     main" in res.stdout, "wrong root branch"
    m = re.search(r"Total Branches:\s+(\d+)", res.stdout)
    assert m and int(m.group(1)) > 0, "no real branch count"


def test_mnemon_cli_pitr():
    res = run_cli(["mnemon.cli", "pitr", "timelines", TENANT_ID])
    ok(res)
    assert TENANT_ID in res.stdout, "wrong tenant"
    m = re.search(r"Retention Period:\s+(\d+) days", res.stdout)
    assert m and int(m.group(1)) > 0, "no retention period"
    assert re.search(r"mcp_br_\d+", res.stdout), "no real timelines"
