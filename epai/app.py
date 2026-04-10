"""
EPAi — Ain
Streamlit-gränssnitt för lokal AI-rådgivning kring vattenrening.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

# Lägg till epai-katalogen i sys.path vid direkt körning
_EPAI_DIR = Path(__file__).parent
if str(_EPAI_DIR) not in sys.path:
    sys.path.insert(0, str(_EPAI_DIR))

from config import ANLAGGNINGAR, OLLAMA_MODEL
from metadata_db import MetadataDB
from pdf_export import (
    answer_filename, export_full_report, export_single_answer, report_filename,
)
from rag import RAGResult, Source, get_collection_counts, stream_ask

# ── Sidkonfiguration ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="EPAi — Ain",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ──────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []   # {role, content, sources(optional)}
if "selected_anlaggning" not in st.session_state:
    st.session_state.selected_anlaggning = "anlaggning_1"


# ── Hjälpfunktioner ────────────────────────────────────────────────────────────

def _anl_key_from_label(label: str) -> str:
    mapping = {v: k for k, v in ANLAGGNINGAR.items()}
    mapping["Alla (tvärsnitt)"] = "alla"
    return mapping.get(label, "anlaggning_1")


def _run_ingest():
    with st.spinner("Indexerar dokument… (kan ta några minuter)"):
        result = subprocess.run(
            [sys.executable, str(_EPAI_DIR / "ingest.py"), "--anlaggning", "all"],
            capture_output=True, text=True,
        )
    if result.returncode == 0:
        st.success("Dokumentindex uppdaterat.")
    else:
        st.error(f"Indexering misslyckades:\n{result.stderr[-500:]}")
    st.rerun()


def _metadata_types(anl_key: str) -> dict[str, int]:
    try:
        from config import METADATA_DB_PATH
        with MetadataDB(METADATA_DB_PATH) as db:
            return db.types_by_customer(anl_key)
    except Exception:
        return {}


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌊 Ain — EPAi")
    st.caption("by DTSM / EnviroProcess")
    st.divider()

    # Anläggningsval
    anl_labels = list(ANLAGGNINGAR.values()) + ["Alla (tvärsnitt)"]
    selected_label = st.selectbox("Anläggning", anl_labels, index=0)
    anl_key = _anl_key_from_label(selected_label)
    st.session_state.selected_anlaggning = anl_key

    # Statistik
    st.divider()
    st.markdown("**Dokumentindex**")
    counts = get_collection_counts()

    if anl_key == "alla":
        for k, label in ANLAGGNINGAR.items():
            n = counts.get(k, 0)
            st.metric(label, f"{n} chunks", label_visibility="visible")
    else:
        n = counts.get(anl_key, 0)
        st.metric(selected_label, f"{n} chunks")
        types = _metadata_types(anl_key)
        if types:
            st.caption("Dokumenttyper:")
            for dtype, cnt in sorted(types.items(), key=lambda x: -x[1]):
                st.caption(f"  • {dtype.replace('_', ' ')}: {cnt}")

    st.divider()
    if st.button("🔄 Uppdatera dokumentindex", use_container_width=True):
        _run_ingest()

    # Om EPAi
    with st.expander("Om EPAi"):
        st.markdown("""
**EPAi** är en lokal, air-gapped AI-rådgivare för vattenrening vid badanläggningar,
byggd av DTSM för EnviroProcess.

**Exempelfrågor:**
- Är gårdagens prover tagna?
- Vilken är din mest akuta åtgärd just nu?
- Vad är din maxbelastning innan ECO-mode?
- Identifiera trender i kemikalieförbrukning
- Vad säger lagstiftningen om bakterieprovtagning?
- Jämför kemikalieförbrukning mellan anläggningarna

**Modell:** `{model}`
        """.format(model=OLLAMA_MODEL))


# ── Huvudvy ────────────────────────────────────────────────────────────────────

col_title, col_actions = st.columns([3, 1])
with col_title:
    st.markdown(f"### 💬 Ain — {selected_label}")
with col_actions:
    if st.button("🧹 Rensa samtalet", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.session_state.messages:
        report_bytes = export_full_report(
            st.session_state.messages, anl_key
        )
        st.download_button(
            label="📄 Exportera rapport (PDF)",
            data=report_bytes,
            file_name=report_filename(),
            mime="application/pdf",
            use_container_width=True,
        )

st.divider()

# ── Konversationshistorik ──────────────────────────────────────────────────────

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🌊" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

        # Källreferenser och export per AI-svar
        if msg["role"] == "assistant":
            sources: list[Source] = msg.get("sources", [])
            n_src = len(sources)

            row1, row2 = st.columns([2, 1])
            with row1:
                if sources:
                    with st.expander(f"📎 Källor ({n_src})"):
                        for s in sources:
                            st.markdown(
                                f"**{s.file_name}** · `{s.doc_type.replace('_', ' ')}` "
                                f"· {s.customer_id or 'global'}"
                                + (f" · sida/rad {s.page_or_row}" if s.page_or_row else "")
                            )
                            if s.excerpt:
                                st.caption(f"> {s.excerpt[:150]}…")
            with row2:
                # Hitta föregående user-meddelande
                user_q = ""
                if idx > 0 and st.session_state.messages[idx - 1]["role"] == "user":
                    user_q = st.session_state.messages[idx - 1]["content"]
                pdf_bytes = export_single_answer(
                    user_q, msg["content"], sources, anl_key
                )
                st.download_button(
                    label="⬇️ Exportera svar (PDF)",
                    data=pdf_bytes,
                    file_name=answer_filename(),
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"export_answer_{idx}",
                )

# ── Chattinput ─────────────────────────────────────────────────────────────────

if prompt := st.chat_input("Ställ en fråga till Ain…"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Bygg historik utan sources-nyckeln (RAG behöver bara role + content)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]  # exkludera aktuell fråga
    ]

    with st.chat_message("assistant", avatar="🌊"):
        response_placeholder = st.empty()
        full_response = ""
        collected_sources: list[Source] = []

        # Streamat svar
        for token in stream_ask(
            question=prompt,
            anlaggning=anl_key,
            history=history,
            model=OLLAMA_MODEL,
        ):
            if isinstance(token, list):
                collected_sources = token
            else:
                full_response += token
                response_placeholder.markdown(full_response + "▌")

        response_placeholder.markdown(full_response)

    # Spara i historik
    st.session_state.messages.append({
        "role":    "assistant",
        "content": full_response,
        "sources": collected_sources,
    })

    st.rerun()
