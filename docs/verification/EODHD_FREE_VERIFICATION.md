# Verifieringsprotokoll för EODHD Free

*Kandidat till read-only-marknadsdataprovider i Hivemind Trading Bot v1.0*

- Dokumentstatus: Underlag för villkorat beslut
- Datum: 14 november 2026
- Omfattning: Historiska EOD OHLCV-data för svenska aktier
- Beslutsobjekt: Om EODHD Free kan kvalificeras som kandidat före separat öppning av REAL_DATA_GATE

## 1 Sammanfattning och rekommendation

EODHD Free rekommenderas inte för godkännande som produktionsaktiv marknadsdataprovider ännu. Underlaget visar en lovande teknisk kandidat för read-only historisk EOD-data: VOLV-B.ST har verifierats med 10 poster för perioden 2026-11-02–2026-11-13 och ATCO-A.ST med fem poster för perioden 2026-11-09–2026-11-13. För samtliga redovisade poster har användaren observerat giltiga OHLC-intervall, positiva volymer, unika datum och fältet adjusted_close.

Rekommendationen är därför: villkorat kandidatstatus, fortsatt sandbox-/fixture-användning och ingen öppning av REAL_DATA_GATE innan de utestående besluten och kompletterande verifieringarna nedan är godkända. Detta protokoll ansluter ingen riktig data och ändrar inte Hivemind Trading Bot, repo eller driftsmiljö.

## 2 Syfte och avgränsning

Syftet är att skapa ett formellt, spårbart beslutsunderlag för EODHD Free som möjlig read-only-leverantör i version 1.0. Protokollet bedömer endast det verifierade användarunderlaget och definierar vad som måste återstå innan en eventuell produktionsmässig dataport kan öppnas.

Utanför scope ligger realtidsdata, orderläggning, skrivande API-anrop, driftkonfiguration, autentiseringsändringar, lasttest mot extern tjänst och anslutning till riktig data. Investor B är ännu inte slutverifierad.

## 3 Verifierat underlag

| Instrument | Verifierad period | Antal poster | Observerade egenskaper | Status |
|---|---:|---:|---|---|
| VOLV-B.ST | 2026-11-02–2026-11-13 | 10 | Giltiga OHLC-intervall; positiva volymer; unika datum; adjusted_close | Preliminärt godkänd |
| ATCO-A.ST | 2026-11-09–2026-11-13 | 5 | Giltiga OHLC-intervall; positiva volymer; unika datum; adjusted_close | Preliminärt godkänd |
| Investor B | Ej slutverifierad | Ej fastställt | Ej slutverifierad | Öppen |

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
| T07 | Investor B | Samma kontrollpaket som T01–T06 | Ej slutverifierad | EJ GODKÄND |
| T08 | Historiska utdelningar och splittar | Corporate actions kan identifieras och hanteras korrekt | Återstår | ÖPPEN |
| T09 | Officiell kurssamstämmighet | Jämförelse mot auktoritativ källa inom definierad tolerans | Återstår | ÖPPEN |
| T10 | Licensvillkor | Read-only-användning, lagring, redistribution och kommersiell användning är klarlagda | Återstår | ÖPPEN |
| T11 | Driftmässig isolering | Test kan ske utan riktig data eller produktionspåverkan | Ska bekräftas separat i designbeslut | ÖPPEN |

## 5 Begränsningar

- Verifieringen omfattar endast de två instrument och tidsfönster som redovisas ovan.
- Investor B är inte slutverifierad och får inte betraktas som täckt av detta protokoll.
- Förekomst av adjusted_close har observerats, men metodik för justering och konsekvens över utdelningar och splittar är inte validerad.
- Ingen officiell, oberoende kurssamstämmighet har genomförts.
- Licensvillkor för EODHD Free är inte slutligt bedömda i detta protokoll; juridisk och operativ användning får därför inte antas vara tillåten.
- Testerna visar inte tillgänglighet, rate limits, felåterhämtning, revisionsspår, tidszonshantering eller långsiktig datakvalitet.
- Resultaten är användarverifierade observationer, inte ett fullständigt leverantörs- eller säkerhetsgodkännande.
- EODHD Free:s uppgivna historikdjup på ett år begränsar flerårig backtesting och historisk validering. Abonnemangsvillkoret och historikdjupet ska bekräftas mot aktuella leverantörsvillkor innan sådana analyser används som beslutsunderlag.
- Investor B:s splitdatum och splitförhållande är identifierade, men prisserien kring splitten kunde inte verifieras med Free-planen.

