"""
Ananke Declarative Speculation DSL.
1-call API for autonomous AI agents to explore parallel multiverse branches.
"""

import time
import concurrent.futures
from typing import List, Dict, Any, Optional

from .context import SpeculationContext
from .bus import SpeculationBus, EventType


class CandidateHypothesis:
    def __init__(self, candidate_id: str, strategy: str, code: Optional[str] = None, is_passing: bool = False, flaw: Optional[str] = None):
        self.id = candidate_id
        self.strategy = strategy
        self.code = code
        self.is_passing = is_passing
        self.flaw = flaw

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "strategy": self.strategy,
            "is_passing": self.is_passing,
            "flaw": self.flaw,
        }


class SpeculationResult:
    def __init__(
        self,
        speculation_id: str,
        winning_branch_id: str,
        winning_strategy: str,
        duration_ms: float,
        pruned_branches: List[str],
        total_tested: int,
        status: str = "SUCCESS",
        hot_swapped: bool = True,
    ):
        self.speculation_id = speculation_id
        self.winning_branch_id = winning_branch_id
        self.winning_strategy = winning_strategy
        self.duration_ms = duration_ms
        self.pruned_branches = pruned_branches
        self.total_tested = total_tested
        self.status = status
        self.hot_swapped = hot_swapped

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speculation_id": self.speculation_id,
            "winning_branch_id": self.winning_branch_id,
            "winning_strategy": self.winning_strategy,
            "duration_ms": self.duration_ms,
            "pruned_branches": self.pruned_branches,
            "total_tested": self.total_tested,
            "status": self.status,
            "hot_swapped": self.hot_swapped,
        }


class SpeculationEngine:
    """Executes declarative speculative exploration across multiple candidates in parallel."""

    def __init__(self, bus: Optional[SpeculationBus] = None):
        self.bus = bus or SpeculationBus()

    def speculate(
        self,
        candidates: List[Dict[str, Any]],
        test_command: str = "pytest",
        base_snapshot: Optional[str] = None,
        timeout_ms: int = 5000,
        strategy: str = "FASTEST_PASSING",
        auto_hot_swap: bool = True,
        tenant_id: str = "default",
    ) -> SpeculationResult:
        start_time = time.perf_counter()

        if not candidates:
            raise ValueError("No candidates provided for speculative multiverse evaluation")

        ctx = SpeculationContext(tenant_id=tenant_id)

        # 1. Broadcast Speculation Spawn
        self.bus.publish(
            EventType.SPECULATION_SPAWN,
            tenant_id=tenant_id,
            branch_id="root",
            payload={"candidates_count": len(candidates), "base_snapshot": base_snapshot},
        )

        parsed_candidates = [
            CandidateHypothesis(
                candidate_id=str(c.get("id")),
                strategy=c.get("strategy", ""),
                code=c.get("code"),
                is_passing=c.get("is_passing", False),
                flaw=c.get("flaw"),
            )
            for c in candidates
        ]

        # 2. Parallel Evaluation
        def eval_candidate(cand: CandidateHypothesis) -> CandidateHypothesis:
            time.sleep(0.005) # 5ms simulated parallel execution
            return cand

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(parsed_candidates)) as executor:
            evaluated = list(executor.map(eval_candidate, parsed_candidates))

        # 3. Elect Winner
        winner = next((c for c in evaluated if c.is_passing), None)
        if winner is None:
            raise RuntimeError("All speculative candidate patches failed validation")

        losers = [c.id for c in evaluated if c.id != winner.id]

        # 4. Broadcast Pruning for losers
        for loser_id in losers:
            self.bus.publish(
                EventType.BRANCH_PRUNED,
                tenant_id=tenant_id,
                branch_id=loser_id,
                payload={"reason": "pruned_by_coordinator"},
            )

        # 5. Broadcast Winner Election
        self.bus.publish(
            EventType.WINNER_ELECTED,
            tenant_id=tenant_id,
            branch_id=winner.id,
            payload={"strategy": winner.strategy, "hot_swapped": auto_hot_swap},
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return SpeculationResult(
            speculation_id=ctx.speculation_id,
            winning_branch_id=winner.id,
            winning_strategy=winner.strategy,
            duration_ms=elapsed_ms,
            pruned_branches=losers,
            total_tested=len(candidates),
            status="SUCCESS",
            hot_swapped=auto_hot_swap,
        )

