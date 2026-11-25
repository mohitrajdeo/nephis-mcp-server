"""Exhaustive Linux-style Manual (man) provider for Eschaton CLI.

Provides rich, copy-pasteable command examples, argument semantics,
default values, credit economics, and machine-readable JSON schemas
for autonomous AI coding agents (Claude, Cursor, Devin, Antigravity)
and competitive programming engineers.
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


GENERAL_MAN = f"""{colorize("ESCHATONCTL(1)", BOLD)}                  {colorize("User Manual", DIM)}                  {colorize("ESCHATONCTL(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl - Sovereign Online Code Execution & Parallel Judging CLI

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl", GREEN)} [{colorize("OPTIONS", CYAN)}] {colorize("COMMAND", BOLD)} [{colorize("ARGS...", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    {colorize("Eschaton", BOLD)} is the sovereign high-throughput code evaluation fabric.
    Features the <4ms Void microkernel, 50-test parallel fan-out (Apex engine in 38ms),
    Valgrind memory leak profiling, empirical Big-O complexity benchmarking,
    and ephemeral in-memory PostgreSQL 16 / MySQL 8.4 database sandboxes.

{colorize("CORE WORKFLOW FOR AI AGENTS", BOLD)}
    1. Inspect Supported Compilers: {colorize("eschatonctl languages", GREEN)}
    2. Check Tenant Credits:        {colorize("eschatonctl account", GREEN)}
    3. Run Code File (<4ms):         {colorize("eschatonctl run solution.cpp --input \"10 20\"", GREEN)}
    4. 50-Test Parallel Batch:      {colorize("eschatonctl batch solution.cpp --tests-file testcases.json", GREEN)}
    5. Big-O Complexity Benchmark:  {colorize("eschatonctl complexity solution.cpp --input 1000", GREEN)}
    6. Memory Leak Sanitization:    {colorize("eschatonctl sanitize solution.cpp", GREEN)}
    7. Ephemeral SQL Sandbox:       {colorize("eschatonctl dbms solution.py --database postgres", GREEN)}

{colorize("ALL AVAILABLE COMMANDS", BOLD)}
    {colorize("run", GREEN)}           Execute local source file (C++, Rust, Python, Go, Java, Zig, TS)
    {colorize("exec", GREEN)}          Submit inline code string to live cluster in real-time
    {colorize("batch", GREEN)}         Evaluate up to 50 test cases concurrently in 38ms (Apex fanout)
    {colorize("complexity", GREEN)}    Deterministic hardware instruction counting & Big-O analyzer
    {colorize("sanitize", GREEN)}      ASan + UBSan memory safety, leak, and buffer overflow profiling
    {colorize("dbms", GREEN)}          Automated SQL database grading with ephemeral schema injection
    {colorize("fileio", GREEN)}        Filesystem sandbox grading with input and output files
    {colorize("special-judge", GREEN)} Custom validator / test checker evaluation
    {colorize("account", GREEN)}       Inspect tenant credits, tier, and rate limit status
    {colorize("languages", GREEN)}     List all 15+ supported compilers, versions, and language IDs
    {colorize("status", GREEN)}        Comprehensive health check across edge proxy, gateway, and brain
    {colorize("gateway", GREEN)}       Tier 2: SaaS Gateway, tenant governance & credit top-ups
    {colorize("brain", GREEN)}         Tier 3: Compiler Microkernel & Worker Fleet status
    {colorize("nginx", GREEN)}         Tier 1: Nginx Edge Proxy & SSL Management
    {colorize("man", GREEN)}           Display Linux-style manual pages for any command

{colorize("GLOBAL OPTIONS", BOLD)}
    {colorize("-h, --help", CYAN)}     Show summary CLI help and options
    {colorize("--json", CYAN)}         Output deterministic machine-readable JSON for AI parsers

{colorize("ENVIRONMENT VARIABLES", BOLD)}
    {colorize("NEPHIS_API_KEY", YELLOW)}      Primary API authentication key
    {colorize("ESCHATON_API_URL", YELLOW)}    Custom gateway URL (default: https://nephis.theeducode.com)

{colorize("MORE INFORMATION", BOLD)}
    Run {colorize("eschatonctl man <command>", GREEN)} for detailed argument documentation,
    schemas, and real copy-pasteable examples for any subcommand.
"""

COMMAND_MANS = {
    "run": f"""{colorize("ESCHATONCTL-RUN(1)", BOLD)}              {colorize("User Manual", DIM)}             {colorize("ESCHATONCTL-RUN(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-run - Execute local code file on live microkernel cluster

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl run", GREEN)} {colorize("FILE", YELLOW)} [{colorize("--lang", CYAN)} {colorize("LANG", YELLOW)}] [{colorize("--input", CYAN)} {colorize("STDIN", YELLOW)}]
                       [{colorize("--expected", CYAN)} {colorize("STDOUT", YELLOW)}] [{colorize("--suite", CYAN)} {colorize("SUITE", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Compiles and executes a local source code file on Eschaton's bare-metal
    worker cluster. Automatically detects language from file extension (.cpp, .rs,
    .py, .go, .java, .js, .ts, .zig, .sql). Evaluates output against expected stdout.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("FILE", BOLD)}
        Path to local source code file (e.g. solution.cpp, test.py).

    {colorize("--lang LANG", BOLD)}
        Override language detection (e.g. cpp, rust, python, java, go, ts).

    {colorize("--input STDIN", BOLD)}
        Standard input string fed to the program via stdin pipe.

    {colorize("--input-file FILE", BOLD)}
        Path to a file containing stdin data.

    {colorize("--expected STDOUT", BOLD)}
        Expected standard output string. If provided, Eschaton automatically
        grades the submission as Accepted (3) or Wrong Answer (4).

    {colorize("--suite SUITE", BOLD)}
        Execution suite engine:
        • Void: <4ms ultra-fast microkernel (default for C/C++)
        • Apex: High concurrency parallel runner (Judge0 drop-in)
        • Valgrind: Memory leak & buffer overflow instrumenter
        • Complexity: Empirical hardware Big-O asymptotic analyzer
        • DBMS: Ephemeral in-memory PostgreSQL/MySQL sandbox

    {colorize("--json", BOLD)}
        Output raw, machine-readable JSON containing time, memory, stdout, and status.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Run C++ solution in <4ms with stdin", DIM)}
    eschatonctl run solution.cpp --input "40 2"

    {colorize("# Example 2: Grade Python submission against expected output", DIM)}
    eschatonctl run solution.py --input "15 27" --expected "42\\n"

    {colorize("# Example 3: Run memory leak profiling via Valgrind", DIM)}
    eschatonctl run main.c --suite Valgrind --input "test-data"

    {colorize("# Example 4: Output machine-readable JSON for agent parsing", DIM)}
    eschatonctl run solution.rs --input "hello" --json
""",

    "exec": f"""{colorize("ESCHATONCTL-EXEC(1)", BOLD)}             {colorize("User Manual", DIM)}            {colorize("ESCHATONCTL-EXEC(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-exec - Submit inline code string to live cluster in real-time

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl exec", GREEN)} [{colorize("--lang", CYAN)} {colorize("LANG", YELLOW)}] [{colorize("--code", CYAN)} {colorize("STRING", YELLOW)}] [{colorize("--input", CYAN)} {colorize("STDIN", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Submits a raw code string directly to the Eschaton microkernel without
    needing to write an intermediate file to disk.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Execute Python snippet directly", DIM)}
    eschatonctl exec --lang python "import sys; print(sum(map(int, sys.stdin.read().split())))" --input "10 20 30"

    {colorize("# Example 2: Test C++ snippet with JSON output", DIM)}
    eschatonctl exec --lang cpp "#include <iostream>\\nint main(){{ std::cout << 42; return 0; }}" --json
""",

    "batch": f"""{colorize("ESCHATONCTL-BATCH(1)", BOLD)}            {colorize("User Manual", DIM)}            {colorize("ESCHATONCTL-BATCH(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-batch - Evaluate up to 50 test cases concurrently in 38ms (Apex fanout)

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl batch", GREEN)} [{colorize("FILE", YELLOW)}] [{colorize("--code", CYAN)} {colorize("CODE", YELLOW)}] [{colorize("--tests-file", CYAN)} {colorize("JSON_FILE", YELLOW)}]
                          [{colorize("--lang", CYAN)} {colorize("LANG", YELLOW)}] [{colorize("--suite", CYAN)} {colorize("SUITE", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Evaluates a solution against up to 50 distinct test cases simultaneously.
    Instead of serial execution (50 x 50ms = 2500ms), Eschaton fans out across
    dedicated hypervisor worker threads in 38ms total batch wall time.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("--tests-file JSON_FILE", BOLD)}
        Path to a JSON file containing an array of testcase objects:
        [ {{"id": 1, "stdin": "10 20", "expected_output": "30\\n"}}, ... ]

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl batch solution.cpp --tests-file testcases.json --json
""",

    "complexity": f"""{colorize("ESCHATONCTL-COMPLEXITY(1)", BOLD)}       {colorize("User Manual", DIM)}       {colorize("ESCHATONCTL-COMPLEXITY(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-complexity - Deterministic hardware instruction counting & Big-O analyzer

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl complexity", GREEN)} [{colorize("FILE", YELLOW)}] [{colorize("--code", CYAN)} {colorize("CODE", YELLOW)}] [{colorize("--input", CYAN)} {colorize("N", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Analyzes algorithmic complexity without reading source code. Executes the submission
    under Valgrind / PMU instruction instrumentation across multiple input size tiers
    and fits instruction curves to O(1), O(log N), O(N), O(N log N), or O(N^2).

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl complexity solution.cpp --input 1000 --json
""",

    "sanitize": f"""{colorize("ESCHATONCTL-SANITIZE(1)", BOLD)}         {colorize("User Manual", DIM)}         {colorize("ESCHATONCTL-SANITIZE(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-sanitize - ASan + UBSan memory safety, leak, and buffer overflow profiling

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl sanitize", GREEN)} [{colorize("FILE", YELLOW)}] [{colorize("--code", CYAN)} {colorize("CODE", YELLOW)}] [{colorize("--input", CYAN)} {colorize("STDIN", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Compiles code with AddressSanitizer (-fsanitize=address) and UndefinedBehaviorSanitizer
    (-fsanitize=undefined). Detects heap buffer overflows, stack out-of-bounds, use-after-free,
    and memory leaks during test execution.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl sanitize solution.cpp --input "42"
""",

    "dbms": f"""{colorize("ESCHATONCTL-DBMS(1)", BOLD)}             {colorize("User Manual", DIM)}             {colorize("ESCHATONCTL-DBMS(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-dbms - Automated SQL database grading with ephemeral schema injection

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl dbms", GREEN)} [{colorize("FILE", YELLOW)}] [{colorize("--database", CYAN)} {colorize("{sqlite,postgres,mysql,oracle}", YELLOW)}]
                         [{colorize("--schema", CYAN)} {colorize("DDL", YELLOW)}] [{colorize("--schema-file", CYAN)} {colorize("FILE", YELLOW)}]
                         [{colorize("--expected", CYAN)} {colorize("OUTPUT", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Instantiates an ephemeral in-memory PostgreSQL 16, MySQL 8.4, or SQLite database
    in <80ms. Injects seed DDL/DML, executes the user's SQL query solution, verifies results,
    and completely tears down the database sandbox upon completion.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl dbms solution.py --database postgres --schema "CREATE TABLE users(id serial, name text); INSERT INTO users(name) VALUES ('Alice');" --expected "1|Alice\\n"
""",

    "fileio": f"""{colorize("ESCHATONCTL-FILEIO(1)", BOLD)}           {colorize("User Manual", DIM)}           {colorize("ESCHATONCTL-FILEIO(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-fileio - Filesystem sandbox grading with input and output files

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl fileio", GREEN)} [{colorize("FILE", YELLOW)}] [{colorize("--input-name", CYAN)} {colorize("NAME", YELLOW)}] [{colorize("--input-content", CYAN)} {colorize("DATA", YELLOW)}]
                           [{colorize("--output-name", CYAN)} {colorize("NAME", YELLOW)}] [{colorize("--expected", CYAN)} {colorize("DATA", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Evaluates solutions that read from and write to named files on disk (e.g. input.txt -> output.txt).
    Pre-populates the input file in tmpfs and verifies output file contents after execution.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl fileio solution.py --input-name "data.in" --input-content "10 20" --output-name "data.out" --expected "30\\n"
""",

    "special-judge": f"""{colorize("ESCHATONCTL-SPECIAL-JUDGE(1)", BOLD)}    {colorize("User Manual", DIM)}    {colorize("ESCHATONCTL-SPECIAL-JUDGE(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-special-judge - Custom validator / special judge evaluation

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl special-judge", GREEN)} {colorize("FILE", YELLOW)} [{colorize("--checker-file", CYAN)} {colorize("CHECKER_SRC", YELLOW)}] [{colorize("--input", CYAN)} {colorize("STDIN", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Compiles a custom validator checker program that evaluates floating-point tolerances,
    multiple valid graph answers, or game permutations where exact stdout matching is insufficient.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl special-judge solution.cpp --checker-file checker.cpp --input "5.0" --expected "2.5"
""",

    "account": f"""{colorize("ESCHATONCTL-ACCOUNT(1)", BOLD)}          {colorize("User Manual", DIM)}          {colorize("ESCHATONCTL-ACCOUNT(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-account - Inspect tenant credits, tier, and rate limit status

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl account", GREEN)} [{colorize("--key", CYAN)} {colorize("API_KEY", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Queries the SaaS gateway to display active tenant identity, remaining execution credits,
    concurrency quotas, and requests-per-second rate limits.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl account --json
""",

    "languages": f"""{colorize("ESCHATONCTL-LANGUAGES(1)", BOLD)}        {colorize("User Manual", DIM)}        {colorize("ESCHATONCTL-LANGUAGES(1)", BOLD)}

{colorize("NAME", BOLD)}
    eschatonctl-languages - List all 15+ supported compilers, versions, and language IDs

{colorize("SYNOPSIS", BOLD)}
    {colorize("eschatonctl languages", GREEN)} [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Lists all available compiler runtimes (GCC 14 C++, rustc 1.79, Python 3.12, OpenJDK 21,
    Go 1.22, Zig 0.13, Node 20) along with their corresponding Judge0 and Eschaton language IDs.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    eschatonctl languages
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
        print(f"[!] No manual entry found for 'eschatonctl {command}'.", file=sys.stderr)
        print(f"    Available manual entries: {', '.join(sorted(COMMAND_MANS.keys()))}", file=sys.stderr)
        print(f"    Run 'eschatonctl man' for general overview.", file=sys.stderr)
        sys.exit(1)
