# Hivemind Trading Bot v1.0 Etapp B

Detta är en isolerad utvecklingsgrund enligt den godkända Etapp A-specifikationen. API:t binds till Hiveminds interna adress på port 18000.

## Säkerhetsgräns

Projektet är låst till fiktiva data. Ingen broker-, Avanza-, order- eller riktig marknadsdataanslutning finns. `docker-compose.yml` publicerar API:t endast på localhost.

## Lokal testkörning

```bash
PYTHONPATH=src .venv/bin/pytest
```

Empire-workergrunden finns i `src/hivemind/worker.py`. Ingen secret eller driftdata ingår i repot.

Driftsättning på Hivemind eller ändringar på Empire ska ske genom separat godkänd deploy-etapp.