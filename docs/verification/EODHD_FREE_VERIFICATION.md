# Verifieringsprotokoll för EODHD Free

*Kandidat till read-only-marknadsdataprovider i Hivemind Trading Bot v1.0*

- Dokumentstatus: Underlag för villkorat beslut
- Datum: 17 november 2026
- Omfattning: Historiska EOD OHLCV-data för svenska aktier
- Beslutsobjekt: Om EODHD Free kan kvalificeras som kandidat före separat öppning av REAL_DATA_GATE

## 1 Sammanfattning och rekommendation

EODHD Free rekommenderas inte som produktionsaktiv marknadsdataprovider ännu. T10 bedöms däremot nedan som **PRELIMINÄRT GODKÄND för det uttryckligen avgränsade privata användningsfallet**, under förutsättning att kontot används av en individ enbart för egna investeringar och att data/resultat inte görs tillgängliga för någon annan. Underlaget visar en lovande teknisk kandidat för read-only historisk EOD-data: VOLV-B.ST har verifierats med 10 poster för perioden 2026-11-02–2026-11-13 och ATCO-A.ST med fem poster för perioden 2026-11-09–2026-11-13. För samtliga redovisade poster har användaren observerat giltiga OHLC-intervall, positiva volymer, unika datum och fältet adjusted_close.

Rekommendationen är därför: villkorat kandidatstatus, fortsatt sandbox-/fixture-användning och ingen öppning av REAL_DATA_GATE innan de utestående besluten och kompletterande verifieringarna nedan är godkända. Detta protokoll ansluter ingen riktig data och ändrar inte Hivemind Trading Bot, repo eller driftsmiljö.

## 2 Syfte och avgränsning

Syftet är att skapa ett formellt, spårbart beslutsunderlag för EODHD Free som möjlig read-only-leverantör i version 1.0. Protokollet bedömer endast det verifierade användarunderlaget och definierar vad som måste återstå innan en eventuell produktionsmässig dataport kan öppnas.

Utanför scope ligger realtidsdata, orderläggning, skrivande API-anrop, driftkonfiguration, autentiseringsändringar, lasttest mot extern tjänst och anslutning till riktig data. Investor B är ännu inte slutverifierad.

## 3 Verifierat underlag

| Instrument | Verifierad period | Antal poster | Observerade egenskaper | Status |
|---|---:|---:|---|---|
| VOLV-B.ST | 2026-11-02–2026-11-13 | 10 | Giltiga OHLC-intervall; positiva volymer; unika datum; adjusted_close | Preliminärt godkänd |
| ATCO-A.ST | 2026-11-09–2026-11-13 | 5 | Giltiga OHLC-intervall; positiva volymer; unika datum; adjusted_close | Preliminärt godkänd |
| Investor B (`INVE-B.ST`) | 2026-11-09–2026-11-13 | 5 | Giltiga OHLC-intervall; positiva volymer; unika datum; adjusted_close | Preliminärt verifierad |

För Investor B avser evidensen fem användarlevererade OHLCV-poster för datumen 2026-11-09, 2026-11-10, 2026-11-11, 2026-11-12 och 2026-11-13. Datum är unika, volymerna positiva och varje post uppfyller `low ≤ open/close ≤ high` samt innehåller `adjusted_close`. De fullständiga råsvaren finns i den refererade användarkonversationen; detta protokoll återger endast verifieringsresultatet och gör inga nya API-anrop.

Evidensgrund: verifierade användarresultat från EODHD EOD-endpointen i den refererade konversationen. Protokollet gör inga påståenden om dataposter som inte uttryckligen ingår i detta underlag.

### Särskilt kontrollfall: Investor B:s historiska split

EODHD:s split-endpoint returnerade för `INVE-B.ST` en split den **19 maj 2021** med förhållandet **4:1** (`4.000000/1.000000`). Detta dokumenteras som ett separat corporate-actions-kontrollfall. EODHD Free:s historikbegränsning på ett år hindrade samtidigt hämtning av EOD-priser kring maj 2021 med det aktuella abonnemanget: en begäran för 2021-05-14–2021-05-24 returnerade i stället en post från 2025-11-14 tillsammans med varningen `Data is limited by one year as you have free subscription`. Splitinformationen är därför observerad, men historisk prisjustering vid splitten är inte verifierad.

