from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.imports.schemas import ImportUploadResponse
from app.imports.service import ImportEngineService, ImportValidationError, MatchNotFoundError
from app.schemas.import_job import ImportJobResponse

router = APIRouter(tags=["Imports"])


async def get_import_service(session: AsyncSession = Depends(get_db_session)) -> ImportEngineService:
    return ImportEngineService(session)


@router.post(
    "/matches/{match_id}/imports/veo-highlights",
    response_model=ImportUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_veo_highlights(
    match_id: UUID,
    file: UploadFile = File(...),
    service: ImportEngineService = Depends(get_import_service),
) -> ImportUploadResponse:
    try:
        return await service.import_veo_highlights(match_id=match_id, file=file)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ImportValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/matches/{match_id}/imports", response_model=list[ImportJobResponse])
async def list_match_imports(
    match_id: UUID,
    service: ImportEngineService = Depends(get_import_service),
) -> list[ImportJobResponse]:
    try:
        return await service.list_imports(match_id)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/import-jobs/{import_job_id}", response_model=ImportJobResponse)
async def get_import_job(
    import_job_id: UUID,
    service: ImportEngineService = Depends(get_import_service),
) -> ImportJobResponse:
    import_job = await service.get_import_job(import_job_id)
    if import_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return import_job
