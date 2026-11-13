from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
import json
from urllib.request import Request, urlopen


class WebhookClient(Protocol):
    def send(self, content: str) -> None: ...


class DiscordWebhookClient:
    def __init__(self, webhook_url: str, timeout_seconds: int = 10):
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send(self, content: str) -> None:
        request = Request(self.webhook_url, data=json.dumps({"content": content[:1900]}).encode(), headers={"Content-Type": "application/json", "User-Agent": "hivemind-trading-dry-run"}, method="POST")
        with urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status not in {200, 204}:
                raise RuntimeError(f"Discord webhook returned {response.status}")


@dataclass
class DiscordOutboxMessage:
    job_id: str
    summary: str
    status: str
    confidence: float

    def render(self) -> str:
        return f"Hivemind analysrapport | jobb {self.job_id}\nStatus: {self.status} | Confidence: {self.confidence:.2f}\n{self.summary}\nIngen handel har utförts."


def publish_once(message: DiscordOutboxMessage, client: WebhookClient, sent_job_ids: set[str]) -> bool:
    if message.job_id in sent_job_ids:
        return False
    client.send(message.render())
    sent_job_ids.add(message.job_id)
    return True