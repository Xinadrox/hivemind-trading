import json
from datetime import date
from decimal import Decimal

import httpx
import pytest

from hivemind.eodhd import EodhdClient, EodhdError, EodhdQuotaError

START = date(2026, 11, 9)
END = date(2026, 11, 13)
BAR = {
    "date": START.isoformat(), "open": 10, "high": 12,
    "low": 9, "close": 11, "adjusted_close": 10.25, "volume": 100,
}


def mock_client(handler, **kwargs):
    return EodhdClient(httpx.MockTransport(handler), **kwargs)


def test_read_only_request_and_decimal_prices():
    def respond(request):
        assert request.method == "GET"
        assert request.url.host == "eodhd.com"
        assert request.url.path == "/api/eod/INVE-B.ST"
        assert dict(request.url.params) == {
            "from": str(START), "to": str(END), "period": "d",
            "fmt": "json", "order": "a",
        }
        return httpx.Response(200, json=[BAR])

    bar, = mock_client(respond).fetch("INVE-B.ST", START, END)
    assert bar.adjusted_close == Decimal("10.25")
    assert bar.trading_date == START


@pytest.mark.parametrize("payload", [
    [], {"warning": "history truncated"}, [BAR, BAR],
    [{**BAR, "date": "2026-11-08"}],
    [{**BAR, "date": "2026-11-10"}, BAR],
    [{**BAR, "date": "20261109"}],
    [{**BAR, "volume": True}], [{**BAR, "volume": 0}],
    [{**BAR, "volume": 2**63}],
    [{**BAR, "high": 10}], [{**BAR, "open": 0}],
    [{**BAR, "adjusted_close": None}],
    [{**BAR, "close": "11"}],
    [{**BAR, "warning": "limited history"}],
    [{key: value for key, value in BAR.items() if key != "close"}],
])
def test_rejects_invalid_responses(payload):
    client = mock_client(lambda _: httpx.Response(200, json=payload))
    with pytest.raises(EodhdError):
        client.fetch("INVE-B.ST", START, END)


@pytest.mark.parametrize("status", [301, 401, 403, 404, 503])
def test_http_errors_do_not_follow_redirects_or_expose_response(status):
    def respond(request):
        assert request.url.host == "eodhd.com"
        return httpx.Response(status, headers={"Location": "https://example.com"},
                              text="sensitive-payload")

    with pytest.raises(EodhdError, match=f"HTTP {status}") as error:
        mock_client(respond).fetch("INVE-B.ST", START, END)
    assert "sensitive-payload" not in str(error.value)


@pytest.mark.parametrize("status", [402, 429])
def test_provider_quota_stops_requests(status):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status)

    client = mock_client(respond)
    for _ in range(2):
        with pytest.raises(EodhdQuotaError):
            client.fetch("INVE-B.ST", START, END)
    assert len(calls) == 1


def test_local_quota_counts_failed_attempts_and_hides_transport_detail():
    def respond(request):
        raise httpx.ReadTimeout("sensitive-payload", request=request)

    client = mock_client(respond, request_budget=1)
    with pytest.raises(EodhdError, match="transport") as error:
        client.fetch("INVE-B.ST", START, END)
    assert "sensitive-payload" not in str(error.value)
    with pytest.raises(EodhdQuotaError):
        client.fetch("INVE-B.ST", START, END)


@pytest.mark.parametrize("body", [b"[", b"\xff", b"{}", b" " * 1_000_001,
                                json.dumps([{**BAR, "close": float("nan")}]).encode()])
def test_rejects_unusable_body(body):
    with pytest.raises(EodhdError):
        mock_client(lambda _: httpx.Response(200, content=body)).fetch("INVE-B.ST", START, END)


def test_live_requires_explicit_approval_and_environment_token(monkeypatch):
    monkeypatch.setenv("EODHD_API_TOKEN", "synthetic-test-token")
    with pytest.raises(EodhdError, match="approval"):
        EodhdClient.live(approved=False)
    monkeypatch.delenv("EODHD_API_TOKEN")
    with pytest.raises(EodhdError, match="EODHD_API_TOKEN"):
        EodhdClient.live(approved=True)


def test_rejects_invalid_request_before_transport():
    client = mock_client(lambda _: pytest.fail("unexpected HTTP request"))
    with pytest.raises(EodhdError):
        client.fetch("../other", START, END)
    with pytest.raises(EodhdError):
        client.fetch("INVE-B.ST", END, START)


def test_live_credentials_are_added_below_request_logging(monkeypatch, caplog):
    token = "synthetic-test-token"
    monkeypatch.setenv("EODHD_API_TOKEN", token)

    def respond(_transport, request):
        assert request.url.params["api_token"] == token
        assert request.url.scheme == "https"
        return httpx.Response(200, json=[BAR])

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    with caplog.at_level("INFO", logger="httpx"):
        with EodhdClient.live(approved=True) as client:
            client.fetch("INVE-B.ST", START, END)
    assert "HTTP Request" in caplog.text
    assert token not in caplog.text
