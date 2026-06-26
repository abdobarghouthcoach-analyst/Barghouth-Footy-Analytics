from uuid import UUID

from app.repositories.import_job import ImportJobRepository
from app.schemas.import_job import ImportJobCreate, ImportJobResponse, ImportJobUpdate


class ImportJobService:
    def __init__(self, repository: ImportJobRepository):
        self.repository = repository

    async def create_import_job(self, payload: ImportJobCreate) -> ImportJobResponse:
        import_job = await self.repository.create(payload)
        return ImportJobResponse.from_orm(import_job)

    async def get_import_job(self, job_id: UUID) -> ImportJobResponse | None:
        import_job = await self.repository.get_by_id(job_id)
        return ImportJobResponse.from_orm(import_job) if import_job else None

    async def list_import_jobs(self, match_id: UUID) -> list[ImportJobResponse]:
        import_jobs = await self.repository.list_for_match(match_id)
        return [ImportJobResponse.from_orm(job) for job in import_jobs]

    async def update_import_job(self, job_id: UUID, payload: ImportJobUpdate) -> ImportJobResponse | None:
        import_job = await self.repository.update(job_id, payload)
        return ImportJobResponse.from_orm(import_job) if import_job else None