## 4 Testmatris

| ID | Kontroll | Förväntat resultat | Evidens/status | Gate |
|---|---|---|---|---|
| T01 | HTTP/API-svar för EOD OHLCV | Svar kan läsas i read-only-flöde | Observerat för VOLV-B.ST och ATCO-A.ST | GODKÄND preliminärt |
| T02 | Obligatoriska datumfält | Varje post har datum | Observerat i samtliga redovisade poster | GODKÄND preliminärt |
| T03 | OHLC-integritet | low ≤ open/close ≤ high och low ≤ high | Observerat som giltiga OHLC-intervall | GODKÄND preliminärt |
| T04 | Volym | volume > 0 | Observerat för samtliga redovisade poster | GODKÄND preliminärt |
| T05 | Datumunikhet | Inga dubbletter inom instrument och period | Observerat för båda instrumenten | GODKÄND preliminärt |
| T06 | Justerat stängningspris | adjusted_close finns och är numeriskt användbart | Observerat för samtliga redovisade poster | GODKÄND preliminärt |
| T07 | Investor B | Samma kontrollpaket som T01–T06 | Fem användarlevererade poster 2026-11-09–2026-11-13; giltiga OHLC-intervall, positiva volymer, unika datum och `adjusted_close` observerade | PRELIMINÄRT VERIFIERAD |
| T08 | Historiska utdelningar och splittar | Corporate actions kan identifieras och hanteras korrekt | Splitjustering kring 2021-05-19 återstår; Free-planens historikbegränsning kvarstår | ÖPPEN |
| T09 | Officiell kurssamstämmighet | Jämförelse mot auktoritativ källa inom definierad tolerans | Financial Times historiktabell kontrollerad 2026-11-14; fem stängningar matchar vid 0,01 SEK visad precision | GODKÄND preliminärt |
| T10 | Licensvillkor | Read-only-användning, lagring, vidareförmedling och kommersiell användning är klarlagda | Officiella Terms/Help Center stöder privat användning enligt villkoren; se avsnitt 11. Villkorad privat användning bedöms preliminärt tillåten. | PRELIMINÄRT GODKÄND* |
| T11 | Driftmässig isolering | Test kan ske utan riktig data eller produktionspåverkan | Ska bekräftas separat i designbeslut | ÖPPEN |

### Evidens för T09: Investor B mot Financial Times

