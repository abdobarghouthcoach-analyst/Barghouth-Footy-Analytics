from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import structlog
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.import_job import ImportProvider, ImportStatus
from app.imports.providers.veo_highlights import VeoHighlightsAdapter
from app.imports.storage import ImportStorage
from app.imports.validators import validate_imported_events
from app.models.event import Event
from app.models.import_job import ImportJob
from app.models.match import Match
from app.schemas.import_job import ImportJobResponse


logger = structlog.get_logger(__name__)


class MatchNotFoundError(ValueError):
    pass


class ImportValidationError(ValueError):
    pass


class ImportEngineService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.storage = ImportStorage(Path(settings.import_storage_root))
        self.veo_adapter = VeoHighlightsAdapter()

    async def import_veo_highlights(self, *, match_id: UUID, file: UploadFile) -> ImportJobResponse:
        match = await self.session.get(Match, match_id)
        if match is None:
            raise MatchNotFoundError("Match not found")
        if not file.filename or not file.filename.lower().endswith(".zip"):
            raise ImportValidationError("Veo Highlights import requires a .zip file.")

        import_job = ImportJob(
            match_id=match_id,
            provider=ImportProvider.VEO,
            status=ImportStatus.CREATED,
            original_filename=file.filename,
            started_at=datetime.now(timezone.utc),
            imported_events_count=0,
            warnings_count=0,
            summary={"message": "Import job created."},
        )
        self.session.add(import_job)
        await self.session.commit()
        await self.session.refresh(import_job)
        import_job_id = import_job.id
        logger.info(
            "import_job.created",
            import_job_id=str(import_job_id),
            match_id=str(match_id),
            provider=ImportProvider.VEO.value,
            original_filename=file.filename,
        )

        try:
            await self._mark(import_job, ImportStatus.UPLOADED)
            stored_path, file_size, checksum = await self.storage.store_original_zip(
                match_id=match_id,
                import_job_id=import_job_id,
                file=file,
            )
            import_job.stored_file_path = str(stored_path)
            import_job.file_size_bytes = file_size
            import_job.checksum_sha256 = checksum
            import_job.summary = {"message": "ZIP uploaded.", "events_imported": 0}
            await self.session.commit()
            logger.info(
                "import_job.zip_stored",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                stored_file_path=str(stored_path),
                file_size_bytes=file_size,
                checksum_sha256=checksum,
            )

            await self._mark(import_job, ImportStatus.EXTRACTING)
            extracted_dir, filenames = self.storage.safe_extract_zip(stored_path, match_id=match_id, import_job_id=import_job_id)
            logger.info(
                "import_job.zip_extracted",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                extracted_dir=str(extracted_dir),
                file_count=len(filenames),
            )

            await self._mark(import_job, ImportStatus.PARSING)
            parsed = self.veo_adapter.parse(extracted_dir, filenames)
            raw_metadata = {
                **parsed.raw_metadata,
                "file_size_bytes": file_size,
                "checksum_sha256": checksum,
            }
            logger.info(
                "import_job.metadata_discovered",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                detected_metadata_files=len(parsed.diagnostics.get("detected_metadata_files", [])),
                ignored_files=len(parsed.diagnostics.get("ignored_files", [])),
            )
            logger.info(
                "import_job.parser_selected",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                parser_selected=parsed.diagnostics.get("parser_selected"),
                selected_metadata_file=parsed.diagnostics.get("selected_metadata_file"),
            )
            logger.info(
                "import_job.rows_parsed",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                total_parsed_provider_rows=parsed.diagnostics.get("total_parsed_provider_rows", len(parsed.events)),
            )

            await self._mark(import_job, ImportStatus.NORMALIZING)
            event_payloads, validation_warnings = validate_imported_events(
                match_id=match_id,
                import_job_id=import_job_id,
                parsed_events=parsed.events,
            )
            warnings = [*parsed.warnings, *validation_warnings]
            normalized_events_count = len(event_payloads)
            raw_metadata["total_normalized_events"] = normalized_events_count
            logger.info(
                "import_job.rows_normalized",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                total_normalized_events=normalized_events_count,
                warnings_count=len(warnings),
            )
            if not parsed.events:
                raise ImportValidationError("No supported Veo event metadata rows found.")
            if not event_payloads:
                raise ImportValidationError("No valid Veo events found in metadata.")

            await self._mark(import_job, ImportStatus.PERSISTING)
            for payload in event_payloads:
                self.session.add(
                    Event(
                        match_id=payload.match_id,
                        team_id=payload.team_id,
                        player_id=payload.player_id,
                        event_type=payload.event_type,
                        minute=payload.minute,
                        second=payload.second,
                        period=payload.period,
                        x_coordinate=payload.x_coordinate,
                        y_coordinate=payload.y_coordinate,
                        notes=payload.notes,
                        tags=payload.tags,
                        source_provider=payload.source_provider,
                        source_event_id=payload.source_event_id,
                        import_job_id=payload.import_job_id,
                        source=payload.source,
                        provider=payload.provider,
                        provider_event_id=payload.provider_event_id,
                        raw_payload=payload.raw_payload,
                    )
                )

            import_job.status = ImportStatus.COMPLETED
            import_job.raw_metadata = raw_metadata
            import_job.imported_events_count = normalized_events_count
            import_job.warnings_count = len(warnings)
            diagnostics = {
                "zip_file_list": parsed.diagnostics.get("zip_file_list", filenames),
                "detected_metadata_files": parsed.diagnostics.get("detected_metadata_files", []),
                "ignored_files": parsed.diagnostics.get("ignored_files", []),
                "parser_selected": parsed.diagnostics.get("parser_selected"),
                "selected_metadata_file": parsed.diagnostics.get("selected_metadata_file"),
                "selected_metadata_type": parsed.diagnostics.get("selected_metadata_type"),
                "provider_version": parsed.diagnostics.get("provider_version"),
                "total_parsed_provider_rows": parsed.diagnostics.get("total_parsed_provider_rows", len(parsed.events)),
                "total_normalized_events": normalized_events_count,
                "unsupported_fields_encountered": parsed.diagnostics.get("unsupported_fields_encountered", []),
            }
            import_job.summary = {
                "message": "Import completed.",
                "events_parsed": len(parsed.events),
                "events_imported": normalized_events_count,
                "events_created": normalized_events_count,
                "warnings": warnings,
                **diagnostics,
                "diagnostics": diagnostics,
            }
            import_job.completed_at = datetime.now(timezone.utc)
            import_job.finished_at = import_job.completed_at
            await self.session.commit()
            await self.session.refresh(import_job)
            logger.info(
                "import_job.events_persisted",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                events_persisted=normalized_events_count,
            )
            logger.info(
                "import_job.completed",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                events_imported=normalized_events_count,
                warnings_count=len(warnings),
            )
            return ImportJobResponse.model_validate(import_job)
        except Exception as exc:
            await self.session.rollback()
            failed_job = await self.session.get(ImportJob, import_job_id)
            if failed_job is None:
                raise
            failed_job.status = ImportStatus.FAILED
            failed_job.error_message = str(exc)
            failed_job.finished_at = datetime.now(timezone.utc)
            failed_job.imported_events_count = 0
            failed_job.warnings_count = 0
            failed_job.summary = {
                "message": "Import failed.",
                "events_imported": 0,
                "error": str(exc),
            }
            await self.session.commit()
            await self.session.refresh(failed_job)
            logger.info(
                "import_job.failed",
                import_job_id=str(import_job_id),
                match_id=str(match_id),
                error_message=str(exc),
            )
            return ImportJobResponse.model_validate(failed_job)

    async def list_imports(self, match_id: UUID) -> list[ImportJobResponse]:
        match = await self.session.get(Match, match_id)
        if match is None:
            raise MatchNotFoundError("Match not found")
        result = await self.session.execute(
            select(ImportJob).where(ImportJob.match_id == match_id).order_by(ImportJob.created_at.desc())
        )
        return [ImportJobResponse.model_validate(job) for job in result.scalars().all()]

    async def get_import_job(self, import_job_id: UUID) -> ImportJobResponse | None:
        import_job = await self.session.get(ImportJob, import_job_id)
        return ImportJobResponse.model_validate(import_job) if import_job else None

    async def _mark(self, import_job: ImportJob, status: ImportStatus) -> None:
        import_job.status = status
        await self.session.commit()
        await self.session.refresh(import_job)
