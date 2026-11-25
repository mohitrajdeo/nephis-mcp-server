#!/usr/bin/env python3
"""
================================================================================
  ESCHATON CONTROL PLANE UNIFIED CLI (eschatonctl)
  Full Multi-Tier Control: Tier 1 (Nginx) -> Tier 2 (Gateway) -> Tier 3 (Brain)
================================================================================
"""

import sys
import os
import json
import time
import argparse
import ssl

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass
import socket
import uuid
from datetime import datetime, timezone

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- Configuration & Credentials ---
GATEWAY_URL = os.getenv("ESCHATON_GATEWAY_URL", "https://nephis.theeducode.com")
PORTAL_URL = os.getenv("ESCHATON_PORTAL_URL", "https://compiler.theeducode.com")
ADMIN_KEY = os.getenv("ESCHATON_ADMIN_KEY", "").strip()
MASTER_KEY = os.getenv("ESCHATON_MASTER_KEY", "").strip()
DEFAULT_API_KEY = (os.getenv("ESCHATON_API_KEY") or os.getenv("NEPHIS_API_KEY") or "").strip()

AWS_PROFILE = os.getenv("AWS_PROFILE", "sujit2")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_INSTANCE_ID = os.getenv("ESCHATON_INSTANCE_ID", "i-006d576ab903ac02e")

# --- Safe Terminal Formatting (Compatible with all Windows CodePages) ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'
    END = '\033[0m'

def colorize(text, color):
    # Disable color if stdout is piped or non-tty
    if not sys.stdout.isatty():
        return str(text)
    return f"{color}{text}{Colors.END}"

def print_header(title):
    print(colorize(f"\n[*] {title}", Colors.BOLD + Colors.CYAN))
    print(colorize("-" * 72, Colors.DIM))

def print_success(msg):
    print(colorize(f"[+] {msg}", Colors.GREEN))

def print_error(msg):
    print(colorize(f"[-] {msg}", Colors.FAIL), file=sys.stderr)

def print_warning(msg):
    print(colorize(f"[!] {msg}", Colors.WARNING))

def require_admin_key(master=False):
    key = MASTER_KEY if master else ADMIN_KEY
    env_name = "ESCHATON_MASTER_KEY" if master else "ESCHATON_ADMIN_KEY"
    if not key:
        print_error(f"Set {env_name} to use this administrative command.")
        return None
    return key

def require_api_key(key=None):
    resolved = (key or DEFAULT_API_KEY or "").strip()
    if not resolved:
        print_error("Set ESCHATON_API_KEY (or a scoped NEPHIS_API_KEY), or pass --key.")
        return None
    return resolved

# --- HTTP Helpers ---
def http_get(url, headers=None, timeout=30):
    req_headers = {"User-Agent": "Eschaton-CLI/2.0"}
    if headers:
        req_headers.update(headers)
    try:
        import requests
        return requests.get(url, headers=req_headers, timeout=timeout)
    except Exception as e:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, headers=req_headers)
        class DummyResp:
            def __init__(self, status_code, text):
                self.status_code = status_code
                self.text = text
            def json(self):
                return json.loads(self.text)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode('utf-8')
                return DummyResp(resp.status, data)
        except urllib.error.HTTPError as he:
            err_data = he.read().decode('utf-8', errors='replace')
            return DummyResp(he.code, err_data)
        except Exception as ue:
            raise RuntimeError(f"HTTP GET failed: {ue}")

def http_post(url, json_data, headers=None, timeout=15):
    req_headers = {'Content-Type': 'application/json', "User-Agent": "Eschaton-CLI/2.0"}
    if headers:
        req_headers.update(headers)
    if url.rstrip("/").endswith("/v1/execute") and not req_headers.get("Idempotency-Key"):
        req_headers["Idempotency-Key"] = str(uuid.uuid4())
    try:
        import requests
        return requests.post(url, json=json_data, headers=req_headers, timeout=timeout)
    except Exception as e:
        import urllib.request
        import urllib.error
        data = json.dumps(json_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=req_headers)
        class DummyResp:
            def __init__(self, status_code, text):
                self.status_code = status_code
                self.text = text
            def json(self):
                return json.loads(self.text)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res_text = resp.read().decode('utf-8')
                return DummyResp(resp.status, res_text)
        except urllib.error.HTTPError as he:
            err_data = he.read().decode('utf-8', errors='replace')
            return DummyResp(he.code, err_data)
        except Exception as ue:
            raise RuntimeError(f"HTTP POST failed: {ue}")

# --- AWS SSM Helper for Host-Level Actions (Nginx reload, Docker logs) ---
_ssm_client = None
def get_ssm_client():
    global _ssm_client
    if _ssm_client is None:
        try:
            import boto3
            session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
            _ssm_client = session.client("ssm")
        except Exception as e:
            try:
                import boto3
                session = boto3.Session(region_name=AWS_REGION)
                _ssm_client = session.client("ssm")
            except Exception:
                raise RuntimeError(f"Failed to initialize AWS SSM client: {e}")
    return _ssm_client

def run_host_command(commands, desc="Executing command on host", timeout=30):
    ssm = get_ssm_client()
    if isinstance(commands, str):
        commands = [commands]
    
    response = ssm.send_command(
        InstanceIds=[AWS_INSTANCE_ID],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": commands}
    )
    cmd_id = response["Command"]["CommandId"]
    
    start = time.time()
    time.sleep(1.5)
    while time.time() - start < timeout:
        try:
            res = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=AWS_INSTANCE_ID)
            status = res["Status"]
            if status in ["Success", "Failed", "TimedOut", "Cancelled"]:
                if status == "Success":
                    return res.get("StandardOutputContent", "")
                else:
                    err = res.get("StandardErrorContent", "") or res.get("StandardOutputContent", "")
                    raise RuntimeError(f"Host command failed with status {status}: {err}")
        except ssm.exceptions.InvocationDoesNotExist:
            pass
        time.sleep(1)
    raise TimeoutError(f"Host command timed out after {timeout} seconds")

# ==============================================================================
# COMMAND IMPLEMENTATIONS
# ==============================================================================

