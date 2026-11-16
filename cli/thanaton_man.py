"""Exhaustive Linux-style Manual (man) provider for Thanaton CLI.

Provides rich, copy-pasteable command examples, argument semantics,
default values, credit economics, and machine-readable JSON schemas
for autonomous AI coding agents (Claude, Cursor, Devin, Antigravity)
and human systems engineers.
"""

import sys

# ANSI Colors
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def colorize(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text


GENERAL_MAN = f"""{colorize("THANATON(1)", BOLD)}                     {colorize("User Manual", DIM)}                     {colorize("THANATON(1)", BOLD)}

{colorize("NAME", BOLD)}
    thanaton - Sovereign sub-6ms hardware KVM MicroVM orchestration CLI

{colorize("SYNOPSIS", BOLD)}
    {colorize("thanaton", GREEN)} [{colorize("OPTIONS", CYAN)}] {colorize("COMMAND", BOLD)} [{colorize("ARGS...", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    {colorize("Thanaton", BOLD)} provides hardware-assisted KVM microVM sandboxes for autonomous
    AI coding agents, sub-6ms cold boot latency, scale-to-zero stasis (0.0% CPU,
    $0.00 idle RAM burn), AST delta caching, and atomic project rollouts.

{colorize("CORE WORKFLOW FOR AI AGENTS", BOLD)}
    1. Check Identity & Quotas:   {colorize("thanaton whoami", GREEN)}
    2. Provision MicroVM:          {colorize("thanaton up --runtime microvm --memory-mb 512", GREEN)}
    3. Run Command in Sandbox:     {colorize("thanaton exec <sandbox_id> -- npm test", GREEN)}
    4. Hibernate to Zero Cost:     {colorize("thanaton sleep <sandbox_id>", GREEN)}
    5. Wake from Stasis (<6ms):    {colorize("thanaton wake <sandbox_id>", GREEN)}
    6. Deploy Full Web Project:    {colorize("thanaton deploy ./app --name my-api --port 3000", GREEN)}

{colorize("PRIMARY COMMANDS", BOLD)}
    {colorize("deploy", GREEN)}       Deploy local project directory to Thanaton Fabric (Preview or Prod)
    {colorize("up", GREEN)}           Provision and start a dedicated KVM microVM sandbox
    {colorize("exec", GREEN)}         Execute bash command inside an active microVM sandbox
    {colorize("ps", GREEN)}           List all active, hibernated, and managed sandboxes
    {colorize("sleep", GREEN)}        Scale a sandbox to zero (hibernate RAM to snapshot, $0 cost)
    {colorize("wake", GREEN)}         Wake hibernated sandbox from NVMe snapshot in <6ms
    {colorize("rm", GREEN)}           Destroy and reclaim sandbox hardware resources
    {colorize("attach", GREEN)}       Connect interactive PTY terminal stream to a sandbox
    {colorize("ports", GREEN)}        Manage Layer 4 raw TCP port forwarding
    {colorize("race", GREEN)}         Execute multi-candidate speculative racing across parallel VMs
    {colorize("snapshot", GREEN)}     Capture or restore point-in-time memory/disk snapshots
    {colorize("volume", GREEN)}       Manage persistent NVMe ext4 block storage volumes
    {colorize("secrets", GREEN)}      Zero-rebuild Firecracker MMDS secret and env injection
    {colorize("domains", GREEN)}      Manage custom domain names and automated TLS certificates
    {colorize("crons", GREEN)}        Manage scheduled background serverless cron invocations
    {colorize("billing", GREEN)}      Manage credits, quotas, and wallet balance
    {colorize("whoami", GREEN)}       Display active authentication session and credit balance
    {colorize("man", GREEN)}          Display Linux-style manual pages for any command

{colorize("GLOBAL OPTIONS", BOLD)}
    {colorize("-h, --help", CYAN)}    Show summary CLI help and options
    {colorize("--json", CYAN)}        Output deterministic machine-readable JSON for AI parsers

{colorize("CREDIT ECONOMICS RATE CARD", BOLD)}
    • 1 Credit = $0.00020 USD ($1.00 USD = 5,000 Credits)
    • MicroVM Cold Boot:      5.0 Credits ($0.0010)
    • Active vCPU Minute:     1.0 Credit / min ($0.00020)
    • Scale-to-Zero Stasis:   0.0 Credits ($0.0000 - 100% Free Idle)
    • AST Cache Hit:          0.2 Credits ($0.00004)
    • Snapshot Capture/Rest:  2.0 Credits ($0.00040)

{colorize("ENVIRONMENT VARIABLES", BOLD)}
    {colorize("NEPHIS_API_KEY", YELLOW)}     Primary API authentication key
    {colorize("THANATON_API_KEY", YELLOW)}    Thanaton-scoped fallback API key
    {colorize("THANATON_URL", YELLOW)}        Custom control-plane gateway URL

{colorize("MORE INFORMATION", BOLD)}
    Run {colorize("thanaton man <command>", GREEN)} for detailed argument documentation,
    schemas, and real copy-pasteable examples for any subcommand.
"""

COMMAND_MANS = {
    "deploy": f"""{colorize("THANATON-DEPLOY(1)", BOLD)}              {colorize("User Manual", DIM)}             {colorize("THANATON-DEPLOY(1)", BOLD)}

{colorize("NAME", BOLD)}
    thanaton-deploy - Deploy directory or project to Thanaton Fabric (Preview or Prod)

{colorize("SYNOPSIS", BOLD)}
    {colorize("thanaton deploy", GREEN)} [{colorize("PATH", YELLOW)}] [{colorize("--name", CYAN)} {colorize("NAME", YELLOW)}]
                   [{colorize("--runtime", CYAN)} {colorize("{nodejs,python,go,rust,docker}", YELLOW)}]
                   [{colorize("--port", CYAN)} {colorize("PORT", YELLOW)}] [{colorize("--preview", CYAN)}] [{colorize("--prod", CYAN)}]
                   [{colorize("--blue-green", CYAN)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Packages the specified local project directory, uploads it over TLS,
    builds an AST-fingerprinted container layer, and boots a dedicated KVM
    microVM with automatic anycast routing and TLS certificates.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("PATH", BOLD)}
        Path to local project directory. If omitted, defaults to current directory (.).
        Example: ./my-express-app

    {colorize("--name NAME", BOLD)}
        Unique project slug / identifier. If omitted, inferred from directory name or package.json.
        Example: --name customer-portal

    {colorize("--runtime {nodejs,python,go,rust,docker}", BOLD)}
        Language execution environment.
        Default: nodejs
        Choices: nodejs, python, go, rust, docker

    {colorize("--port PORT", BOLD)}
        Internal TCP port the service listens on inside the guest microVM.
        Default: 3000
        Example: --port 8000 (for FastAPI or Django)

    {colorize("--preview", BOLD)}
        Deploys to an isolated staging / preview URL instead of mutating production.
        Example URL: https://customer-portal-pr-42.preview.thanaton.cloud

    {colorize("--prod", BOLD)}
        Deploys directly to the canonical production domain (default).

    {colorize("--blue-green", BOLD)}
        Executes an atomic blue/green rollout with zero HTTP 502 dropped requests.
        Spawns a new microVM, verifies health check passes, swaps edge routing,
        and leaves the previous microVM in warm stasis for 1-click instant rollback.

    {colorize("--json", BOLD)}
        Outputs raw, machine-readable JSON for AI agent programmatic parsing.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Deploy a Node.js API to production on port 3000", DIM)}
    thanaton deploy ./api --name backend-api --runtime nodejs --port 3000

    {colorize("# Example 2: Deploy a FastAPI Python service to preview staging on port 8000", DIM)}
    thanaton deploy ./service --name analytics-svc --runtime python --port 8000 --preview

    {colorize("# Example 3: Deploy with blue-green zero-downtime routing and get JSON output", DIM)}
    thanaton deploy ./web --name frontend --runtime nodejs --blue-green --json

{colorize("CREDIT COST", BOLD)}
    5.0 Credits ($0.0010 USD) per cold deployment.
    Scale-to-zero idle stasis: 0.0 Credits ($0.0000).

{colorize("EXIT STATUS", BOLD)}
    0       Deployment succeeded; service is healthy and receiving traffic.
    1       Build failure, validation error, or authentication failure.
""",

    "up": f"""{colorize("THANATON-UP(1)", BOLD)}                  {colorize("User Manual", DIM)}                 {colorize("THANATON-UP(1)", BOLD)}

{colorize("NAME", BOLD)}
    thanaton-up - Provision and start a dedicated hardware KVM microVM sandbox

{colorize("SYNOPSIS", BOLD)}
    {colorize("thanaton up", GREEN)} [{colorize("--runtime", CYAN)} {colorize("{microvm,silicon,node,python}", YELLOW)}]
                [{colorize("--memory-mb", CYAN)} {colorize("MB", YELLOW)}] [{colorize("--cpu-quota", CYAN)} {colorize("PERCENT", YELLOW)}]
                [{colorize("--db", CYAN)}] [{colorize("--config", CYAN)} {colorize("FILE", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Instantiates an isolated, hardware-virtualized microVM sandbox via Linux KVM
    and Firecracker jailer in under 6 milliseconds. Supports automatic scale-to-zero,
    memory snapshots, and an optional embedded PostgreSQL 16 database.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("--runtime {microvm,silicon,node,python}", BOLD)}
        Virtualization substrate:
        • microvm: Hardware KVM with custom Linux kernel (default)
        • silicon: Lightweight isolated process sandbox
        • node: Pre-warmed Node.js runtime isolate
        • python: Pre-warmed Python 3.11 data science isolate

    {colorize("--memory-mb MB", BOLD)}
        Guest RAM allocation in MiB.
        Default: 256. Range: 128 to 4096.

    {colorize("--cpu-quota PERCENT", BOLD)}
        cgroup v2 vCPU quota percentage.
        Default: 100 (1 full vCPU core). Range: 25 to 800.

    {colorize("--db", BOLD)}
        Bundles a co-located, zero-copy PostgreSQL 16 database instance
        connected via UNIX domain socket for instant database tests.

    {colorize("--config FILE", BOLD)}
        Path to declarative nephis.toml or thanaton.toml specification file.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Provision a standard microVM for code execution", DIM)}
    thanaton up --runtime microvm --memory-mb 512

    {colorize("# Example 2: Provision a heavy microVM with embedded PostgreSQL", DIM)}
    thanaton up --runtime microvm --memory-mb 1024 --cpu-quota 200 --db

    {colorize("# Example 3: Provision microVM and capture ID via JSON output", DIM)}
    thanaton up --runtime microvm --json
""",

    "exec": f"""{colorize("THANATON-EXEC(1)", BOLD)}                {colorize("User Manual", DIM)}               {colorize("THANATON-EXEC(1)", BOLD)}

{colorize("NAME", BOLD)}
    thanaton-exec - Execute an arbitrary shell command inside an active sandbox

{colorize("SYNOPSIS", BOLD)}
    {colorize("thanaton exec", GREEN)} {colorize("SANDBOX_ID", YELLOW)} [{colorize("--timeout", CYAN)} {colorize("MS", YELLOW)}] {colorize("--", BOLD)} {colorize("COMMAND...", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Dispatches a command directly into the microVM guest operating system
    via internal vsock communication. Returns real-time stdout, stderr,
    exit status code, and microsecond-level execution latency.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("SANDBOX_ID", BOLD)}
        Unique identifier of the target running or sleeping sandbox.
        If the sandbox is in stasis (sleeping), it is automatically thawed
        in <8ms before executing the command.

    {colorize("--timeout MS", BOLD)}
        Maximum execution wall-time in milliseconds before SIGKILL is dispatched.
        Default: 15000 (15 seconds).

    {colorize("-- COMMAND...", BOLD)}
        The shell command and all trailing flags/arguments. Always separate
        with double-dash (--) to prevent flag collision with the CLI.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Run unit tests inside the sandbox", DIM)}
    thanaton exec sbx-kvm-9f82d1 -- pytest tests/ -v

    {colorize("# Example 2: Inspect hardware kernel and memory in the guest", DIM)}
    thanaton exec sbx-kvm-9f82d1 -- uname -a && free -m

    {colorize("# Example 3: Build npm project and output machine-readable JSON", DIM)}
    thanaton exec sbx-kvm-9f82d1 --timeout 30000 --json -- npm run build
""",

    "sleep": f"""{colorize("THANATON-SLEEP(1)", BOLD)}               {colorize("User Manual", DIM)}              {colorize("THANATON-SLEEP(1)", BOLD)}

{colorize("NAME", BOLD)}
    thanaton-sleep - Scale a microVM to zero (hibernate RAM to snapshot, $0 cost)

{colorize("SYNOPSIS", BOLD)}
    {colorize("thanaton sleep", GREEN)} {colorize("SANDBOX_ID", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Freezes all guest vCPU threads and pauses instruction cycling. Memory
    is preserved intact in NVMe stasis storage. vCPU utilization drops to
    exactly 0.0%, and ongoing billing immediately pauses ($0.00 / 0 CR).

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    thanaton sleep sbx-kvm-9f82d1
""",

    "wake": f"""{colorize("THANATON-WAKE(1)", BOLD)}                {colorize("User Manual", DIM)}               {colorize("THANATON-WAKE(1)", BOLD)}

{colorize("NAME", BOLD)}
    thanaton-wake - Instantly wake a hibernated microVM from snapshot in <6ms

{colorize("SYNOPSIS", BOLD)}
    {colorize("thanaton wake", GREEN)} {colorize("SANDBOX_ID", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Restores guest physical memory from snapshot storage via userfaultfd
    lazy-paging and unfreezes scheduler threads in under 6 milliseconds.
    Network connections, loaded libraries, and process heaps remain exactly
    as they were prior to sleep.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    thanaton wake sbx-kvm-9f82d1
""",

    "ports": f"""{colorize("THANATON-PORTS(1)", BOLD)}               {colorize("User Manual", DIM)}              {colorize("THANATON-PORTS(1)", BOLD)}

{colorize("NAME", BOLD)}
    thanaton-ports - Manage Layer 4 raw TCP port forwarding for microVMs

{colorize("SYNOPSIS", BOLD)}
    {colorize("thanaton ports expose", GREEN)} {colorize("SANDBOX_ID", YELLOW)} {colorize("--port", CYAN)} {colorize("PORT", YELLOW)} [{colorize("--service", CYAN)} {colorize("NAME", YELLOW)}]
    {colorize("thanaton ports list", GREEN)} {colorize("SANDBOX_ID", YELLOW)}
    {colorize("thanaton ports close", GREEN)} {colorize("SANDBOX_ID", YELLOW)} {colorize("--port", CYAN)} {colorize("HOST_PORT", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Configures low-latency iptables and eBPF socket forwarding rules
    to expose internal guest services (PostgreSQL 5432, Redis 6379, Next.js 3000)
    to external developer networks or live browser previews.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Expose Next.js frontend on port 3000 for browser preview", DIM)}
    thanaton ports expose sbx-kvm-9f82d1 --port 3000 --service frontend

    {colorize("# Expose internal PostgreSQL database on port 5432", DIM)}
    thanaton ports expose sbx-kvm-9f82d1 --port 5432 --service postgres
"""
}


def print_man_page(command: str = None) -> None:
    """Print the manual page for a command or general overview."""
    if not command:
        print(GENERAL_MAN)
        return

    cmd_key = command.strip().lower()
    if cmd_key in COMMAND_MANS:
        print(COMMAND_MANS[cmd_key])
    else:
        print(f"[!] No manual entry found for 'thanaton {command}'.", file=sys.stderr)
        print(f"    Available manual entries: {', '.join(sorted(COMMAND_MANS.keys()))}", file=sys.stderr)
        print(f"    Run 'thanaton man' for general overview.", file=sys.stderr)
        sys.exit(1)
