"""Standalone, read-only client for daily EODHD prices."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, DecimalException
import json
import os
import re
from threading import Lock

import httpx


class EodhdError(RuntimeError):
    pass


class EodhdQuotaError(EodhdError):
    pass


@dataclass(frozen=True)
class DailyBar:
    symbol: str
    trading_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int


class _AuthenticatedTransport(httpx.HTTPTransport):
    def __init__(self, token: str):
        super().__init__(trust_env=False, retries=0)
        self._token = token

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        # Add credentials below the client layer, which logs request URLs.
        authenticated = httpx.Request(
            request.method,
            request.url.copy_add_param("api_token", self._token),
            headers=request.headers,
            extensions=request.extensions,
        )
        return super().handle_request(authenticated)


class EodhdClient:
    """One budget per client/run. A provider quota refusal stops the run."""

    def __init__(self, transport: httpx.BaseTransport, *, request_budget: int = 3):
        if type(request_budget) is not int or not 1 <= request_budget <= 20:
            raise ValueError("request_budget must be between 1 and 20")
        self._client = httpx.Client(
            transport=transport, timeout=10.0, follow_redirects=False, trust_env=False,
        )
        self._remaining = request_budget
        self._lock = Lock()

    @classmethod
    def live(cls, *, approved: bool = False) -> "EodhdClient":
        if approved is not True:
            raise EodhdError("Live EODHD requests require separate approval")
        token = os.getenv("EODHD_API_TOKEN", "").strip()
        if not token:
            raise EodhdError("EODHD_API_TOKEN is required")
        return cls(_AuthenticatedTransport(token))

    def __enter__(self) -> "EodhdClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._client.close()

    def fetch(self, symbol: str, start: date, end: date) -> list[DailyBar]:
        if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9][A-Z0-9-]{0,19}\.ST", symbol):
            raise EodhdError("Expected a Stockholm symbol in EODHD format")
        if type(start) is not date or type(end) is not date or start > end:
            raise EodhdError("Invalid date range")

        params = {
            "from": start.isoformat(), "to": end.isoformat(),
            "period": "d", "fmt": "json", "order": "a",
        }
        with self._lock:
            if not self._remaining:
                raise EodhdQuotaError("EODHD request budget exhausted")
            self._remaining -= 1
            body = self._get(symbol, params)
        return _parse_bars(symbol, start, end, body)

    def _get(self, symbol: str, params: dict[str, str]) -> bytes:
        try:
            with self._client.stream(
                "GET", f"https://eodhd.com/api/eod/{symbol}",
                params=params, headers={"Accept": "application/json"},
            ) as response:
                if response.status_code in (402, 429):
                    self._remaining = 0
                    raise EodhdQuotaError(f"EODHD quota refused request (HTTP {response.status_code})")
                if response.status_code != 200:
                    raise EodhdError(f"EODHD request failed (HTTP {response.status_code})")
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > 1_000_000:
                        raise EodhdError("EODHD response exceeds size limit")
                return bytes(body)
        except httpx.HTTPError:
            raise EodhdError("EODHD transport failed") from None


def _parse_bars(symbol: str, start: date, end: date, body: bytes) -> list[DailyBar]:
    try:
        payload = json.loads(body, parse_float=Decimal)
    except (ValueError, RecursionError, DecimalException):
        raise EodhdError("Invalid EODHD JSON response") from None
    if not isinstance(payload, list) or not payload:
        raise EodhdError("Expected a nonempty EODHD daily price list")

    bars = []
    for index, row in enumerate(payload, start=1):
        try:
            if not isinstance(row, dict) or {"warning", "warnings", "error", "message"} & row.keys():
                raise ValueError
            trading_date = date.fromisoformat(row["date"])
            if trading_date.isoformat() != row["date"] or not start <= trading_date <= end:
                raise ValueError
            if bars and trading_date <= bars[-1].trading_date:
                raise ValueError
            open_price, high, low, close, adjusted = (
                _price(row[key]) for key in ("open", "high", "low", "close", "adjusted_close")
            )
            if not (low <= open_price <= high and low <= close <= high):
                raise ValueError
            volume = row["volume"]
            if type(volume) is not int or not 0 < volume < 2**63:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise EodhdError(f"Invalid EODHD daily price at row {index}") from None
        bars.append(DailyBar(symbol, trading_date, open_price, high, low, close, adjusted, volume))
    return bars


def _price(value: object) -> Decimal:
    if type(value) not in (int, Decimal):
        raise ValueError
    price = Decimal(value)
    # Match the finite storage range while avoiding silent database rounding.
    if not price.is_finite() or not 0 < price < 10**12 or price.as_tuple().exponent < -12:
        raise ValueError
    return price
