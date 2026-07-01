from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.domain.import_job import ImportProvider, ImportStatus
from app.models.import_job import ImportJob
from app.models.match import Match
from app.services.match import MatchService


MATCH_ID = UUID("11111111-1111-1111-1111-111111111111")
IMPORT_JOB_ID = UUID("22222222-2222-2222-2222-222222222222")


class FakeMatchSession:
    def __init__(self) -> None:
        self.match = Match(
            id=MATCH_ID,
            competition_id=UUID(int=1),
            season_id=UUID(int=2),
            home_team_id=UUID(int=3),
            away_team_id=UUID(int=4),
            kickoff_datetime=datetime.now(timezone.utc),
            venue="Test Ground",
        )
        self.import_jobs = [
            ImportJob(
                id=IMPORT_JOB_ID,
                match_id=MATCH_ID,
                provider=ImportProvider.VEO,
                status=ImportStatus.COMPLETED,
                original_filename="veo.zip",
            )
        ]
        self.deleted_match: Match | None = None
        self.commit_count = 0

    async def get(self, model, item_id):
        if model is Match and item_id == MATCH_ID:
            return self.match
        return None

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        if entity is ImportJob:
            return FakeResult(self.import_jobs)
        return FakeResult([])

    async def delete(self, item):
        if isinstance(item, Match):
            self.deleted_match = item
            return
        raise TypeError(f"Unsupported item type: {type(item)!r}")

    async def commit(self):
        self.commit_count += 1


class FakeResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


@pytest.mark.asyncio
async def test_delete_match_removes_import_storage_and_deletes_match(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "import_storage_root", str(tmp_path / "imports"))
    job_dir = tmp_path / "imports" / str(MATCH_ID) / str(IMPORT_JOB_ID)
    extracted_dir = job_dir / "extracted"
    extracted_dir.mkdir(parents=True)
    (job_dir / "original.zip").write_bytes(b"zip")
    (extracted_dir / "clip.mp4").write_bytes(b"video")
    session = FakeMatchSession()
    service = MatchService(session)  # type: ignore[arg-type]

    deleted = await service.delete_match(MATCH_ID)

    assert deleted is True
    assert session.deleted_match is session.match
    assert session.commit_count == 1
    assert not job_dir.exists()
