from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from app.domain.football.rules.base import FootballRule
from app.domain.football.rules.event_facts import ProviderNeutralEvent
from app.domain.football.rules.rules import default_football_rules
from app.domain.football.rules.types import DerivedFootballFact, FootballRuleResult


@dataclass(frozen=True)
class FootballRulesEngine:
    rules: Sequence[FootballRule]

    @classmethod
    def with_default_rules(cls) -> "FootballRulesEngine":
        return cls(rules=default_football_rules())

    def apply(self, events: Iterable[ProviderNeutralEvent]) -> tuple[FootballRuleResult, ...]:
        event_list = tuple(events)
        return tuple(rule.apply(event_list) for rule in self.rules)

    def derive_facts(self, events: Iterable[ProviderNeutralEvent]) -> tuple[DerivedFootballFact, ...]:
        results = self.apply(events)
        return tuple(fact for result in results for fact in result.facts)
