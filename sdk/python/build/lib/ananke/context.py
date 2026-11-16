"""
Ananke Speculation Context (W3C-Compatible Canonical Context Envelope).
Propagated across HTTP, PostgreSQL session settings, eBPF, and asynchronous agents.
"""

import base64
import json
import secrets
import time
from typing import Optional, Dict, Any


class SpeculationContext:
    """Canonical 128-bit Speculation Context Envelope."""

    HEADER_NAME = "X-Ananke-Speculation-Context"

    def __init__(
        self,
        tenant_id: str,
        speculation_id: Optional[str] = None,
        branch_id: str = "root",
        parent_lsn: str = "0/16B3490",
        trace_id: Optional[str] = None,
        fuel_budget: int = 1_000_000,
        isolation_level: str = "HARDWARE_MICROVM",
        virtual_timestamp_ns: Optional[int] = None,
    ):
        self.tenant_id = tenant_id
        self.trace_id = trace_id or secrets.token_hex(16)
        self.speculation_id = speculation_id or f"spec_{secrets.token_hex(8)}"
        self.branch_id = branch_id
        self.parent_lsn = parent_lsn
        self.virtual_timestamp_ns = virtual_timestamp_ns or time.time_ns()
        self.fuel_budget = fuel_budget
        self.isolation_level = isolation_level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "trace_id": self.trace_id,
            "speculation_id": self.speculation_id,
            "branch_id": self.branch_id,
            "parent_lsn": self.parent_lsn,
            "virtual_timestamp_ns": self.virtual_timestamp_ns,
            "fuel_budget": self.fuel_budget,
            "isolation_level": self.isolation_level,
        }

    def to_header(self) -> str:
        """Encodes context into URL-safe base64 string for HTTP headers."""
        raw_json = json.dumps(self.to_dict()).encode("utf-8")
        return base64.urlsafe_b64encode(raw_json).decode("utf-8")

    @classmethod
    def from_header(cls, header_val: str) -> "SpeculationContext":
        """Decodes context from base64 HTTP header."""
        raw_json = base64.urlsafe_b64decode(header_val.encode("utf-8")).decode("utf-8")
        data = json.loads(raw_json)
        return cls(**data)

    def to_sql_injection(self) -> str:
        """Generates PostgreSQL session variable configuration SQL."""
        raw_json = json.dumps(self.to_dict()).replace("'", "''")
        return f"SET LOCAL ananke.speculation_context = '{raw_json}';"

    def fork(self, child_branch_id: str) -> "SpeculationContext":
        """Creates a child branch context inheriting parent trace and LSN."""
        return SpeculationContext(
            tenant_id=self.tenant_id,
            speculation_id=self.speculation_id,
            branch_id=child_branch_id,
            parent_lsn=self.parent_lsn,
            trace_id=self.trace_id,
            fuel_budget=self.fuel_budget,
            isolation_level=self.isolation_level,
            virtual_timestamp_ns=self.virtual_timestamp_ns,
        )

