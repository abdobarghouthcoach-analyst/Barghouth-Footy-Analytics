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


@dataclass(frozen=True)
class StatisticExplanation:
    contributing_event_ids: tuple[str, ...]
    contributing_fact_refs: tuple[str, ...]
    rule_ids: tuple[str, ...]
    rule_names: tuple[str, ...]
    reason: str
    derivation_path: tuple[str, ...]


@dataclass(frozen=True)
class MatchStatistic:
    name: StatisticName
    value: int
    explanation: StatisticExplanation


@dataclass(frozen=True)
class MatchStatisticsSummary:
    statistics: tuple[MatchStatistic, ...]

    def get(self, name: StatisticName) -> MatchStatistic | None:
        return next((statistic for statistic in self.statistics if statistic.name == name), None)


@dataclass(frozen=True)
class TeamStatistic:
    team_id: str
    name: StatisticName
    value: int
    explanation: StatisticExplanation


@dataclass(frozen=True)
class TeamStatisticsSummary:
    statistics: tuple[TeamStatistic, ...]

    def get(self, team_id: str, name: StatisticName) -> TeamStatistic | None:
        return next(
            (statistic for statistic in self.statistics if statistic.team_id == team_id and statistic.name == name),
            None,
        )


@dataclass(frozen=True)
class PlayerStatistic:
    player_id: str
    name: StatisticName
    value: int
    explanation: StatisticExplanation


@dataclass(frozen=True)
class PlayerStatisticsSummary:
    statistics: tuple[PlayerStatistic, ...]

    def get(self, player_id: str, name: StatisticName) -> PlayerStatistic | None:
        return next(
            (statistic for statistic in self.statistics if statistic.player_id == player_id and statistic.name == name),
            None,
        )
