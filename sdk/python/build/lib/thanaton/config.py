"""Declarative configuration management and project runtime auto-detection for Nephis & Thanaton.

Supports declarative nephis.toml specification, auto-detecting language runtimes,
frameworks, database requirements, and resource boundaries.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback
    except ImportError:
        tomllib = None  # Fallback to internal lightweight parser


def parse_toml_fallback(content: str) -> Dict[str, Any]:
    """Lightweight zero-dependency TOML parser for standard nephis.toml structures."""
    result: Dict[str, Any] = {}
    current_section: Dict[str, Any] = result

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Section header e.g. [project]
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            current_section = {}
            result[section_name] = current_section
            continue

        # Key-value pair e.g. name = "my-service"
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()

            # Strip inline comments
            if " #" in val:
                val = val.split(" #", 1)[0].strip()

            # Parse types
            if val.lower() == "true":
                parsed_val: Any = True
            elif val.lower() == "false":
                parsed_val = False
            elif (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                parsed_val = val[1:-1]
            elif val.isdigit():
                parsed_val = int(val)
            else:
                try:
                    parsed_val = float(val)
                except ValueError:
                    parsed_val = val

            current_section[key] = parsed_val

    return result


def parse_nephis_toml(path: str = "nephis.toml") -> Dict[str, Any]:
    """Parse and validate a nephis.toml (or thanaton.toml) configuration file."""
    config_file = Path(path)
    if not config_file.exists():
        # Check alternative thanaton.toml
        alt = config_file.parent / "thanaton.toml"
        if alt.exists():
            config_file = alt
        else:
            raise FileNotFoundError(f"Configuration file not found: {path}")

    content = config_file.read_text(encoding="utf-8")
    if tomllib is not None:
        try:
            raw_data = tomllib.loads(content)
        except Exception:
            raw_data = parse_toml_fallback(content)
    else:
        raw_data = parse_toml_fallback(content)

    # Apply defaults
    data = {
        "project": {
            "name": raw_data.get("project", {}).get("name", "app"),
            "runtime": raw_data.get("project", {}).get("runtime", "python"),
            "version": str(raw_data.get("project", {}).get("version", "3.12")),
            "entrypoint": raw_data.get("project", {}).get("entrypoint", "python main.py"),
        },
        "resources": {
            "memory_mb": int(raw_data.get("resources", {}).get("memory_mb", 256)),
            "vcpus": int(raw_data.get("resources", {}).get("vcpus", 1)),
            "cpu_quota_pct": int(raw_data.get("resources", {}).get("cpu_quota_pct", 100)),
            "idle_timeout_sec": int(raw_data.get("resources", {}).get("idle_timeout_sec", 300)),
        },
        "database": {
            "enabled": bool(raw_data.get("database", {}).get("enabled", False)),
            "engine": raw_data.get("database", {}).get("engine", "postgres"),
            "version": str(raw_data.get("database", {}).get("version", "16")),
            "branch": raw_data.get("database", {}).get("branch", "main"),
        },
        "network": {
            "public_port": int(raw_data.get("network", {}).get("public_port", 8000)),
            "egress_policy": raw_data.get("network", {}).get("egress_policy", "allow"),
        },
        "env": raw_data.get("env", {}),
    }
    return data


def detect_project_runtime(project_dir: str = ".") -> Dict[str, Any]:
    """Inspect workspace files and automatically synthesize the optimal nephis.toml configuration."""
    root = Path(project_dir).resolve()
    dir_name = root.name.lower().replace(" ", "-").replace("_", "-")

    runtime = "python"
    version = "3.12"
    entrypoint = "python main.py"
    public_port = 8000
    has_db = False

    # 1. Python Detection
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists() or (root / "Pipfile").exists() or (root / "setup.py").exists():
        runtime = "python"
        version = "3.12"
        public_port = 8000
        req_content = ""
        for req_f in ["requirements.txt", "pyproject.toml", "setup.py"]:
            p = root / req_f
            if p.exists():
                try:
                    req_content += p.read_text(encoding="utf-8", errors="ignore").lower()
                except Exception:
                    pass

        # Detect Web Frameworks
        if "fastapi" in req_content or "uvicorn" in req_content:
            entrypoint = "uvicorn main:app --host 0.0.0.0 --port 8000"
        elif "django" in req_content:
            entrypoint = "python manage.py runserver 0.0.0.0:8000"
        elif "flask" in req_content:
            entrypoint = "flask run --host=0.0.0.0 --port=8000"
        elif (root / "main.py").exists():
            entrypoint = "python main.py"
        elif (root / "app.py").exists():
            entrypoint = "python app.py"

        # Detect Database requirements
        db_indicators = ["psycopg", "asyncpg", "sqlalchemy", "tortoise", "prisma", "databases", "dj-database-url"]
        if any(ind in req_content for ind in db_indicators):
            has_db = True

    # 2. Node.js / TypeScript Detection
    elif (root / "package.json").exists():
        runtime = "nodejs"
        version = "22"
        public_port = 3000
        entrypoint = "npm start"
        try:
            import json
            pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
            if "start" in scripts:
                entrypoint = "npm start"
            elif "dev" in scripts:
                entrypoint = "npm run dev"
            elif (root / "index.js").exists():
                entrypoint = "node index.js"
            elif (root / "server.js").exists():
                entrypoint = "node server.js"

            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            db_indicators = ["pg", "pg-promise", "postgres", "prisma", "@prisma/client", "typeorm", "drizzle-orm", "knex", "sequelize"]
            if any(ind in deps for ind in db_indicators):
                has_db = True
        except Exception:
            pass

    # 3. Rust Detection
    elif (root / "Cargo.toml").exists():
        runtime = "rust"
        version = "1.82"
        public_port = 8080
        entrypoint = "cargo run --release"
        try:
            cargo_txt = (root / "Cargo.toml").read_text(encoding="utf-8").lower()
            if any(d in cargo_txt for d in ["sqlx", "diesel", "tokio-postgres", "postgres"]):
                has_db = True
        except Exception:
            pass

    # 4. Go Detection
    elif (root / "go.mod").exists():
        runtime = "go"
        version = "1.23"
        public_port = 8080
        entrypoint = "go run ."
        try:
            go_mod = (root / "go.mod").read_text(encoding="utf-8").lower()
            if any(d in go_mod for d in ["lib/pq", "pgx", "gorm", "sqlx"]):
                has_db = True
        except Exception:
            pass

    # 5. C / C++ Detection
    elif (root / "Makefile").exists() or (root / "CMakeLists.txt").exists():
        runtime = "cpp"
        version = "gcc-14"
        entrypoint = "make && ./app"
        public_port = 8080

    return {
        "project": {
            "name": dir_name,
            "runtime": runtime,
            "version": version,
            "entrypoint": entrypoint,
        },
        "resources": {
            "memory_mb": 512 if has_db else 256,
            "vcpus": 1,
            "cpu_quota_pct": 100,
            "idle_timeout_sec": 300,
        },
        "database": {
            "enabled": has_db,
            "engine": "postgres",
            "version": "16",
            "branch": "main",
        },
        "network": {
            "public_port": public_port,
            "egress_policy": "allow",
        },
        "env": {
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "info",
        },
    }


def generate_nephis_toml(config: Dict[str, Any], output_path: str = "nephis.toml") -> str:
    """Format and write a clean, well-commented nephis.toml file."""
    proj = config.get("project", {})
    res = config.get("resources", {})
    db = config.get("database", {})
    net = config.get("network", {})
    env = config.get("env", {})

    lines = [
        "# ==============================================================================",
        "# NEPHIS & THANATON DECLARATIVE SPECIFICATION (nephis.toml)",
        "# Sub-6ms KVM MicroVMs & 31ms Zero-Copy PostgreSQL Branching",
        "# ==============================================================================",
        "",
        "[project]",
        f'name = "{proj.get("name", "app")}"',
        f'runtime = "{proj.get("runtime", "python")}"',
        f'version = "{proj.get("version", "3.12")}"',
        f'entrypoint = "{proj.get("entrypoint", "python main.py")}"',
        "",
        "[resources]",
        f'memory_mb = {res.get("memory_mb", 256)}  # Guest RAM allocation in MiB (e.g. 256, 512, 1024)',
        f'vcpus = {res.get("vcpus", 1)}             # Virtual CPUs',
        f'cpu_quota_pct = {res.get("cpu_quota_pct", 100)}  # 100 = 1 full physical core',
        f'idle_timeout_sec = {res.get("idle_timeout_sec", 300)}  # Scale-to-zero stasis timeout (0 = always-on)',
        "",
        "[database]",
        f'enabled = {str(db.get("enabled", False)).lower()}      # Attach 31ms zero-copy Mnemon-DB Postgres instance',
        f'engine = "{db.get("engine", "postgres")}"',
        f'version = "{db.get("version", "16")}"',
        f'branch = "{db.get("branch", "main")}"',
        "",
        "[network]",
        f'public_port = {net.get("public_port", 8000)}  # Internal application port exposed via HTTPS router',
        f'egress_policy = "{net.get("egress_policy", "allow")}"  # "allow" | "isolated" | "locked"',
        "",
        "[env]",
    ]

    for k, v in env.items():
        lines.append(f'{k} = "{v}"')

    lines.append("")
    content = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")

    return content
