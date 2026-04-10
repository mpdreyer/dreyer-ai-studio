"""
Enhetstester för SupabaseSwarmRepository med mockad Supabase-klient.
"""

import pytest
from unittest.mock import MagicMock, call

from db.swarm_repository import SupabaseSwarmRepository, SwarmRun


def _make_mock_client(rows: list[dict]) -> MagicMock:
    """Bygger en minimal mock av Supabase-klienten."""
    client = MagicMock()
    execute = MagicMock()
    execute.data = rows
    (
        client.table.return_value
        .select.return_value
        .order.return_value
        .limit.return_value
        .execute.return_value
    ) = execute
    return client


class TestSupabaseSwarmRepositoryGetRuns:
    def test_returns_swarm_runs(self):
        rows = [
            {
                "id": "abc",
                "variant_id": "v1",
                "variant": "{input}",
                "n_workers": 5,
                "status": "completed",
                "pass_rate": 0.8,
                "median_score": 0.8,
                "p95_latency": 500,
                "decision": "✅ GODKÄND",
                "created_at": "2026-04-07T10:00:00",
            }
        ]
        repo = SupabaseSwarmRepository(_make_mock_client(rows))
        runs = repo.get_runs()
        assert len(runs) == 1
        assert isinstance(runs[0], SwarmRun)
        assert runs[0].variant_id == "v1"
        assert runs[0].pass_rate == pytest.approx(0.8)

    def test_returns_empty_list_when_no_data(self):
        repo = SupabaseSwarmRepository(_make_mock_client([]))
        assert repo.get_runs() == []

    def test_handles_missing_optional_fields(self):
        rows = [{
            "id": "x",
            "variant_id": "v1",
            "variant": "{input}",
            "n_workers": 1,
            "status": "running",
        }]
        repo = SupabaseSwarmRepository(_make_mock_client(rows))
        run = repo.get_runs()[0]
        assert run.pass_rate is None
        assert run.decision is None


class TestSupabaseSwarmRepositoryInsert:
    def test_insert_run_calls_table(self):
        client = MagicMock()
        repo = SupabaseSwarmRepository(client)
        run = SwarmRun(
            id="r1", variant_id="v1", variant="{input}", n_workers=5,
            status="completed", pass_rate=1.0,
        )
        repo.insert_run(run)
        client.table.assert_called_with("swarm_runs")

    def test_insert_worker_results_calls_table(self):
        client = MagicMock()
        repo = SupabaseSwarmRepository(client)
        results = [
            {"worker_idx": 1, "testcase_id": "t1", "score": 1.0,
             "latency_ms": 200, "passed": True, "error": None},
        ]
        repo.insert_worker_results("run-1", results)
        client.table.assert_called_with("worker_results")
