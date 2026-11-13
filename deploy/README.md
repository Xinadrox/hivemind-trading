# Etapp C Deploypaket

Förberedelse- och deployunderlag för Hivemind och Empire. Inga secrets ingår.

- Hivemind: Ubuntu/Docker, intern adress 192.168.0.116
- Empire: Linux med fish och Codex CLI
- Kommunikation: Empire initierar utgående anslutning
- Data: endast fiktiva data

Kör preflight, skapa secrets utanför repot, applicera migrationer, kör smoke tests och verifiera rollback innan en ny deploy-etapp godkänns.