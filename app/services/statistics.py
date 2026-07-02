from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.football.rules import ProviderNeutralEvent
from app.domain.football.statistics import (
    MatchStatisticsCalculator,
    PlayerStatisticsCalculator,
    StatisticExplanationDetail,
    StatisticName,
    StatisticScope,
    TeamStatisticsCalculator,
)
from app.models.event import Event
from app.models.match import Match
from app.schemas.statistics import (
    MatchStatisticResponse,
    MatchStatisticsResponse,
    PlayerStatisticResponse,
    PlayerStatisticsResponse,
    StatisticExplanationResponse,
    TeamStatisticResponse,
    TeamStatisticsResponse,
)


class MatchNotFoundError(ValueError):
    pass


class StatisticExplanationNotFoundError(ValueError):
    pass


class StatisticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.match_calculator = MatchStatisticsCalculator.with_default_rules()
        self.team_calculator = TeamStatisticsCalculator.with_default_rules()
        self.player_calculator = PlayerStatisticsCalculator.with_default_rules()

    async def get_match_statistics(self, match_id: UUID) -> MatchStatisticsResponse:
        events = await self._events_for_match(match_id)
        if not events:
            return MatchStatisticsResponse(match_id=str(match_id), statistics=[])
        summary = self.match_calculator.calculate(events)
        return MatchStatisticsResponse(
            match_id=str(match_id),
            statistics=[
                MatchStatisticResponse(
                    name=statistic.name,
                    value=statistic.value,
                    explanation=_explanation_response(statistic.explain()),
                )
                for statistic in summary.statistics
            ],
        )

    async def get_team_statistics(self, match_id: UUID) -> TeamStatisticsResponse:
        events = await self._events_for_match(match_id)
        if not events:
            return TeamStatisticsResponse(match_id=str(match_id), statistics=[])
        summary = self.team_calculator.calculate(events)
        return TeamStatisticsResponse(
            match_id=str(match_id),
            statistics=[
                TeamStatisticResponse(
                    team_id=statistic.team_id,
                    name=statistic.name,
                    value=statistic.value,
                    explanation=_explanation_response(statistic.explain()),
                )
                for statistic in summary.statistics
            ],
        )

    async def get_player_statistics(self, match_id: UUID) -> PlayerStatisticsResponse:
        events = await self._events_for_match(match_id)
        if not events:
            return PlayerStatisticsResponse(match_id=str(match_id), statistics=[])
        summary = self.player_calculator.calculate(events)
        return PlayerStatisticsResponse(
            match_id=str(match_id),
            statistics=[
                PlayerStatisticResponse(
                    player_id=statistic.player_id,
                    name=statistic.name,
                    value=statistic.value,
                    explanation=_explanation_response(statistic.explain()),
                )
                for statistic in summary.statistics
            ],
        )

    async def explain_statistic(
        self,
        *,
        match_id: UUID,
        scope: StatisticScope,
        name: StatisticName,
        team_id: str | None = None,
        player_id: str | None = None,
    ) -> StatisticExplanationResponse:
        events = await self._events_for_match(match_id)
        if not events:
            raise StatisticExplanationNotFoundError("Statistic explanation not found")

        detail: StatisticExplanationDetail | None = None
        if scope == StatisticScope.MATCH:
            detail = self.match_calculator.calculate(events).explain(name)
        elif scope == StatisticScope.TEAM and team_id:
            detail = self.team_calculator.calculate(events).explain(team_id, name)
        elif scope == StatisticScope.PLAYER and player_id:
            detail = self.player_calculator.calculate(events).explain(player_id, name)

        if detail is None:
            raise StatisticExplanationNotFoundError("Statistic explanation not found")
        return _explanation_response(detail)

    async def _events_for_match(self, match_id: UUID) -> list[ProviderNeutralEvent]:
        match = await self.session.get(Match, match_id)
        if match is None:
            raise MatchNotFoundError("Match not found")

        result = await self.session.execute(
            select(Event).where(Event.match_id == match_id).order_by(Event.created_at.asc())
        )
        return [_event_to_provider_neutral(event) for event in result.scalars().all()]


def _event_to_provider_neutral(event: Event) -> ProviderNeutralEvent:
    raw_payload = event.raw_payload if isinstance(event.raw_payload, dict) else {}
    return ProviderNeutralEvent(
        id=str(event.id) if event.id is not None else None,
        event_type=event.event_type,
        team_id=str(event.team_id) if event.team_id is not None else None,
        player_id=str(event.player_id) if event.player_id is not None else None,
        assist_player_id=_string_or_none(raw_payload.get("assist_player_id")),
        period=event.period.value if hasattr(event.period, "value") else event.period,
        minute=event.minute,
        second=event.second,
        notes=event.notes,
        raw_payload=event.raw_payload,
    )


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _explanation_response(detail: StatisticExplanationDetail) -> StatisticExplanationResponse:
    return StatisticExplanationResponse(
        statistic_name=detail.statistic_name,
        value=detail.value,
        scope=detail.scope,
        team_id=detail.team_id,
        player_id=detail.player_id,
        contributing_event_ids=list(detail.contributing_event_ids),
        contributing_fact_refs=list(detail.contributing_fact_refs),
        rule_ids=list(detail.rule_ids),
        rule_names=list(detail.rule_names),
        reason=detail.reason,
        derivation_path=list(detail.derivation_path),
        incomplete_attribution_notes=list(detail.incomplete_attribution_notes),
    )
