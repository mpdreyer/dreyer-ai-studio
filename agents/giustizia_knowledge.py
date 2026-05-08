"""
Giustizia Knowledge Base
========================
Juridisk kunskapsbas for EU AI Act, GDPR och eIDAS 2.0.
Anvands som kontextinjicering i Giustizias analyser.

Kalla:
- EU AI Act: https://artificialintelligenceact.eu/
- eIDAS 2.0: https://www.european-digital-identity-regulation.com/
- GDPR: https://gdpr-info.eu/
"""

EU_AI_ACT_KNOWLEDGE = """
# EU AI ACT -- KUNSKAPSBAS (Forordning (EU) 2024/1689)

## Tillampningsdatum (KRITISKT)
- 2 feb 2025: Art. 5 -- Forbjudna AI-system GALLER REDAN
- 2 aug 2025: Kap. V -- GPAI-krav GALLER REDAN
- 2 aug 2026: Kap. III -- Hogrisk-krav (Annex III) TRADER I KRAFT
- 2 aug 2027: Annex I-system (maskineri, medicintekniska produkter m.fl.)

## Riskpyramiden

### FORBJUDNA SYSTEM (Art. 5) -- galler fran feb 2025
- Social scoring baserat pa beteende eller personliga egenskaper
- Subliminal manipulation som skadar beslutformagan
- Utnyttjande av sarbarheter (alder, funktionsnedsattning, socioekonomisk situation)
- Biometrisk kategorisering baserat pa kansliga attribut (ras, religion, sexuell laggning m.fl.)
- Realtids-RBI (Remote Biometric Identification) i offentliga rum for brottsbekampning (med snava undantag)
- Bedomning av brottsrisk enbart baserat pa profilering
- Ansiktsigenkannningsdatabaser via oriktat skrapning av internet/CCTV
- Kansloigenkanning pa arbetsplatser och i utbildningsmiljoer (utom medicinsk/sakerhet)

### HOG RISK (Annex III) -- krav galler aug 2026
Kraver: riskhanteringssystem, datastyrning, teknisk dokumentation,
        loggning, transparens, mansklig tillsyn, noggrannhet/robusthet,
        kvalitetsledningssystem, registrering i EU-databas

Annex III use cases:
1. BIOMETRI: Biometrisk identifiering (ej verifiering), kategorisering, kansloigenkanning
2. KRITISK INFRASTRUKTUR: Sakerhetskomponenter i el, vatten, gas, vag, digital infrastruktur
3. UTBILDNING: Antagning, betygsattning, overvakning under prov
4. HR/ARBETSMARKNAD: Rekrytering, urval, befordran, uppsagning, prestationsovervakning
5. OFFENTLIGA TJANSTER: Bidragsbedomning, kreditvardighet, prioritering av larmsamtal, forsakring
6. BROTTSBEKAMPNING: Brottsofferprofil, polygraf, bevisvardering, aterfallsrisk
7. MIGRATION: Polygraf, irreguljar migration, asyl-/visumansokningar
8. RATTSVASENDET: Faktatolkning, alternativ tvistelosning, valinfluens

Undantag fran hogrisk-klassificering (Art. 6.3):
- Smal procedurell uppgift
- Forbattrar resultat av redan slutford mansklig aktivitet
- Bereder underlag (utan att ersatta mansklig bedomning)
- Profilerar INTE individer

### BEGRANSAD RISK
- Chatbottar: maste informera anvandaren att de interagerar med AI
- Deepfakes: markning kravs
- Emotionsigenkanning: transparenskrav

### MINIMAL RISK
- Majoriteten av AI-applikationer (spamfilter, AI i videospel m.fl.)
- Inga specifika krav -- men etiska riktlinjer rekommenderas

## GPAI -- General Purpose AI (Kap. V) -- galler fran aug 2025

### Alla GPAI-modell-providers maste:
1. Teknisk dokumentation (traning, testning, utvarderingsresultat)
2. Information till nedstromsleverantorer om kapacitet och begransningar
3. Policy for att respektera upphovsrattsdirektivet
4. Sammanfattning av traningsdata (publiceras)

### Oppen licens-GPAI (parametrar, vikter och arkitektur publikt tillgangliga):
- Endast copyright-policy + traningsdata-sammanfattning
- UNDANTAG: om de presenterar systemisk risk

### Systemisk risk (>10^25 FLOPs traning):
Utover ovan aven:
- Modell-evaluering inkl. adversarial testing
- Bedomning och mitigering av systemiska risker
- Sparning och rapportering av allvarliga incidenter till AI Office
- Cybersakerhetsskydd

### Nota bene for Claude, GPT-4, Gemini:
Dessa ar GPAI-system. Providers (Anthropic, OpenAI, Google) har GPAI-skyldigheter.
Deployers (du som bygger ovanpa) har skyldigheter baserat pa vad du bygger.

## KRAV FOR HOGRISK-PROVIDERS (Art. 8-17)
1. Riskhanteringssystem (livscykelbaserat)
2. Datastyrning (tranings-, validerings- och testdata)
3. Teknisk dokumentation (visa compliance)
4. Automatisk loggning (sparbarhet)
5. Transparens mot deployers (instructions for use)
6. Mansklig tillsyn (design for human oversight)
7. Noggrannhet, robusthet, cybersakerhet
8. Kvalitetsledningssystem (QMS)
9. Registrering i EU-databas (fore marknadslansering)
10. Fundamental rights impact assessment (FRIA) for offentliga deployers

## BOTER
- Forbjudna system: upp till 35 MEUR eller 7% av global omsattning
- Hogrisk-violations: upp till 15 MEUR eller 3% av global omsattning
- Felaktig information till myndigheter: upp till 7,5 MEUR eller 1% av global omsattning
"""

