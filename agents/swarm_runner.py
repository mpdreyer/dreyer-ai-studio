#!/usr/bin/env python3
"""
Dreyer AI Studio — Ruflo Testsvärm
Kör prompt-varianter mot N parallella worker-agenter.

Användning:
  python3 -m agents.swarm_runner --help
  bash run_swarm.sh --variant "Svara på: {input}" --variant-id v1 --workers 10
"""

import argparse
import asyncio
import json
import os
import pathlib
import sys
import time
import uuid
from statistics import median

# ── Ladda secrets från .streamlit/secrets.toml om env-vars saknas ─────────────

def load_secrets():
    secrets_path = pathlib.Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return
    try:
        # Använd tomllib (3.11+) eller falla tillbaka på manuell parsing
        try:
            import tomllib
            data = tomllib.loads(secrets_path.read_text())
        except ImportError:
            try:
                import toml
                data = toml.load(secrets_path)
            except ImportError:
                # Manuell enkel parsning som fallback
                data = {}
                for line in secrets_path.read_text().splitlines():
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        data[k.strip()] = v.strip().strip('"').strip("'")

        for key, val in data.items():
            if key not in os.environ:
                os.environ[key] = str(val)
    except Exception as e:
        print(f"⚠  Kunde inte läsa secrets.toml: {e}", file=sys.stderr)

load_secrets()

# ── Testcase-bibliotek ─────────────────────────────────────────────────────────

TESTCASES = {
    "general": [
        {"id": "gen-001", "input": "Vad är 17 gånger 8?",                "expected": "136"},
        {"id": "gen-002", "input": "Vilken är Europas folkrikaste stad?", "expected": "Istanbul"},
        {"id": "gen-003", "input": "Vad är vattnets kemiska formel?",     "expected": "H2O"},
        {"id": "gen-004", "input": "Hur många dagar har ett skottår?",    "expected": "366"},
        {"id": "gen-005", "input": "Vad heter Sveriges statsminister 2024?", "expected": "Ulf Kristersson"},
        {"id": "gen-006", "input": "Vad är Pi avrundat till 4 decimaler?","expected": "3.1416"},
        {"id": "gen-007", "input": "Vilken planet är störst i solsystemet?", "expected": "Jupiter"},
        {"id": "gen-008", "input": "Hur många sekunder är en timme?",     "expected": "3600"},
        {"id": "gen-009", "input": "Vad är roten ur 144?",                "expected": "12"},
        {"id": "gen-010", "input": "Vilket år grundades Google?",         "expected": "1998"},
    ],
    "ai": [
        {"id": "ai-001", "input": "Vad är RAG inom AI?",                  "expected": "Retrieval-Augmented Generation"},
        {"id": "ai-002", "input": "Vad innebär 'hallucination' hos LLM?", "expected": "fabricated"},
        {"id": "ai-003", "input": "Vad är en transformer-arkitektur?",    "expected": "attention"},
        {"id": "ai-004", "input": "Vad är CoT-prompting?",                "expected": "Chain-of-Thought"},
        {"id": "ai-005", "input": "Vad är temperatur i LLM-context?",     "expected": "randomness"},
    ],
    "code": [
        {"id": "code-001", "input": "Vad returnerar len('hello') i Python?",  "expected": "5"},
        {"id": "code-002", "input": "Vad är en list comprehension i Python?",  "expected": "list"},
        {"id": "code-003", "input": "Vad gör git rebase?",                      "expected": "rebase"},
        {"id": "code-004", "input": "Vad är en REST API?",                      "expected": "HTTP"},
        {"id": "code-005", "input": "Vad är Docker?",                          "expected": "container"},
    ],
}


def _get_testcases(domain: str, n_workers: int) -> list[dict]:
    """Bygger testcase-listan, cyklar om n_workers > antal i domänen."""
    base = TESTCASES.get(domain, TESTCASES["general"])
    cases = []
    for i in range(n_workers):
        tc = base[i % len(base)].copy()
        tc["id"] = f"{tc['id']}-w{i+1:03d}"
        cases.append(tc)
    return cases


# ── Claude API-anrop (utan streamlit-beroende) ────────────────────────────────

