# Dreyer AI Studio

AI-konsultens projektverktyg. Tar AI-projekt från brief till levererad POC.
12 rådsagenter · Ruflo-testsvärm · NotebookLM-integration · Deployment-konfigurator.

## Snabbstart

### 1. Klona och installera
```bash
git clone https://github.com/mpdreyer/dreyer-ai-studio.git
cd dreyer-ai-studio
pip install -r requirements.txt
```

### 2. Konfigurera secrets
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fyll i dina nycklar i .streamlit/secrets.toml
```

### 3. Sätt upp Supabase
Kör `db/schema.sql` i Supabase SQL Editor.
Projektet använder befintlig Supabase-instans: `jpeijjnpkayzrgdefjxi`

### 4. Starta appen
```bash
streamlit run app.py
```

## Struktur

```
dreyer-ai-studio/
├── app.py                    # Entrypoint
├── requirements.txt
├── agents/
│   ├── council.py            # 12 agenter med systemprompts
│   └── router.py             # Routing till Claude API
├── components/
│   ├── topbar.py             # Health Score + token-meter
│   ├── sidebar.py            # Navigation + agentval
│   └── chat.py               # Rådslag-chattkomponent
├── views/
│   ├── overview.py           # Projektöversikt
│   ├── council.py            # Rådet
│   ├── tasks.py              # Uppgifter
│   ├── deliverables.py       # Leveranser
│   ├── roi.py                # ROI-kalkylator
│   ├── swarm.py              # Ruflo-testsvärm UI
│   ├── deploy.py             # Deployment-konfigurator
│   ├── tokens.py             # Token-ekonomi
│   ├── intelligence.py       # Omvärldsbevakning
│   └── correction.py        # Correction Delta
└── db/
    ├── schema.sql            # Supabase-schema
    └── supabase_client.py    # DB-wrapper
```

## Rådet — 12 agenter

| Agent | Roll | Modell (Fas 1) |
|-------|------|----------------|
| Architetto | Chief Architect · Ordförande | Claude Sonnet |
| Codex | Lead Developer | Claude Sonnet |
| Logica | Prompt Engineer & QA | Claude Sonnet |
| Datatjej | Data & Integration | Claude Sonnet |
| Guardiano | AI Safety & Ethics | Claude Sonnet |
| Narratrix | Demo & Storytelling | Claude Sonnet |
| Scalero | Deployment & Scale | Claude Sonnet |
| Kontrakto | Kund & Affär | Claude Sonnet |
| Spejaren | Intelligence | Claude Sonnet |
| Risico | Risk & Critique | Claude Sonnet |
| Memoria | Pattern Memory | Claude Sonnet |
| Diavolo | Red Team · Agent 12 | Claude Sonnet |

## Fas 2 — Multi-model routing
När Fas 1 är stabil byts modeller ut per agent:
- Claude: Architetto, Narratrix
- GPT-4o: Logica, Kontrakto
- Gemini Pro: Datatjej, Gemma, Spejaren, Memoria
- DeepSeek R1: Diavolo, Risico, Guardiano
- Claude Code: Codex (faktisk kodexekvering)

## Ruflo-testsvärm
Separat motor i `swarm.py` — upp till 90 parallella workers.
Kör via terminal: `python swarm.py --workers 30 --multi`

## Deploy på Streamlit Cloud
1. Pusha till GitHub
2. Anslut repo på share.streamlit.io
3. Lägg in secrets i Streamlit Cloud Secrets-panelen:
   - ANTHROPIC_API_KEY
   - SUPABASE_URL
   - SUPABASE_KEY

---
*Forza Dreyer.* 🏎
