from dataclasses import dataclass
from enum import Enum
from typing import Any


class FactCategory(str, Enum):
    GOAL = "goal"
    SHOT = "shot"
    CARD = "card"
    CORNER = "corner"
    FOUL = "foul"
    OFFSIDE = "offside"


@dataclass(frozen=True)
class RuleExplanation:
    rule_id: str
    rule_name: str
    contributing_event_ids: tuple[str, ...]
    reason: str
    derivation_path: tuple[str, ...]


@dataclass(frozen=True)
class DerivedFootballFact:
    category: FactCategory
    event_id: str
    value: bool
    explanation: RuleExplanation
    attributes: dict[str, Any]


@dataclass(frozen=True)
class FootballRuleResult:
    rule_id: str
    rule_name: str
    facts: tuple[DerivedFootballFact, ...]