def _get_anthropic_client():
    import anthropic
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("❌ ANTHROPIC_API_KEY saknas. Kontrollera .streamlit/secrets.toml",
              file=sys.stderr)
        sys.exit(1)
    return anthropic.Anthropic(api_key=key)


async def _run_worker(
    client,
    worker_idx: int,
    testcase: dict,
    variant_template: str,
    sem: asyncio.Semaphore,
) -> dict:
    """Kör ett enskilt worker-anrop mot Claude API."""
    async with sem:
        prompt = variant_template.replace("{input}", testcase["input"])
        t0 = time.monotonic()
        try:
            # Synkront anrop i executor för att inte blockera event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    model="claude-haiku-4-5-20251001",  # Haiku = snabbast + billigast för svärm
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                )
            )
            reply   = response.content[0].text.strip()
            latency = int((time.monotonic() - t0) * 1000)
            expected = testcase.get("expected", "").lower()
            passed   = expected in reply.lower() if expected else True
            score    = 1.0 if passed else 0.0

            return {
                "worker_idx":  worker_idx,
                "testcase_id": testcase["id"],
                "reply":       reply,
                "score":       score,
                "latency_ms":  latency,
                "passed":      passed,
                "error":       None,
            }
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return {
                "worker_idx":  worker_idx,
                "testcase_id": testcase["id"],
                "reply":       "",
                "score":       0.0,
                "latency_ms":  latency,
                "passed":      False,
                "error":       str(e),
            }


async def _run_swarm_async(
    variant: str,
    testcases: list[dict],
    max_concurrent: int,
) -> list[dict]:
    """Kör hela svärmen asynkront med semaphor för rate-limiting.

    Använder asyncio.gather(return_exceptions=True) så att ett enskilt
    worker-fel aldrig avbryter hela svärmen.
    """
    client = _get_anthropic_client()
    sem    = asyncio.Semaphore(max_concurrent)
    tasks  = [
        _run_worker(client, i + 1, tc, variant, sem)
        for i, tc in enumerate(testcases)
    ]

    raw = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for i, item in enumerate(raw):
        if isinstance(item, BaseException):
            # Worker kraschade utan att catch:a — bygg ett fellobjekt
            result = {
                "worker_idx":  i + 1,
                "testcase_id": testcases[i]["id"],
                "reply":       "",
                "score":       0.0,
                "latency_ms":  0,
                "passed":      False,
                "error":       f"Okänt fel: {item}",
            }
        else:
            result = item

        status = "✅" if result["passed"] else "❌"
        err    = f" [{result['error'][:40]}]" if result["error"] else ""
        print(f"  {status} Worker {result['worker_idx']:03d} · "
              f"{result['testcase_id']} · {result['latency_ms']}ms{err} "
              f"[{i + 1}/{len(tasks)}]")
        results.append(result)

    return results


# ── Supabase-sparning via repository ──────────────────────────────────────────

def _save_to_supabase(run_id: str, variant_id: str, variant: str,
                      n_workers: int, results: list[dict],
                      pass_rate: float, med_score: float,
                      p95: float, decision: str):
    try:
        from supabase import create_client
        from db.swarm_repository import SupabaseSwarmRepository, SwarmRun

        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            print("⚠  Supabase-env saknas — hoppar över DB-sparning.")
            return

        repo = SupabaseSwarmRepository(create_client(url, key))
        run = SwarmRun(
            id=run_id,
            variant_id=variant_id,
            variant=variant,
            n_workers=n_workers,
            status="completed",
            pass_rate=pass_rate,
            median_score=med_score,
            p95_latency=p95,
            decision=decision,
        )
        repo.insert_run(run)
        repo.insert_worker_results(run_id, results)
        print(f"💾 Resultat sparat i Supabase (run_id: {run_id[:8]}…)")
    except Exception as e:
        print(f"⚠  Supabase-sparning misslyckades: {e}", file=sys.stderr)


# ── Aggregering och beslut ────────────────────────────────────────────────────

