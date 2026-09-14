from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderReply:
    content: str


class ChatProvider(Protocol):
    def reply(self, message: str) -> ProviderReply: ...


class DummyProvider:
    """Deterministic, network-free provider for adapter and contract tests."""

    def reply(self, message: str) -> ProviderReply:
        normalized = message.strip().lower()
        if "inventory" in normalized or "bestand" in normalized:
            return ProviderReply("Use the registered inventory read tool.")
        if normalized.startswith(("reserve ", "reserviere ")):
            return ProviderReply(
                "Prepare a reservation proposal; confirmation is required."
            )
        return ProviderReply("Ask about inventory, risk, or a reservation proposal.")
