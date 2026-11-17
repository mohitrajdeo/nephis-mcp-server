"""Thanaton Exception Classes."""


class ThanatonError(Exception):
    """Base exception for all Thanaton SDK errors."""
    pass


class APIError(ThanatonError):
    """Raised when the Thanaton Control Plane returns an HTTP error status."""
    def __init__(self, status_code: int, message: str):
        super().__init__(f"Thanaton API Error [{status_code}]: {message}")
        self.status_code = status_code
        self.message = message


class SandboxNotFoundError(ThanatonError):
    """Raised when referencing a non-existent or expired sandbox ID."""
    pass


class SQLError(ThanatonError):
    """Raised when a sandbox database query fails execution."""
    pass


class ExecutionTimeoutError(ThanatonError):
    """Raised when an in-sandbox command exceeds its specified timeout window."""
    pass


class EschatonFuelExhaustedError(ThanatonError):
    """Raised when bytecode/script execution exhausts allocated gas/fuel budget."""
    def __init__(self, message: str = "Execution halted: Eschaton gas/fuel budget exhausted"):
        super().__init__(f"EschatonFuelExhaustedError: {message}. Recommendation: Optimize computational complexity or increase initial execution fuel.")


class ThanatonCapacityError(ThanatonError):
    """Raised when the microVM control plane is temporarily at capacity (HTTP 503)."""
    def __init__(self, message: str = "Host capacity saturated"):
        super().__init__(f"ThanatonCapacityError: {message}. Recommendation: Retry with exponential backoff and jitter.")


class ThanatonRateLimitError(ThanatonError):
    """Raised when tenant rate limit is exceeded (HTTP 429)."""
    def __init__(self, retry_after: int = 5, message: str = "Rate limit quota exceeded"):
        super().__init__(f"ThanatonRateLimitError: {message} (Retry after {retry_after}s)")
        self.retry_after = retry_after


class ThanatonTimeoutError(ThanatonError):
    """Raised when control plane HTTP request times out."""
    pass


class ThanatonConnectionError(ThanatonError):
    """Raised when the client cannot connect to the Thanaton control plane daemon."""
    def __init__(self, url: str, reason: str):
        msg = (
            f"Cannot connect to Thanaton Daemon at {url} ({reason}).\n"
            "  -> If using managed cloud: Set base_url='https://nephis.theeducode.com' and api_key='sk_live_...'\n"
            "  -> Quickstart guide: https://nephis.theeducode.com/docs"
        )
        super().__init__(msg)
        self.url = url
        self.reason = reason


class SSRFSecurityViolationError(ThanatonError):
    """Raised when sandbox execution attempts prohibited access to cloud metadata (169.254.169.254) or private networks."""
    def __init__(self, message: str = "Access to cloud metadata IP (169.254.169.254) prohibited"):
        super().__init__(f"SSRFSecurityViolationError: {message}")


class EgressPolicyViolationError(ThanatonError):
    """Raised when sandbox execution attempts unauthorized outbound networking under locked or allowlisted egress policies."""
    def __init__(self, message: str = "Outbound network access prohibited by egress policy"):
        super().__init__(f"EgressPolicyViolationError: {message}")


class EscalationRequiredException(ThanatonError):
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
