"""Exhaustive Linux-style Manual (man) provider for Mnemon CLI.

Provides rich, copy-pasteable command examples, argument semantics,
default values, credit economics, and machine-readable JSON schemas
for autonomous AI coding agents (Claude, Cursor, Devin, Antigravity)
and human database engineers.
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


GENERAL_MAN = f"""{colorize("MNEMON(1)", BOLD)}                       {colorize("User Manual", DIM)}                       {colorize("MNEMON(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon - Sovereign Serverless PostgreSQL 16 & Zero-Copy Branching CLI

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon", GREEN)} [{colorize("OPTIONS", CYAN)}] {colorize("COMMAND", BOLD)} [{colorize("ARGS...", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    {colorize("Mnemon", BOLD)} provides dedicated PostgreSQL 16 sovereign cluster instances,
    instant 31ms zero-copy database branching via Linux XFS FICLONE block reflinks,
    Point-in-Time Recovery (PITR) WAL rewinds, pgvector HNSW-PQ vector quantization,
    Lethe Real-time Change Data Capture (CDC) streaming, 3-way schema reconciliation,
    and automated database migration from Neon/Supabase.

{colorize("CORE WORKFLOW FOR AI AGENTS", BOLD)}
    1. List Databases:           {colorize("mnemon list", GREEN)}
    2. Fork Zero-Copy Branch:     {colorize("mnemon branch <db> feat-pr-42 --parent main", GREEN)}
    3. Run SQL against Branch:   {colorize("mnemon sql <db> \"SELECT count(*) FROM users;\" --branch feat-pr-42", GREEN)}
    4. Check Schema Diff:        {colorize("mnemon diff <db> --branch feat-pr-42", GREEN)}
    5. Reconcile 3-Way Schema:   {colorize("mnemon reconcile <db> feat-pr-42 --target main", GREEN)}
    6. Promote Branch to Root:   {colorize("mnemon promote <db> feat-pr-42", GREEN)}
    7. Quantize Vectors:         {colorize("mnemon quantize set <db> --table docs --dimensions 1536", GREEN)}

{colorize("ALL AVAILABLE COMMANDS", BOLD)}
    {colorize("branch", GREEN)}       Create instant 31ms CoW reflink branch (0 initial bytes copied)
    {colorize("quantize", GREEN)}     pgvector + HNSW-PQ vector quantization & disk-spill memory indexing
    {colorize("import", GREEN)}       Zero-downtime database importer from Neon / Supabase with live cutover
    {colorize("reconcile", GREEN)}    3-way schema reconciliation and migration conflict resolution
    {colorize("advisor", GREEN)}      Slow query circuit breaker, cache diagnostics & index recommendations
    {colorize("lineage", GREEN)}      Display visual DAG tree of branch ancestry and LSN delta commits
    {colorize("pitr", GREEN)}         Point-In-Time Recovery via continuous WAL archiving & timelines
    {colorize("scale", GREEN)}        Configure Aurora Serverless v2 ACU capacity scaling & stasis
    {colorize("pooler", GREEN)}       Inspect or dynamically tune PgBouncer connection pooler
    {colorize("cdc", GREEN)}          Lethe Real-time Change Data Capture (CDC) streaming and inspection
    {colorize("diff", GREEN)}         Show structural schema DDL diff between branch and parent
    {colorize("reset", GREEN)}        One-click branch rollback / reset to parent state
    {colorize("search", GREEN)}       ParadeDB BM25 / tsvector hybrid full-text search
    {colorize("ext", GREEN)}          Manage extensions (pgvector, ParadeDB, PostGIS)
    {colorize("sql", GREEN)}          Execute raw SQL query directly against database or branch
    {colorize("tables", GREEN)}       Inspect database tables, columns, constraints, and schemas
    {colorize("slow-queries", GREEN)} Inspect slow query diagnostics and shared-buffer hit rates
    {colorize("snapshot", GREEN)}     Manage point-in-time database cluster snapshots
    {colorize("promote", GREEN)}      Promote preview branch to primary production root zero-downtime
    {colorize("freeze", GREEN)}       Freeze database into 0.0% CPU scale-to-zero stasis
    {colorize("resume", GREEN)}       Wake database cluster from stasis in <200µs
    {colorize("man", GREEN)}          Display Linux-style manual pages for any command

{colorize("CREDIT ECONOMICS RATE CARD", BOLD)}
    • 1 Credit = $0.00020 USD ($1.00 USD = 5,000 Credits)
    • Branch Creation (CoW):   5.0 Credits ($0.0010 one-time)
    • Active Branch Storage:   1.0 Credit / 100MB / hour ($0.00020)
    • Stasis Branch Storage:   0.1 Credits / 100MB / hour (90% discount)
    • Cached Read Queries:     0.1 Credits / 10,000 queries ($0.00002)
    • ACID Write Transactions: 0.5 Credits / 1,000 transactions ($0.00010)
    • Vector Search (HNSW):    2.0 Credits / 1,000 searches ($0.00040)
    • Time-Travel WAL Rewind:  3.0 Credits / restore event ($0.00060)

{colorize("ENVIRONMENT VARIABLES", BOLD)}
    {colorize("NEPHIS_API_KEY", YELLOW)}     Primary API authentication key
    {colorize("MNEMON_API_URL", YELLOW)}     Custom database control-plane gateway URL

{colorize("MORE INFORMATION", BOLD)}
    Run {colorize("mnemon man <command>", GREEN)} for detailed argument documentation,
    schemas, and real copy-pasteable examples for any subcommand.
"""

COMMAND_MANS = {
    "branch": f"""{colorize("MNEMON-BRANCH(1)", BOLD)}              {colorize("User Manual", DIM)}             {colorize("MNEMON-BRANCH(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-branch - Create instant zero-copy database branch via XFS FICLONE reflinks

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon branch", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("NEW_BRANCH", YELLOW)} [{colorize("--parent", CYAN)} {colorize("PARENT", YELLOW)}] [{colorize("--lsn", CYAN)} {colorize("LSN", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Creates a new isolated branch of a PostgreSQL 16 database cluster in under
    31 milliseconds. Leverages Linux kernel filesystem block reflinks (ioctl FICLONE).
    Zero physical disk space is initially allocated; reads hit the shared parent extents,
    and writes append copy-on-write delta extents.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("TENANT_ID", BOLD)}
        Unique database cluster / project identifier (e.g. prod-db, my-app-db).

    {colorize("NEW_BRANCH", BOLD)}
        Name of the new branch to create (e.g. staging, pr-42, migration-test).

    {colorize("--parent PARENT", BOLD)}
        Source parent branch to fork from. Default: main.

    {colorize("--lsn LSN", BOLD)}
        Target Log Sequence Number (LSN) for historical point-in-time branch forks. Default: 0.

    {colorize("--json", BOLD)}
        Outputs raw JSON containing connection string, branch ID, and creation latency.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Fork a staging branch from main in 31ms", DIM)}
    mnemon branch prod-db staging --parent main

    {colorize("# Example 2: Fork a feature branch for an automated pull request", DIM)}
    mnemon branch my-app feat-auth-migration --parent main

    {colorize("# Example 3: Fork from historical LSN to isolate a corrupt transaction", DIM)}
    mnemon branch prod-db audit-recovery --parent main --lsn 0/16B38D8 --json

{colorize("CREDIT COST", BOLD)}
    5.0 Credits ($0.0010 USD) per branch created.
""",

    "quantize": f"""{colorize("MNEMON-QUANTIZE(1)", BOLD)}            {colorize("User Manual", DIM)}            {colorize("MNEMON-QUANTIZE(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-quantize - pgvector + HNSW-PQ vector quantization & disk-spill memory indexing

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon quantize set", GREEN)} {colorize("PROJECT_ID", YELLOW)} [{colorize("--table", CYAN)} {colorize("TABLE", YELLOW)}] [{colorize("--column", CYAN)} {colorize("COLUMN", YELLOW)}]
                        [{colorize("--dimensions", CYAN)} {colorize("DIMS", YELLOW)}] [{colorize("--type", CYAN)} {colorize("{PQ,SQ8}", YELLOW)}] [{colorize("--disk-spill", CYAN)}]
    {colorize("mnemon quantize stats", GREEN)} {colorize("PROJECT_ID", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Compresses high-dimensional vector embeddings (e.g. OpenAI 1536-dim, Gemini 768-dim)
    using Product Quantization (PQ) or 8-bit Scalar Quantization (SQ8). Reduces vector memory
    footprint by up to 96% while maintaining >98% recall accuracy, spilling index cold tiers to NVMe.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("PROJECT_ID", BOLD)}
        Database project identifier.

    {colorize("--table TABLE", BOLD)}
        Target relational table containing vector embeddings. Default: documents.

    {colorize("--column COLUMN", BOLD)}
        Column storing vector data. Default: embedding.

    {colorize("--dimensions DIMS", BOLD)}
        Vector dimensionality. Default: 1536.

    {colorize("--type {PQ,SQ8}", BOLD)}
        Quantization algorithm:
        • PQ: Product Quantization (96% memory reduction, sub-vector centroid clustering)
        • SQ8: 8-bit Scalar Quantization (75% memory reduction, uniform float-to-int8 scaling)

    {colorize("--disk-spill", BOLD)}
        Enable disk-backed memory spill for massive multi-million vector graphs.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Configure 1536-dim Product Quantization on documents table", DIM)}
    mnemon quantize set prod-db --table documents --column embedding --dimensions 1536 --type PQ

    {colorize("# Example 2: Check vector memory compression and recall accuracy", DIM)}
    mnemon quantize stats prod-db
""",

    "import": f"""{colorize("MNEMON-IMPORT(1)", BOLD)}              {colorize("User Manual", DIM)}              {colorize("MNEMON-IMPORT(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-import - Zero-downtime database importer from Neon or Supabase with live cutover

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon import start", GREEN)} {colorize("PROJECT_ID", YELLOW)} {colorize("--source", CYAN)} {colorize("POSTGRES_URI", YELLOW)}
    {colorize("mnemon import status", GREEN)} {colorize("PROJECT_ID", YELLOW)}
    {colorize("mnemon import cutover", GREEN)} {colorize("PROJECT_ID", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Migrates external PostgreSQL databases (Neon, Supabase, AWS RDS, self-hosted)
    into Mnemon sovereign clusters with zero downtime. Initial table heaps are synchronized
    via logical dump, and live ongoing transactions are streamed via CDC logical replication.
    Once replication lag hits <10ms, issuing cutover promotes Mnemon to primary.

{colorize("ARGUMENTS & OPTIONS", BOLD)}
    {colorize("--source POSTGRES_URI", BOLD)}
        Connection string for external PostgreSQL instance (postgres://user:pass@host:5432/db?sslmode=require).

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# Example 1: Start continuous replication from Supabase", DIM)}
    mnemon import start prod-db --source "postgres://postgres:secret@db.supabase.co:5432/postgres?sslmode=require"

    {colorize("# Example 2: Monitor replication lag and sync percentage", DIM)}
    mnemon import status prod-db

    {colorize("# Example 3: Execute 1-click zero-downtime cutover", DIM)}
    mnemon import cutover prod-db
""",

    "reconcile": f"""{colorize("MNEMON-RECONCILE(1)", BOLD)}           {colorize("User Manual", DIM)}           {colorize("MNEMON-RECONCILE(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-reconcile - 3-way schema reconciliation and migration conflict resolution

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon reconcile", GREEN)} {colorize("PROJECT_ID", YELLOW)} {colorize("BRANCH", YELLOW)} [{colorize("--target", CYAN)} {colorize("TARGET_BRANCH", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Performs a 3-way structural AST diff between the base common ancestor, the active
    preview branch, and the target production branch. Detects schema conflicts (e.g. conflicting
    column additions, type mutations, foreign key violations) before merging.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon reconcile prod-db feat-user-auth --target main
""",

    "advisor": f"""{colorize("MNEMON-ADVISOR(1)", BOLD)}             {colorize("User Manual", DIM)}             {colorize("MNEMON-ADVISOR(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-advisor - Slow query circuit breaker, cache diagnostics & index recommendations

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon advisor", GREEN)} {colorize("PROJECT_ID", YELLOW)} [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Inspects pg_stat_statements and shared buffer activity. Automatically recommends
    missing composite or partial B-tree/GIN/HNSW indexes and flags rogue N+1 query patterns.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon advisor prod-db --json
""",

    "lineage": f"""{colorize("MNEMON-LINEAGE(1)", BOLD)}             {colorize("User Manual", DIM)}             {colorize("MNEMON-LINEAGE(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-lineage - Display visual DAG tree of branch ancestry and LSN delta commits

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon lineage", GREEN)} {colorize("PROJECT_ID", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Renders an ASCII Directed Acyclic Graph (DAG) displaying the parent-child relationship,
    fork LSNs, dirty page delta sizes, and active connection count across all branches.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon lineage prod-db
""",

    "pitr": f"""{colorize("MNEMON-PITR(1)", BOLD)}                {colorize("User Manual", DIM)}                {colorize("MNEMON-PITR(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-pitr - Point-In-Time Recovery via continuous WAL archiving & timelines

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon pitr timelines", GREEN)} {colorize("TENANT_ID", YELLOW)}
    {colorize("mnemon pitr restore", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("TARGET_BRANCH", YELLOW)} [{colorize("--lsn", CYAN)} {colorize("LSN", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Lists available recovery time windows and restores the database to any past LSN
    or microsecond epoch on a fresh, isolated branch without mutating production data.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    {colorize("# List available recovery windows", DIM)}
    mnemon pitr timelines prod-db

    {colorize("# Restore database to historical state 0/16B38D8 on branch recovery-42", DIM)}
    mnemon pitr restore prod-db recovery-42 --lsn 0/16B38D8
""",

    "scale": f"""{colorize("MNEMON-SCALE(1)", BOLD)}               {colorize("User Manual", DIM)}               {colorize("MNEMON-SCALE(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-scale - Configure Aurora Serverless v2 ACU capacity scaling & stasis

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon scale get", GREEN)} {colorize("PROJECT_ID", YELLOW)}
    {colorize("mnemon scale set", GREEN)} {colorize("PROJECT_ID", YELLOW)} [{colorize("--min-acu", CYAN)} {colorize("MIN", YELLOW)}] [{colorize("--max-acu", CYAN)} {colorize("MAX", YELLOW)}]
                     [{colorize("--scale-to-zero", CYAN)}] [{colorize("--no-scale-to-zero", CYAN)}] [{colorize("--idle-suspend", CYAN)} {colorize("SECS", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Configures Aurora Capacity Units (ACUs) and auto-suspension. Setting --min-acu 0.0
    enables true 0.0% CPU scale-to-zero stasis when traffic halts.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon scale set prod-db --min-acu 0.0 --max-acu 16.0 --scale-to-zero --idle-suspend 300
""",

    "pooler": f"""{colorize("MNEMON-POOLER(1)", BOLD)}              {colorize("User Manual", DIM)}              {colorize("MNEMON-POOLER(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-pooler - Inspect or dynamically tune PgBouncer connection pooler

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon pooler", GREEN)} {colorize("TENANT_ID", YELLOW)} [{colorize("--mode", CYAN)} {colorize("{transaction,session}", YELLOW)}] [{colorize("--max-size", CYAN)} {colorize("N", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Configures PgBouncer connection multiplexing. Transaction mode enables thousands
    of serverless microVMs and AI agents to share pool connections without backend exhaustion.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon pooler prod-db --mode transaction --max-size 100
""",

    "diff": f"""{colorize("MNEMON-DIFF(1)", BOLD)}                {colorize("User Manual", DIM)}                {colorize("MNEMON-DIFF(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-diff - Show schema DDL diff between a branch and its parent

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon diff", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("--branch", CYAN)} {colorize("BRANCH", YELLOW)} [{colorize("--parent", CYAN)} {colorize("PARENT", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Generates exact SQL DDL migration statements (CREATE TABLE, ALTER COLUMN, DROP INDEX)
    representing the structural delta between the target branch and parent.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon diff prod-db --branch staging --parent main
""",

    "reset": f"""{colorize("MNEMON-RESET(1)", BOLD)}               {colorize("User Manual", DIM)}               {colorize("MNEMON-RESET(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-reset - One-click branch rollback / reset to parent state

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon reset", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("BRANCH", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Instantly wipes all unmerged modifications on the specified branch and resets
    its storage pointers to match the current HEAD of its parent in under 35ms.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon reset prod-db test-branch
""",

    "search": f"""{colorize("MNEMON-SEARCH(1)", BOLD)}              {colorize("User Manual", DIM)}              {colorize("MNEMON-SEARCH(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-search - ParadeDB BM25 / tsvector hybrid full-text search

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon search", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("TABLE", YELLOW)} {colorize("QUERY", YELLOW)} [{colorize("--columns", CYAN)} {colorize("COLS", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Executes BM25 full-text rank search on table text columns with sub-10ms latency.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon search prod-db articles "vector database" --columns id,title,snippet
""",

    "ext": f"""{colorize("MNEMON-EXT(1)", BOLD)}                 {colorize("User Manual", DIM)}                 {colorize("MNEMON-EXT(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-ext - Manage PostgreSQL extensions (pgvector, ParadeDB, PostGIS)

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon ext", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("{list,enable,disable}", CYAN)} [{colorize("NAME", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Inspects, installs, or removes database extensions dynamically without restarts.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon ext prod-db enable vector
    mnemon ext prod-db list
""",

    "sql": f"""{colorize("MNEMON-SQL(1)", BOLD)}                 {colorize("User Manual", DIM)}                {colorize("MNEMON-SQL(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-sql - Execute raw SQL query against database cluster or branch

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon sql", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("QUERY", YELLOW)} [{colorize("--branch", CYAN)} {colorize("BRANCH", YELLOW)}] [{colorize("--json", CYAN)}]

{colorize("DESCRIPTION", BOLD)}
    Executes an arbitrary SQL query (SELECT, INSERT, UPDATE, DDL) against the
    specified database cluster. Returns execution latency, rows affected, and
    query results in ASCII table or JSON format.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon sql prod-db "SELECT count(*), status FROM orders GROUP BY status;"
    mnemon sql prod-db "SELECT id, title FROM docs LIMIT 5;" --json
""",

    "cdc": f"""{colorize("MNEMON-CDC(1)", BOLD)}                 {colorize("User Manual", DIM)}                {colorize("MNEMON-CDC(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-cdc - Lethe Real-time Change Data Capture (CDC) streaming and inspection

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon cdc stream", GREEN)} {colorize("PROJECT_ID", YELLOW)} [{colorize("--table", CYAN)} {colorize("TABLE", YELLOW)}] [{colorize("--action", CYAN)} {colorize("ACTION", YELLOW)}]
    {colorize("mnemon cdc stats", GREEN)} {colorize("PROJECT_ID", YELLOW)}

{colorize("DESCRIPTION", BOLD)}
    Streams real-time database modifications (INSERT, UPDATE, DELETE) directly
    from PostgreSQL's logical replication engine over Server-Sent Events (SSE)
    without running periodic polling queries.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon cdc stream prod-db --table users --action INSERT
    mnemon cdc stats prod-db
""",

    "promote": f"""{colorize("MNEMON-PROMOTE(1)", BOLD)}             {colorize("User Manual", DIM)}            {colorize("MNEMON-PROMOTE(1)", BOLD)}

{colorize("NAME", BOLD)}
    mnemon-promote - Promote a preview branch to primary production root (zero-downtime)

{colorize("SYNOPSIS", BOLD)}
    {colorize("mnemon promote", GREEN)} {colorize("TENANT_ID", YELLOW)} {colorize("BRANCH", YELLOW)} [{colorize("--target", CYAN)} {colorize("TARGET", YELLOW)}]

{colorize("DESCRIPTION", BOLD)}
    Atomically swaps the LSN write stream and promotes a verified staging branch
    to become the primary production cluster without downtime or dropped client connections.

{colorize("EXAMPLES FOR AI AGENTS", BOLD)}
    mnemon promote prod-db staging --target main
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
        print(f"[!] No manual entry found for 'mnemon {command}'.", file=sys.stderr)
        print(f"    Available manual entries: {', '.join(sorted(COMMAND_MANS.keys()))}", file=sys.stderr)
        print(f"    Run 'mnemon man' for general overview.", file=sys.stderr)
        sys.exit(1)
