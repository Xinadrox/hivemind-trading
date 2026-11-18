"""Manually exercise T12 using synthetic API responses and a disposable database."""

from dataclasses import astuple
from datetime import date, timedelta
import os
import sys

import httpx
import psycopg

from .config import RuntimeConfig
from .eodhd import EodhdClient, EodhdError

SYMBOLS = ("INVE-B.ST", "VOLV-B.ST", "ATCO-A.ST")
START = date(2026, 11, 9)
END = date(2026, 11, 13)

UPSERT = """
    INSERT INTO eodhd_daily_prices AS existing
        (symbol, trading_date, open, high, low, close, adjusted_close, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (symbol, trading_date) DO UPDATE SET
        (open, high, low, close, adjusted_close, volume) =
        (EXCLUDED.open, EXCLUDED.high, EXCLUDED.low, EXCLUDED.close,
         EXCLUDED.adjusted_close, EXCLUDED.volume)
    WHERE (existing.open, existing.high, existing.low, existing.close,
           existing.adjusted_close, existing.volume) IS DISTINCT FROM
          (EXCLUDED.open, EXCLUDED.high, EXCLUDED.low, EXCLUDED.close,
           EXCLUDED.adjusted_close, EXCLUDED.volume)
"""


def _fixture_response(request: httpx.Request) -> httpx.Response:
    symbol = request.url.path.rsplit("/", 1)[-1]
    rows = []
    for offset in range((END - START).days + 1):
        price = 10 + SYMBOLS.index(symbol) * 10 + offset
        rows.append({
            "date": (START + timedelta(days=offset)).isoformat(),
            "open": price,
            "high": price + 2,
            "low": price - 1,
            "close": price + 1,
            "adjusted_close": price + 0.5,
            "volume": 100 + offset,
        })
    return httpx.Response(200, json=rows)


def import_fixture(database_url: str) -> int:
    RuntimeConfig.from_env()
    with EodhdClient(httpx.MockTransport(_fixture_response)) as client:
        bars = [bar for symbol in SYMBOLS for bar in client.fetch(symbol, START, END)]

    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.executemany(UPSERT, [astuple(bar) for bar in bars])
        return cursor.rowcount


def main() -> int:
    database_url = os.getenv("T12_TEST_DATABASE_URL")
    if not database_url:
        print("T12_TEST_DATABASE_URL must point to a migrated disposable database.", file=sys.stderr)
        return 1
    if database_url == os.getenv("DATABASE_URL"):
        print("Use a separate disposable database for the T12 fixture import.", file=sys.stderr)
        return 1
    try:
        changed = import_fixture(database_url)
    except psycopg.Error:
        print("T12 fixture import failed. Check the test database and its migrations.", file=sys.stderr)
        return 1
    except (EodhdError, ValueError):
        print("T12 fixture import failed. Check fixture validation and REAL_DATA_GATE.", file=sys.stderr)
        return 1
    print(f"T12 fixture import validated 15 synthetic bars. Inserted or updated {changed}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