GDPR_KNOWLEDGE = """
# GDPR -- KUNSKAPSBAS (Forordning (EU) 2016/679)

## Sex rattsliga grunder for behandling (Art. 6)
1. Samtycke -- frivilligt, specifikt, informerat, otvetydigt
2. Avtal -- nodvandigt for avtalets fullgorande
3. Rattslig forpliktelse -- lagstadgad skyldighet
4. Vitala intressen -- livsviktiga intressen
5. Allmant intresse -- myndighetsutovning
6. Berrattigat intresse -- intresseavvagning (ej for myndigheter)

## Grundprinciper (Art. 5)
- Laglighet, korrekthet, oppenhet
- Andamalsbegransning (inget scope creep)
- Uppgiftsminimering (bara nodvandig data)
- Korrekthet (uppdaterade uppgifter)
- Lagringsbegransning (inte langre an nodvandigt)
- Integritet och konfidentialitet (sakerhet)
- Ansvarsskyldighet (kan bevisa compliance)

## Registrerades rattigheter (Art. 15-22)
- Tillgang: ratt att veta vad som behandlas
- Rattelse: korrigera felaktig data
- Radering ("ratten att bli glomd"): under vissa forutsattningar
- Begransning: pausa behandling under utredning
- Dataportabilitet: exportera data i maskinlasbart format
- Invandning: mot profilering och berattigat intresse
- Automatiserat beslutsfattande: ratt till mansklig granskning

## Kansliga personuppgifter (Art. 9) -- kraver explicit samtycke eller undantag
Ras/etniskt ursprung, politiska asikter, religion, fackmedlemskap,
genetiska uppgifter, biometriska data, halsoupgifter, sexuell laggning

## DPIA -- Data Protection Impact Assessment (Art. 35)
Obligatorisk vid:
- Systematisk och omfattande profilering
- Storskalig behandling av kansliga uppgifter
- Systematisk overvakning av offentliga platser
Rekommenderas vid AI-system som behandlar personuppgifter

## AI + GDPR -- Viktiga skarningspunkter
- Automatiserat beslutsfattande (Art. 22): ratt att inte vara foremal for
  enbart automatiserade beslut med rattslig eller liknande effekt
- Profilering: kraver tydlig rattslig grund
- Traning av AI-modeller pa personuppgifter: kraver rattslig grund
- Anonymisering vs. pseudonymisering: pseudonymiserade data ar fortfarande personuppgifter

## GDPR + EU AI ACT -- Samspel
- Hogrisk-AI som behandlar personuppgifter: BADA regelverken galler
- DPIA (GDPR) + FRIA (AI Act) kan samordnas
- Dataminimering (GDPR) stodjer AI Acts krav pa datastyrning
"""

