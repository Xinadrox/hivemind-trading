# T12 – dagliga historiska priser från EODHD

`hivemind.eodhd.EodhdClient` läser Stockholmssymboler via HTTPS GET på EODHD:s EOD-endpoint. Den begär dagliga JSON-poster i stigande datumordning. Adaptern används av den fristående testimporten. Tjänsternas konfiguration har fortsatt `REAL_DATA_GATE=closed`.

Importen validerar hela svaret innan den skriver till databasen. Datum ska vara strikt stigande och inom det begärda intervallet. Svaret måste innehålla OHLC, justerad stängningskurs och positiv heltalsvolym. Priser ska vara ändliga, positiva och rymmas i PostgreSQLs `numeric(24,12)`. Öppnings- och stängningspris ska ligga mellan dagens lägsta och högsta. Tomma, felaktiga, för stora och avbrutna svar avbryter körningen, liksom varningsobjekt och rader som innehåller varningar. Saknade handelsdagar upptäcks endast om svaret är tomt. Helgdagar, utdelningar, splittar och leverantörens beräkning av justerad stängning behöver verifieras separat.

Migration `004_eodhd_daily_prices.sql` lagrar en rad per symbol och handelsdatum. Testimporten skriver alla tre instrument i en transaktion. En identisk omkörning gör noll ändringar. Ändrade värden uppdaterar den befintliga raden.

## Manuell testimport

Använd en separat, tom och temporär PostgreSQL 16-databas. Sätt `T12_TEST_DATABASE_URL` i den lokala miljön. Kör från repots rot i projektets Python-miljö.

```sh
REAL_DATA_GATE=closed DATABASE_URL="$T12_TEST_DATABASE_URL" python -m hivemind.migrate
REAL_DATA_GATE=closed python -m hivemind.eodhd_import
REAL_DATA_GATE=closed python -m hivemind.eodhd_import
```

Importen genererar fem syntetiska handelsdagar vardera för `INVE-B.ST`, `VOLV-B.ST` och `ATCO-A.ST` (9–13 november 2026). Den loggar bara antal poster. Första körningen ändrar 15 rader och andra körningen 0. PostgreSQL-testet körs med `REAL_DATA_GATE=closed pytest tests/test_eodhd_import.py` och behöver en ny tom databas.

## Kvot och separat godkännande

Tre EOD-förfrågningar förbrukar tre av Free-planens 20 dagliga API-anrop om kontot har full kvot. Free-planen ger tillgång till ett års historik. Välj vid en eventuell godkänd livetest ett kort intervall inom tillgänglig historik och kontrollera återstående kontokvot före körning. [EODHD:s kvotdokumentation](https://eodhd.com/financial-apis/api-limits) · [EODHD:s dokumentation för historiska dagskurser](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes)

Adaptern räknar alla försök mot en lokal budget, normalt tre per klient. HTTP 402 eller 429 stoppar klienten direkt. Den följer inga omdirigeringar och gör inga automatiska återförsök. Den lokala budgeten gäller bara den enskilda klienten och samordnas inte med andra körningar eller kontots faktiska förbrukning.

Den manuella importen använder enbart mocktransport. För en framtida, separat godkänd körning finns en fristående HTTPS-klient som kräver explicit godkännande av anroparen och läser `EODHD_API_TOKEN` från miljön. T12-verifieringen använder mockade svar och en isolerad databas. Håll nycklar, hämtade svar och databaskopior utanför GitHub och CI-loggar.
