from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.competition import CompetitionLevel, CompetitionType
from app.models.competition import Competition
from app.schemas.competition import CompetitionCreate, CompetitionUpdate
from app.services.competition import CompetitionService


@pytest.fixture
def competition_service() -> CompetitionService:
    mock_session = Mock()
    service = CompetitionService(session=mock_session)
    service.repository = Mock()
    return service


def make_competition(id_value, name="Premier League", country="England", level=CompetitionLevel.FIRST, competition_type=CompetitionType.LEAGUE):
    competition = Competition(
        name=name,
        country=country,
        level=level,
        competition_type=competition_type,
    )
    competition.id = id_value
    return competition


@pytest.mark.asyncio
async def test_list_competitions(competition_service: CompetitionService):
    competition = make_competition("11111111-1111-1111-1111-111111111111")
    competition_service.repository.list = AsyncMock(return_value=[competition])

    result = await competition_service.list_competitions()

    assert len(result) == 1
    assert result[0].id == competition.id
    assert result[0].name == competition.name


@pytest.mark.asyncio
async def test_get_competition_found(competition_service: CompetitionService):
    competition = make_competition("22222222-2222-2222-2222-222222222222")
    competition_service.repository.get = AsyncMock(return_value=competition)

    result = await competition_service.get_competition(competition.id)

    assert result is not None
    assert result.id == competition.id
    assert result.name == competition.name


@pytest.mark.asyncio
async def test_get_competition_not_found(competition_service: CompetitionService):
    competition_service.repository.get = AsyncMock(return_value=None)

    result = await competition_service.get_competition("33333333-3333-3333-3333-333333333333")

    assert result is None


@pytest.mark.asyncio
async def test_create_competition(competition_service: CompetitionService):
    competition = make_competition("44444444-4444-4444-4444-444444444444")
    competition_service.repository.create = AsyncMock(return_value=competition)

    data = CompetitionCreate(
        name="Bundesliga",
        country="Germany",
        level=CompetitionLevel.FIRST,
        competition_type=CompetitionType.LEAGUE,
    )
    result = await competition_service.create_competition(data)

    assert result.id == competition.id
    assert result.name == "Bundesliga"
    assert result.level == CompetitionLevel.FIRST
    assert result.competition_type == CompetitionType.LEAGUE


@pytest.mark.asyncio
async def test_update_competition(competition_service: CompetitionService):
    competition = make_competition("55555555-5555-5555-5555-555555555555")
    competition_service.repository.get = AsyncMock(return_value=competition)
    competition_service.repository.update = AsyncMock(return_value=competition)

    update_payload = CompetitionUpdate(name="Serie A", country="Italy", level=CompetitionLevel.FIRST, competition_type=CompetitionType.LEAGUE)
    result = await competition_service.update_competition(competition.id, update_payload)

    assert result is not None
    assert result.name == "Serie A"
    assert result.country == "Italy"
    assert result.level == CompetitionLevel.FIRST
    assert result.competition_type == CompetitionType.LEAGUE


@pytest.mark.asyncio
async def test_delete_competition_not_found(competition_service: CompetitionService):
    competition_service.repository.get = AsyncMock(return_value=None)

    result = await competition_service.delete_competition("66666666-6666-6666-6666-666666666666")

    assert result is False


def test_competition_create_schema_rejects_invalid_enum():
    with pytest.raises(ValueError):
        CompetitionCreate(
            name="Invalid",
            country="Nowhere",
            level="third",  # invalid enum value
            competition_type=CompetitionType.LEAGUE,
        )


def test_competition_update_schema_rejects_invalid_enum():
    with pytest.raises(ValueError):
        CompetitionUpdate(level="third")


@pytest.mark.asyncio
async def test_delete_competition_success(competition_service: CompetitionService):
    competition = make_competition("77777777-7777-7777-7777-777777777777")
    competition_service.repository.get = AsyncMock(return_value=competition)
    competition_service.repository.delete = AsyncMock(return_value=None)

    result = await competition_service.delete_competition(competition.id)

    assert result is True