# ----------------- GLOBAL STATUS -----------------
def cmd_status(args):
    print_header("Eschaton Multi-Tier Fleet Status")
    
    status_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nginx": {},
        "gateway": {},
        "brain": {}
    }

    # 1. Tier 1: Nginx / SSL check
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection(('eschaton.theeducode.com', 443), timeout=4) as sock:
            with ctx.wrap_socket(sock, server_hostname='eschaton.theeducode.com') as ssock:
                cert = ssock.getpeercert()
                expiry = cert.get('notAfter')
                status_summary["nginx"] = {"status": "ONLINE", "ssl_expiry": expiry}
                print(f"[{colorize('TIER 1 - NGINX', Colors.BOLD)}]   "
                      f"SSL Edge Proxy: {colorize('ONLINE', Colors.GREEN)} (Valid until {expiry})")
    except Exception as e:
        status_summary["nginx"] = {"status": "ERROR", "error": str(e)}
        print(f"[{colorize('TIER 1 - NGINX', Colors.BOLD)}]   "
              f"SSL Edge Proxy: {colorize('ERROR', Colors.FAIL)} ({e})")

    # 2. Tier 2: Gateway Health check
    try:
        resp = http_get(f"{GATEWAY_URL}/v1/livez", timeout=4)
        if resp.status_code != 200:
            resp = http_get(f"{GATEWAY_URL}/health", timeout=4)
        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception:
                data = {"status": "ONLINE", "raw": resp.text.strip()[:60]}
            status_summary["gateway"] = data
            print(f"[{colorize('TIER 2 - GATEWAY', Colors.BOLD)}] "
                  f"SaaS Control:   {colorize('HEALTHY', Colors.GREEN)} "
                  f"(Upstream: {data.get('upstream', 'live')}, v{data.get('version', '2.0')})")
        else:
            status_summary["gateway"] = {"status": "ERROR", "code": resp.status_code}
            print(f"[{colorize('TIER 2 - GATEWAY', Colors.BOLD)}] "
                  f"SaaS Control:   {colorize('FAIL', Colors.FAIL)} (HTTP {resp.status_code})")
    except Exception as e:
        status_summary["gateway"] = {"status": "ERROR", "error": str(e)}
        print(f"[{colorize('TIER 2 - GATEWAY', Colors.BOLD)}] "
              f"SaaS Control:   {colorize('UNREACHABLE', Colors.FAIL)} ({e})")

    # 3. Tier 3: Brain Telemetry check (via Gateway Admin API)
    try:
        resp = http_get(
            f"{GATEWAY_URL}/v1/admin/telemetry",
            headers={"X-Admin-Key": ADMIN_KEY},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            status_summary["brain"] = data
            metrics = data.get("metrics", {})
            active_null = data.get("active_nullifiers", 0)
            active_anni = data.get("active_annihilators", 0)
            queue_depth = metrics.get("queue_depth", 0)
            completed = data.get("telemetry", {}).get("submissions_completed", 0)
            
            print(f"[{colorize('TIER 3 - BRAIN', Colors.BOLD)}]   "
                  f"Engine Cluster: {colorize('ONLINE', Colors.GREEN)} "
                  f"({active_null} Nullifier, {active_anni} Annihilator | Queue: {queue_depth} | Completed: {completed})")
        else:
            status_summary["brain"] = {"status": "ERROR", "code": resp.status_code}
            print(f"[{colorize('TIER 3 - BRAIN', Colors.BOLD)}]   "
              f"Engine Cluster: {colorize('AUTH_ERROR', Colors.WARNING)} (HTTP {resp.status_code})")
    except Exception as e:
        status_summary["brain"] = {"status": "ERROR", "error": str(e)}
        print(f"[{colorize('TIER 3 - BRAIN', Colors.BOLD)}]   "
              f"Engine Cluster: {colorize('ERROR', Colors.FAIL)} ({e})")

    if getattr(args, 'json', False):
        print("\n" + json.dumps(status_summary, indent=2))

# ----------------- TIER 1: NGINX COMMANDS -----------------
def cmd_nginx(args):
    action = args.action
    if action == "status":
        print_header("Nginx Edge Proxy Status")
        try:
            out = run_host_command([
                "docker ps --filter 'name=eschaton-nginx' --format 'Container: {{.Names}} | Status: {{.Status}} | Ports: {{.Ports}}'",
                "docker exec eschaton-nginx nginx -v"
            ])
            print(out)
            print_success("Nginx container is running.")
        except Exception as e:
            print_error(f"Failed to query Nginx container: {e}")

    elif action == "test":
        print_header("Nginx Syntax Configuration Test")
        try:
            out = run_host_command("docker exec eschaton-nginx nginx -t")
            print(out)
            print_success("Nginx configuration syntax is valid.")
        except Exception as e:
            print_error(f"Nginx test failed: {e}")

    elif action == "reload":
        print_header("Zero-Downtime Nginx Reload")
        try:
            out = run_host_command("docker exec eschaton-nginx nginx -s reload")
            if out: print(out)
            print_success("Nginx configuration reloaded cleanly without dropping connections.")
        except Exception as e:
            print_error(f"Failed to reload Nginx: {e}")

    elif action == "logs":
        lines = getattr(args, 'lines', 50)
        print_header(f"Nginx Container Logs (Last {lines} Lines)")
        try:
            out = run_host_command(f"docker logs --tail {lines} eschaton-nginx")
            print(out)
        except Exception as e:
            print_error(f"Failed to fetch Nginx logs: {e}")

# ----------------- TIER 2: GATEWAY COMMANDS -----------------
def cmd_gateway(args):
    action = args.action
    if action == "status":
        print_header("SaaS Gateway Health & Upstream")
        try:
            resp = http_get(f"{GATEWAY_URL}/v1/livez")
            if resp.status_code != 200:
                resp = http_get(f"{GATEWAY_URL}/health")
            print(f"Status Code: {colorize(str(resp.status_code), Colors.GREEN if resp.status_code==200 else Colors.FAIL)}")
            try:
                print(json.dumps(resp.json(), indent=2))
            except Exception:
                print(resp.text[:300])
        except Exception as e:
            print_error(f"Failed to connect to Gateway: {e}")

    elif action == "telemetry":
        print_header("Live Cluster Telemetry (Via Gateway)")
        admin_key = require_admin_key()
        if not admin_key:
            return
        try:
            resp = http_get(
                f"{GATEWAY_URL}/v1/admin/telemetry",
                headers={"X-Admin-Key": admin_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(json.dumps(data, indent=2))
            else:
                print_error(f"Unauthorized (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            print_error(f"Failed to fetch telemetry: {e}")

    elif action == "tenants":
        print_header("Registered Tenants & Credit Quotas")
        master_key = require_admin_key(master=True)
        if not master_key:
            return
        try:
            resp = http_get(
                f"{PORTAL_URL}/api/master/overview",
                headers={"X-Admin-Master-Key": master_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                tenants = data.get("tenants", [])
                if getattr(args, 'json', False):
                    print(json.dumps(tenants, indent=2))
                    return

                print(f"{'SLUG':<22} {'NAME':<24} {'CREDITS':<12} {'TIER':<10} {'ACTIVE':<8} {'24H USAGE'}")
                print(colorize("-" * 84, Colors.DIM))
                for t in tenants:
                    credits = f"{t.get('credits_balance', 0):,}"
                    active = colorize("YES", Colors.GREEN) if t.get('is_active') else colorize("NO", Colors.FAIL)
                    print(f"{t.get('slug', '')[:20]:<22} {t.get('name', '')[:22]:<24} {credits:<12} {t.get('tier', 'free'):<10} {active:<17} {t.get('daily_usage_count', 0)}")
                print_success(f"Retrieved {len(tenants)} registered tenants.")
            else:
                print_error(f"Master API returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            print_error(f"Failed to fetch tenants: {e}")

    elif action == "keys":
        print_header("Active API Keys Overview")
        master_key = require_admin_key(master=True)
        if not master_key:
            return
        try:
            resp = http_get(
                f"{PORTAL_URL}/api/master/overview",
                headers={"X-Admin-Master-Key": master_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                tenants = data.get("tenants", [])
                # Flatten keys from all tenants
                keys = []
                for t in tenants:
                    for k in t.get("keys", []):
                        k["tenant_slug"] = t.get("slug")
                        keys.append(k)

                if getattr(args, 'json', False):
                    print(json.dumps(keys, indent=2))
                    return

                print(f"{'PREFIX':<20} {'TENANT':<20} {'NAME':<22} {'ENV':<8} {'ACTIVE':<8} {'LAST USED'}")
                print(colorize("-" * 88, Colors.DIM))
                for k in keys:
                    active = colorize("YES", Colors.GREEN) if k.get('is_active') else colorize("NO", Colors.FAIL)
                    last_used = k.get('last_used_at') or "Never"
                    if last_used != "Never": last_used = last_used[:10]
                    print(f"{k.get('key_prefix', ''):<20} {k.get('tenant_slug', '')[:18]:<20} {k.get('name', 'Default')[:20]:<22} {k.get('environment', 'live'):<8} {active:<17} {last_used}")
                print_success(f"Retrieved {len(keys)} active API keys.")
            else:
                print_error(f"Master API returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            print_error(f"Failed to fetch API keys: {e}")

    elif action == "topup":
        master_key = require_admin_key(master=True)
        if not master_key:
            return
        tenant_id = args.tenant_id
        amount = args.amount
        reason = getattr(args, 'reason', 'CLI manual top-up')
        print_header(f"Top-Up Credits for Tenant: {tenant_id}")
        try:
            resp = http_post(
                f"{PORTAL_URL}/api/master/adjust-credits",
                json_data={
                    "tenantId": tenant_id,
                    "mode": "add",
                    "amount": int(amount),
                    "reason": reason
                },
                headers={"X-Admin-Master-Key": master_key}
            )
            if resp.status_code == 200:
                res = resp.json()
                print_success(f"Successfully added {amount} credits!")
                print(f"Previous Balance: {res.get('previous_balance'):,}")
                new_bal = f"{res.get('new_balance', 0):,}"
                print(f"New Balance:      {colorize(new_bal, Colors.BOLD + Colors.GREEN)}")
            else:
                print_error(f"Topup failed (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            print_error(f"Failed to adjust credits: {e}")

    elif action == "logs":
        lines = getattr(args, 'lines', 50)
        print_header(f"Gateway Container Logs (Last {lines} Lines)")
        try:
            out = run_host_command(f"docker logs --tail {lines} eschaton-saas-gateway")
            print(out)
        except Exception as e:
            print_error(f"Failed to fetch Gateway logs: {e}")

# ----------------- TIER 3: BRAIN COMMANDS -----------------
def cmd_brain(args):
    action = args.action
    if action == "status" or action == "workers":
        print_header("Brain Compiler Cluster & Worker Nodes")
        admin_key = require_admin_key()
        if not admin_key:
            return
        try:
            resp = http_get(
                f"{GATEWAY_URL}/v1/admin/telemetry",
                headers={"X-Admin-Key": admin_key}
            )
            if resp.status_code == 200:
                data = resp.json()
                workers = data.get("active_workers", [])
                print(f"Uptime:         {data.get('uptime_seconds')} seconds")
                print(f"Active Workers: {len(workers)} ({data.get('active_nullifiers')} Nullifiers, {data.get('active_annihilators')} Annihilators)")
                print(f"Success Rate:   {data.get('telemetry', {}).get('success_rate', 'N/A')}\n")
                
                print(f"{'TYPE':<16} {'RPC ADDRESS':<24} {'CAPACITY':<12} {'IN FLIGHT':<12} {'LAST SEEN'}")
                print(colorize("-" * 80, Colors.DIM))
                for w in workers:
                    w_type = colorize(w.get('type', '').upper(), Colors.CYAN if w.get('type')=='nullifier' else Colors.BLUE)
                    print(f"{w_type:<25} {w.get('rpc_addr', ''):<24} {w.get('capacity', 0):<12} {w.get('in_flight', 0):<12} {w.get('last_seen')}")
            else:
                print_error(f"Failed to query Brain status (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            print_error(f"Failed to connect to Brain: {e}")

    elif action == "metrics":
        print_header("Internal Worker Saturation & Queue Depth (Raw /metrics)")
        try:
            out = run_host_command("curl -s http://127.0.0.1:9010/metrics")
            try:
                parsed = json.loads(out)
                print(json.dumps(parsed, indent=2))
            except Exception:
                print(out)
        except Exception as e:
            print_error(f"Failed to scrape /metrics on host: {e}")

    elif action == "selfcheck":
        print_header("Running Brain 15-Point Internal Compiler Sanity Battery")
        try:
            out = run_host_command("curl -s http://127.0.0.1:9010/selfcheck", timeout=45)
            try:
                parsed = json.loads(out)
                print(json.dumps(parsed, indent=2))
            except Exception:
                print(out)
        except Exception as e:
            print_error(f"Failed to run selfcheck: {e}")

    elif action == "restart":
        print_header("Restarting Engine Worker Fleet Containers")
        try:
            out = run_host_command("docker restart eschaton-brain")
            print(out)
            print_success("Brain container restarted cleanly.")
        except Exception as e:
            print_error(f"Failed to restart containers: {e}")

    elif action == "logs":
        lines = getattr(args, 'lines', 50)
        print_header(f"Brain Container Logs (Last {lines} Lines)")
        try:
            out = run_host_command(f"docker logs --tail {lines} eschaton-brain")
            print(out)
        except Exception as e:
            print_error(f"Failed to fetch Brain logs: {e}")

# ----------------- EXECUTION TEST -----------------
CORE_VOID_LANG_IDS = {
    50, 201, 221,  # C (GCC 9, C17, C23)
    54, 202, 222,  # C++ (GCC 9, C++20, C++23)
}

LANG_MAP = {
    'cpp': 202,
    'c++': 202,
    'c++20': 202,
    'c++23': 222,
    'c': 201,
    'c17': 201,
    'python': 71,
    'py': 71,
    'python3': 71,
    'java': 205,
    'java21': 205,
    'rust': 208,
    'rs': 208,
    'go': 203,
    'golang': 203,
    'js': 207,
    'javascript': 207,
    'node': 207,
    'ts': 209,
    'typescript': 209,
    'sql': 82,
    'zig': 224,
    'kotlin': 206,
    'bash': 212,
    'ruby': 216
}

EXT_MAP = {
    '.cpp': 202,
    '.cc': 202,
    '.cxx': 202,
    '.hpp': 202,
    '.c': 201,
    '.h': 201,
    '.py': 204,
    '.java': 205,
    '.rs': 208,
    '.go': 203,
    '.js': 207,
    '.ts': 209,
    '.sql': 82,
    '.zig': 224,
    '.kt': 206,
    '.sh': 212,
    '.rb': 216
}

def execute_code_payload(lang_id, code, stdin_input="", expected="", suite="Void", key=None, as_json=False):
    api_key = require_api_key(key)
    if not api_key:
        return
    tc = {
        "id": 1,
        "stdin": stdin_input or ""
    }
    if expected:
        tc["expected_output"] = expected

    payload = {
        "language_id": lang_id,
        "suite": suite or "Void",
        "source_code": code,
        "test_cases": [tc]
    }

    start = time.time()
    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "Eschaton-CLI/2.0"
        }

        resp = http_post(f"{GATEWAY_URL}/v1/execute", json_data=payload, headers=headers, timeout=20)
        roundtrip_ms = round((time.time() - start) * 1000, 2)
        
        if resp.status_code == 200:
            data = resp.json()
            if as_json:
                print(json.dumps(data, indent=2))
                return

            print(f"Roundtrip Latency: {colorize(f'{roundtrip_ms} ms', Colors.BOLD + Colors.GREEN)}")
            results = data.get("Results") or []
            if results:
                r = results[0]
                status_id = r.get("status_id")
                passed = r.get("passed", False)
                has_stderr = bool(r.get("stderr"))

                if expected:
                    is_success = (passed or status_id == 3)
                    status_label = "ACCEPTED" if is_success else f"STATUS_{status_id}"
                else:
                    # Execution-only run (no answer key asserted by caller)
                    is_success = (status_id in (0, 3) or (status_id == 4 and not has_stderr))
                    status_label = "SUCCESS / EXECUTED" if is_success else f"STATUS_{status_id}"

                status_color = Colors.GREEN if is_success else Colors.FAIL
                
                print(f"Verdict:           {colorize(status_label, Colors.BOLD + status_color)}")
                print(f"Execution Time:    {r.get('time')} s")
                print(f"Peak Memory:       {r.get('memory')} KB")
                stdout_val = r.get('stdout', '')
                print(f"\nSTDOUT:\n{stdout_val}")
                if r.get('stderr'):
                    print(colorize(f"STDERR:\n{r.get('stderr')}", Colors.WARNING))
            elif data.get("Error"):
                print_error(f"Compilation/Engine Error:\n{data.get('Error')}")
                sys.exit(1)
            else:
                print(json.dumps(data, indent=2))
        else:
            print_error(f"Gateway returned HTTP {resp.status_code}:\n{resp.text}")
            sys.exit(1)
    except Exception as e:
        print_error(f"Execution request failed: {e}")
        sys.exit(1)

def cmd_exec(args):
    lang = args.lang.lower()
    code = args.code
    stdin_input = getattr(args, 'input', '') or ''
    expected = getattr(args, 'expected', '') or ''
    key = getattr(args, 'key', '') or DEFAULT_API_KEY
    lang_id = LANG_MAP.get(lang)
    if not lang_id:
        valid_langs = ", ".join(sorted(set(LANG_MAP.keys())))
        print_error(f"Unrecognized language '{lang}'. Available choices: {valid_langs}")
        sys.exit(1)

    user_suite = getattr(args, 'suite', None)
    if user_suite and user_suite.upper() != "AUTO":
        suite = user_suite
    else:
        suite = "Void" if lang_id in CORE_VOID_LANG_IDS else "Apex"

    print_header(f"Executing {lang.upper()} (Suite: {suite}) against {GATEWAY_URL}")
    execute_code_payload(lang_id, code, stdin_input, expected, suite, key, getattr(args, 'json', False))

def cmd_run(args):
    file_path = args.file
    if not os.path.exists(file_path):
        print_error(f"File not found: {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    lang_id = None
    if getattr(args, 'lang', None):
        lang_id = LANG_MAP.get(args.lang.lower())
    if not lang_id:
        lang_id = EXT_MAP.get(ext)

    if not lang_id:
        print_error(f"Cannot auto-detect language for extension '{ext}'. Specify --lang (e.g. --lang cpp, python, rust, go)")
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()
    except Exception as e:
        print_error(f"Failed to read file {file_path}: {e}")
        sys.exit(1)

    stdin_input = getattr(args, 'input', '') or ''
    if getattr(args, 'input_file', None) and os.path.exists(args.input_file):
        try:
            with open(args.input_file, 'r', encoding='utf-8', errors='replace') as f:
                stdin_input = f.read()
        except Exception as e:
            print_warning(f"Could not read stdin file: {e}")

    expected = getattr(args, 'expected', '') or ''
    if getattr(args, 'expected_file', None) and os.path.exists(args.expected_file):
        try:
            with open(args.expected_file, 'r', encoding='utf-8', errors='replace') as f:
                expected = f.read()
        except Exception as e:
            print_warning(f"Could not read expected file: {e}")

    user_suite = getattr(args, 'suite', None)
    if user_suite and user_suite.upper() != "AUTO":
        suite = user_suite
    else:
        suite = "Void" if lang_id in CORE_VOID_LANG_IDS else "Apex"

    key = getattr(args, 'key', '') or DEFAULT_API_KEY

    print_header(f"Running File: {os.path.basename(file_path)} (Lang ID: {lang_id}, Suite: {suite})")
    execute_code_payload(lang_id, code, stdin_input, expected, suite, key, getattr(args, 'json', False))

def cmd_account(args):
    key = require_api_key(getattr(args, 'key', ''))
    if not key:
        return
    masked_key = f"{key[:12]}...{key[-4:]}" if len(key) > 16 else key
    print_header(f"Fetching Account Quota & Metering for Key: {masked_key}")
    try:
        resp = http_get(f"{GATEWAY_URL}/v1/account", headers={"X-API-Key": key})
        if resp.status_code == 200:
            data = resp.json()
            if getattr(args, 'json', False):
                print(json.dumps(data, indent=2))
                return
            print(f"Tenant ID:         {colorize(data.get('tenant_id'), Colors.BOLD)}")
            print(f"Tier:              {colorize(str(data.get('tier', 'standard')).upper(), Colors.CYAN)}")
            status_text = 'ACTIVE' if data.get('active') else 'SUSPENDED'
            status_col = Colors.GREEN if data.get('active') else Colors.FAIL
            print(f"Status:            {colorize(status_text, status_col)}")
            print(f"Remaining Credits: {colorize(str(data.get('credits', 0)), Colors.BOLD + Colors.GREEN)}")
            rl_str = f"{data.get('rate_limit_rps', 0)} req/s"
            print(f"Rate Limit:        {colorize(rl_str, Colors.WARNING)}")
            print(f"Key Prefix:        {data.get('key_prefix')}")
        else:
            print_error(f"Account check failed (HTTP {resp.status_code}): {resp.text}")
    except Exception as e:
        print_error(f"Failed to query account endpoint: {e}")

def cmd_languages(args):
    key = getattr(args, 'key', '') or DEFAULT_API_KEY
    print_header(f"Supported Compilers & Runtimes ({GATEWAY_URL}/v1/languages)")
    try:
        resp = http_get(f"{GATEWAY_URL}/v1/languages", headers={"X-API-Key": key})
        if resp.status_code == 200:
            data = resp.json()
            if getattr(args, 'json', False):
                print(json.dumps(data, indent=2))
                return
            langs = data.get("languages", data) if isinstance(data, dict) else data
            if not isinstance(langs, list):
                print_warning(f"Unexpected response format: {data}")
                return
            print(f"{'ID':<6} | {'Language / Runtime / Compiler':<50}")
            print("-" * 60)
            for item in langs:
                if isinstance(item, dict):
                    print(f"{item.get('id', ''):<6} | {item.get('name', '')}")
                else:
                    print(f"{item}")
            print(colorize(f"\nTotal Available Compilers/Runtimes: {len(langs)}", Colors.DIM))
        else:
            print_error(f"Failed to fetch languages (HTTP {resp.status_code}): {resp.text}")
    except Exception as e:
        print_error(f"Failed to query languages endpoint: {e}")

def cmd_preflight(args):
    try:
        with open(args.file, "r", encoding="utf-8") as source_file:
            source_code = source_file.read()
        response = http_post(
            f"{GATEWAY_URL}/v1/execute/preflight",
            json_data={"source_code": source_code, "language_id": args.language_id},
            headers={"Content-Type": "application/json", "User-Agent": "Eschaton-CLI/2.1"},
            timeout=15,
        )
        if response.status_code not in (200, 422):
            print_error(f"Preflight request failed (HTTP {response.status_code}): {response.text}")
            sys.exit(1)
        result = response.json()
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result, indent=2))
        if not result.get("passed", False):
            sys.exit(1)
    except FileNotFoundError:
        print_error(f"Source file not found: {args.file}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Preflight did not produce a verdict: {e}")
        sys.exit(1)

# ==============================================================================
# MAIN ENTRYPOINT & CLI PARSER
# ==============================================================================

def dispatch_suite_payload(payload, key=None, as_json=False, title="Executing"):
    api_key = require_api_key(key)
    if not api_key:
        return
    start = time.time()
    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "Eschaton-CLI/2.1"
        }

        # Never replay on a second origin after an ambiguous response: the first
        # service may already have run the code and charged for the execution.
        url = f"{GATEWAY_URL}/v1/execute"
        resp = http_post(url, json_data=payload, headers=headers, timeout=30)

        roundtrip_ms = round((time.time() - start) * 1000, 2)
        if resp.status_code == 200:
            data = resp.json()
            if as_json:
                print(json.dumps(data, indent=2))
                return

            print(f"Roundtrip Latency: {colorize(f'{roundtrip_ms} ms', Colors.BOLD + Colors.GREEN)}")
            results = data.get("Results") or []
            if results:
                print(colorize(f"\n{'='*72}", Colors.DIM))
                print(colorize(f"  {title.upper()} EVALUATION REPORT ({len(results)} Test Cases)", Colors.BOLD + Colors.CYAN))
                print(colorize(f"{'='*72}", Colors.DIM))
                for i, r in enumerate(results, 1):
                    tcid = r.get("test_case_id", i)
                    passed = r.get("passed", False)
                    status_id = r.get("status_id", 0)
                    t_val = r.get("time", 0)
                    m_val = r.get("memory", 0)
                    out = r.get("stdout") or ""
                    err = r.get("stderr") or ""

                    status_str = "ACCEPTED (PASS)" if passed or status_id == 3 else f"FAIL (Status {status_id})"
                    status_color = Colors.GREEN if (passed or status_id == 3) else Colors.FAIL

                    print(f"\n[Test Case #{tcid}] {colorize(status_str, Colors.BOLD + status_color)}")
                    print(f"  * Execution Time : {t_val} s")
                    print(f"  * Peak Memory    : {m_val} KB")
                    if out:
                        print(f"  * STDOUT         : {out}")
                    if err:
                        print(colorize(f"  * DIAGNOSTICS    : {err}", Colors.WARNING))

                print(colorize(f"\n{'='*72}", Colors.DIM))
            elif data.get("Error"):
                print_error(f"Execution Error: {data.get('Error')}")
            else:
                print(json.dumps(data, indent=2))
        else:
            print_error(f"HTTP {resp.status_code} Error: {resp.text}")
    except Exception as e:
        print_error(f"Request failed: {e}")

def resolve_code_and_lang(args):
    if hasattr(args, "file") and args.file:
        if not os.path.exists(args.file):
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        ext = os.path.splitext(args.file)[1].lower()
        lang_id = LANG_MAP.get(getattr(args, "lang", "").lower()) if getattr(args, "lang", None) else EXT_MAP.get(ext)
        with open(args.file, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
    elif hasattr(args, "code") and args.code:
        code = args.code
        lang_id = LANG_MAP.get(getattr(args, "lang", "python").lower(), 204)
    else:
        print_error("Must specify a code file or --code string")
        sys.exit(1)

    if not lang_id:
        print_error("Cannot resolve language ID. Use --lang (e.g. cpp, c, python, java, rust)")
        sys.exit(1)
    return code, lang_id

def cmd_batch(args):
    code, lang_id = resolve_code_and_lang(args)
    test_cases = []
    if getattr(args, "tests_file", None):
        with open(args.tests_file, "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    elif getattr(args, "tests", None):
        test_cases = json.loads(args.tests)
    else:
        # Default 2 demo cases
        test_cases = [
            {"id": 1, "stdin": "10\n", "expected_output": "20\n"},
            {"id": 2, "stdin": "20\n", "expected_output": "40\n"}
        ]

    suite = (getattr(args, "suite", "Omni") or "Omni").capitalize()
    payload = {
        "language_id": lang_id,
        "suite": suite,
        "source_code": code,
        "test_cases": test_cases
    }
    dispatch_suite_payload(payload, key=getattr(args, "key", None), as_json=getattr(args, "json", False), title=f"Batch Matrix ({suite} Suite)")

def cmd_complexity(args):
    code, lang_id = resolve_code_and_lang(args)
    if lang_id not in (50, 54, 201, 202, 221, 222):
        print_error("Complexity suite (Valgrind lackey) is supported for C and C++ (IDs 50, 54, 201, 202).")
        sys.exit(1)

    inp = getattr(args, "input", "100") or "100"
    payload = {
        "language_id": lang_id,
        "suite": "Complexity",
        "source_code": code,
        "test_cases": [{"id": 1, "stdin": inp}]
    }
    dispatch_suite_payload(payload, key=getattr(args, "key", None), as_json=getattr(args, "json", False), title="Complexity (Valgrind Lackey)")

def cmd_sanitize(args):
    code, lang_id = resolve_code_and_lang(args)
    inp = getattr(args, "input", "") or ""
    payload = {
        "language_id": lang_id,
        "suite": "Sanitizer",
        "source_code": code,
        "test_cases": [{"id": 1, "stdin": inp}]
    }
    dispatch_suite_payload(payload, key=getattr(args, "key", None), as_json=getattr(args, "json", False), title="Memory Sanitizer (ASan + UBSan)")

def cmd_dbms(args):
    code, lang_id = resolve_code_and_lang(args)
    schema_sql = getattr(args, "schema", "") or ""
    if getattr(args, "schema_file", None):
        with open(args.schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

    database = getattr(args, "database", "sqlite") or "sqlite"
    expected = getattr(args, "expected", "") or ""
    payload = {
        "language_id": lang_id,
        "suite": "DBMS",
        "database": database,
        "source_code": code,
        "test_cases": [
            {
                "id": 1,
                "schema_sql": schema_sql,
                "stdin": getattr(args, "input", "") or "",
                "expected_output": expected
            }
        ]
    }
    dispatch_suite_payload(payload, key=getattr(args, "key", None), as_json=getattr(args, "json", False), title=f"DBMS SQL Evaluation ({database.upper()})")

def cmd_fileio(args):
    code, lang_id = resolve_code_and_lang(args)
    in_file = getattr(args, "input_name", "input.txt")
    in_content = getattr(args, "input_content", "DATA")
    out_file = getattr(args, "output_name", "output.txt")
    expected = getattr(args, "expected", "")

    payload = {
        "language_id": lang_id,
        "suite": "FileIO",
        "source_code": code,
        "test_cases": [
            {
                "id": 1,
                "files": {in_file: in_content},
                "output_file": out_file,
                "expected_output": expected
            }
        ]
    }
    dispatch_suite_payload(payload, key=getattr(args, "key", None), as_json=getattr(args, "json", False), title="FileIO Filesystem Sandbox Grading")

def cmd_special_judge(args):
    code, lang_id = resolve_code_and_lang(args)
    checker_code = ""
    if getattr(args, "checker_file", None):
        with open(args.checker_file, "r", encoding="utf-8") as f:
            checker_code = f.read()
    elif getattr(args, "checker", None):
        checker_code = args.checker
    else:
        print_error("Must specify --checker or --checker-file")
        sys.exit(1)

    checker_lang_id = LANG_MAP.get(getattr(args, "checker_lang", "cpp").lower(), 202)
    payload = {
        "language_id": lang_id,
        "suite": "SpecialJudge",
        "source_code": code,
        "checker_code": checker_code,
        "checker_language_id": checker_lang_id,
        "test_cases": [
            {
                "id": 1,
                "stdin": getattr(args, "input", "5.0") or "5.0",
                "expected_output": getattr(args, "expected", "2.5") or "2.5"
            }
        ]
    }
    dispatch_suite_payload(payload, key=getattr(args, "key", None), as_json=getattr(args, "json", False), title="SpecialJudge Custom Checker")

def cmd_man(args):
    try:
        try:
            from .man import print_man_page
        except (ImportError, ValueError):
            from eschatonctl_man import print_man_page
        print_man_page(getattr(args, "command", None))
    except ImportError:
        print_error("Eschaton manual provider not found.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        prog="eschatonctl",
        description="Eschaton Multi-Tier Fleet Control Plane (Nginx + Gateway + Brain)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
AI AGENT QUICKSTART WORKFLOW:
  1. Inspect supported compilers & runtime IDs:
     $ eschatonctl languages

  2. Check remaining execution credits:
     $ eschatonctl account

  3. Execute local code file in <4ms:
     $ eschatonctl run solution.cpp --input "40 2"

  4. Read full Linux-style manual pages:
     $ eschatonctl man
     $ eschatonctl man run
""",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON results where supported")
    subparsers = parser.add_subparsers(dest="component", help="Target component or action")

    # 0. man (Linux-style manual pages)
    p_man = subparsers.add_parser("man", help="Display Linux-style manual pages for commands and arguments")
    p_man.add_argument("command", nargs="?", default=None, help="Target command to inspect (e.g. run, exec, account, languages)")

    # 1. status
    p_status = subparsers.add_parser("status", help="Comprehensive health check across all 3 tiers")

    # 2. nginx
    p_nginx = subparsers.add_parser("nginx", help="Tier 1: Nginx Edge Proxy & SSL Management")
    p_nginx.add_argument("action", choices=["status", "test", "reload", "logs"], help="Nginx action")
    p_nginx.add_argument("--lines", type=int, default=50, help="Number of log lines to tail")

    # 3. gateway
    p_gateway = subparsers.add_parser("gateway", help="Tier 2: SaaS Gateway & Metering Management")
    p_gateway.add_argument("action", choices=["status", "telemetry", "tenants", "keys", "topup", "logs"], help="Gateway action")
    p_gateway.add_argument("--tenant-id", help="Tenant ID for top-up")
    p_gateway.add_argument("--amount", type=int, help="Credit amount to add")
    p_gateway.add_argument("--reason", default="CLI Topup", help="Audit reason for top-up")
    p_gateway.add_argument("--lines", type=int, default=50, help="Number of log lines to tail")

    # 4. brain
    p_brain = subparsers.add_parser("brain", help="Tier 3: Compiler Microkernel & Worker Fleet")
    p_brain.add_argument("action", choices=["status", "metrics", "workers", "selfcheck", "restart", "logs"], help="Brain action")
    p_brain.add_argument("--lines", type=int, default=50, help="Number of log lines to tail")

    # 5. exec
    p_exec = subparsers.add_parser(
        "exec",
        help="Submit inline code string to live cluster in real-time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Execute Python code string with stdin:
  $ eschatonctl exec --lang python "import sys; print(sum(map(int, sys.stdin.read().split())))" --input "10 20 30"

  # Execute C++ code with JSON output:
  $ eschatonctl exec --lang cpp "#include <iostream>\\nint main(){ std::cout << 42; return 0; }" --json
""",
    )
    p_exec.add_argument("--lang", default="python", help="Language: cpp, c, python, java, rust, go, js, ts, sql, zig (default: python)")
    p_exec.add_argument("code", help="Inline source code string")
    p_exec.add_argument("--input", default="", help="Standard input (stdin)")
    p_exec.add_argument("--expected", default="", help="Expected stdout for grading")
    p_exec.add_argument("--suite", default=None, help="Execution suite (default: auto-detected, Void for C/C++, Apex for others)")
    p_exec.add_argument("--key", default="", help="Optional API key (defaults to active tenant key)")

    # 6. run (File execution with auto-language detection)
    p_run = subparsers.add_parser(
        "run",
        help="Execute local code file on live cluster (auto-detects language)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Run a C++ solution in <4ms microkernel:
  $ eschatonctl run solution.cpp --input "40 2"

  # Grade a Python submission with expected output:
  $ eschatonctl run solution.py --input "15 27" --expected "42\\n"

  # Run Valgrind memory leak & pointer profiling:
  $ eschatonctl run solution.c --suite Valgrind --input "sample_data"

  # Output machine-readable JSON for AI agent orchestration:
  $ eschatonctl run solution.rs --input "test" --json
""",
    )
    p_run.add_argument("file", help="Path to source file (.cpp, .py, .rs, .go, .java, .js, .ts, .sql, etc.)")
    p_run.add_argument("--lang", help="Override auto-detected language")
    p_run.add_argument("--input", default="", help="Standard input (stdin string)")
    p_run.add_argument("--input-file", dest="input_file", help="Path to stdin file")
    p_run.add_argument("--expected", default="", help="Expected stdout string for grading")
    p_run.add_argument("--expected-file", dest="expected_file", help="Path to expected stdout file")
    p_run.add_argument("--suite", default=None, help="Execution suite (default: auto-detected, Void for C/C++, Apex for others)")
    p_run.add_argument("--key", default="", help="Optional API key (defaults to active tenant key)")

    # 7. account (Developer tenant credits and rate limits)
    p_account = subparsers.add_parser("account", help="Check tenant credits, tier, and rate limit status")
    p_account.add_argument("--key", default="", help="API key to inspect (defaults to active tenant key)")

    # 8. languages (List supported compilers and runtimes)
    p_langs = subparsers.add_parser("languages", help="List all supported languages, compilers, and IDs")
    p_langs.add_argument("--key", default="", help="Optional API key")

    p_preflight = subparsers.add_parser("preflight", help="Request the real Eschaton preflight verdict for a source file")
    p_preflight.add_argument("file", help="Path to source code file")
    p_preflight.add_argument("--language-id", type=int, default=71, help="Eschaton compiler language ID")

    # 9. batch (Multi-testcase execution across Omni, Apex, or Void suites)
    p_batch = subparsers.add_parser("batch", help="Run parallel or streamed testcase matrix (Omni, Apex, Void suites)")
    p_batch.add_argument("file", nargs="?", help="Path to source file")
    p_batch.add_argument("--code", help="Inline code string")
    p_batch.add_argument("--lang", help="Programming language (e.g. cpp, python, rust)")
    p_batch.add_argument("--suite", choices=["Omni", "Apex", "Void"], default="Omni", help="Execution suite")
    p_batch.add_argument("--tests", help="Inline JSON string of testcases array")
    p_batch.add_argument("--tests-file", dest="tests_file", help="Path to JSON testcases file")
    p_batch.add_argument("--key", default="", help="Optional API key")

    # 10. complexity (Deterministic Valgrind instruction counter)
    p_comp = subparsers.add_parser("complexity", help="Deterministic instruction counting & algorithmic complexity (C/C++)")
    p_comp.add_argument("file", nargs="?", help="Path to source file (.c, .cpp)")
    p_comp.add_argument("--code", help="Inline C/C++ code")
    p_comp.add_argument("--lang", choices=["c", "cpp"], default="cpp", help="Language")
    p_comp.add_argument("--input", default="100", help="Standard input for algorithm")
    p_comp.add_argument("--key", default="", help="Optional API key")

    # 11. sanitize (ASan + UBSan memory leak and safety profiling)
    p_san = subparsers.add_parser("sanitize", help="ASan + UBSan memory safety, leak, and buffer overflow profiling")
    p_san.add_argument("file", nargs="?", help="Path to source file (.c, .cpp)")
    p_san.add_argument("--code", help="Inline code string")
    p_san.add_argument("--lang", default="cpp", help="Language")
    p_san.add_argument("--input", default="", help="Standard input")
    p_san.add_argument("--key", default="", help="Optional API key")

    # 12. dbms (Automated SQL database grading across SQLite, Postgres, MySQL, Oracle)
    p_dbms = subparsers.add_parser("dbms", help="Automated SQL database grading with ephemeral schema injection")
    p_dbms.add_argument("file", nargs="?", help="Path to Python database solution")
    p_dbms.add_argument("--code", help="Inline Python database solution")
    p_dbms.add_argument("--database", choices=["sqlite", "postgres", "mysql", "oracle"], default="sqlite", help="Target database backend")
    p_dbms.add_argument("--schema", default="", help="Inline schema DDL/DML string")
    p_dbms.add_argument("--schema-file", dest="schema_file", help="Path to schema SQL file")
    p_dbms.add_argument("--input", default="", help="Standard input")
    p_dbms.add_argument("--expected", default="", help="Expected query output")
    p_dbms.add_argument("--key", default="", help="Optional API key")

    # 13. fileio (Filesystem sandbox grading)
    p_fio = subparsers.add_parser("fileio", help="Filesystem sandbox grading with input and output files")
    p_fio.add_argument("file", nargs="?", help="Path to solution file")
    p_fio.add_argument("--code", help="Inline code")
    p_fio.add_argument("--lang", default="python", help="Language")
    p_fio.add_argument("--input-name", dest="input_name", default="input.txt", help="Input file name")
    p_fio.add_argument("--input-content", dest="input_content", default="DATA", help="Input file text")
    p_fio.add_argument("--output-name", dest="output_name", default="output.txt", help="Expected output file name")
    p_fio.add_argument("--expected", default="", help="Expected file contents")
    p_fio.add_argument("--key", default="", help="Optional API key")

    # 14. special-judge (Custom validator checker binary)
    p_sp = subparsers.add_parser("special-judge", help="Custom validator / special judge evaluation")
    p_sp.add_argument("file", nargs="?", help="Path to solution file")
    p_sp.add_argument("--code", help="Inline solution code")
    p_sp.add_argument("--lang", default="cpp", help="Language")
    p_sp.add_argument("--checker", help="Inline checker source code")
    p_sp.add_argument("--checker-file", dest="checker_file", help="Path to checker source code")
    p_sp.add_argument("--checker-lang", dest="checker_lang", default="cpp", help="Checker language")
    p_sp.add_argument("--input", default="5.0", help="Standard input")
    p_sp.add_argument("--expected", default="2.5", help="Standard expected output")
    p_sp.add_argument("--key", default="", help="Optional API key")

    args = parser.parse_args()

    if not args.component:
        # Default behavior with no arguments: show overall status
        cmd_status(args)
        return

    if args.component == "man":
        cmd_man(args)
    elif args.component == "status":
        cmd_status(args)
    elif args.component == "nginx":
        cmd_nginx(args)
    elif args.component == "gateway":
        cmd_gateway(args)
    elif args.component == "brain":
        cmd_brain(args)
    elif args.component == "exec":
        cmd_exec(args)
    elif args.component == "run":
        cmd_run(args)
    elif args.component == "account":
        cmd_account(args)
    elif args.component == "languages":
        cmd_languages(args)
    elif args.component == "preflight":
        cmd_preflight(args)
    elif args.component == "batch":
        cmd_batch(args)
    elif args.component == "complexity":
        cmd_complexity(args)
    elif args.component == "sanitize":
        cmd_sanitize(args)
    elif args.component == "dbms":
        cmd_dbms(args)
    elif args.component == "fileio":
        cmd_fileio(args)
    elif args.component == "special-judge":
        cmd_special_judge(args)

if __name__ == "__main__":
    main()