EIDAS_KNOWLEDGE = """
# eIDAS 2.0 -- KUNSKAPSBAS (Forordning (EU) 2024/1183)
Andrar ursprungliga eIDAS (Forordning (EU) 910/2014)
Ikrafttradande: 20 maj 2024
EU Digital Identity Wallet: senast 2026 i alla EU-lander

## Tillitsnivaer (LoA -- Level of Assurance)
- LAG: grundlaggande identitetskontroll
- VASENTLIG: robust identitetskontroll, reducerad risk for missbruk
- HOG: stark autentisering, stark identitetskontroll, minimal risk

## EU Digital Identity Wallet (Art. 5a)
- Alla EU-medborgare och -invanare ska ha tillgang
- Fungerar for offentliga och privata tjanster i hela EU
- Lagrar: person-ID-data, utbildningsintyg, yrkeskvalifikationer, korkort m.m.
- Anvandaren kontrollerar alltid vad som delas
- Inget sparande eller profilering i wallet-designen
- Privacy dashboard inbyggt

## E-signaturer (Art. 3)
- Enkel e-signatur: lagsta niva (t.ex. att skriva namn i mejl)
- Avancerad e-signatur (AdES): lankad till signaturen, identifiering mojlig
- Kvalificerad e-signatur (QES): rattslig verkan likvard med handskriven signatur i hela EU
  Kraver: kvalificerat certifikat + kvalificerad signaturanordning (QSCD)

## Elektronisk identifiering -- Anmalda system
- Anmalda eID-system erkanns omsesidigt i hela EU
- BankID Sverige: anmalt med tillitsniva HOG
- Galler for offentliga tjanster online som kraver autentisering

## Kvalificerade Betrodda Tjanster (Art. 3)
- Kvalificerat certifikat for e-signatur
- Kvalificerat certifikat for webbautentisering
- Kvalificerad e-tidsstampel
- Kvalificerad ERDS (elektronisk rekommenderad leverans)
- Kvalificerad WAC (webbplatscertifikat)

## eIDAS + BankID
- BankID ar ett anmalt eID-system under eIDAS med LoA Hog
- Accepteras for gransoverskridande EU-tjanster (offentliga)
- For privata tjanster: frivilligt men vanligt i Sverige

## eIDAS + AI Act -- Skarningspunkter
- Biometrisk autentisering via eID-wallet: potentiellt hogrisk under AI Act (Annex III)
- Automatiserad identitetsverifiering: kontrollera om det ar hogrisk-AI
- Kansloigenkanning vid autentisering: FORBJUDET under AI Act
- Remote Biometric Identification: restriktioner under AI Act Art. 5

## Implementing Acts (senaste, maj 2026)
- EU 2025/1944 (sep 2025): Kvalificerade elektroniska leveranstjanster
- EU 2025/1569-1572 (jul 2025): Elektroniska attributsintyg, rQSCDs,
  kvalificerade betrodda tjanster, initieringsprocedurer
- EU 2024/2977-2982 (nov 2024): Wallet-funktionalitet, protokoll,
  person-ID-data, certifiering, notifieringar
"""

# Kombinerad kunskapsbas for full-context-injektion
FULL_KNOWLEDGE = f"""
{EU_AI_ACT_KNOWLEDGE}

---

{GDPR_KNOWLEDGE}

---

{EIDAS_KNOWLEDGE}
"""


def get_knowledge(domain: str = "all") -> str:
    """
    Hamta relevant kunskapsbas.
    domain: 'ai_act', 'gdpr', 'eidas', 'all'
    """
    if domain == "ai_act":
        return EU_AI_ACT_KNOWLEDGE
    elif domain == "gdpr":
        return GDPR_KNOWLEDGE
    elif domain == "eidas":
        return EIDAS_KNOWLEDGE
    else:
        return FULL_KNOWLEDGE


def get_relevant_knowledge(query: str) -> str:
    """
    Hamta relevant kunskapsbas baserat pa query-innehall.
    Smart: laddar bara det som behovs for token-effektivitet.
    """
    query_lower = query.lower()

    domains = []

    if any(kw in query_lower for kw in [
        "ai act", "ai-act", "gpai", "hogrisk", "high risk",
        "forbjuden", "prohibited", "annex", "riskklassificering",
        "ai system", "ai-system", "artificiell intelligens"
    ]):
        domains.append(EU_AI_ACT_KNOWLEDGE)

    if any(kw in query_lower for kw in [
        "gdpr", "personuppgift", "dataskydd", "samtycke", "consent",
        "dpia", "datasubjekt", "registrerade", "behandling", "rattslig grund"
    ]):
        domains.append(GDPR_KNOWLEDGE)

    if any(kw in query_lower for kw in [
        "eidas", "e-signatur", "esignatur", "bankid", "digital wallet",
        "kvalificerad", "loa", "tillitsniva", "autentisering", "eid"
    ]):
        domains.append(EIDAS_KNOWLEDGE)

    # Om inget specifikt hittas -- ladda allt
    if not domains:
        return FULL_KNOWLEDGE

    return "\n\n---\n\n".join(domains)
