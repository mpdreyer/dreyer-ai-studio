"""
Enhetstester för SwarmController och SwarmConfig.
"""

import pytest
from agents.swarm_controller import SwarmConfig, SwarmController, ValidationError


# ── SwarmConfig.validate ───────────────────────────────────────────────────────

class TestSwarmConfigValidate:
    def test_valid_config(self):
        cfg = SwarmConfig.validate(
            variant="Svara på: {input}",
            variant_id="v1",
            n_workers=10,
            max_concurrent=5,
            domain="general",
        )
        assert cfg.variant == "Svara på: {input}"
        assert cfg.variant_id == "v1"
        assert cfg.n_workers == 10
        assert cfg.max_concurrent == 5

    def test_strips_whitespace(self):
        cfg = SwarmConfig.validate(
            variant="  Svara: {input}  ",
            variant_id="  v1  ",
            n_workers=5,
            max_concurrent=5,
            domain="general",
        )
        assert cfg.variant == "Svara: {input}"
        assert cfg.variant_id == "v1"

    def test_missing_input_placeholder(self):
        with pytest.raises(ValidationError, match=r"\{input\}"):
            SwarmConfig.validate("Ingen placeholder", "v1", 10, 5, "general")

    def test_empty_variant(self):
        with pytest.raises(ValidationError, match="tom"):
            SwarmConfig.validate("", "v1", 10, 5, "general")

    def test_whitespace_only_variant(self):
        with pytest.raises(ValidationError, match="tom"):
            SwarmConfig.validate("   ", "v1", 10, 5, "general")

    def test_empty_variant_id(self):
        with pytest.raises(ValidationError, match="Variant-ID"):
            SwarmConfig.validate("{input}", "", 10, 5, "general")

    def test_zero_workers(self):
        with pytest.raises(ValidationError, match="workers"):
            SwarmConfig.validate("{input}", "v1", 0, 5, "general")

    def test_concurrent_exceeds_workers(self):
        with pytest.raises(ValidationError, match="parallella"):
            SwarmConfig.validate("{input}", "v1", 5, 10, "general")

    def test_to_cli_args_contains_variant_id(self):
        cfg = SwarmConfig.validate("{input}", "baseline", 10, 5, "ai")
        args = cfg.to_cli_args()
        assert "baseline" in args
        assert "--workers 10" in args
        assert "--concurrent 5" in args
        assert "ai" in args

    def test_to_cli_args_truncates_long_variant(self):
        long_variant = "A" * 100 + " {input}"
        cfg = SwarmConfig.validate(long_variant, "v1", 5, 5, "general")
        args = cfg.to_cli_args()
        assert "..." in args

    def test_to_cli_args_shell_safe(self):
        """variant_id med farliga tecken ska inte gå igenom."""
        with pytest.raises(ValidationError):
            SwarmConfig.validate("{input}", "v1; rm -rf /", 5, 5, "general")

    def test_variant_id_rejects_special_chars(self):
        for bad in ["v1 v2", "v1/v2", "v1$", "v1`cmd`"]:
            with pytest.raises(ValidationError):
                SwarmConfig.validate("{input}", bad, 5, 5, "general")


# ── SwarmController.get_runs ───────────────────────────────────────────────────

class TestSwarmControllerGetRuns:
    def test_returns_empty_list(self, controller):
        assert controller.get_runs() == []

    def test_returns_runs_from_repo(self, controller_with_data):
        runs = controller_with_data.get_runs()
        assert len(runs) == 2
        assert runs[0].variant_id == "v1"

    def test_limit_respected(self, controller_with_data):
        runs = controller_with_data.get_runs(limit=1)
        assert len(runs) == 1

    def test_run_fields(self, controller_with_data):
        run = controller_with_data.get_runs()[0]
        assert run.pass_rate == pytest.approx(0.90)
        assert run.status == "completed"
        assert "GODKÄND" in run.decision
