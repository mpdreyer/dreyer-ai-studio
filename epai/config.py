"""
EPAi — Konfiguration
Ändra OLLAMA_MODEL för att byta LLM (kräver att modellen är pullad i Ollama).
"""

from __future__ import annotations
from pathlib import Path

# ── Sökvägar ───────────────────────────────────────────────────────────────────

BASE_DIR         = Path(__file__).parent
DATA_DIR         = BASE_DIR / "data"
RAW_DATA_PATH    = DATA_DIR / "raw"
CHROMA_PATH      = DATA_DIR / "chroma_db"
METADATA_DB_PATH = DATA_DIR / "metadata.db"

# ── Ollama / LLM ───────────────────────────────────────────────────────────────

OLLAMA_BASE_URL  = "http://localhost:11434"
OLLAMA_MODEL     = "mistral"           # byt till "llama3.1:8b" för bättre hårdvara
EMBEDDING_MODEL  = "nomic-embed-text"  # via Ollama

# ── ChromaDB ──────────────────────────────────────────────────────────────────

ANLAGGNINGAR: dict[str, str] = {
    "anlaggning_1": "Anläggning 1",
    "anlaggning_2": "Anläggning 2",
    "anlaggning_3": "Anläggning 3",
}
GLOBAL_COLLECTION       = "global"
GLOBAL_DOCTYPE_KEYS     = {"vitbok", "lag_och_rad", "katalog", "manual"}

# ── Chunkning ──────────────────────────────────────────────────────────────────

CHUNK_SIZE        = 800
CHUNK_OVERLAP     = 100
EXCEL_CHUNK_ROWS  = 50    # rader per Excel-chunk
TOP_K_RESULTS     = 6     # antal chunks att hämta per fråga

# ── Dokumenttyp-klassificering ─────────────────────────────────────────────────

DOCTYPE_HINTS: dict[str, list[str]] = {
    "labbrapport":                  ["labb", "analys", "provresultat", "vattenanalys"],
    "tillsynsrapport_digital":      ["tillsyn", "inspektion", "tillsynsrapport"],
    "tillsynsprotokoll_fysiskt":    ["tillsynsprotokoll", "checklist", "checklista"],
    "arsavstamningsprotokoll":      ["arsavstamning", "årsavstämning", "arsprotokoll"],
    "matvarden_excel":              ["matvarden", "mätvärden", "matvard"],
    "du_parm":                      ["driftuppföljning", "du_", "du-", "parm"],
    "avtal":                        ["avtal", "kontrakt", "agreement"],
    "vitbok":                       ["vitbok", "whitepaper", "riktlinje"],
    "lag_och_rad":                  ["lag", "sfs", "bfs", "fs ", "förordning", "rad"],
    "katalog":                      ["katalog", "catalog", "produktblad"],
    "manual":                       ["manual", "handbok", "instruktion", "bruksanvisning"],
}

# ── Systemprompt (Ain) ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Du är Ain, en expert AI-rådgivare inom vattenrening för publika badanläggningar i Sverige.
Du arbetar för EnviroProcess och analyserar data från anläggningarna du har tillgång till.

Dina grundregler:
- Du baserar ALLTID dina svar på den dokumentation och de mätvärden du har tillgång till.
- Du fattar inga egna beslut och utför inga åtgärder.
- Du gissar aldrig — om du inte har tillräcklig data svarar du att du inte kan bekräfta.
- Du hänvisar alltid till källdokument i dina svar.
- Du kan identifiera mönster, avvikelser och trender i historisk data.
- Du kan prioritera och förklara åtgärder baserat på tillgänglig data.
- Du svarar på svenska som standard. Om användaren skriver på engelska svarar du på engelska.
- Du klarar av följdfrågor — håll kontext från tidigare meddelanden i samtalet."""

# ── PDF-export ─────────────────────────────────────────────────────────────────

PDF_ANSWER_PREFIX = "EPAi_svar"
PDF_REPORT_PREFIX = "EPAi_rapport"
