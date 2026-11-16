"""
Ananke Cryptographic License & Authority Engine
Manages tenant entitlement, quota enforcement, and tier verification.
Supports offline cryptographic signature verification and telemetry reporting to ananked.
"""

import hmac
import hashlib
import json
import base64
import time
from typing import Dict, Any, List, Optional

DEFAULT_SECRET = "ananke_enterprise_signing_secret_prod_2026"

TIERS = {
    "community": {
        "max_sandboxes": 5,
        "max_cdc_events_per_day": 1000000,
        "max_webhooks_per_day": 10000,
        "max_pool_connections": 20,
        "max_pipe_gb_per_month": 50,
        "max_dns_qps": 50000,
        "max_bastion_sessions": 2,
        "max_pki_certs": 10,
        "max_compress_gb_month": 20,
        "max_nvme_cache_gb": 10,
        "ebpf_sockmap_allowed": False,
        "tcp_repair_allowed": False,
        "features": [
            "sandboxes", "cdc_basic", "webhooks_basic", "pool_basic", "pipe_basic", "dns_basic",
            "bastion_basic", "pki_basic", "compress_basic", "nvme_basic", "reclaim_basic", "graynet_basic", "arbiter_basic", "shm_basic"
        ]
    },
    "pro": {
        "max_sandboxes": 100,
        "max_cdc_events_per_day": 50000000,
        "max_webhooks_per_day": 500000,
        "max_pool_connections": 500,
        "max_pipe_gb_per_month": 5000,
        "max_dns_qps": 500000,
        "max_bastion_sessions": 100,
        "max_pki_certs": 5000,
        "max_compress_gb_month": 50000,
        "max_nvme_cache_gb": 1000,
        "ebpf_sockmap_allowed": True,
        "tcp_repair_allowed": True,
        "features": [
            "sandboxes", "cdc_pro", "webhooks_pro", "finops", "flight_recorder", "chaos", "pool_pro", "pipe_pro", "rootfs", "dns_pro", "live_migration",
            "bastion_pro", "pki_pro", "compress_pro", "socket_handoff", "nvme_cache", "mem_reclaim", "net_chaos", "io_arbiter", "shm_preparser"
        ]
    },
    "enterprise": {
        "max_sandboxes": 999999,
        "max_cdc_events_per_day": 999999999999,
        "max_webhooks_per_day": 999999999999,
        "max_pool_connections": 999999,
        "max_pipe_gb_per_month": 999999999999,
        "max_dns_qps": 999999999999,
        "max_bastion_sessions": 999999,
        "max_pki_certs": 999999,
        "max_compress_gb_month": 999999999999,
        "max_nvme_cache_gb": 999999,
        "ebpf_sockmap_allowed": True,
        "tcp_repair_allowed": True,
        "features": ["*"]
    }
}


class LicenseError(Exception):
    """Raised when license verification fails or quota is exceeded."""
    pass


class LicenseToken:
    def __init__(self, tenant_id: str, tier: str = "community", expires_in_days: int = 365, secret: str = DEFAULT_SECRET):
        if tier not in TIERS:
            raise ValueError(f"Unknown tier: {tier}. Must be one of: {list(TIERS.keys())}")
        self.tenant_id = tenant_id
        self.tier = tier
        self.issued_at = int(time.time())
        self.expires_at = self.issued_at + (expires_in_days * 86400)
        self.entitlements = TIERS[tier]
        self.secret = secret

    def generate(self) -> str:
        """Create a cryptographically signed license token string."""
        claims = {
            "iss": "ananke-authority",
            "tid": self.tenant_id,
            "tier": self.tier,
            "iat": self.issued_at,
            "exp": self.expires_at,
            "ent": self.entitlements
        }
        raw_json = json.dumps(claims, sort_keys=True).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(raw_json).decode("utf-8").rstrip("=")
        
        sig = hmac.new(self.secret.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"ank_lic_{b64_payload}.{sig}"

    @classmethod
    def verify(cls, token: str, secret: str = DEFAULT_SECRET) -> Dict[str, Any]:
        """Validate signature, expiration, and return license claims."""
        if not token or not token.startswith("ank_lic_"):
            raise LicenseError("Invalid license token format. Must start with 'ank_lic_'")

        token_body = token[len("ank_lic_"):]
        if "." not in token_body:
            raise LicenseError("Malformed license token: missing signature delimiter.")

        payload_b64, sig = token_body.rsplit(".", 1)

        # Verify HMAC
        expected_sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            raise LicenseError("Cryptographic signature verification failed: invalid or tampered license.")

        # Decode payload
        padding = "=" * (4 - len(payload_b64) % 4)
        try:
            raw_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
            claims = json.loads(raw_json)
        except Exception as e:
            raise LicenseError(f"Failed to decode license payload: {e}")

        # Check expiration
        now = int(time.time())
        if claims.get("exp", 0) < now:
            raise LicenseError(f"License token expired at {claims.get('exp')}. Current time: {now}")

        return claims


class LicenseAuthority:
    """Authority controller used across CLI, SDK, and MicroVM engines."""
    def __init__(self, token: Optional[str] = None, secret: str = DEFAULT_SECRET):
        self.secret = secret
        self.token = token
        if token:
            try:
                self.claims = LicenseToken.verify(token, secret)
                self.tier = self.claims.get("tier", "community")
                self.tenant_id = self.claims.get("tid", "default")
                self.entitlements = self.claims.get("ent", TIERS["community"])
            except LicenseError as e:
                # Fallback to restricted community tier
                self.claims = None
                self.tier = "community"
                self.tenant_id = "unlicensed"
                self.entitlements = TIERS["community"]
                self.error = str(e)
        else:
            self.claims = None
            self.tier = "community"
            self.tenant_id = "default"
            self.entitlements = TIERS["community"]
            self.error = None

    def assert_feature(self, feature_name: str):
        """Assert that the tenant's license tier allows this feature."""
        features = self.entitlements.get("features", [])
        if "*" in features or feature_name in features:
            return True
        raise LicenseError(
            f"Feature '{feature_name}' requires an upgraded Ananke license tier (Current: {self.tier.upper()}). "
            f"Please upgrade to PRO or ENTERPRISE at https://ananke.run/pricing"
        )

    def is_feature_allowed(self, feature_name: str) -> bool:
        features = self.entitlements.get("features", [])
        return "*" in features or feature_name in features

    def status(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.upper(),
            "tenant_id": self.tenant_id,
            "is_valid": self.claims is not None,
            "entitlements": self.entitlements,
            "expires_at": self.claims.get("exp") if self.claims else None
        }
