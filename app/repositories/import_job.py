from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_job import ImportJob
from app.schemas.import_job import ImportJobCreate, ImportJobUpdate


class ImportJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload: ImportJobCreate) -> ImportJob:
        import_job = ImportJob(**payload.model_dump())
        self.session.add(import_job)
        await self.session.commit()
        await self.session.refresh(import_job)
        return import_job

    async def get_by_id(self, job_id: UUID) -> ImportJob | None:
        statement = select(ImportJob).where(ImportJob.id == job_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_for_match(self, match_id: UUID) -> list[ImportJob]:
        statement = select(ImportJob).where(ImportJob.match_id == match_id).order_by(ImportJob.created_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def update(self, job_id: UUID, payload: ImportJobUpdate) -> ImportJob | None:
        values = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
        if not values:
            return await self.get_by_id(job_id)

        statement = update(ImportJob).where(ImportJob.id == job_id).values(**values)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(job_id)
