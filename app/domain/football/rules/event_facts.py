from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderNeutralEvent:
    id: str | None
    event_type: str | None
    team_id: str | None = None
    player_id: str | None = None
    period: str | None = None
    minute: int | None = None
    second: int | None = None
    notes: str | None = None
    raw_payload: dict[str, Any] | None = None


def normalize_event_type(event_type: str | None) -> str | None:
    if event_type is None:
        return None
    normalized = event_type.strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized or None
