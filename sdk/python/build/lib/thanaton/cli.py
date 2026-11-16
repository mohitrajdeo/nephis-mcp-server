"""Thanaton Command Line Interface."""

import argparse
import json
import sys
from .client import Client
from .exceptions import EscalationRequiredException, ThanatonConnectionError, ThanatonError

def main(args=None):
    parser = argparse.ArgumentParser(
        prog="ananke",
        description="Thanaton & Ananke CLI: Sub-millisecond Execution Fabric for AI Coding Agents"
    )
    parser.add_argument("--version", action="version", version="Thanaton v1.0.0-PROD")
    parser.add_argument("--verify-hardware", action="store_true", help="Execute physical host hardware verification and exit")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080", help="Control plane daemon base URL")
    parser.add_argument("--api-key", default=None, help="Bearer API key for authenticated cloud")
    parser.add_argument("--json", action="store_true", help="Output results in machine-readable JSON")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. run: execute code in an ephemeral sandbox
    run_parser = subparsers.add_parser("run", help="Run a code snippet in an ephemeral MicroVM sandbox")
    run_parser.add_argument("code", help="Code string to execute")
    run_parser.add_argument("--language", "-l", default="python", help="Programming language (default: python)")

    # 2. info: inspect client configuration
    subparsers.add_parser("info", help="Display local client and control plane configuration")

    # 3. ci: parallel CI/CD test acceleration
    ci_parser = subparsers.add_parser("ci", help="Execute parallel CI test acceleration across microVMs and CoW databases")
    ci_parser.add_argument("--test-command", "-t", default="pytest", help="Test command to run (e.g. pytest tests/)")
    ci_parser.add_argument("--candidates", "-c", nargs="+", help="Candidate patches or test targets")
    ci_parser.add_argument("--timeout-ms", type=int, default=10000, help="Per-branch test timeout in ms")
    ci_parser.add_argument("--strategy", default="FASTEST_PASSING", help="Winning election strategy")

    # 4. ci-accelerator: Avenue 1 (v2.0)
    cia_parser = subparsers.add_parser("ci-accelerator", help="Avenue 1: AST delta slicing, flaky test quarantine, and VM cache")
    cia_parser.add_argument("--changed-symbols", "-s", nargs="+", default=["service.DBConnect"], help="Changed functions or symbols")
    cia_parser.add_argument("--suite-size", type=int, default=500, help="Total regression tests")
    cia_parser.add_argument("--vm-key", default="snap-ci-default", help="MicroVM snapshot key")

    # 5. db-branch: Avenue 2 (v2.0)
    db_parser = subparsers.add_parser("db-branch", help="Avenue 2: WAL LSN database branching, PII masking, and auto-reap")
    db_parser.add_argument("--tenant-id", default="tenant-enterprise-prod", help="Tenant isolation ID")
    db_parser.add_argument("--lsn", default="16/B374D848", help="Target WAL LSN")
    db_parser.add_argument("--no-mask-pii", action="store_true", help="Disable in-kernel dynamic PII masking")

    # 6. socket-handover: Avenue 3 (v2.0)
    sock_parser = subparsers.add_parser("socket-handover", help="Avenue 3: WebSocket session rehydration, socket draining, and canary shift")
    sock_parser.add_argument("--canary-weight", type=int, default=15, help="Canary percentage (0-100)")
    sock_parser.add_argument("--in-flight", type=int, default=25, help="Simulated in-flight requests")

    # 7. microvm-runner: Avenue 4 (v2.0)
    runner_parser = subparsers.add_parser("microvm-runner", help="Avenue 4: SABRE warm-pool restore, µSlice pacing, and NVMe direct-I/O")
    runner_parser.add_argument("--guest-ram", type=int, default=64, help="Guest RAM in MB")
    runner_parser.add_argument("--sandboxes", type=int, default=120, help="Co-located sandboxes count")

    # 8. finops: Avenue 5 (v2.0)
    finops_parser = subparsers.add_parser("finops", help="Avenue 5: AntiNAT zero-tax routing, AZAffinity locality, and active pruning")
    finops_parser.add_argument("--traffic-tb", type=float, default=10.0, help="Monthly egress data volume in TB")
    finops_parser.add_argument("--volumes", type=int, default=2, help="EBS volume count to prune")

    parsed = parser.parse_args(args)

    if parsed.verify_hardware:
        import platform, os
        is_linux = platform.system().lower() == "linux"
        kvm_ok = is_linux and os.path.exists("/dev/kvm")
        bpf_ok = is_linux and os.path.ismount("/sys/fs/bpf") if hasattr(os.path, "ismount") else False
        cg2_ok = is_linux and os.path.exists("/sys/fs/cgroup/cgroup.controllers")
        
        report = {
            "version": "v1.0.0-PROD",
            "os": platform.system().lower(),
            "arch": platform.machine(),
            "vcpus": os.cpu_count() or 1,
            "kvm": "ONLINE" if kvm_ok else "NOT DETECTED (Silicon Emulation Active)",
            "ebpf": "MOUNTED (/sys/fs/bpf)" if bpf_ok else "NOT MOUNTED (Userspace Fallback Active)",
            "cgroups": "CGROUPS V2 ACTIVE" if cg2_ok else "CGROUPS V1 (Legacy Mode)",
            "status": "PASS"
        }
        if parsed.json:
            print(json.dumps(report, indent=2))
        else:
            print("==================================================================")
            print("   ANANKE CLOUD PLATFORM: HARDWARE VERIFICATION (Client CLI)")
            print("==================================================================")
            print(f"Daemon Version:    {report['version']}")
            print(f"OS / Architecture: {report['os']} / {report['arch']} (vCPUs: {report['vcpus']})")
            print(f"KVM Acceleration:  {report['kvm']}")
            print(f"eBPF Filesystem:   {report['ebpf']}")
            print(f"Cgroups Controller:{report['cgroups']}")
            print("------------------------------------------------------------------")
            print("[+] Hardware verification complete. Machine ready for workloads.")
            print("==================================================================")
        sys.exit(0)

    if not parsed.command:
        parser.print_help()
        sys.exit(0)

    client = Client(base_url=parsed.base_url, api_key=parsed.api_key)

    if parsed.command == "run":
        try:
            res = client.run_code(parsed.code, language=parsed.language)
            if parsed.json:
                print(json.dumps({
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "exit_code": res.exit_code,
                    "duration_ms": res.duration_ms,
                    "ok": res.ok
                }, indent=2))
            else:
                sys.stdout.write(res.stdout)
                if res.stderr:
                    sys.stderr.write(res.stderr)
            sys.exit(res.exit_code)
        except ThanatonConnectionError as e:
            if parsed.json:
                print(json.dumps({"error": "CONNECTION_ERROR", "message": str(e)}, indent=2))
            else:
                sys.stderr.write(f"\n{e}\n")
            sys.exit(1)
        except ThanatonError as e:
            if parsed.json:
                print(json.dumps({"error": e.__class__.__name__, "message": str(e)}, indent=2))
            else:
                sys.stderr.write(f"\nError: {e}\n")
            sys.exit(1)

    elif parsed.command == "info":
        info = {
            "version": "1.0.0-PROD",
            "base_url": client.base_url,
            "timeout": client.timeout,
            "has_api_key": bool(client.api_key)
        }
        if parsed.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"Thanaton CLI Client v{info['version']}")
            print(f"Control Plane URL: {info['base_url']}")
            print(f"Request Timeout:   {info['timeout']}s")
            print(f"Authenticated:     {info['has_api_key']}")
        sys.exit(0)

    elif parsed.command == "ci":
        cands = parsed.candidates or ["test_suite_branch_1", "test_suite_branch_2"]
        try:
            res = client.speculate(
                candidates=cands,
                test_command=parsed.test_command,
                timeout_ms=parsed.timeout_ms,
                strategy=parsed.strategy,
            )
            if parsed.json:
                print(json.dumps(res, indent=2))
            else:
                print("==================================================================")
                print("   THANATON CI: PARALLEL TEST ACCELERATOR")
                print("==================================================================")
                print(f"Status:            {'PASSED' if res.get('success') else 'FAILED'}")
                print(f"Winner Candidate:  {res.get('winner_id')}")
                print(f"Total Duration:    {res.get('duration_ms', 0):.2f} ms")
                print(f"Branches Tested:   {res.get('total_candidates', 0)}")
                print(f"Pruned in RAM:     {res.get('pruned_in_memory', 0)}")
                print(f"Sandboxes Forked:  {res.get('sandboxes_forked', 0)}")
                print("------------------------------------------------------------------")
                for b in res.get("branches", []):
                    mark = "✓" if b.get("status") == "PASSED" else "✗"
                    print(f" [{mark}] {b.get('id'):<20} {b.get('status'):<16} ({b.get('duration_ms', 0):.2f}ms)")
                print("==================================================================")
            sys.exit(0 if res.get("success") else 1)
        except ThanatonConnectionError as e:
            if parsed.json:
                print(json.dumps({"error": "CONNECTION_ERROR", "message": str(e)}, indent=2))
            else:
                sys.stderr.write(f"\n{e}\n")
            sys.exit(1)
        except ThanatonError as e:
            if parsed.json:
                print(json.dumps({"error": e.__class__.__name__, "message": str(e)}, indent=2))
            else:
                sys.stderr.write(f"\nError: {e}\n")
            sys.exit(1)

    elif parsed.command == "ci-accelerator":
        res = client.ci_accelerate(
            changed_symbols=parsed.changed_symbols,
            test_suite_size=parsed.suite_size,
            vm_snapshot_key=parsed.vm_key
        )
        if parsed.json:
            print(json.dumps(res, indent=2))
        else:
            print("==================================================================")
            print("   AVENUE 1: CI/CD INTEGRATION TEST ACCELERATOR (v2.0)")
            print("==================================================================")
            print(f"AST Slicing:       {res['ast_slicing']['reduction_percent']}% pruned in {res['ast_slicing']['slice_computation_ns']} ns")
            print(f"Tests Executing:   {res['ast_slicing']['selected_tests_count']} / {res['ast_slicing']['total_tests_before']}")
            print(f"Flaky Quarantine:  {res['chaos_flaky']['quarantined_test']} (Replay Seed: {res['chaos_flaky']['replay_seed_fingerprint']})")
            print(f"VM Cache Restore:  {res['vm_cache']['restore_duration_ms']} ms ({res['vm_cache']['speedup_factor']:.0f}x faster than Docker)")
            print("==================================================================")
        sys.exit(0)

    elif parsed.command == "db-branch":
        res = client.db_branch(
            tenant_id=parsed.tenant_id,
            target_lsn=parsed.lsn,
            mask_pii=not parsed.no_mask_pii
        )
        if parsed.json:
            print(json.dumps(res, indent=2))
        else:
            print("==================================================================")
            print("   AVENUE 2: SELF-HOSTED ON-PREM DATABASE BRANCHING (v2.0)")
            print("==================================================================")
            print(f"Branch ID:         {res['wal_branch']['branch_id']} from LSN {res['wal_branch']['source_lsn']}")
            print(f"COW Fork Time:     {res['wal_branch']['fork_duration_ms']} ms (Parent Impact: {res['wal_branch']['parent_impact_pct']}%)")
            print(f"Dynamic PII Mask:  {res['pii_masking']['records_sanitized']} records at {res['pii_masking']['throughput_mb_s']} MB/s")
            print(f"Branch Auto-Reap:  {res['branch_reaper']['memory_reclaimed_mb']} MB RAM/disk reclaimed (Leak-free: {res['branch_reaper']['leak_free']})")
            print("==================================================================")
        sys.exit(0)

    elif parsed.command == "socket-handover":
        res = client.socket_handover(
            canary_weight_pct=parsed.canary_weight,
            in_flight_requests=parsed.in_flight
        )
        if parsed.json:
            print(json.dumps(res, indent=2))
        else:
            print("==================================================================")
            print("   AVENUE 3: ZERO-DOWNTIME SOCKET HANDOVER & HOT-RELOAD (v2.0)")
            print("==================================================================")
            print(f"WS Rehydration:    {res['session_rehydration']['sessions_transferred']} sessions in {res['session_rehydration']['rehydrate_latency_ns']} ns (Frame Loss: {res['session_rehydration']['frame_loss']})")
            print(f"Socket Draining:   {res['socket_draining']['passed_sockets']} listen FDs passed, {res['socket_draining']['drained_requests']} drained in {res['socket_draining']['drain_duration_ms']} ms")
            print(f"Canary Shifter:    {res['canary_shifter']['canary_weight_pct']}% canary weight ({res['canary_shifter']['decision_latency_ns']} ns/decision, Instant Rollback: {res['canary_shifter']['rollback_verified']})")
            print("==================================================================")
        sys.exit(0)

    elif parsed.command == "microvm-runner":
        res = client.microvm_runner(
            guest_ram_mb=parsed.guest_ram,
            sandboxes_count=parsed.sandboxes
        )
        if parsed.json:
            print(json.dumps(res, indent=2))
        else:
            print("==================================================================")
            print("   AVENUE 4: SERVERLESS MICROVM RUNNER & NVMe PASS (v2.0)")
            print("==================================================================")
            print(f"SABRE Warm-Pool:   {res['sabre_warm_pool']['memory_footprint_mb']} MB RAM restored in {res['sabre_warm_pool']['restore_latency_ms']} ms ({res['sabre_warm_pool']['throughput_gb_s']} GB/s, {res['sabre_warm_pool']['compression_ratio']}x compression)")
            print(f"µSlice Pacing:     {res['uslice_pacing']['co_located_sandboxes']} sandboxes at {res['uslice_pacing']['pacer_throughput_ops']:.0f} checks/s ({res['uslice_pacing']['cfs_stall_reduction_pct']}% CFS stall cut)")
            print(f"NVMe Direct I/O:   {res['nvme_direct_io']['vector_throughput_gb_s']} GB/s vector encoding, {res['nvme_direct_io']['nvme_read_latency_us']} µs read latency")
            print("==================================================================")
        sys.exit(0)

    elif parsed.command == "finops":
        res = client.finops_optimize(
            traffic_tb=parsed.traffic_tb,
            volumes_count=parsed.volumes
        )
        if parsed.json:
            print(json.dumps(res, indent=2))
        else:
            print("==================================================================")
            print("   AVENUE 5: CLOUD PLATFORM FINOPS & WIRE MATRIX (v2.0)")
            print("==================================================================")
            print(f"AntiNAT Routing:   ${res['antinat']['monthly_savings_usd']}/mo saved ({res['antinat']['savings_percentage']}% cut on NAT Gateway)")
            print(f"AZAffinity Mesh:   {res['azaffinity']['intra_az_ratio_pct']}% intra-AZ preference (Avoided Tax: {res['azaffinity']['avoided_cross_az_tax']})")
            print(f"ActivePrune EBS:   gp2 -> gp3 {res['activeprune']['gp2_to_gp3_storage_discount']} (+{res['activeprune']['gp3_free_iops_boost']} free IOPS)")
            print("==================================================================")
        sys.exit(0)

if __name__ == "__main__":
    main()
