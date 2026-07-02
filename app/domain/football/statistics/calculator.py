from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.football.rules import FactCategory, FootballRulesEngine, ProviderNeutralEvent
from app.domain.football.rules.types import DerivedFootballFact, FootballRuleResult
from app.domain.football.statistics.types import MatchStatistic, MatchStatisticsSummary, StatisticExplanation, StatisticName


@dataclass(frozen=True)
class MatchStatisticsCalculator:
    rules_engine: FootballRulesEngine

    @classmethod
    def with_default_rules(cls) -> "MatchStatisticsCalculator":
        return cls(rules_engine=FootballRulesEngine.with_default_rules())

    def calculate(self, events: Iterable[ProviderNeutralEvent]) -> MatchStatisticsSummary:
        return self.calculate_from_rule_results(self.rules_engine.apply(events))

    def calculate_from_rule_results(self, rule_results: Iterable[FootballRuleResult]) -> MatchStatisticsSummary:
        facts = tuple(fact for result in rule_results for fact in result.facts if fact.value is True)
        statistics = (
            self._count_statistic(StatisticName.GOALS, facts, lambda fact: fact.category == FactCategory.GOAL),
            self._count_statistic(StatisticName.SHOTS, facts, lambda fact: fact.category == FactCategory.SHOT),
            self._count_statistic(
                StatisticName.SHOTS_ON_TARGET,
                facts,
                lambda fact: fact.category == FactCategory.SHOT and _normalized_event_type(fact) == "shot_on_goal",
            ),
            self._count_statistic(StatisticName.CORNERS, facts, lambda fact: fact.category == FactCategory.CORNER),
            self._count_statistic(StatisticName.FOULS, facts, lambda fact: fact.category == FactCategory.FOUL),
            self._count_statistic(StatisticName.OFFSIDES, facts, lambda fact: fact.category == FactCategory.OFFSIDE),
            self._count_statistic(
                StatisticName.YELLOW_CARDS,
                facts,
                lambda fact: fact.category == FactCategory.CARD and _normalized_event_type(fact) == "yellow_card",
            ),
            self._count_statistic(
                StatisticName.RED_CARDS,
                facts,
                lambda fact: fact.category == FactCategory.CARD and _normalized_event_type(fact) == "red_card",
            ),
        )
        return MatchStatisticsSummary(statistics=statistics)

    def _count_statistic(
        self,
        name: StatisticName,
        facts: tuple[DerivedFootballFact, ...],
        predicate,
    ) -> MatchStatistic:
        contributing_facts = tuple(fact for fact in facts if predicate(fact))
        event_ids = tuple(fact.event_id for fact in contributing_facts)
        fact_refs = tuple(_fact_ref(fact) for fact in contributing_facts)
        rule_ids = _unique(fact.explanation.rule_id for fact in contributing_facts)
        rule_names = _unique(fact.explanation.rule_name for fact in contributing_facts)
        reason = f"{name.value} is derived by counting matching football facts."
        return MatchStatistic(
            name=name,
            value=len(contributing_facts),
            explanation=StatisticExplanation(
                contributing_event_ids=event_ids,
                contributing_fact_refs=fact_refs,
                rule_ids=rule_ids,
                rule_names=rule_names,
                reason=reason,
                derivation_path=("football_rules_engine", "filter_matching_facts", f"statistic:{name.value}"),
            ),
        )


def _normalized_event_type(fact: DerivedFootballFact) -> str | None:
    value = fact.attributes.get("normalized_event_type")
    return value if isinstance(value, str) else None


def _fact_ref(fact: DerivedFootballFact) -> str:
    return f"{fact.explanation.rule_id}:{fact.event_id}:{fact.category.value}"


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)
