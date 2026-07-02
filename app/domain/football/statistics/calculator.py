from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable

from app.domain.football.rules import FactCategory, FootballRulesEngine, ProviderNeutralEvent
from app.domain.football.rules.types import DerivedFootballFact, FootballRuleResult
from app.domain.football.statistics.types import (
    MatchStatistic,
    MatchStatisticsSummary,
    PlayerStatistic,
    PlayerStatisticsSummary,
    StatisticExplanation,
    StatisticName,
    TeamStatistic,
    TeamStatisticsSummary,
)


FactPredicate = Callable[[DerivedFootballFact], bool]


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
        predicate: FactPredicate,
    ) -> MatchStatistic:
        contributing_facts = tuple(fact for fact in facts if predicate(fact))
        return MatchStatistic(
            name=name,
            value=len(contributing_facts),
            explanation=_statistic_explanation(name=name, facts=contributing_facts, derivation_scope="match"),
        )


@dataclass(frozen=True)
class TeamStatisticsCalculator:
    rules_engine: FootballRulesEngine

    @classmethod
    def with_default_rules(cls) -> "TeamStatisticsCalculator":
        return cls(rules_engine=FootballRulesEngine.with_default_rules())

    def calculate(self, events: Iterable[ProviderNeutralEvent]) -> TeamStatisticsSummary:
        return self.calculate_from_rule_results(self.rules_engine.apply(events))

    def calculate_from_rule_results(self, rule_results: Iterable[FootballRuleResult]) -> TeamStatisticsSummary:
        facts = tuple(fact for result in rule_results for fact in result.facts if fact.value is True)
        team_ids = _team_ids(facts)
        statistics: list[TeamStatistic] = []
        for team_id in team_ids:
            team_facts = tuple(fact for fact in facts if _team_id(fact) == team_id)
            for name, predicate in _statistic_predicates():
                contributing_facts = tuple(fact for fact in team_facts if predicate(fact))
                statistics.append(
                    TeamStatistic(
                        team_id=team_id,
                        name=name,
                        value=len(contributing_facts),
                        explanation=_statistic_explanation(
                            name=name,
                            facts=contributing_facts,
                            derivation_scope="team",
                            team_id=team_id,
                        ),
                    )
                )
        return TeamStatisticsSummary(statistics=tuple(statistics))


@dataclass(frozen=True)
class PlayerStatisticsCalculator:
    rules_engine: FootballRulesEngine

    @classmethod
    def with_default_rules(cls) -> "PlayerStatisticsCalculator":
        return cls(rules_engine=FootballRulesEngine.with_default_rules())

    def calculate(self, events: Iterable[ProviderNeutralEvent]) -> PlayerStatisticsSummary:
        return self.calculate_from_rule_results(self.rules_engine.apply(events))

    def calculate_from_rule_results(self, rule_results: Iterable[FootballRuleResult]) -> PlayerStatisticsSummary:
        facts = tuple(fact for result in rule_results for fact in result.facts if fact.value is True)
        player_ids = _player_ids(facts)
        statistics: list[PlayerStatistic] = []
        for player_id in player_ids:
            player_facts = tuple(fact for fact in facts if _player_id(fact) == player_id)
            for name, predicate in _player_statistic_predicates():
                contributing_facts = tuple(fact for fact in player_facts if predicate(fact))
                statistics.append(
                    PlayerStatistic(
                        player_id=player_id,
                        name=name,
                        value=len(contributing_facts),
                        explanation=_statistic_explanation(
                            name=name,
                            facts=contributing_facts,
                            derivation_scope="player",
                            player_id=player_id,
                        ),
                    )
                )

            assist_facts = tuple(
                fact
                for fact in facts
                if fact.category == FactCategory.GOAL and _assist_player_id(fact) == player_id
            )
            if assist_facts:
                statistics.append(
                    PlayerStatistic(
                        player_id=player_id,
                        name=StatisticName.ASSISTS,
                        value=len(assist_facts),
                        explanation=_statistic_explanation(
                            name=StatisticName.ASSISTS,
                            facts=assist_facts,
                            derivation_scope="player",
                            player_id=player_id,
                        ),
                    )
                )
        return PlayerStatisticsSummary(statistics=tuple(statistics))


