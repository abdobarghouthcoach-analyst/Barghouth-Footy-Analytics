from pydantic import BaseModel

from app.domain.football.statistics import StatisticName, StatisticScope


class StatisticExplanationResponse(BaseModel):
    statistic_name: StatisticName
    value: int
    scope: StatisticScope
    team_id: str | None = None
    player_id: str | None = None
    contributing_event_ids: list[str]
    contributing_fact_refs: list[str]
    rule_ids: list[str]
    rule_names: list[str]
    reason: str
    derivation_path: list[str]
    incomplete_attribution_notes: list[str]


class MatchStatisticResponse(BaseModel):
    name: StatisticName
    value: int
    explanation: StatisticExplanationResponse


class TeamStatisticResponse(BaseModel):
    team_id: str
    name: StatisticName
    value: int
    explanation: StatisticExplanationResponse


class PlayerStatisticResponse(BaseModel):
    player_id: str
    name: StatisticName
    value: int
    explanation: StatisticExplanationResponse


class MatchStatisticsResponse(BaseModel):
    match_id: str
    statistics: list[MatchStatisticResponse]


class TeamStatisticsResponse(BaseModel):
    match_id: str
    statistics: list[TeamStatisticResponse]


class PlayerStatisticsResponse(BaseModel):
    match_id: str
    statistics: list[PlayerStatisticResponse]
