import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate
from app.services.team import TeamService


@pytest.fixture
def team_service() -> TeamService:
    mock_session = Mock()
    service = TeamService(session=mock_session)
    service.repository = Mock()
    return service


def make_team(
    id_value,
    name="First Team",
    short_name="FT",
    city="London",
    country="England",
    stadium="Stadium",
    colours="Blue / White",
    badge_url="https://example.com/badge.png",
    club_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
):
    team = Team(
        name=name,
        short_name=short_name,
        city=city,
        country=country,
        stadium=stadium,
        colours=colours,
        badge_url=badge_url,
        club_id=club_id,
    )
    team.id = uuid.UUID(id_value)
    team.created_at = datetime.now(timezone.utc)
    team.updated_at = team.created_at
    return team


@pytest.mark.asyncio
async def test_list_teams(team_service: TeamService):
    team = make_team("22222222-2222-2222-2222-222222222222")
    team_service.repository.list = AsyncMock(return_value=[team])

    result = await team_service.list_teams()

    assert len(result) == 1
    assert result[0].id == team.id
    assert result[0].name == team.name


@pytest.mark.asyncio
async def test_get_team_found(team_service: TeamService):
    team = make_team("33333333-3333-3333-3333-333333333333")
    team_service.repository.get = AsyncMock(return_value=team)

    result = await team_service.get_team(team.id)

    assert result is not None
    assert result.id == team.id
    assert result.name == team.name


@pytest.mark.asyncio
async def test_get_team_not_found(team_service: TeamService):
    team_service.repository.get = AsyncMock(return_value=None)

    result = await team_service.get_team(uuid.UUID("44444444-4444-4444-4444-444444444444"))

    assert result is None


@pytest.mark.asyncio
async def test_create_team(team_service: TeamService):
    team = make_team("55555555-5555-5555-5555-555555555555")
    team_service.repository.create = AsyncMock(return_value=team)

    data = TeamCreate(
        name="First Team",
        short_name="FT",
        city="London",
        country="England",
        stadium="Stadium",
        colours="Blue / White",
        badge_url="https://example.com/badge.png",
        club_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )
    result = await team_service.create_team(data)

    assert result.id == team.id
    assert result.name == "First Team"


@pytest.mark.asyncio
async def test_update_team(team_service: TeamService):
    team = make_team("66666666-6666-6666-6666-666666666666")
    team_service.repository.get = AsyncMock(return_value=team)
    team_service.repository.update = AsyncMock(return_value=team)

    result = await team_service.update_team(
        team.id,
        TeamUpdate(name="Updated Team", city="Liverpool"),
    )

    assert result is not None
    assert result.name == "Updated Team"
    assert result.city == "Liverpool"


@pytest.mark.asyncio
async def test_delete_team_not_found(team_service: TeamService):
    team_service.repository.get = AsyncMock(return_value=None)

    result = await team_service.delete_team(uuid.UUID("77777777-7777-7777-7777-777777777777"))

    assert result is False


@pytest.mark.asyncio
async def test_delete_team_success(team_service: TeamService):
    team = make_team("88888888-8888-8888-8888-888888888888")
    team_service.repository.get = AsyncMock(return_value=team)
    team_service.repository.delete = AsyncMock(return_value=None)

    result = await team_service.delete_team(team.id)

    assert result is True
