"""
Pytest fixtures för Dreyer AI Studio.
"""

import pytest
from unittest.mock import MagicMock

from db.swarm_repository import SwarmRepository, SwarmRun
from agents.swarm_controller import SwarmController


# ── Fake repository (ingen Supabase-anslutning behövs) ────────────────────────

class FakeSwarmRepository(SwarmRepository):
    def __init__(self, runs: list[SwarmRun] | None = None):
        self._runs: list[SwarmRun] = runs or []
        self.inserted_runs: list[SwarmRun] = []
        self.inserted_results: list[dict] = []

    def get_runs(self, limit: int = 10) -> list[SwarmRun]:
        return self._runs[:limit]

    def insert_run(self, run: SwarmRun) -> None:
        self.inserted_runs.append(run)

    def insert_worker_results(self, run_id: str, results: list[dict]) -> None:
        self.inserted_results.extend(results)


@pytest.fixture
def fake_repo() -> FakeSwarmRepository:
    return FakeSwarmRepository()


@pytest.fixture
def repo_with_runs() -> FakeSwarmRepository:
    runs = [
        SwarmRun(
            id="run-001",
            variant_id="v1",
            variant="Svara på: {input}",
            n_workers=10,
            status="completed",
            pass_rate=0.90,
            median_score=1.0,
            p95_latency=450,
            decision="✅ GODKÄND — 90.0% pass rate",
            created_at="2026-04-07T10:00:00",
        ),
        SwarmRun(
            id="run-002",
            variant_id="v2",
            variant="Kort svar: {input}",
            n_workers=20,
            status="completed",
            pass_rate=0.60,
            median_score=0.6,
            p95_latency=600,
            decision="❌ UNDERKÄND — 60.0% pass rate",
            created_at="2026-04-06T09:00:00",
        ),
    ]
    return FakeSwarmRepository(runs=runs)


@pytest.fixture
def controller(fake_repo) -> SwarmController:
    return SwarmController(fake_repo)


@pytest.fixture
def controller_with_data(repo_with_runs) -> SwarmController:
    return SwarmController(repo_with_runs)
