import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, UploadFile

from app.domain.event import EventProvider, EventSource
from app.domain.import_job import ImportStatus
from app.imports.router import upload_veo_highlights
from app.imports.service import ImportEngineService, ImportValidationError
from app.models.event import Event
from app.models.import_job import ImportJob
from app.models.match import Match


MATCH_ID = UUID("11111111-1111-1111-1111-111111111111")
HOME_TEAM_ID = UUID("22222222-2222-2222-2222-222222222222")
AWAY_TEAM_ID = UUID("33333333-3333-3333-3333-333333333333")


class FakeImportSession:
    def __init__(self, *, fail_event_commit: bool = False) -> None:
        self.match = Match(
            id=MATCH_ID,
            competition_id=UUID(int=10),
            season_id=UUID(int=11),
            home_team_id=HOME_TEAM_ID,
            away_team_id=AWAY_TEAM_ID,
            kickoff_datetime=datetime.now(timezone.utc),
            venue="Test Ground",
        )
        self.import_jobs: list[ImportJob] = []
        self.events: list[Event] = []
        self.pending_events: list[Event] = []
        self.fail_event_commit = fail_event_commit
        self.rollback_count = 0

    async def get(self, model, item_id):
        if model is Match and item_id == MATCH_ID:
            return self.match
        if model is ImportJob:
            return next((job for job in self.import_jobs if job.id == item_id), None)
        return None

    def add(self, item):
        if isinstance(item, ImportJob):
            if item.id is None:
                item.id = uuid4()
            self._stamp(item)
            if item not in self.import_jobs:
                self.import_jobs.append(item)
            return
        if isinstance(item, Event):
            if item.id is None:
                item.id = uuid4()
            self._stamp(item)
            self.pending_events.append(item)
            return
        raise TypeError(f"Unsupported item type: {type(item)!r}")

    async def commit(self):
        if self.pending_events:
            if self.fail_event_commit:
                raise RuntimeError("forced event persistence failure")
            self.events.extend(self.pending_events)
            self.pending_events = []
        for job in self.import_jobs:
            self._stamp(job)

    async def refresh(self, item):
        self._stamp(item)

    async def rollback(self):
        self.rollback_count += 1
        self.pending_events = []

    def _stamp(self, item):
        now = datetime.now(timezone.utc)
        if getattr(item, "created_at", None) is None:
            item.created_at = now
        item.updated_at = now


def upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def zip_bytes(entries: dict[str, bytes | str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, value in entries.items():
            data = value.encode("utf-8") if isinstance(value, str) else value
            archive.writestr(name, data)
    return buffer.getvalue()


def empty_zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w"):
        pass
    return buffer.getvalue()


def service(tmp_path: Path, session: FakeImportSession, monkeypatch: pytest.MonkeyPatch) -> ImportEngineService:
    from app.config import settings

    monkeypatch.setattr(settings, "import_storage_root", str(tmp_path / "imports"))
    return ImportEngineService(session)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_router_rejects_non_zip_upload_with_http_400():
    class RejectingService:
        def __init__(self) -> None:
            self.calls = 0

        async def import_veo_highlights(self, *, match_id: UUID, file: UploadFile):
            self.calls += 1
            raise ImportValidationError("Veo Highlights import requires a .zip file.")

    fake_service = RejectingService()

    with pytest.raises(HTTPException) as exc_info:
        await upload_veo_highlights(MATCH_ID, upload("notes.txt", b"not a zip"), fake_service)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 400
    assert fake_service.calls == 1


@pytest.mark.asyncio
async def test_service_rejects_non_zip_before_creating_import_job(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)

    with pytest.raises(ImportValidationError):
        await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("notes.txt", b"not a zip"))

    assert session.import_jobs == []


@pytest.mark.asyncio
async def test_corrupt_zip_creates_failed_import_job_with_error(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("bad.zip", b"not a real zip"))

    assert result.status == ImportStatus.FAILED
    assert len(session.import_jobs) == 1
    assert session.import_jobs[0].error_message


@pytest.mark.asyncio
async def test_empty_zip_fails_with_no_supported_metadata_summary(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("empty.zip", empty_zip_bytes()))

    assert result.status == ImportStatus.FAILED
    assert result.summary is not None
    assert result.summary["error"] == "No supported Veo event metadata file found."


@pytest.mark.asyncio
async def test_zip_with_no_supported_metadata_fails_without_events(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)
    content = zip_bytes({"highlights.mp4": b"video", "readme.txt": "nothing useful"})

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("video-only.zip", content))

    assert result.status == ImportStatus.FAILED
    assert result.error_message == "No supported Veo event metadata file found."
    assert session.events == []


@pytest.mark.asyncio
async def test_zip_path_traversal_fails_and_writes_no_file_outside_job_dir(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)
    content = zip_bytes({"../../evil.csv": "team_id,event_type,minute,second\nx,shot,1,2\n"})

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("unsafe.zip", content))

    assert result.status == ImportStatus.FAILED
    assert result.error_message == "ZIP contains an unsafe path."
    assert not (tmp_path / "evil.csv").exists()
    assert not (tmp_path / "imports" / "evil.csv").exists()
    assert session.events == []


@pytest.mark.asyncio
async def test_successful_json_metadata_import_creates_imported_veo_events_with_null_period(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)
    metadata = {
        "events": [
            {
                "id": "veo-1",
                "team_id": str(HOME_TEAM_ID),
                "event_type": "shot",
                "minute": 12,
                "second": 5,
                "notes": "Saved",
                "confidence": "high",
            }
        ]
    }
    content = zip_bytes({"metadata/events.json": json.dumps(metadata)})

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("events.zip", content))

    assert result.status == ImportStatus.COMPLETED
    assert result.imported_events_count == 1
    assert len(session.events) == 1
    event = session.events[0]
    assert event.match_id == MATCH_ID
    assert event.import_job_id == session.import_jobs[0].id
    assert event.source == EventSource.IMPORT
    assert event.provider == EventProvider.VEO
    assert event.raw_payload
    assert event.raw_payload["confidence"] == "high"
    assert event.period is None
    assert result.summary is not None
    assert result.summary["zip_file_list"] == ["metadata/events.json"]
    assert result.summary["detected_metadata_files"] == [{"filename": "metadata/events.json", "type": "json"}]
    assert result.summary["parser_selected"] == "veo_highlights_json"
    assert result.summary["total_parsed_provider_rows"] == 1
    assert result.summary["total_normalized_events"] == 1
    assert result.summary["unsupported_fields_encountered"] == ["confidence"]


@pytest.mark.asyncio
async def test_event_persistence_failure_marks_job_failed_and_rolls_back_events(tmp_path, monkeypatch):
    session = FakeImportSession(fail_event_commit=True)
    importer = service(tmp_path, session, monkeypatch)
    rows = [
        {"id": "veo-1", "team_id": str(HOME_TEAM_ID), "event_type": "shot", "minute": 1, "second": 0},
        {"id": "veo-2", "team_id": str(AWAY_TEAM_ID), "event_type": "pass", "minute": 2, "second": 4},
    ]
    content = zip_bytes({"events.json": json.dumps(rows)})

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("events.zip", content))

    assert result.status == ImportStatus.FAILED
    assert result.error_message == "forced event persistence failure"
    assert session.import_jobs[0].status == ImportStatus.FAILED
    assert session.events == []
    assert session.pending_events == []
    assert session.rollback_count == 1
