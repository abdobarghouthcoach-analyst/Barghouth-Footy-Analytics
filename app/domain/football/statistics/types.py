from dataclasses import dataclass
from enum import Enum


class StatisticName(str, Enum):
    GOALS = "goals"
    ASSISTS = "assists"
    SHOTS = "shots"
    SHOTS_ON_TARGET = "shots_on_target"
    CORNERS = "corners"
    FOULS = "fouls"
    OFFSIDES = "offsides"
    YELLOW_CARDS = "yellow_cards"
    RED_CARDS = "red_cards"


class StatisticScope(str, Enum):
    MATCH = "match"
    TEAM = "team"
    PLAYER = "player"


@dataclass(frozen=True)
class StatisticExplanation:
    statistic_name: StatisticName
    value: int
    scope: StatisticScope
    team_id: str | None
    player_id: str | None
    contributing_event_ids: tuple[str, ...]
    contributing_fact_refs: tuple[str, ...]
    rule_ids: tuple[str, ...]
    rule_names: tuple[str, ...]
    reason: str
    derivation_path: tuple[str, ...]
    incomplete_attribution_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatisticExplanationDetail:
    statistic_name: StatisticName
    value: int
    scope: StatisticScope
    team_id: str | None
    player_id: str | None
    contributing_event_ids: tuple[str, ...]
    contributing_fact_refs: tuple[str, ...]
    rule_ids: tuple[str, ...]
    rule_names: tuple[str, ...]
    reason: str
    derivation_path: tuple[str, ...]
    incomplete_attribution_notes: tuple[str, ...]


@dataclass(frozen=True)
class MatchStatistic:
    name: StatisticName
    value: int
    explanation: StatisticExplanation

    def explain(self) -> StatisticExplanationDetail:
        return _detail(self.explanation)


@dataclass(frozen=True)
class MatchStatisticsSummary:
    statistics: tuple[MatchStatistic, ...]

    def get(self, name: StatisticName) -> MatchStatistic | None:
        return next((statistic for statistic in self.statistics if statistic.name == name), None)

    def explain(self, name: StatisticName) -> StatisticExplanationDetail | None:
        statistic = self.get(name)
        return statistic.explain() if statistic else None


@dataclass(frozen=True)
class TeamStatistic:
    team_id: str
    name: StatisticName
    value: int
    explanation: StatisticExplanation

    def explain(self) -> StatisticExplanationDetail:
        return _detail(self.explanation)


@dataclass(frozen=True)
class TeamStatisticsSummary:
    statistics: tuple[TeamStatistic, ...]

    def get(self, team_id: str, name: StatisticName) -> TeamStatistic | None:
        return next(
            (statistic for statistic in self.statistics if statistic.team_id == team_id and statistic.name == name),
            None,
        )

    def explain(self, team_id: str, name: StatisticName) -> StatisticExplanationDetail | None:
        statistic = self.get(team_id, name)
        return statistic.explain() if statistic else None


@dataclass(frozen=True)
class PlayerStatistic:
    player_id: str
    name: StatisticName
    value: int
    explanation: StatisticExplanation

    def explain(self) -> StatisticExplanationDetail:
        return _detail(self.explanation)


@dataclass(frozen=True)
class PlayerStatisticsSummary:
    statistics: tuple[PlayerStatistic, ...]

    def get(self, player_id: str, name: StatisticName) -> PlayerStatistic | None:
        return next(
            (statistic for statistic in self.statistics if statistic.player_id == player_id and statistic.name == name),
            None,
        )

    def explain(self, player_id: str, name: StatisticName) -> StatisticExplanationDetail | None:
        statistic = self.get(player_id, name)
        return statistic.explain() if statistic else None


def _detail(explanation: StatisticExplanation) -> StatisticExplanationDetail:
    return StatisticExplanationDetail(
        statistic_name=explanation.statistic_name,
        value=explanation.value,
        scope=explanation.scope,
        team_id=explanation.team_id,
        player_id=explanation.player_id,
        contributing_event_ids=explanation.contributing_event_ids,
        contributing_fact_refs=explanation.contributing_fact_refs,
        rule_ids=explanation.rule_ids,
        rule_names=explanation.rule_names,
        reason=explanation.reason,
        derivation_path=explanation.derivation_path,
        incomplete_attribution_notes=explanation.incomplete_attribution_notes,
    )
