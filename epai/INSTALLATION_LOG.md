# EPAi — Installationslogg

**Datum:** 2026-04-11
**Maskin:** Lokal Windows 11-dator (air-gapped POC-miljö)

---

## Genomförd installation

### Hårdvara (ej verifierad än)
- Intel Core Ultra 9 285H
- 64 GB RAM
- NVIDIA RTX 5090 24GB

### Installerade komponenter
| Komponent | Version | Plats |
|-----------|---------|-------|
| Python | 3.13.13 (pip 26.0.1) | C:\Users\matti\AppData\Local\Programs\Python\Python313 |
| Node.js | v24.0.1 | — |
| Claude Code | (npm global) | — |
| Ollama | 0.20.5 | — |
| Tesseract OCR | v5.5.0 | C:\Program Files\Tesseract-OCR |

> Tesseract installerades med svenska språkfiler (swe).

### Modeller (Ollama)
| Modell | Storlek | Användning |
|--------|---------|------------|
| gemma4:26b | 17 GB | LLM — MoE, 128 experter, 128K context, multimodal |
| nomic-embed-text | 274 MB | Embeddings för ChromaDB |

### Projektstruktur (C:\EPAi\)
```
C:\EPAi\
  venv\                  Python 3.13.13 virtuell miljö
  requirements.txt       13 paket
  data\anlaggning_1\
  data\anlaggning_2\
  data\anlaggning_3\
  data\global\
  chromadb\
```

### Python-paket installerade
Alla 13 paket från requirements.txt installerades i `C:\EPAi\venv\`.
Två versioner justerades pga Python 3.13-kompatibilitet:

| Paket | Planerad version | Installerad version | Orsak |
|-------|-----------------|--------------------|----|
| pandas | 2.1.4 | **2.2.3** | 2.1.4 saknar cp313-wheel; Cython-kompilering misslyckas mot Python 3.13 C-API |
| Pillow | 10.2.0 | **10.4.0** | 10.4.0 är första versionen med cp313-wheel; måste vara <11 pga streamlit 1.30.0 |

Övriga 11 paket installerades med exakt begärda versioner.

---

## Avvikelser från ursprungsplan

| Komponent | Ursprungsplan | Utfall | Kommentar |
|-----------|--------------|--------|-----------|
| Python | 3.11 | **3.13.13** | Fungerar med versionsjusteringar för pandas/Pillow |
| LLM-modell | gemma2:27b | **gemma4:26b** | Nyare modell, bättre prestanda, likvärdig storlek |
| pandas | 2.1.4 | **2.2.3** | Python 3.13-kompatibilitet |
| Pillow | 10.2.0 | **10.4.0** | Python 3.13-kompatibilitet, kompatibel med streamlit <11-krav |

---

*EPAi POC · DTSM · 2026-04-11*
