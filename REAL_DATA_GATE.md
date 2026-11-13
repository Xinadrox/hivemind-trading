# Gräns före faktisk data

Följande villkor måste vara godkända innan någon riktig marknadsdatakälla kopplas in:

1. GitHub CI är grön för den versionsmärkta dry-run-versionen.
2. PostgreSQL backup och restore är verifierade.
3. Rollback av API och worker är övad.
4. Transport, tokenrotation och logggranskning är dokumenterade.
5. Discord-rapportering är separerad från handelsbeslut.
6. En read-only datakälla och dess licensvillkor är uttryckligen godkänd.
7. Testfall med historiska och fiktiva data är definierade.

Avanza, orderläggning och annan handelsintegration ligger utanför nästa steg och kräver ett separat beslut.