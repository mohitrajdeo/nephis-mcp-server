"""Ananke SDK Exceptions."""

class AnankeError(Exception):
    """Base exception for all Ananke SDK errors."""
    pass


class APIError(AnankeError):
    """Raised when the Ananke API returns an HTTP error."""

    def __init__(self, message: str, status_code: int = 500, response_body: str = ""):
        super().__init__(f"[{status_code}] {message}")
        self.status_code = status_code
        self.response_body = response_body


class SandboxNotFoundError(APIError):
    """Raised when the requested sandbox does not exist."""
    pass


class SQLError(APIError):
    """Raised when an embedded PostgreSQL query fails."""
    pass


class ExecutionTimeoutError(AnankeError):
    """Raised when an executed command exceeds its timeout limit."""
    pass


class AnankeConnectionError(AnankeError):
    """Raised when the client cannot connect to the Ananke control plane daemon."""
    def __init__(self, url: str, reason: str):
        msg = (
            f"Cannot connect to Ananke Daemon at {url} ({reason}).\n"
            "  -> If running locally: Launch the daemon with 'ananked' or 'python scripts/ananked.py'\n"
            "  -> If using managed cloud: Set base_url='https://api.ananke.run' and api_key='sk_live_...'\n"
            "  -> Quickstart guide: https://nephis.theeducode.com/docs"
        )
        super().__init__(msg)
        self.url = url
        self.reason = reason


class EscalationRequiredException(AnankeError):
    """Raised when an in-memory Tier 0 verifier operation requires hardware MicroVM escalation."""
    def __init__(
        self,
        capability: str,
        attempted: str,
        reason: str,
        upgrade_code: str = "sandbox = client.upgrade_to_thanaton(session)",
        serialized_state: dict = None,
    ):
        self.capability = capability
        self.attempted = attempted
        self.reason = reason
        self.upgrade_code = upgrade_code
        self.serialized_state = serialized_state or {}
        super().__init__(
            f"EscalationRequired [{capability}]: Attempted `{attempted}` ({reason}). "
            f"Upgrade to Thanaton MicroVM using: `{upgrade_code}`"
        )

