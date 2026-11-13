# Rollback för Etapp C

1. Pausa nya leases.
2. Stoppa workerprocessen.
3. Låt pågående leases löpa ut eller markera retry.
4. Behåll jobb, resultat och auditdata.
5. Återställ föregående image/version.
6. Kör readiness-, schema- och idempotენstester.
7. Återuppta endast fiktiva jobb efter godkänd kontroll.

Ingen verklig orderfunktion ingår.