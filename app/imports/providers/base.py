from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ParsedProviderEvent:
    event_type: str
    minute: int
    second: int
    team_id: str
    period: str | None = None
    player_id: str | None = None
    provider_event_id: str | None = None
    x_coordinate: float | None = None
    y_coordinate: float | None = None
    notes: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderParseResult:
    raw_metadata: dict[str, Any]
    events: list[ParsedProviderEvent]
    warnings: list[str] = field(default_factory=list)


class ProviderAdapter(Protocol):
    def parse(self, extracted_dir: Path, filenames: list[str]) -> ProviderParseResult:
        """Parse provider metadata from an extracted import directory."""