Oberoende källa: [Financial Times, Investor AB (INVE B:STO), Historical Prices](https://markets.ft.markitdigital.com/data/equities/tearsheet/historical?s=INVE+B%3ASTO), kontrollerad 2026-11-14. Källans historiktabell visar följande stängningskurser i SEK:

| Datum | EODHD/user API | Financial Times | Avvikelse |
|---|---:|---:|---:|
| 2026-11-09 | 429,60 | 429,60 | 0,00 |
| 2026-11-10 | 431,05 | 431,05 | 0,00 |
| 2026-11-11 | 435,25 | 435,25 | 0,00 |
| 2026-11-12 | 436,05 | 436,05 | 0,00 |
| 2026-11-13 | 436,25 | 436,25 | 0,00 |

Jämförelsetolerans: högst ±0,01 SEK per stängningskurs, motsvarande den tvådecimalsprecision som visas i FT-tabellen. Observerad maximal avvikelse är 0,00 SEK. FT:s sida anger samtidigt att prisinformation kan vara avrundad och därför inte helt exakt; T09 markeras därför som **godkänd preliminärt**, inte slutligt godkänd. Käll-URL, kontrolltidpunkt, instrument, intervall, jämförelsefält, tolerans och avvikelser är därmed spårbara.

## 5 Begränsningar

- Verifieringen omfattar de tre instrument och tidsfönster som redovisas ovan: VOLV-B.ST, ATCO-A.ST och INVE-B.ST.
- Investor B är inte slutverifierad och får inte betraktas som täckt av detta protokoll.
- Förekomst av adjusted_close har observerats, men metodik för justering och konsekvens över utdelningar och splittar är inte validerad.
- T09-jämförelsen mot Financial Times matchar fem Investor B-stängningar vid visad precision; Financial Times anger att prisinformation kan vara avrundad eller ned-/uppjusterad och jämförelsen är därför preliminär, inte ett bevis på underliggande tick- eller fullprecisionlikhet.
- T10 är preliminärt godkänd endast för det specificerade privata användningsfallet. Bedömningen är en dokumenterad tolkning av EODHD:s publicerade villkor och hjälpsidor, inte juridisk rådgivning eller ett individuellt licensbrev. Om Empire/Hivemind används för ett företag, en kund, en grupp eller annan person krävs separat licensbedömning.
- Testerna visar inte tillgänglighet, rate limits, felåterhämtning, revisionsspår, tidszonshantering eller långsiktig datakvalitet.
- Resultaten är användarverifierade observationer, inte ett fullständigt leverantörs- eller säkerhetsgodkännande.
- EODHD Free:s aktuella planinformation anger 20 API-anrop per dag och ett års historik för EOD-priser, utdelningar och splittar. Planinformationen skiljer mellan API-anrop och HTTP-förfrågningar; vissa endpoints kostar flera anrop. Detta begränsar flerårig backtesting och historisk validering.
- Investor B:s splitdatum och splitförhållande är identifierade, men prisserien kring splitten kunde inte verifieras med Free-planen.

## 6 Riskregister och motåtgärder

| Risk | Konsekvens | Bedömning | Motåtgärd före gate |
|---|---|---|---|
| Felaktiga justeringar | Backtest och signaler kan bli fel | Hög | Verifiera utdelningar/splittar och dokumentera policy |
| Kursskillnad mot officiell källa | Felaktiga beslut eller avvikande historik | Hög | Genomför stickprov och definiera toleranser |
| Licensöverträdelse | Juridisk och kommersiell exponering | Hög | Dokumentera tillåtna användningsfall och lagring |
| Ofullständig instrumentsupport | Luckor i universum och tester | Medel | Slutverifiera Investor B och definiera instrumentlista |
| Rate limit eller förändrat API-svar | Driftstörning och ofullständiga data | Medel | Separat negativtest, cache-/fallbackbeslut och monitorering |
| För tidig gate-öppning | Riktig data når strategi eller beslut | Hög | Namngiven gate-ägare, explicit spärrstatus och separat beslut |

## 7 Godkännandekriterier

EODHD Free får endast gå från kandidat till godkänd read-only-provider när samtliga kriterier är uppfyllda och signerade av utsedda beslutsägare:

- Investor B är slutverifierad med samma datakvalitetskontroller som de redan verifierade instrumenten.
- Historiska utdelningar och splittar är verifierade, inklusive hur adjusted_close ska användas i Hivemind Trading Bot v1.0.
- Officiell kurssamstämmighet är genomförd med dokumenterad källa, datumintervall, tolerans och avvikelsehantering.
- Licensvillkor är lästa och beslutade för exakt användningsfall: read-only, historisk data, lagring, intern användning och eventuell distribution. T10:s privata användningsfall måste fortsatt uppfylla villkoren i avsnitt 11.
- Negativa och operativa tester är utförda för rate limits, tomma svar, felstatus, dubbletter, saknade fält och avbrutna svar.
- REAL_DATA_GATE har ett separat beslut, en namngiven ägare och en återställnings-/spärrmekanism.

## 8 Separata beslut före öppning av REAL_DATA_GATE

| Beslut | Fråga | Nuvarande status | Kräver |
|---|---|---|---|
| D1 Datakvalitet | Är EODHD Free tillräckligt korrekt för avsett read-only-bruk? | Inte slutligt beslutat | T07–T09 |
| D2 Corporate actions | Är utdelningar och splittar hanterade på ett verifierat sätt? | Öppet | T08 |
| D3 Licens | Är användning och lagring tillåtna för Hivemind Trading Bot v1.0? | Preliminärt godkänt endast för avgränsat privat bruk; kommersiell/annan användning öppen | T10 |
| D4 Driftisolering | Är leverantören isolerad från strategi-/orderflöden tills gate öppnas? | Öppet | T11 |
| D5 REAL_DATA_GATE | Ska gate öppnas, av vem och med vilka spärrar? | Nej, inte ännu | D1–D4 godkända separat |

## 9 Slutligt protokollbeslut

**Beslut:** EODHD Free klassificeras som preliminärt verifierad kandidat för read-only historisk marknadsdata, inte som produktionsgodkänd provider. REAL_DATA_GATE ska förbli stängd. Ingen anslutning till riktig data ska göras på grundval av detta dokument ensamt.

Nästa rekommenderade steg är att slutföra T07–T11 i isolerad verifieringsmiljö, samla evidens per test-ID och fatta D1–D4 som separata beslut. Först därefter kan D5 behandlas.

## 11 T10 – licensgranskning av EODHD Free

### Beslutsomfattning

Detta avsnitt gäller endast följande avsedda användning:

- Empire hämtar EOD-data automatiskt via EODHD:s read-only-API för en individs egna investeringsanalyser, screening, backtesting eller paper trading.
- Hivemind lagrar råa API-svar, normaliserade/transponerade data, analyser, modellresultat, provenance/audit-data och krypterade säkerhetskopior för samma privata ändamål.
- Discord används endast som privat rapportkanal till den användande individen. Ingen annan person, grupp, kund, arbetsgivare eller organisation får åtkomst.
- Ingen orderläggning, brokerintegration, offentlig dashboard eller vidareförsäljning ingår.

### Källor och vad de stöder

Källorna är officiella EODHD-sidor, åtkomna 2026-11-17:

1. [Terms and Conditions](https://eodhd.com/financial-apis/terms-conditions) — styrande villkor. Non-Professional User får lagra, manipulera och analysera information för privata, icke-kommersiella ändamål, men får inte dela konto/API-nyckel eller sälja, retransmittera, redistribuera, visa eller ge annan åtkomst till informationen eller tjänsten.
2. [What a Personal Plan Allows](https://eodhd.com/help/personal-use) — officiell förklaring att privat kvantitativ forskning, backtesting, screening, portföljmål, värderingsmodeller, paper trading och automatiska beräkningar kan omfattas när data och resultat inte lämnas till någon annan. Samma sida säger att användning för företag, arbetsgivare, kund, fond, grupp eller annan person inte omfattas.
3. [ChatGPT, Claude and Your Own Apps](https://eodhd.com/help/ai-tools) — officiell vägledning att privata AI-/appflöden kan användas när de är för användaren själv, använder inkluderade API:er, följer gränserna och håller API-nycklar, nedladdade dataset, cache och data-innehållande output borta från publika repos och exempel.
4. [Cancel a Plan, Keep Your Data, Refunds](https://eodhd.com/help/storage) — officiell FAQ som anger att icke-professionella användare får lagra råsvar, transformerade versioner, databaser och krypterade backuper; härledda forskningsresultat får behållas även efter uppsägning. FAQ:n anger också att data som hämtats under aktiv period får behållas efter uppsägning/nedgradering för privat, icke-kommersiellt bruk, men att nya uppdateringar kräver en aktiv plan och att förbudet mot vidareförmedling kvarstår.
5. [Plans, Free Trial and Student Discount](https://eodhd.com/help/plans), [Pricing](https://eodhd.com/pricing), [API Limits](https://eodhd.com/financial-apis/api-limits) och [EOD Historical Data API](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes) — Free-planens uppgivna 20 API-anrop per dag och ett års historik/past year för EOD-priser, splittar och utdelningar. API-anrop är en förbrukningsenhet; vissa förfrågningar kostar flera anrop.

### Bedömning per användningsfall

| Användningsfall | Bedömning | Grund och villkor |
|---|---|---|
| Privat automatiserad analys/AI på Empire | **Tillåtet enligt publicerad vägledning, villkorat** | Tillåtet om Empire kör för användarens egna investeringar och inte för företag, kund, grupp eller annan person. AI ändrar inte datalicensen och får bara nå endpoints som planen omfattar. |
| Lagring av rådata på Hivemind | **Tillåtet enligt officiell FAQ, villkorat** | Råsvar, normaliserade data och databaser får lagras för privat, icke-kommersiellt bruk. API-nycklar och licensierade dataset får inte hamna i publika repos eller publika exempel. |
| Lagring av analyser, modellresultat och backuper | **Tillåtet enligt officiell FAQ, villkorat** | Egna härledda resultat, audit/provenance och krypterade backuper får behållas för privat bruk. Detta är inte ett tillstånd att publicera eller dela resultaten. |
| Privat Discord-rapportering endast till användaren | **Förenligt med villkoren, villkorat** | Bedömningen bygger på EODHD:s privata visning/egen användning. Discord måste vara privat, endast användaren får åtkomst och rapporterna får inte innehålla information som delas vidare. |
| Vidareförmedling, delning eller publicering | **Inte tillåtet på personlig/Non-Professional-licens** | Förbudet omfattar rådata, ompaketerad data, visning, rapporter och åtkomst. Även härledda signaler/rankningar/backtestresultat får inte publiceras utan separat licensbedömning; EODHD:s sida ber uttryckligen användaren kontakta sales vid sådan användning. |
| Användning efter uppsägning | **Befintliga nedladdningar: tillåtet enligt FAQ; nya data: inte automatiskt tillåtet** | Data och analyser som hämtats under aktiv period får behållas och användas privat även efter uppsägning. Nya eller uppdaterade svar kräver aktiv plan/åtkomst; uppsägning tar inte bort vidareförmedlingsförbudet. |
| Free-planens kapacitet | **Teknisk begränsning, inte licensdispens** | 20 API-anrop per dag och ett års historik enligt aktuell planinformation. Den faktiska kostnaden per endpoint måste räknas; 20 anrop betyder inte 20 godtyckliga HTTP-förfrågningar med samma datamängd. |

### Öppet eller inte styrkt

- EODHD:s publika texter avgör inte en eventuell företags-/arbetsgivarrelation i Hivemind utan fakta om ägande, användare och syfte. Om “Empire” eller “Hivemind” är ett företagsprojekt, används på uppdrag av någon annan eller exponeras för fler än användaren ska T10 inte behandlas som godkänd; kontakta EODHD:s sales/licensing.
- “Privat Discord endast till användaren” är en tillämpning av regeln om privat användning, inte ett särskilt Discord-tillstånd. Kanalmedlemmar, botloggar, webhookar, externa integrationer och backup-åtkomst måste kontrolleras.
- Terms and Conditions är styrande dokument; Help Center är leverantörens tolkning/FAQ. Vid konflikt gäller Terms, och juridiskt bindande klartecken från EODHD har inte inhämtats.
- Inga API-nycklar, rådata, data-innehållande rapporter eller backuper får committas till GitHub. REAL_DATA_GATE förblir stängd oavsett T10-status.

### T10-beslut

**PRELIMINÄRT GODKÄND** endast för det avgränsade privata användningsfallet ovan. T10 är inte godkänd för kommersiell användning, användning för annan person/organisation, delning/publicering eller en publik/community-bot. T10 måste öppnas igen om användare, ägande, målgrupp, lagringsexponering eller distributionskanal ändras.


## 12 Signering och spårbarhet

| Roll | Namn | Beslut/status | Datum | Signatur |
|---|---|---|---|---|
| Verifieringsansvarig |  |  |  |  |
| Teknikansvarig |  |  |  |  |
| Licensansvarig |  |  |  |  |
| Gate-ägare |  |  |  |  |

Dokumentet är ett beslutsunderlag. Ändringar av verifieringsresultat, kriterier eller gate-status ska göras genom ny version med ändringsnotering och spårbar evidens.
