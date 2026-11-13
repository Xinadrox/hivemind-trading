from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


class MarketDataProvider(Protocol):
    def fetch(self, symbol: str) -> dict: ...


@dataclass
class FictionalDataProvider:
    """Deterministic provider used until real data is explicitly approved."""

    def fetch(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "source": "fictional",
            "as_of": "1970-01-01T00:00:00Z",
            "facts": [{"text": "Detta är en fiktiv datapunkt."}],
        }