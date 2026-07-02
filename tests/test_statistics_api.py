import ast
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.v1.statistics import (
    explain_statistic,
    get_match_statistics,
    get_player_statistics,
    get_team_statistics,
)
from app.domain.event import EventSource, SourceProvider
from app.domain.football.statistics import StatisticName, StatisticScope
from app.models.event import Event
from app.models.match import Match
from app.services.statistics import StatisticsService


MATCH_ID = UUID("11111111-1111-1111-1111-111111111111")
HOME_TEAM_ID = UUID("22222222-2222-2222-2222-222222222222")
PLAYER_ID = UUID("33333333-3333-3333-3333-333333333333")
ASSIST_PLAYER_ID = UUID("44444444-4444-4444-4444-444444444444")
MISSING_MATCH_ID = UUID("99999999-9999-9999-9999-999999999999")


class FakeStatisticsSession:
    def __init__(self, events: list[Event] | None = None, *, match_exists: bool = True) -> None:
        self.events = events or []
        self.match_exists = match_exists
        self.match = Match(
            id=MATCH_ID,
            competition_id=UUID(int=1),
            season_id=UUID(int=2),
            home_team_id=HOME_TEAM_ID,
            away_team_id=UUID(int=4),
            kickoff_datetime=datetime.now(timezone.utc),
            venue="Test Ground",
        )

    async def get(self, model, item_id):
        if model is Match and item_id == MATCH_ID and self.match_exists:
            return self.match
        return None

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        if entity is Event:
            return FakeResult(self.events)
        return FakeResult([])


class FakeResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


def event(
    event_id: str,
    event_type: str,
    *,
    team_id: UUID | None = HOME_TEAM_ID,
    player_id: UUID | None = PLAYER_ID,
    raw_payload: dict | None = None,
) -> Event:
    now = datetime.now(timezone.utc)
    item = Event(
        id=UUID(event_id),
        match_id=MATCH_ID,
        team_id=team_id,
        player_id=player_id,
        event_type=event_type,
        minute=1,
        second=0,
        source_provider=SourceProvider.MANUAL,
        source=EventSource.MANUAL,
        raw_payload=raw_payload,
    )
    item.created_at = now
    item.updated_at = now
    return item


@pytest.mark.asyncio
async def test_api_returns_match_statistics_derived_from_events():
    session = FakeStatisticsSession(
        [
            event("00000000-0000-0000-0000-000000000001", "goal"),
            event("00000000-0000-0000-0000-000000000002", "shot_on_goal"),
        ]
    )

    response = await get_match_statistics(MATCH_ID, service=StatisticsService(session))  # type: ignore[arg-type]

    stats = {stat.name: stat.value for stat in response.statistics}
    assert stats[StatisticName.GOALS] == 1
    assert stats[StatisticName.SHOTS] == 1
    assert stats[StatisticName.SHOTS_ON_TARGET] == 1


@pytest.mark.asyncio
async def test_api_returns_team_statistics_derived_from_events():
    session = FakeStatisticsSession(
        [
            event("00000000-0000-0000-0000-000000000001", "goal", team_id=HOME_TEAM_ID),
            event("00000000-0000-0000-0000-000000000002", "shot", team_id=None),
        ]
    )

    response = await get_team_statistics(MATCH_ID, service=StatisticsService(session))  # type: ignore[arg-type]

    home_stats = {stat.name: stat for stat in response.statistics if stat.team_id == str(HOME_TEAM_ID)}
    assert home_stats[StatisticName.GOALS].value == 1
    assert home_stats[StatisticName.SHOTS].value == 0
    assert "missing" in home_stats[StatisticName.SHOTS].explanation.incomplete_attribution_notes[0]


@pytest.mark.asyncio
async def test_api_returns_player_statistics_derived_from_events():
    session = FakeStatisticsSession(
        [
            event(
                "00000000-0000-0000-0000-000000000001",
                "goal",
                player_id=PLAYER_ID,
                raw_payload={"assist_player_id": str(ASSIST_PLAYER_ID)},
            ),
            event("00000000-0000-0000-0000-000000000002", "yellow_card", player_id=PLAYER_ID),
        ]
    )

    response = await get_player_statistics(MATCH_ID, service=StatisticsService(session))  # type: ignore[arg-type]

    player_stats = {stat.name: stat for stat in response.statistics if stat.player_id == str(PLAYER_ID)}
    assist_stats = {stat.name: stat for stat in response.statistics if stat.player_id == str(ASSIST_PLAYER_ID)}
    assert player_stats[StatisticName.GOALS].value == 1
    assert player_stats[StatisticName.YELLOW_CARDS].value == 1
    assert assist_stats[StatisticName.ASSISTS].value == 1


@pytest.mark.asyncio
async def test_api_returns_explanation_detail():
    shot = event("00000000-0000-0000-0000-000000000001", "shot_on_goal")
    session = FakeStatisticsSession([shot])

    response = await explain_statistic(
        MATCH_ID,
        scope=StatisticScope.MATCH,
        name=StatisticName.SHOTS_ON_TARGET,
        service=StatisticsService(session),  # type: ignore[arg-type]
    )

    assert response.statistic_name == StatisticName.SHOTS_ON_TARGET
    assert response.scope == StatisticScope.MATCH
    assert response.contributing_event_ids == [str(shot.id)]
    assert response.rule_ids == ["football.shot.recognition.v1"]


@pytest.mark.asyncio
async def test_empty_match_returns_empty_statistics():
    session = FakeStatisticsSession([])

    response = await get_match_statistics(MATCH_ID, service=StatisticsService(session))  # type: ignore[arg-type]

    assert response.statistics == []


@pytest.mark.asyncio
async def test_missing_match_returns_404():
    session = FakeStatisticsSession([], match_exists=False)

    with pytest.raises(HTTPException) as exc:
        await get_match_statistics(MISSING_MATCH_ID, service=StatisticsService(session))  # type: ignore[arg-type]

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_missing_attribution_does_not_fabricate_scoped_stats():
    session = FakeStatisticsSession(
        [
            event("00000000-0000-0000-0000-000000000001", "goal", team_id=None, player_id=None),
        ]
    )

    team_response = await get_team_statistics(MATCH_ID, service=StatisticsService(session))  # type: ignore[arg-type]
    player_response = await get_player_statistics(MATCH_ID, service=StatisticsService(session))  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc:
        await explain_statistic(
            MATCH_ID,
            scope=StatisticScope.TEAM,
            name=StatisticName.GOALS,
            team_id=str(HOME_TEAM_ID),
            service=StatisticsService(session),  # type: ignore[arg-type]
        )

    assert team_response.statistics == []
    assert player_response.statistics == []
    assert exc.value.status_code == 404


def test_statistics_api_adds_no_persistence_or_domain_dependency_leaks():
    for path in (
        Path("app/models/statistic.py"),
        Path("app/models/match_statistic.py"),
        Path("app/models/team_statistic.py"),
        Path("app/models/player_statistic.py"),
    ):
        assert not path.exists()

    forbidden_import_prefixes = ("app.api", "app.models", "app.repositories", "app.services", "fastapi", "sqlalchemy")
    for root in (Path("app/domain/football/statistics"), Path("app/domain/football/rules")):
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        assert not module.startswith(forbidden_import_prefixes), f"{path} imports {module}"
                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    if module:
                        assert not module.startswith(forbidden_import_prefixes), f"{path} imports {module}"
