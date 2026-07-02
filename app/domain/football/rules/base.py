from collections.abc import Iterable
from typing import Protocol

from app.domain.football.rules.event_facts import ProviderNeutralEvent
from app.domain.football.rules.types import FootballRuleResult


class FootballRule(Protocol):
    rule_id: str
    rule_name: str

    def apply(self, events: Iterable[ProviderNeutralEvent]) -> FootballRuleResult:
        """Return derived football facts for provider-neutral events."""
