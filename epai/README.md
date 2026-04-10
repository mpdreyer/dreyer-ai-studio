# EPAi — Ain
**Lokal AI-rådgivare för vattenrening vid badanläggningar**
by DTSM · för EnviroProcess · POC April 2026

---

## Vad är EPAi?

EPAi (EnviroProcess AI) är ett lokalt, air-gapped AI-system som låter driftpersonal
ställa frågor om vattenrening, analysera mätvärden och identifiera trender —
utan att data lämnar anläggningens dator.

AI:ns namn är **Ain**. Hon baserar alla svar på era egna dokument och mätvärden.

---

## Installationsguide — Windows 11

### Steg 1 — Installera Python 3.11

1. Gå till [python.org/downloads](https://www.python.org/downloads/)
2. Ladda ner **Python 3.11.x** (64-bit)
3. Kör installationsfilen — **bocka i "Add Python to PATH"**
4. Verifiera i CMD: `python --version`

---

### Steg 2 — Installera Tesseract OCR (för inskannade dokument)

Krävs för handskrivna checklistor och inskannade tillsynsprotokoll.

1. Ladda ner från: https://github.com/UB-Mannheim/tesseract/wiki
   → Välj senaste **tesseract-ocr-w64-setup-x.x.x.exe**
2. Under installationen:
   - Bocka i **"Add to PATH"**
   - Under "Additional language data" → bocka i **Swedish (swe)**
3. Verifiera i CMD: `tesseract --version`

---

### Steg 3 — Installera Poppler (krävs av pdf2image)

1. Ladda ner från: https://github.com/oschwartz10612/poppler-windows/releases/
   → Ladda ner senaste `Release-xx.xx.x-0.zip`
2. Packa upp till t.ex. `C:\poppler\`
3. Lägg till `C:\poppler\Library\bin` i systemets **PATH**:
   - Sök "Miljövariabler" i Start → Systemvariabler → Path → Redigera → Ny
4. Verifiera i CMD: `pdftoppm -v`

---

### Steg 4 — Installera Ollama och ladda ner modeller

1. Gå till [ollama.com](https://ollama.com) och ladda ner för Windows
2. Installera och starta Ollama
3. Öppna CMD och kör:

```cmd
ollama pull mistral
ollama pull nomic-embed-text
```

> **Obs:** `mistral` är ~4 GB. `nomic-embed-text` är ~270 MB.
> Ollama måste köra i bakgrunden när EPAi används.

---

### Steg 5 — Installera Python-beroenden

Öppna CMD i projektmappen och kör:

```cmd
pip install -r epai\requirements.txt
```

---

### Steg 6 — Lägg in datafiler

Kopiera dokumenten till rätt katalog:

```
epai\data\raw\
  anlaggning_1\    ← Alla dokument för Anläggning 1
  anlaggning_2\    ← Alla dokument för Anläggning 2
  anlaggning_3\    ← Alla dokument för Anläggning 3
  global\          ← Vitböcker, lagar, manualer, kataloger (delas mellan alla)
```

**Rekommenderat filnamnsformat:**
```
documentType_AnlaggningsNamn_yyyymmdd.pdf
Exempel: labbrapport_Anlaggning1_20260401.pdf
         tillsynsprotokoll_fysiskt_Anlaggning2_20260315.xlsx
```

**Dokumenttyper som stöds:**
| Typ | Nyckelord i filnamnet |
|---|---|
| `labbrapport` | labb, analys, provresultat |
| `tillsynsrapport_digital` | tillsyn, inspektion |
| `tillsynsprotokoll_fysiskt` | tillsynsprotokoll, checklist |
| `arsavstamningsprotokoll` | arsavstamning, årsavstämning |
| `matvarden_excel` | matvarden, mätvärden |
| `du_parm` | driftuppföljning, du_, parm |
| `avtal` | avtal, kontrakt |
| `vitbok` | vitbok, whitepaper |
| `lag_och_rad` | lag, sfs, bfs, förordning |
| `katalog` | katalog, produktblad |
| `manual` | manual, handbok, instruktion |

---

### Steg 7 — Indexera dokument

```cmd
python epai\ingest.py --anlaggning all
```

Alternativt bara en anläggning:
```cmd
python epai\ingest.py --anlaggning 1
```

Tvinga omindexering:
```cmd
python epai\ingest.py --anlaggning all --force-reindex
```

---

### Steg 8 — Starta EPAi

```cmd
streamlit run epai\app.py
```

Öppnas automatiskt i webbläsaren på `http://localhost:8501`

---

## Verifikation

Kör smoke-testet för att verifiera att allt fungerar:

```cmd
python epai\test_smoke.py
```

---

## Byta LLM-modell

Redigera `epai\config.py`:

```python
OLLAMA_MODEL = "llama3.1:8b"   # Bättre svar, kräver ~5 GB RAM extra
```

Ladda ner modellen först: `ollama pull llama3.1:8b`

---

## Felsökning

| Problem | Lösning |
|---|---|
| `Ollama ej tillgänglig` | Starta Ollama från Start-menyn |
| `Tesseract not found` | Kontrollera att Tesseract är i PATH |
| `pdf2image: pdftoppm not found` | Kontrollera att Poppler bin/ är i PATH |
| `Inga dokument indexerade` | Kör `python epai\ingest.py --anlaggning all` |
| Långsamma svar | Byt till `mistral` (snabbare än llama3.1) |

---

## Projektstruktur

```
epai/
  app.py              Streamlit-gränssnitt (Ain)
  ingest.py           Dataingestion: PDF + Excel + OCR → ChromaDB
  rag.py              RAG-pipeline: LangChain + Ollama
  pdf_export.py       PDF-export av svar och rapporter
  ocr_utils.py        OCR för inskannade/handskrivna dokument
  config.py           Konfiguration (modell, sökvägar)
  metadata_db.py      SQLite-wrapper för filspårning
  test_smoke.py       Rök-test för verifiering
  data/
    raw/              Indata-filer (kopieras hit manuellt)
    chroma_db/        ChromaDB (genereras automatiskt)
    metadata.db       SQLite (genereras automatiskt)
  requirements.txt
  README.md
```

---

*EPAi POC · DTSM · April 2026*
