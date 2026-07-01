from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.match import MatchStatus
from app.models.match import Match
from app.repositories.match import MatchRepository
from app.schemas.match import MatchCreate, MatchResponse, MatchUpdate


class MatchService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = MatchRepository(session)

    async def list_matches(self) -> list[MatchResponse]:
        rows = await self.repository.list_with_team_names()
        return [self._response_with_team_names(match, home_team_name, away_team_name) for match, home_team_name, away_team_name in rows]

    async def get_match(self, match_id: UUID) -> MatchResponse | None:
        row = await self.repository.get_with_team_names(match_id)
        if row is None:
            return None
        match, home_team_name, away_team_name = row
        return self._response_with_team_names(match, home_team_name, away_team_name)

    async def create_match(self, data: MatchCreate) -> MatchResponse:
        if data.home_team_id == data.away_team_id:
            raise ValueError("home_team_id and away_team_id must differ")

        match = Match(
            competition_id=data.competition_id,
            season_id=data.season_id,
            home_team_id=data.home_team_id,
            away_team_id=data.away_team_id,
            kickoff_datetime=data.kickoff_datetime,
            venue=data.venue,
            status=data.status,
            analyst_notes=data.analyst_notes,
        )
        match = await self.repository.create(match)
        return await self.get_match(match.id) or MatchResponse.model_validate(match)

    async def update_match(self, match_id: UUID, data: MatchUpdate) -> MatchResponse | None:
        match = await self.repository.get(match_id)
        if match is None:
            return None

        if data.competition_id is not None:
            match.competition_id = data.competition_id
        if data.season_id is not None:
            match.season_id = data.season_id
        if data.home_team_id is not None:
            match.home_team_id = data.home_team_id
        if data.away_team_id is not None:
            match.away_team_id = data.away_team_id
        if match.home_team_id == match.away_team_id:
            raise ValueError("home_team_id and away_team_id must differ")
        if data.kickoff_datetime is not None:
            match.kickoff_datetime = data.kickoff_datetime
        if data.venue is not None:
            match.venue = data.venue
        if data.status is not None:
            match.status = data.status
        if data.analyst_notes is not None:
            match.analyst_notes = data.analyst_notes

        match = await self.repository.update(match)
        return await self.get_match(match.id) or MatchResponse.model_validate(match)

    async def delete_match(self, match_id: UUID) -> bool:
        match = await self.repository.get(match_id)
        if match is None:
            return False

        await self.repository.delete(match)
        return True

    def _response_with_team_names(
        self,
        match: Match,
        home_team_name: str | None,
        away_team_name: str | None,
    ) -> MatchResponse:
        response = MatchResponse.model_validate(match)
        response.home_team_name = home_team_name
        response.away_team_name = away_team_name
        return response
