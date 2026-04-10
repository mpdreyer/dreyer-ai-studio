"""
EPAi — Smoke test
Verifierar att Ollama svarar, ChromaDB är tillgänglig och RAG-pipeline fungerar.

Kör: python epai/test_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Lägg till epai i path
_EPAI_DIR = Path(__file__).parent
if str(_EPAI_DIR) not in sys.path:
    sys.path.insert(0, str(_EPAI_DIR))

import urllib.request
import json


def check_ollama() -> bool:
    print("\n[1/3] Kontrollerar Ollama…")
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            print(f"  ✓ Ollama svarar. Tillgängliga modeller: {models}")
            return True
    except Exception as e:
        print(f"  ✗ Ollama ej tillgänglig: {e}")
        print("    → Starta Ollama och kör: ollama pull mistral && ollama pull nomic-embed-text")
        return False


def check_chromadb() -> bool:
    print("\n[2/3] Kontrollerar ChromaDB-collections…")
    try:
        from rag import get_collection_counts
        counts = get_collection_counts()
        all_empty = all(v == 0 for v in counts.values())
        for col, n in counts.items():
            status = "✓" if n > 0 else "○"
            print(f"  {status} {col:20s}: {n} chunks")
        if all_empty:
            print("  ⚠  Inga dokument indexerade. Kör: python epai/ingest.py --anlaggning all")
        return True
    except Exception as e:
        print(f"  ✗ ChromaDB-fel: {e}")
        return False


def check_rag() -> bool:
    print("\n[3/3] Kör testfrågor mot RAG-pipeline…")
    from rag import ask

    test_cases = [
        ("Är gårdagens prover tagna?",                                          "anlaggning_1"),
        ("Identifiera trender i kemikalieförbrukning för alla anläggningar",    "alla"),
        ("Vad säger lagstiftningen om bakterieprovtagning i publika bad?",      "anlaggning_1"),
    ]

    all_ok = True
    for question, anl in test_cases:
        print(f"\n  Fråga [{anl}]: {question[:60]}…")
        try:
            result = ask(question, anlaggning=anl)
            if result.error:
                print(f"  ⚠  Svar med fel: {result.error}")
                print(f"     {result.answer[:200]}")
            else:
                print(f"  ✓ Svar ({result.n_chunks_used} chunks använda):")
                print(f"     {result.answer[:300]}{'…' if len(result.answer) > 300 else ''}")
                if result.sources:
                    print(f"  📎 Källor ({len(result.sources)}):")
                    for s in result.sources[:3]:
                        print(f"     · {s.file_name} [{s.doc_type}]")
        except Exception as e:
            print(f"  ✗ RAG-fel: {e}")
            all_ok = False

    return all_ok


def main():
    print("=" * 50)
    print("🌊 EPAi Smoke Test")
    print("=" * 50)

    ok_ollama = check_ollama()
    ok_chroma = check_chromadb()

    if ok_ollama and ok_chroma:
        ok_rag = check_rag()
    else:
        print("\n[3/3] Hoppar RAG-test — krav ej uppfyllda ovan.")
        ok_rag = False

    print("\n" + "=" * 50)
    if ok_ollama and ok_chroma and ok_rag:
        print("✅ Alla kontroller godkända — EPAi är redo.")
        sys.exit(0)
    else:
        results = {
            "Ollama": ok_ollama,
            "ChromaDB": ok_chroma,
            "RAG": ok_rag,
        }
        failed = [k for k, v in results.items() if not v]
        print(f"⚠️  Kontroller med fel: {', '.join(failed)}")
        print("   Se felmeddelanden ovan för åtgärd.")
        sys.exit(1)


if __name__ == "__main__":
    main()
