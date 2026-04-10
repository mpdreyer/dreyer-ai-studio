"""
Swarm Repository — abstrakt + Supabase-implementation.
Isolerar all databasåtkomst för swarm_runs och worker_results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SwarmRun:
    id: str
    variant_id: str
    variant: str
    n_workers: int
    status: str
    pass_rate: Optional[float] = None
    median_score: Optional[float] = None
    p95_latency: Optional[float] = None
    decision: Optional[str] = None
    created_at: Optional[str] = None


class SwarmRepository(ABC):
    @abstractmethod
    def get_runs(self, limit: int = 10) -> list[SwarmRun]:
        """Hämta senaste svärm-körningar."""
        ...

    @abstractmethod
    def insert_run(self, run: SwarmRun) -> None:
        """Spara en ny körning."""
        ...

    @abstractmethod
    def insert_worker_results(self, run_id: str, results: list[dict]) -> None:
        """Spara worker-resultat för en körning."""
        ...


class SupabaseSwarmRepository(SwarmRepository):
    def __init__(self, client):
        self._sb = client

    def get_runs(self, limit: int = 10) -> list[SwarmRun]:
        resp = (
            self._sb.table("swarm_runs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [
            SwarmRun(
                id=r["id"],
                variant_id=r["variant_id"],
                variant=r.get("variant", ""),
                n_workers=r["n_workers"],
                status=r["status"],
                pass_rate=r.get("pass_rate"),
                median_score=r.get("median_score"),
                p95_latency=r.get("p95_latency"),
                decision=r.get("decision"),
                created_at=r.get("created_at"),
            )
            for r in (resp.data or [])
        ]

    def insert_run(self, run: SwarmRun) -> None:
        self._sb.table("swarm_runs").insert({
            "id":           run.id,
            "variant_id":   run.variant_id,
            "variant":      run.variant,
            "n_workers":    run.n_workers,
            "status":       run.status,
            "pass_rate":    run.pass_rate,
            "median_score": run.median_score,
            "p95_latency":  run.p95_latency,
            "decision":     run.decision,
        }).execute()

    def insert_worker_results(self, run_id: str, results: list[dict]) -> None:
        rows = [
            {
                "run_id":      run_id,
                "worker_idx":  r["worker_idx"],
                "testcase_id": r["testcase_id"],
                "score":       r["score"],
                "latency_ms":  r["latency_ms"],
                "passed":      r["passed"],
                "error":       r["error"],
            }
            for r in results
        ]
        self._sb.table("worker_results").insert(rows).execute()
