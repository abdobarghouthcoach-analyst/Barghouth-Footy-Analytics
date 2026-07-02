from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.football.rules.event_facts import ProviderNeutralEvent, normalize_event_type, normalize_team_id
from app.domain.football.rules.types import DerivedFootballFact, FactCategory, FootballRuleResult, RuleExplanation


@dataclass(frozen=True)
class EventTypeRecognitionRule:
    rule_id: str
    rule_name: str
    category: FactCategory
    recognized_event_types: frozenset[str]

    def apply(self, events: Iterable[ProviderNeutralEvent]) -> FootballRuleResult:
        facts: list[DerivedFootballFact] = []
        for event in events:
            event_id = _event_id(event)
            event_type = normalize_event_type(event.event_type)
            if event_id is None or event_type is None:
                continue
            if event_type not in self.recognized_event_types:
                continue
            facts.append(self._fact(event_id=event_id, event_type=event_type, team_id=normalize_team_id(event.team_id)))
        return FootballRuleResult(rule_id=self.rule_id, rule_name=self.rule_name, facts=tuple(facts))

    def _fact(self, *, event_id: str, event_type: str, team_id: str | None) -> DerivedFootballFact:
        explanation = RuleExplanation(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            contributing_event_ids=(event_id,),
            reason=f"Event type '{event_type}' is recognised as {self.category.value}.",
            derivation_path=("normalize_event_type", f"match:{event_type}", f"fact:{self.category.value}"),
        )
        attributes = {"normalized_event_type": event_type}
        if team_id is not None:
            attributes["team_id"] = team_id
        return DerivedFootballFact(
            category=self.category,
            event_id=event_id,
            value=True,
            explanation=explanation,
            attributes=attributes,
        )


def default_football_rules() -> tuple[EventTypeRecognitionRule, ...]:
    return (
        EventTypeRecognitionRule(
            rule_id="football.goal.recognition.v1",
            rule_name="Goal event recognition",
            category=FactCategory.GOAL,
            recognized_event_types=frozenset({"goal"}),
        ),
        EventTypeRecognitionRule(
            rule_id="football.shot.recognition.v1",
            rule_name="Shot event recognition",
            category=FactCategory.SHOT,
            recognized_event_types=frozenset({"shot", "shot_on_goal", "shot_off_target", "shot_blocked"}),
        ),
        EventTypeRecognitionRule(
            rule_id="football.card.recognition.v1",
            rule_name="Card event recognition",
            category=FactCategory.CARD,
            recognized_event_types=frozenset({"card", "yellow_card", "red_card", "second_yellow"}),
        ),
        EventTypeRecognitionRule(
            rule_id="football.corner.recognition.v1",
            rule_name="Corner event recognition",
            category=FactCategory.CORNER,
            recognized_event_types=frozenset({"corner", "corner_kick"}),
        ),
        EventTypeRecognitionRule(
            rule_id="football.foul.recognition.v1",
            rule_name="Foul event recognition",
            category=FactCategory.FOUL,
            recognized_event_types=frozenset({"foul"}),
        ),
        EventTypeRecognitionRule(
            rule_id="football.offside.recognition.v1",
            rule_name="Offside event recognition",
            category=FactCategory.OFFSIDE,
            recognized_event_types=frozenset({"offside"}),
        ),
    )


def _event_id(event: ProviderNeutralEvent) -> str | None:
    if event.id is None:
        return None
    value = str(event.id).strip()
    return value or None
