import os

import psycopg
import pytest

from hivemind.eodhd_import import SYMBOLS, import_fixture
from hivemind.migrate import run_migrations


def test_fixture_import_is_repeatable_on_isolated_postgres():
    database_url = os.getenv("T12_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set T12_TEST_DATABASE_URL to a disposable PostgreSQL database")

    for _ in range(2):
        run_migrations(database_url)
    assert import_fixture(database_url) == 15
    assert import_fixture(database_url) == 0

    with psycopg.connect(database_url) as connection:
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone() == (4,)
        assert connection.execute(
            """
            SELECT symbol, count(*), min(trading_date)::text, max(trading_date)::text
            FROM eodhd_daily_prices GROUP BY symbol ORDER BY symbol
            """
        ).fetchall() == [(symbol, 5, "2026-11-09", "2026-11-13") for symbol in sorted(SYMBOLS)]

        with pytest.raises(psycopg.errors.CheckViolation), connection.transaction():
            connection.execute("UPDATE eodhd_daily_prices SET volume = 0")
        with pytest.raises(psycopg.errors.UniqueViolation), connection.transaction():
            connection.execute("INSERT INTO eodhd_daily_prices SELECT * FROM eodhd_daily_prices")

        connection.execute("UPDATE eodhd_daily_prices SET adjusted_close = 1 WHERE symbol = %s",
                           (SYMBOLS[0],))
        connection.commit()

    assert import_fixture(database_url) == 5
    assert import_fixture(database_url) == 0


def test_fixture_import_stops_before_database_if_gate_is_open(monkeypatch):
    monkeypatch.setenv("REAL_DATA_GATE", "open")
    with pytest.raises(ValueError, match="REAL_DATA_GATE"):
        import_fixture("unused")
