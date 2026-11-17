import os
import tempfile
from pathlib import Path
import pytest

from thanaton.config import (
    detect_project_runtime,
    generate_nephis_toml,
    parse_nephis_toml,
    parse_toml_fallback,
)


def test_toml_fallback_parser():
    content = """
    # Sample nephis.toml
    [project]
    name = "agent-service"
    runtime = "python"
    version = "3.12"
    entrypoint = "uvicorn main:app"

    [resources]
    memory_mb = 512
    vcpus = 2
    cpu_quota_pct = 100
    idle_timeout_sec = 120

    [database]
    enabled = true
    engine = "postgres"
    version = "16"

    [env]
    API_KEY = "sec_test_123"
    DEBUG = false
    """
    data = parse_toml_fallback(content)
    assert data["project"]["name"] == "agent-service"
    assert data["project"]["runtime"] == "python"
    assert data["resources"]["memory_mb"] == 512
    assert data["resources"]["idle_timeout_sec"] == 120
    assert data["database"]["enabled"] is True
    assert data["env"]["API_KEY"] == "sec_test_123"
    assert data["env"]["DEBUG"] is False


def test_generate_and_parse_nephis_toml():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = Path(tmpdir) / "nephis.toml"
        initial_cfg = {
            "project": {
                "name": "enterprise-fastapi",
                "runtime": "python",
                "version": "3.12",
                "entrypoint": "uvicorn main:app --host 0.0.0.0 --port 8000",
            },
            "resources": {
                "memory_mb": 512,
                "vcpus": 1,
                "cpu_quota_pct": 100,
                "idle_timeout_sec": 300,
            },
            "database": {
                "enabled": True,
                "engine": "postgres",
                "version": "16",
                "branch": "staging",
            },
            "network": {
                "public_port": 8000,
                "egress_policy": "allow",
            },
            "env": {
                "ENV": "staging",
                "METRICS": "true",
            },
        }

        generated = generate_nephis_toml(initial_cfg, str(cfg_path))
        assert cfg_path.exists()
        assert "[project]" in generated
        assert 'name = "enterprise-fastapi"' in generated

        parsed = parse_nephis_toml(str(cfg_path))
        assert parsed["project"]["name"] == "enterprise-fastapi"
        assert parsed["resources"]["memory_mb"] == 512
        assert parsed["database"]["enabled"] is True
        assert parsed["database"]["branch"] == "staging"
        assert parsed["network"]["public_port"] == 8000


def test_detect_python_fastapi_and_database():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "requirements.txt").write_text("fastapi==0.115.0\nuvicorn==0.32.0\nasyncpg==0.29.0\n", encoding="utf-8")
        (root / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")

        detected = detect_project_runtime(str(root))
        assert detected["project"]["runtime"] == "python"
        assert "uvicorn" in detected["project"]["entrypoint"]
        assert detected["database"]["enabled"] is True  # asyncpg detected
        assert detected["resources"]["memory_mb"] == 512  # boosted for db


def test_detect_nodejs_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pkg_json = """{
            "name": "my-express-api",
            "scripts": {
                "start": "node server.js"
            },
            "dependencies": {
                "express": "^4.21.0",
                "pg": "^8.13.0"
            }
        }"""
        (root / "package.json").write_text(pkg_json, encoding="utf-8")
        (root / "server.js").write_text("console.log('Server running');", encoding="utf-8")

        detected = detect_project_runtime(str(root))
        assert detected["project"]["runtime"] == "nodejs"
        assert detected["project"]["entrypoint"] == "npm start"
        assert detected["database"]["enabled"] is True  # pg detected


def test_detect_rust_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        cargo_toml = """[package]
name = "hyperion-agent"
version = "0.1.0"
edition = "2021"

[dependencies]
sqlx = { version = "0.8", features = ["postgres"] }
tokio = { version = "1", features = ["full"] }
"""
        (root / "Cargo.toml").write_text(cargo_toml, encoding="utf-8")

        detected = detect_project_runtime(str(root))
        assert detected["project"]["runtime"] == "rust"
        assert detected["project"]["entrypoint"] == "cargo run --release"
        assert detected["database"]["enabled"] is True  # sqlx detected


def test_detect_go_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        go_mod = """module example.com/thanaton-worker

go 1.23

require (
    github.com/lib/pq v1.10.9
)
"""
        (root / "go.mod").write_text(go_mod, encoding="utf-8")

        detected = detect_project_runtime(str(root))
        assert detected["project"]["runtime"] == "go"
        assert detected["project"]["entrypoint"] == "go run ."
        assert detected["database"]["enabled"] is True  # lib/pq detected
