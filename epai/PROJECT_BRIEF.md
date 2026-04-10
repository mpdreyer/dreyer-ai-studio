# EPAi — Project Brief & Lösningsbeskrivning v1.1
*Beslutad information per 8 april 2026. Källan till sanning för EPAi.*

## Kund & projekt
- Kund: EnviroProcess (EP)
- Projekt: EPAi — AI-rådgivare för vattenrening, publika badanläggningar
- DTSM-ansvarig: Mattias Dreyer / mattias@dtsm.se
- AI-assistentens namn i applikationen: Ain
- POC-deadline: 20 april 2026
- POC-budget: 95 timmar / 3 veckor
- Steg 1 (efter godkänd POC): 255 timmar
- Total estimerad omfattning: 350 timmar
- POC-hårdvara: ASUS ROG Zephyrus G16, Intel Core Ultra 9 285H,
  64GB RAM, 2TB SSD, RTX 5090 Laptop GPU 24GB VRAM, Windows 11
- Deployment: Air-gapped, lokalt på POC-dator (ej publik URL)

## Syfte
EPAi är ett rådgivande, spårbart och datadrivet beslutsstöd för
vattenrening vid publika badanläggningar i Sverige.

Systemet ska:
- Ge rekommendationer, förklaringar och åtgärdslistor
- Basera ALLA svar på tillgänglig dokumentation — aldrig gissa
- Reducera personberoende kompetens hos EnviroProcess
- Möjliggöra tvärsnittsanalys över flera anläggningar
- INTE fatta egna beslut eller utföra åtgärder

## Målgrupp
EP-användare: Full åtkomst alla anläggningars data, tvärsnittsanalys
Kundanvändare: Isolerade till sin anläggning. Undantag: globala dok.
Roller Steg 1 (ej POC): Kundanvändare / EP-användare / EP-Admin
Användarvolym Steg 1: 1000+ (ej simultana)

## POC-scope — ingår
- Chattgränssnitt mot 3 anläggningar
- Svar med källhänvisningar (filnamn, dokumenttyp, sida/rad)
- Tvärsnittsanalys och jämförelse mellan anläggningar
- Trendidentifiering i historisk data (1 år bakåt)
- PDF-export av enskilda svar och hela samtal
- Körbar lokalt på Windows 11

## POC-scope — ingår INTE (kravspec explicit)
- Inloggning och autentisering
- Användarhantering och roller
- Datainsamlingsfunktion (data läggs in manuellt)
- Publik URL eller deploy

## Beslutad teknisk stack
- UI: Streamlit
- LLM: Ollama + Gemma 4 26B (lokal, air-gapped, inga externa anrop)
- Vektordatabas: ChromaDB (persistent, lokal)
- RAG-orkestrering: LangChain + langchain-community
- PDF-läsning: pdfplumber (primär) + pypdf (fallback)
- OCR: pytesseract + pdf2image — OBLIGATORISKT för inskannade dok
- Excel: openpyxl + pandas
- PDF-export: reportlab
- Metadata: SQLite
- Embedding: nomic-embed-text via Ollama

## Arkitektur — 4 lager
1. Användarmiljö: Streamlit-chatt, anläggningsval, PDF-export
2. Tjänstelager: RAG-logik (LangChain), Ain-systemprompt,
   tvärsnittsanalys, källspårning
3. Informationslager: ChromaDB (per anläggning + global),
   SQLite metadata, rådatafiler
4. Integrationsdel: Manuell filimport POC,
   schemalagd API-hämtning Steg 1

## Datakällor — 11 beslutade typer

### Kundspecifika (per anläggning, isolerade)
1. Labbrapporter — PDF
   Provtagning, bakterieresultat, bedömningar
2. Digitala tillsynsrapporter — PDF
   Manuella bedömningar från driftjournal och styrsystem
3. Fysiska tillsynsprotokoll — PDF (inskannad, handskriven) + OCR
   Checklistor med bläckpenna, godkännanden, kommentarer
