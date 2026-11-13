#!/usr/bin/env bash
set -euo pipefail
fail() { echo "PREFLIGHT FAILED: $1" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || fail "Docker saknas"
docker compose version >/dev/null 2>&1 || fail "Docker Compose saknas"
test -f docker-compose.yml || fail "Kör från projektroten"
test -f migrations/001_initial.sql || fail "Migration saknas"
test -f schemas/analysis-result-1.0.json || fail "JSON Schema saknas"
docker compose config --quiet || fail "Docker Compose-konfigurationen är ogiltig"
echo "PREFLIGHT OK"