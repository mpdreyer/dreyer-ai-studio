import streamlit as st

from agents.swarm_controller import SwarmController, ValidationError
from core.state_manager import state
from db.swarm_repository import SupabaseSwarmRepository, SwarmRun
from utils.exceptions import handle_error


def _get_controller(sb) -> SwarmController:
    return SwarmController(SupabaseSwarmRepository(sb))


# ── Delfunktioner ──────────────────────────────────────────────────────────────

def _render_header():
    st.subheader("🐝 Ruflo Testsvärm")
    st.caption("Upp till 90 parallella worker-agenter · Claude Code kör svärmens motor")


def _render_form(controller: SwarmController):
    """Konfigurationsformulär med validering. Returnerar True om svärm startades."""
    with st.container(border=True):
        st.markdown("**Svärm-konfiguration**")
        col1, col2, col3 = st.columns(3)
        with col1:
            variant = st.text_area(
                "Prompt-variant att testa", height=80,
                value="Du är en hjälpsam AI-assistent. Besvara frågan: {input}",
            )
            variant_id = st.text_input("Variant-ID", value="v1")
        with col2:
            n_workers = st.slider("Antal workers", 5, 90, 30, step=5)
            max_concurrent = st.slider("Max parallella (rate limit)", 5, 30, 20, step=5)
        with col3:
            domain = st.selectbox("Testdomän", ["general", "ai", "code"], index=0)
            st.metric("Estimerad kostnad", f"~{n_workers * 0.001:.3f} USD")
            st.metric("Estimerad tid", f"~{n_workers // max_concurrent * 3 + 10}s")

    if st.button("🐝 Starta svärm", use_container_width=True, type="primary"):
        try:
            config = controller.build_config(
                variant, variant_id, n_workers, max_concurrent, domain
            )
            state.set_active_swarm(config)
            st.info(f"""**Svärm konfigurerad:**
- {config.n_workers} workers · max {config.max_concurrent} parallella
- Variant-ID: `{config.variant_id}` · Domän: `{config.domain}`

**Kör i terminal (rekommenderat):**
```bash
cd ~/dreyer-ai-studio
bash run_swarm.sh {config.to_cli_args()}
```

**Eller direkt med python3:**
```bash
cd ~/dreyer-ai-studio
python3 -m agents.swarm_runner {config.to_cli_args()}
```

**Hjälp:** `python3 -m agents.swarm_runner --help`""")
        except ValidationError as e:
            st.error(f"Konfigurationsfel: {e}")


@handle_error("Kunde inte ladda körningshistorik", fallback=None)
def _render_history(controller: SwarmController):
    st.markdown("**Historiska svärm-körningar**")
    runs = controller.get_runs(limit=10)
    if not runs:
        st.caption("Inga svärm-körningar ännu. Kör din första svärm via terminalen.")
        return

    for run in runs:
        _render_run_card(run)


def _render_run_card(run: SwarmRun):
    status_icon = (
        "✅" if run.status == "completed"
        else "🔄" if run.status == "running"
        else "❌"
    )
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        col1.markdown(f"{status_icon} **{run.variant_id}**")
        col1.caption(run.created_at[:16] if run.created_at else "—")
        col2.metric("Workers", run.n_workers)
        col3.metric(
            "Pass rate",
            f"{run.pass_rate * 100:.1f}%" if run.pass_rate is not None else "—",
        )
        decision = run.decision or "—"
        if "GODKÄND" in decision:
            col4.success(decision[:80])
        elif decision != "—":
            col4.error(decision[:80])


def _render_architecture():
    st.markdown("**Ruflo-arkitektur**")
    st.code("""
Spawner (Claude Code)
    │
    ├── Worker-01 (testcase #001) ─┐
    ├── Worker-02 (testcase #002)  │  Alla parallella
    ├── Worker-03 (testcase #003)  │  Supabase tar emot resultaten
    ├── ...                         │  live medan de trillar in
    └── Worker-90 (testcase #090) ─┘
                   │
              Supabase (worker_results)
                   │
    Architetto aggregerar + beslutar
                   │
    Diavolo säkerhetsgranskar parallellt
    """, language="text")


# ── Publik entry point ─────────────────────────────────────────────────────────

def render_swarm(project: dict | None, sb):
    controller = _get_controller(sb)
    _render_header()
    _render_form(controller)
    st.divider()
    _render_history(controller)
    st.divider()
    _render_architecture()