def _aggregate(results: list[dict]) -> tuple[float, float, float, str]:
    passed   = [r for r in results if r["passed"]]
    pass_rate = len(passed) / len(results) if results else 0.0
    scores   = [r["score"] for r in results]
    latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None]

    med_score = median(scores) if scores else 0.0
    latencies_sorted = sorted(latencies)
    p95_idx  = int(len(latencies_sorted) * 0.95) - 1
    p95      = latencies_sorted[max(p95_idx, 0)] if latencies_sorted else 0

    if pass_rate >= 0.85:
        decision = f"✅ GODKÄND — {pass_rate*100:.1f}% pass rate"
    elif pass_rate >= 0.65:
        decision = f"⚠️  VILLKORAD — {pass_rate*100:.1f}% pass rate (gräns: 85%)"
    else:
        decision = f"❌ UNDERKÄND — {pass_rate*100:.1f}% pass rate (gräns: 85%)"

    return pass_rate, med_score, p95, decision


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="swarm_runner",
        description="Dreyer AI Studio — Ruflo Testsvärm\n"
                    "Kör prompt-varianter mot N parallella Claude-workers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exempel:
  python3 -m agents.swarm_runner --variant "Svara kortfattat: {input}" --variant-id v1 --workers 10
  bash run_swarm.sh --variant-id v2 --workers 30 --concurrent 10 --domain ai
        """,
    )
    parser.add_argument("--variant",    type=str,
                        default="Svara kort och korrekt på svenska: {input}",
                        help="Prompt-template med {input}-placeholder")
    parser.add_argument("--variant-id", type=str,  default="v1",
                        help="Kort ID för denna variant (t.ex. v1, baseline)")
    parser.add_argument("--workers",    type=int,  default=10,
                        help="Antal workers att köra (default: 10)")
    parser.add_argument("--concurrent", type=int,  default=5,
                        help="Max parallella workers (default: 5)")
    parser.add_argument("--domain",     type=str,  default="general",
                        choices=list(TESTCASES.keys()),
                        help=f"Testdomän: {', '.join(TESTCASES.keys())} (default: general)")
    parser.add_argument("--no-db",      action="store_true",
                        help="Spara inte resultaten i Supabase")
    parser.add_argument("--json-out",   type=str,  default=None,
                        help="Spara råresultat som JSON-fil")

    args = parser.parse_args()

    print(f"\n🐝 Dreyer Ruflo Testsvärm")
    print(f"{'─'*50}")
    print(f"  Variant-ID : {args.variant_id}")
    print(f"  Template   : {args.variant[:60]}{'…' if len(args.variant) > 60 else ''}")
    print(f"  Workers    : {args.workers}")
    print(f"  Concurrent : {args.concurrent}")
    print(f"  Domän      : {args.domain}")
    print(f"{'─'*50}\n")

    testcases = _get_testcases(args.domain, args.workers)
    t_start   = time.monotonic()

    results = asyncio.run(_run_swarm_async(
        variant=args.variant,
        testcases=testcases,
        max_concurrent=args.concurrent,
    ))

    elapsed = time.monotonic() - t_start
    pass_rate, med_score, p95, decision = _aggregate(results)
    run_id = str(uuid.uuid4())

    print(f"\n{'─'*50}")
    print(f"  Tid          : {elapsed:.1f}s")
    print(f"  Pass rate    : {pass_rate*100:.1f}% ({sum(1 for r in results if r['passed'])}/{len(results)})")
    print(f"  Median score : {med_score:.2f}")
    print(f"  P95 latens   : {p95}ms")
    print(f"  Beslut       : {decision}")
    print(f"{'─'*50}\n")

    if args.json_out:
        out_path = pathlib.Path(args.json_out)
        out_path.write_text(json.dumps({
            "run_id":    run_id,
            "variant_id": args.variant_id,
            "variant":   args.variant,
            "domain":    args.domain,
            "n_workers": args.workers,
            "pass_rate": pass_rate,
            "median_score": med_score,
            "p95_latency": p95,
            "decision":  decision,
            "elapsed_s": round(elapsed, 2),
            "results":   results,
        }, indent=2, ensure_ascii=False))
        print(f"📄 Resultat sparat: {args.json_out}")

    if not args.no_db:
        _save_to_supabase(run_id, args.variant_id, args.variant,
                          args.workers, results, pass_rate,
                          med_score, p95, decision)

    # Exit-kod: 0 = godkänd, 1 = underkänd
    sys.exit(0 if pass_rate >= 0.85 else 1)


if __name__ == "__main__":
    main()