## 6 Riskregister och motåtgärder

| Risk | Konsekvens | Bedömning | Motåtgärd före gate |
|---|---|---|---|
| Felaktiga justeringar | Backtest och signaler kan bli fel | Hög | Verifiera utdelningar/splittar och dokumentera policy |
| Kursskillnad mot officiell källa | Felaktiga beslut eller avvikande historik | Hög | Genomför stickprov och definiera toleranser |
| Licensöverträdelse | Juridisk och kommersiell exponering | Hög | Dokumentera tillåtna användningsfall och lagring |
| Ofullständig instrumentsupport | Luckor i universum och tester | Medel | Slutverifiera Investor B och definiera instrumentlista |
| Rate limit eller förändrat API-svar | Driftstörning och ofullständiga data | Medel | Separat negativtest, cache-/fallbackbeslut och monitorering |
| För tidig gate-öppning | Riktig data når strategi eller beslut | Hög | Tvåpersonersbeslut och explicit spärrstatus |

## 7 Godkännandekriterier

EODHD Free får endast gå från kandidat till godkänd read-only-provider när samtliga kriterier är uppfyllda och signerade av utsedda beslutsägare:

- Investor B är slutverifierad med samma datakvalitetskontroller som de redan verifierade instrumenten.
- Historiska utdelningar och splittar är verifierade, inklusive hur adjusted_close ska användas i Hivemind Trading Bot v1.0.
- Officiell kurssamstämmighet är genomförd med dokumenterad källa, datumintervall, tolerans och avvikelsehantering.
- Licensvillkor är lästa och beslutade för exakt användningsfall: read-only, historisk data, lagring, intern användning och eventuell distribution.
- Negativa och operativa tester är utförda för rate limits, tomma svar, felstatus, dubbletter, saknade fält och avbrutna svar.
- REAL_DATA_GATE har ett separat beslut, en namngiven ägare och en återställnings-/spärrmekanism.

## 8 Separata beslut före öppning av REAL_DATA_GATE

| Beslut | Fråga | Nuvarande status | Kräver |
|---|---|---|---|
| D1 Datakvalitet | Är EODHD Free tillräckligt korrekt för avsett read-only-bruk? | Inte slutligt beslutat | T07–T09 |
| D2 Corporate actions | Är utdelningar och splittar hanterade på ett verifierat sätt? | Öppet | T08 |
| D3 Licens | Är användning och lagring tillåtna för Hivemind Trading Bot v1.0? | Öppet | T10 |
| D4 Driftisolering | Är leverantören isolerad från strategi-/orderflöden tills gate öppnas? | Öppet | T11 |
| D5 REAL_DATA_GATE | Ska gate öppnas, av vem och med vilka spärrar? | Nej, inte ännu | D1–D4 godkända separat |

## 9 Slutligt protokollbeslut

**Beslut:** EODHD Free klassificeras som preliminärt verifierad kandidat för read-only historisk marknadsdata, inte som produktionsgodkänd provider. REAL_DATA_GATE ska förbli stängd. Ingen anslutning till riktig data ska göras på grundval av detta dokument ensamt.

Nästa rekommenderade steg är att slutföra T07–T11 i isolerad verifieringsmiljö, samla evidens per test-ID och fatta D1–D4 som separata beslut. Först därefter kan D5 behandlas.

## 10 Signering och spårbarhet

| Roll | Namn | Beslut/status | Datum | Signatur |
|---|---|---|---|---|
| Verifieringsansvarig |  |  |  |  |
| Teknikansvarig |  |  |  |  |
| Licensansvarig |  |  |  |  |
| Gate-ägare |  |  |  |  |

Dokumentet är ett beslutsunderlag. Ändringar av verifieringsresultat, kriterier eller gate-status ska göras genom ny version med ändringsnotering och spårbar evidens.
