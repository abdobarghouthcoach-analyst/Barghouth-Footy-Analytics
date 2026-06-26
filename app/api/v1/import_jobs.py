from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db_session
from app.repositories.import_job import ImportJobRepository
from app.schemas.import_job import ImportJobCreate, ImportJobResponse, ImportJobUpdate
from app.services.import_job import ImportJobService

import_jobs_router = APIRouter(prefix="/import-jobs", tags=["Import Jobs"])


async def get_service(session: AsyncSession = Depends(get_db_session)) -> ImportJobService:
    return ImportJobService(ImportJobRepository(session))


@import_jobs_router.post("/", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
async def create_import_job(
    payload: ImportJobCreate,
    service: ImportJobService = Depends(get_service),
) -> ImportJobResponse:
    return await service.create_import_job(payload)


@import_jobs_router.get("/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: UUID = Path(...),
    service: ImportJobService = Depends(get_service),
) -> ImportJobResponse:
    import_job = await service.get_import_job(job_id)
    if not import_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return import_job


@import_jobs_router.get("/match/{match_id}", response_model=list[ImportJobResponse])
async def list_import_jobs(
    match_id: UUID = Path(...),
    service: ImportJobService = Depends(get_service),
) -> list[ImportJobResponse]:
    return await service.list_import_jobs(match_id)


@import_jobs_router.patch("/{job_id}", response_model=ImportJobResponse)
async def update_import_job(
    payload: ImportJobUpdate,
    job_id: UUID = Path(...),
    service: ImportJobService = Depends(get_service),
) -> ImportJobResponse:
    import_job = await service.update_import_job(job_id, payload)
    if not import_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return import_job
