"""Thanaton: Sub-6ms MicroVM Sandboxes and Execution Fabric for AI Coding Agents."""

from .client import Client, SandboxManager
from .config import detect_project_runtime, generate_nephis_toml, parse_nephis_toml
from .exceptions import (
    APIError,
    EgressPolicyViolationError,
    EschatonFuelExhaustedError,
    EscalationRequiredException,
    ExecutionTimeoutError,
    SSRFSecurityViolationError,
    SandboxNotFoundError,
    SQLError,
    ThanatonCapacityError,
    ThanatonConnectionError,
    ThanatonError,
    ThanatonRateLimitError,
    ThanatonTimeoutError,
)
from .sandbox import ExecResult, Sandbox

__version__ = "1.0.0"
__all__ = [
    "Client",
    "Sandbox",
    "SandboxManager",
    "ExecResult",
    "parse_nephis_toml",
    "detect_project_runtime",
    "generate_nephis_toml",
    "ThanatonError",
    "APIError",
    "SandboxNotFoundError",
    "SQLError",
    "ExecutionTimeoutError",
    "ThanatonTimeoutError",
    "ThanatonRateLimitError",
    "ThanatonCapacityError",
    "EschatonFuelExhaustedError",
    "ThanatonConnectionError",
    "EscalationRequiredException",
    "SSRFSecurityViolationError",
    "EgressPolicyViolationError",
]