4. Fysiska årsavstämningsprotokoll — PDF (inskannad, handskriven) + OCR
   Checklistor med kommentarer och åtgärder
5. Mätvärden från styrsystem — Excel
   PH, temperatur, kemikalieförbrukning, el
6. DU-pärmar (drift och underhåll) — PDF
   Dokumentation från avslutade entreprenadprojekt
7. Avtal — PDF
   Avtal mellan anläggning och EnviroProcess

### Globala (delas av alla anläggningar)
8. Vitböcker — PDF
   Idéer, problemanalyser, lösningar inom vattenprocessing
9. Lagar och råd — PDF
   Myndighetskrav för publikt bad i Sverige
10. Kataloger — PDF
    EnviroProcess produktkataloger
11. Manualer — PDF
    Produktmanualer för anläggningarnas system

## Metadata-modell (beslutad, enligt kravspec)
- customerId: anläggnings-ID (LIME CRM _Id)
- fileName: documentType_AnlaggningsNamn_yyyymmdd.ext
- documentType: ett av 11 beslutade typer
- dataSource: manuell_upload / scheduled_job
- timeStamp: ISO 8601 (när filen ingestades)
- hashValue: SHA-256 (duplikatdetektion)
- chroma_ids: chunk-IDs i ChromaDB
- ocr_used: 0/1

## ChromaDB-struktur
- anlaggning_1, anlaggning_2, anlaggning_3 (kundspecifikt)
- global (vitböcker, lagar, kataloger, manualer)
- Global collection söks ALLTID oavsett vald anläggning

## Ain — systemprompt (beslutad)
"Du är Ain, en expert AI-rådgivare inom vattenrening för publika
badanläggningar i Sverige. Du arbetar för EnviroProcess och
analyserar data från de anläggningar du har tillgång till.
Du baserar ALLTID dina svar på tillgänglig dokumentation.
Du fattar inga egna beslut och utför inga åtgärder.
Du gissar aldrig — om data saknas säger du det.
Du hänvisar alltid till källdokument.
Du svarar på svenska. Om användaren skriver engelska svarar du engelska."

## Exempelfrågor (ur kravspec)
- "Är gårdagens prover tagna?"
- "Vilken är din mest akuta åtgärd just nu?"
- "Vad är din maxbelastning innan ECO-mode?"
- "Identifiera trender i kemikalieförbrukning för alla anläggningar"
- "Jämför anläggning 1 och 2 avseende bakterieprovtagning senaste månaden"

## Riskregister
1. OCR-kvalitet handskrivna dok
   Sannolikhet: Hög / Impact: Medium
   Mitigering: pytesseract swe+eng + PIL bildförprocessning

2. Gemma 4 26B svarskvalitet på svenska
   Sannolikhet: Medium / Impact: Hög
   Mitigering: testa vecka 1 mot exempeldata, fallback Mistral

3. EP levererar testdata sent
   Sannolikhet: Medium / Impact: Hög
   Mitigering: bygg med syntetisk testdata parallellt

4. Torque/Truespar (uppdragsgivarens önskemål)
   Sannolikhet: Låg / Impact: Medium
   Mitigering: utvärderas Steg 1, ej i POC, ingen Python SDK bekräftad

## Steg 1 — ska byggas efter godkänd POC
- IdP-inloggning (Azure AD B2C eller motsvarande)
- MFA obligatoriskt EP-användare, konfigurerbart per kund
- JWT-sessionshantering med silent refresh
- Strikt dataisolering per customerId
- Automatisk säkerhetskopiering dagligen
- 10 GB fillagring per kund (skalbart)
- Schemalagd datainsamling från styrsystem via API
- LIME CRM-integration för customerId
- GDPR-compliance
- TLS 1.2+
- Rate-limiting och brute-force-skydd
- Incidentloggning för autentisering
- Horisontell skalning för 1000+ användare
