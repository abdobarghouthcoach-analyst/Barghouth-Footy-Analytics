from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from app.domain.import_job import ImportProvider, ImportStatus
from app.schemas.import_job import ImportJobCreate, ImportJobUpdate
from app.services.import_job import ImportJobService


@pytest.fixture
def import_job_service() -> ImportJobService:
    service = ImportJobService(repository=Mock())
    return service


@pytest.mark.asyncio
async def test_create_import_job(import_job_service: ImportJobService):
    job = Mock()
    job.id = UUID(int=1)
    job.match_id = UUID(int=2)
    job.provider = ImportProvider.VEO
    job.filename = "game.zip"
    job.status = ImportStatus.CREATED
    job.started_at = None
    job.finished_at = None
    job.imported_events_count = 0
    job.warnings_count = 0
    job.error_message = None
    job.created_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()

    import_job_service.repository.create = AsyncMock(return_value=job)
    payload = ImportJobCreate(match_id=UUID(int=2), provider=ImportProvider.VEO, filename="game.zip")

    result = await import_job_service.create_import_job(payload)

    assert result.id == job.id
    assert result.provider == ImportProvider.VEO
    assert result.filename == "game.zip"


@pytest.mark.asyncio
async def test_get_import_job_found(import_job_service: ImportJobService):
    job = Mock()
    job.id = UUID(int=3)
    job.match_id = UUID(int=2)
    job.provider = ImportProvider.CSV
    job.filename = "stats.csv"
    job.status = ImportStatus.COMPLETED
    job.started_at = None
    job.finished_at = None
    job.imported_events_count = 1
    job.warnings_count = 0
    job.error_message = None
    job.created_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()

    import_job_service.repository.get_by_id = AsyncMock(return_value=job)

    result = await import_job_service.get_import_job(UUID(int=3))

    assert result is not None
    assert result.id == job.id
    assert result.status == ImportStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_import_job_not_found(import_job_service: ImportJobService):
    import_job_service.repository.get_by_id = AsyncMock(return_value=None)

    result = await import_job_service.get_import_job(UUID(int=4))

    assert result is None


@pytest.mark.asyncio
async def test_list_import_jobs(import_job_service: ImportJobService):
    job = Mock()
    job.id = UUID(int=5)
    job.match_id = UUID(int=2)
    job.provider = ImportProvider.OTHER
    job.filename = "unknown.dat"
    job.status = ImportStatus.CREATED
    job.started_at = None
    job.finished_at = None
    job.imported_events_count = 0
    job.warnings_count = 0
    job.error_message = None
    job.created_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()

    import_job_service.repository.list_for_match = AsyncMock(return_value=[job])

    results = await import_job_service.list_import_jobs(UUID(int=2))

    assert len(results) == 1
    assert results[0].id == job.id


@pytest.mark.asyncio
async def test_update_import_job(import_job_service: ImportJobService):
    job = Mock()
    job.id = UUID(int=6)
    job.match_id = UUID(int=2)
    job.provider = ImportProvider.VEO
    job.filename = "game.zip"
    job.status = ImportStatus.COMPLETED
    job.started_at = datetime.utcnow()
    job.finished_at = datetime.utcnow()
    job.imported_events_count = 10
    job.warnings_count = 0
    job.error_message = None
    job.created_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()

    import_job_service.repository.update = AsyncMock(return_value=job)
    payload = ImportJobUpdate(status=ImportStatus.COMPLETED, imported_events_count=10)

    result = await import_job_service.update_import_job(job.id, payload)

    assert result is not None
    assert result.id == job.id
    assert result.status == ImportStatus.COMPLETED


@pytest.mark.asyncio
async def test_update_import_job_not_found(import_job_service: ImportJobService):
    import_job_service.repository.update = AsyncMock(return_value=None)

    result = await import_job_service.update_import_job(UUID(int=7), ImportJobUpdate(status=ImportStatus.FAILED))

    assert result is None
