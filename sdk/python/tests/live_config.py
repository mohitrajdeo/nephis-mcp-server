import os
import json
import ssl
import urllib.request

try:
    _DEFAULT_SSL_CTX = ssl._create_unverified_context()
except Exception:
    _DEFAULT_SSL_CTX = ssl.create_default_context()
    _DEFAULT_SSL_CTX.check_hostname = False
    _DEFAULT_SSL_CTX.verify_mode = ssl.CERT_NONE

DEV_SESSION_URL = "https://nephis.theeducode.com/v1/auth/developer-session"
THANATON_URL = os.environ.get("THANATON_API_URL", "https://nephis.theeducode.com")
NEPHIS_URL = os.environ.get("NEPHIS_API_URL", "https://nephis.theeducode.com")
MNEMON_URL = os.environ.get("MNEMON_API_URL", "https://db.theeducode.com")
ANCHOR_PROJECT_ID = os.environ.get("NEPHIS_ANCHOR_PROJECT", "3eb8d9e9-819f-47b1-89b3-5157b88570a8")

_cached_key = None

def get_live_api_key():
    global _cached_key
    if _cached_key:
        return _cached_key
    env_key = os.environ.get("NEPHIS_API_KEY") or os.environ.get("THANATON_API_KEY")
    if env_key:
        _cached_key = env_key
        return _cached_key

    try:
        req = urllib.request.Request(
            DEV_SESSION_URL,
            data=json.dumps({"github_username": "mohitrajdeo", "email": "mohit@mohitrajdeo.in"}).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "NephisLivePyTests/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10, context=_DEFAULT_SSL_CTX) as resp:
            data = json.loads(resp.read().decode())
            _cached_key = data.get("api_key") or data.get("session_token")
            return _cached_key
    except Exception as e:
        # Fallback to persistent test key
        return "mrd_live_63bb486dd0718806c08fb3ec9428cbd9dc8e7e88e20073f1"
