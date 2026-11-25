"""API key resolution and secure local credential storage for NEPHIS clients."""

import hashlib
import json
import os
import platform
import socket
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

CANONICAL_BASE_URL = "https://nephis.theeducode.com"
USER_AGENT = "nephis-sdk/1.0.0"


def resolve_base_url(override: Optional[str] = None) -> str:
    """Resolve the canonical base URL, defaulting strictly to https://nephis.theeducode.com."""
    if override and override.strip():
        url = override.strip().rstrip("/")
        if url != "http://127.0.0.1:8080":
            return url

    for env_var in ("NEPHIS_BASE_URL", "NEPHIS_API_URL", "CIEL_BASE_URL", "THANATON_BASE_URL", "ANANKE_BASE_URL"):
        val = os.environ.get(env_var)
        if val and val.strip():
            url = val.strip().rstrip("/")
            if url != "http://127.0.0.1:8080":
                return url

    return CANONICAL_BASE_URL


def get_credentials_path() -> Path:
    """Return ~/.nephis/credentials.json path."""
    return Path.home() / ".nephis" / "credentials.json"


def load_stored_credentials() -> Optional[Dict[str, Any]]:
    """Load credentials from ~/.nephis/credentials.json if available."""
    cred_file = get_credentials_path()
    if not cred_file.is_file():
        return None
    try:
        with open(cred_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and data.get("api_key"):
                return data
    except Exception:
        pass
    return None


def save_credentials(creds: Dict[str, Any]) -> Path:
    """Save credentials to ~/.nephis/credentials.json with chmod 0600."""
    cred_file = get_credentials_path()
    try:
        cred_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    except Exception:
        pass

    temp_file = cred_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2)

    temp_file.replace(cred_file)

    try:
        os.chmod(cred_file, 0o600)
        os.chmod(cred_file.parent, 0o700)
    except Exception:
        pass

    return cred_file


def compute_hardware_signature() -> str:
    """Compute deterministic hardware signature: sha256(hostname + mac_address + os_platform)."""
    hostname = socket.gethostname()
    try:
        raw_mac = uuid.getnode()
        mac = ":".join(f"{(raw_mac >> (8 * i)) & 0xFF:02x}" for i in reversed(range(6)))
    except Exception:
        mac = "00:00:00:00:00:00"
    os_plat = f"{platform.system().lower()}-{platform.machine().lower()}"
    raw_str = f"{hostname}:{mac}:{os_plat}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def solve_pow(challenge_nonce: str, machine_signature: str, difficulty: int = 4) -> str:
    """Solve Hashcash difficulty (finding solution_nonce in <600ms)."""
    target_prefix = "0" * max(1, difficulty)
    for i in range(10_000_000):
        sol = str(i)
        data = challenge_nonce + machine_signature + sol
        h = hashlib.sha256(data.encode("utf-8")).hexdigest()
        if h.startswith(target_prefix):
            return sol
    raise RuntimeError("Failed to solve Proof-of-Work challenge within iteration bounds")


def resolve_developer_identity() -> tuple[str, str]:
    """
    Resolve developer/agent name and deliverable contact email.
    Checks environment variables -> local git configuration -> interactive prompt (if TTY).
    """
    name = os.environ.get("NEPHIS_NAME") or os.environ.get("NEPHIS_DEVELOPER_NAME") or os.environ.get("CIEL_NAME") or ""
    email = os.environ.get("NEPHIS_EMAIL") or os.environ.get("NEPHIS_DEVELOPER_EMAIL") or os.environ.get("CIEL_EMAIL") or ""

    name = name.strip()
    email = email.strip()

    if not name or not email:
        try:
            import subprocess
            if not name:
                git_name = subprocess.check_output(
                    ["git", "config", "user.name"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=2
                ).strip()
                if git_name:
                    name = git_name
            if not email:
                git_email = subprocess.check_output(
                    ["git", "config", "user.email"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=2
                ).strip()
                if git_email:
                    email = git_email
        except Exception:
            pass

    if (not name or not email) and sys.stdin.isatty():
        try:
            if not name:
                name = input("Enter developer/agent name for Nephis key claim: ").strip()
            if not email:
                email = input("Enter reachable contact email (e.g. Gmail) to receive key and alerts: ").strip()
        except (EOFError, KeyboardInterrupt):
            pass

    if not name:
        name = socket.gethostname() or "Nephis Agent"
    if not email:
        raise RuntimeError(
            "Nephis API key claim requires a contact email and name so credentials and alerts can be delivered. "
            "Please set NEPHIS_EMAIL and NEPHIS_NAME environment variables or configure 'git config user.email' / 'git config user.name'."
        )

    return name, email


def bootstrap_agent_key(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Execute zero-human bootstrap: fetch challenge, solve Hashcash PoW, claim key, save creds."""
    canonical_url = resolve_base_url(base_url)

    # 1. Fetch challenge
    ch_url = f"{canonical_url}/v1/auth/challenge"
    ch_req = urllib.request.Request(
        ch_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="GET",
    )

    with urllib.request.urlopen(ch_req, timeout=15) as resp:
        ch_data = json.loads(resp.read().decode("utf-8"))

    nonce = ch_data.get("nonce")
    difficulty = ch_data.get("difficulty", 4)
    if not nonce:
        raise RuntimeError("Server returned challenge without nonce")

    # 2. Compute hardware signature
    sig = compute_hardware_signature()

    # 3. Solve Hashcash
    sol = solve_pow(nonce, sig, difficulty)

    # 4. Resolve Developer / Agent Identity
    name, email = resolve_developer_identity()

    # 5. Claim Agent Key
    claim_url = f"{canonical_url}/v1/auth/claim-agent-key"
    payload = json.dumps({
        "challenge_nonce": nonce,
        "solution_nonce": sol,
        "machine_signature": sig,
        "client_version": "1.0.2",
        "name": name,
        "email": email,
    }).encode("utf-8")

    claim_req = urllib.request.Request(
        claim_url,
        data=payload,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(claim_req, timeout=15) as resp:
        claim_data = json.loads(resp.read().decode("utf-8"))

    api_key = claim_data.get("api_key")
    if not api_key:
        raise RuntimeError("Server failed to issue api_key in claim response")

    credentials = {
        "api_key": api_key,
        "tenant_id": claim_data.get("tenant_id", ""),
        "tier": claim_data.get("tier"),
        "machine_signature": sig,
        "created_at": time.time(),
    }
    for field in ("credits", "daily_quota"):
        value = claim_data.get(field)
        if isinstance(value, (int, float)) and value >= 0:
            credentials[field] = value

    # 5. Save credentials to ~/.nephis/credentials.json (chmod 0600)
    save_credentials(credentials)

    return credentials


def resolve_api_key(override: Optional[str] = None, base_url: Optional[str] = None) -> str:
    """
    Resolve API Key strictly following precedence:
    1. Direct override
    2. NEPHIS_API_KEY -> CIEL_API_KEY -> THANATON_API_KEY (also ANANKE_API_KEY)
    3. ~/.nephis/credentials.json
    4. Empty string (the caller reports missing credentials)
    """
    if override and override.strip():
        return override.strip()

    # 1. Environment variables
    for env_var in ("NEPHIS_API_KEY", "CIEL_API_KEY", "THANATON_API_KEY", "ANANKE_API_KEY"):
        val = os.environ.get(env_var)
        if val and val.strip():
            return val.strip()

    # 2. Check ~/.nephis/credentials.json
    stored = load_stored_credentials()
    if stored and stored.get("api_key"):
        return stored["api_key"]

    return ""