def _statistic_predicates() -> tuple[tuple[StatisticName, FactPredicate], ...]:
    return (
        (StatisticName.GOALS, lambda fact: fact.category == FactCategory.GOAL),
        (StatisticName.SHOTS, lambda fact: fact.category == FactCategory.SHOT),
        (
            StatisticName.SHOTS_ON_TARGET,
            lambda fact: fact.category == FactCategory.SHOT and _normalized_event_type(fact) == "shot_on_goal",
        ),
        (StatisticName.CORNERS, lambda fact: fact.category == FactCategory.CORNER),
        (StatisticName.FOULS, lambda fact: fact.category == FactCategory.FOUL),
        (StatisticName.OFFSIDES, lambda fact: fact.category == FactCategory.OFFSIDE),
        (
            StatisticName.YELLOW_CARDS,
            lambda fact: fact.category == FactCategory.CARD and _normalized_event_type(fact) == "yellow_card",
        ),
        (
            StatisticName.RED_CARDS,
            lambda fact: fact.category == FactCategory.CARD and _normalized_event_type(fact) == "red_card",
        ),
    )


def _player_statistic_predicates() -> tuple[tuple[StatisticName, FactPredicate], ...]:
    return (
        (StatisticName.GOALS, lambda fact: fact.category == FactCategory.GOAL),
        (StatisticName.SHOTS, lambda fact: fact.category == FactCategory.SHOT),
        (
            StatisticName.YELLOW_CARDS,
            lambda fact: fact.category == FactCategory.CARD and _normalized_event_type(fact) == "yellow_card",
        ),
        (
            StatisticName.RED_CARDS,
            lambda fact: fact.category == FactCategory.CARD and _normalized_event_type(fact) == "red_card",
        ),
    )


def _statistic_explanation(
    *,
    name: StatisticName,
    facts: tuple[DerivedFootballFact, ...],
    derivation_scope: str,
    team_id: str | None = None,
    player_id: str | None = None,
) -> StatisticExplanation:
    event_ids = tuple(fact.event_id for fact in facts)
    fact_refs = tuple(_fact_ref(fact) for fact in facts)
    rule_ids = _unique(fact.explanation.rule_id for fact in facts)
    rule_names = _unique(fact.explanation.rule_name for fact in facts)
    reason = f"{name.value} is derived by counting matching football facts."
    derivation_path = ("football_rules_engine", "filter_matching_facts", f"statistic:{name.value}")
    if team_id is not None:
        reason = f"{name.value} for team {team_id} is derived by counting matching team-attributed football facts."
        derivation_path = (
            "football_rules_engine",
            "filter_team_attributed_facts",
            f"team:{team_id}",
            f"statistic:{name.value}",
        )
    elif player_id is not None:
        reason = f"{name.value} for player {player_id} is derived by counting matching player-attributed football facts."
        derivation_path = (
            "football_rules_engine",
            "filter_player_attributed_facts",
            f"player:{player_id}",
            f"statistic:{name.value}",
        )
    elif derivation_scope != "match":
        derivation_path = ("football_rules_engine", f"scope:{derivation_scope}", f"statistic:{name.value}")
    return StatisticExplanation(
        contributing_event_ids=event_ids,
        contributing_fact_refs=fact_refs,
        rule_ids=rule_ids,
        rule_names=rule_names,
        reason=reason,
        derivation_path=derivation_path,
    )


def _normalized_event_type(fact: DerivedFootballFact) -> str | None:
    value = fact.attributes.get("normalized_event_type")
    return value if isinstance(value, str) else None


def _team_id(fact: DerivedFootballFact) -> str | None:
    value = fact.attributes.get("team_id")
    return value if isinstance(value, str) and value.strip() else None


def _player_id(fact: DerivedFootballFact) -> str | None:
    value = fact.attributes.get("player_id")
    return value if isinstance(value, str) and value.strip() else None


def _assist_player_id(fact: DerivedFootballFact) -> str | None:
    value = fact.attributes.get("assist_player_id")
    return value if isinstance(value, str) and value.strip() else None


def _team_ids(facts: tuple[DerivedFootballFact, ...]) -> tuple[str, ...]:
    return _unique(team_id for fact in facts if (team_id := _team_id(fact)) is not None)


def _player_ids(facts: tuple[DerivedFootballFact, ...]) -> tuple[str, ...]:
    return _unique(
        player_id
        for fact in facts
        for player_id in (_player_id(fact), _assist_player_id(fact))
        if player_id is not None
    )


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
