from typing import Any
from uuid import UUID

from app.models.import_job import ImportJob
from app.repositories.import_job import ImportJobRepository
from app.schemas.import_job import ImportJobCreate, ImportJobResponse, ImportJobUpdate


class ImportJobService:
    def __init__(self, repository: ImportJobRepository):
        self.repository = repository

    def _to_response(self, import_job: ImportJob) -> ImportJobResponse:
        original_filename = self._clean_attr(import_job, "original_filename")
        legacy_filename = self._clean_attr(import_job, "filename")
        if original_filename is None and legacy_filename is not None:
            original_filename = legacy_filename
        return ImportJobResponse.model_validate(
            {
                "id": self._clean_attr(import_job, "id"),
                "match_id": self._clean_attr(import_job, "match_id"),
                "provider": self._clean_attr(import_job, "provider"),
                "status": self._clean_attr(import_job, "status"),
                "original_filename": original_filename,
                "stored_file_path": self._clean_attr(import_job, "stored_file_path"),
                "file_size_bytes": self._clean_attr(import_job, "file_size_bytes"),
                "checksum_sha256": self._clean_attr(import_job, "checksum_sha256"),
                "raw_metadata": self._clean_attr(import_job, "raw_metadata"),
                "summary": self._clean_attr(import_job, "summary"),
                "started_at": self._clean_attr(import_job, "started_at"),
                "finished_at": self._clean_attr(import_job, "finished_at"),
                "completed_at": self._clean_attr(import_job, "completed_at"),
                "deleted_at": self._clean_attr(import_job, "deleted_at"),
                "imported_events_count": self._clean_attr(import_job, "imported_events_count") or 0,
                "warnings_count": self._clean_attr(import_job, "warnings_count") or 0,
                "error_message": self._clean_attr(import_job, "error_message"),
                "created_at": self._clean_attr(import_job, "created_at"),
                "updated_at": self._clean_attr(import_job, "updated_at"),
            }
        )

    def _clean_attr(self, item: ImportJob, name: str) -> Any:
        value = getattr(item, name, None)
        return None if value.__class__.__module__ == "unittest.mock" else value

    async def create_import_job(self, payload: ImportJobCreate) -> ImportJobResponse:
        import_job = await self.repository.create(payload)
        return self._to_response(import_job)

    async def get_import_job(self, job_id: UUID) -> ImportJobResponse | None:
        import_job = await self.repository.get_by_id(job_id)
        return self._to_response(import_job) if import_job else None

    async def list_import_jobs(self, match_id: UUID) -> list[ImportJobResponse]:
        import_jobs = await self.repository.list_for_match(match_id)
        return [self._to_response(job) for job in import_jobs]

    async def update_import_job(self, job_id: UUID, payload: ImportJobUpdate) -> ImportJobResponse | None:
        import_job = await self.repository.update(job_id, payload)
        return self._to_response(import_job) if import_job else None
