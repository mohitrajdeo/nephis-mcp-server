"""
Ananke Speculation Bus (In-Memory / eBPF RingBuffer Event Mesh).
Broadcasts lifecycle events across the speculation fabric.
"""

import json
import queue
import threading
import time
from typing import Dict, Any, List, Optional, Callable


class EventType:
    SPECULATION_SPAWN = "EVENT_SPECULATION_SPAWN"
    UFFD_PAGE_FAULT_RESOLVED = "EVENT_UFFD_PAGE_FAULT_RESOLVED"
    POSTGRES_SCHEMA_EVOLVED = "EVENT_POSTGRES_SCHEMA_EVOLVED"
    GRAY_NETWORK_DETECTED = "EVENT_GRAY_NETWORK_DETECTED"
    BRANCH_PRUNED = "EVENT_BRANCH_PRUNED"
    WINNER_ELECTED = "EVENT_WINNER_ELECTED"


class SpeculationEvent:
    def __init__(
        self,
        event_id: int,
        event_type: str,
        tenant_id: str,
        branch_id: str,
        payload: Dict[str, Any],
        timestamp_ns: Optional[int] = None,
    ):
        self.id = event_id
        self.type = event_type
        self.tenant_id = tenant_id
        self.branch_id = branch_id
        self.payload = payload
        self.timestamp_ns = timestamp_ns or time.time_ns()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "tenant_id": self.tenant_id,
            "branch_id": self.branch_id,
            "timestamp_ns": self.timestamp_ns,
            "payload": self.payload,
        }


class SpeculationBus:
    """Thread-safe in-memory event mesh and circular history ring."""

    def __init__(self, ring_capacity: int = 4096):
        self.ring_capacity = ring_capacity
        self._seq = 0
        self._lock = threading.Lock()
        self._subscribers: Dict[str, queue.Queue] = {}
        self._ring: List[SpeculationEvent] = []

    def publish(
        self,
        event_type: str,
        tenant_id: str,
        branch_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> SpeculationEvent:
        with self._lock:
            self._seq += 1
            ev = SpeculationEvent(
                event_id=self._seq,
                event_type=event_type,
                tenant_id=tenant_id,
                branch_id=branch_id,
                payload=payload or {},
            )
            self._ring.append(ev)
            if len(self._ring) > self.ring_capacity:
                self._ring.pop(0)

            # Broadcast non-blocking to active subscribers
            for sub_queue in list(self._subscribers.values()):
                try:
                    sub_queue.put_nowait(ev)
                except queue.Full:
                    pass
            return ev

    def subscribe(self, subscriber_id: str, max_buffer: int = 256) -> queue.Queue:
        with self._lock:
            q = queue.Queue(maxsize=max_buffer)
            self._subscribers[subscriber_id] = q
            return q

    def unsubscribe(self, subscriber_id: str) -> None:
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "published_events": self._seq,
                "active_listeners": len(self._subscribers),
                "ring_stored": len(self._ring),
                "ring_capacity": self.ring_capacity,
                "status": "OPERATIONAL",
            }

