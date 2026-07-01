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
from app.models.video_clip import MatchVideoClip


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
        self.video_clips: list[MatchVideoClip] = []
        self.pending_video_clips: list[MatchVideoClip] = []
        self.fail_event_commit = fail_event_commit
        self.rollback_count = 0

    async def get(self, model, item_id):
        if model is Match and item_id == MATCH_ID:
            return self.match
        if model is ImportJob:
            return next((job for job in self.import_jobs if job.id == item_id), None)
        if model is MatchVideoClip:
            return next((clip for clip in self.video_clips if clip.id == item_id), None)
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
        if isinstance(item, MatchVideoClip):
            if item.id is None:
                item.id = uuid4()
            self._stamp(item)
            self.pending_video_clips.append(item)
            return
        raise TypeError(f"Unsupported item type: {type(item)!r}")

    async def commit(self):
        if self.pending_events:
            if self.fail_event_commit:
                raise RuntimeError("forced event persistence failure")
            self.video_clips.extend(self.pending_video_clips)
            self.pending_video_clips = []
            self.events.extend(self.pending_events)
            self.pending_events = []
        elif self.pending_video_clips:
            self.video_clips.extend(self.pending_video_clips)
            self.pending_video_clips = []
        for job in self.import_jobs:
            self._stamp(job)

    async def flush(self):
        for clip in self.pending_video_clips:
            self._stamp(clip)

    async def refresh(self, item):
        self._stamp(item)

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        if entity is Event:
            target_import_job_id = self._first_where_value(statement)
            return FakeResult([event for event in self.events if event.import_job_id == target_import_job_id])
        if entity is ImportJob:
            return FakeResult(self.import_jobs)
        if entity is MatchVideoClip:
            target_import_job_id = self._first_where_value(statement)
            return FakeResult([clip for clip in self.video_clips if clip.import_job_id == target_import_job_id])
        return FakeResult([])

    async def delete(self, item):
        if isinstance(item, Event):
            self.events = [event for event in self.events if event.id != item.id]
            return
        if isinstance(item, MatchVideoClip):
            self.video_clips = [clip for clip in self.video_clips if clip.id != item.id]
            return
        raise TypeError(f"Unsupported item type: {type(item)!r}")

    async def rollback(self):
        self.rollback_count += 1
        self.pending_events = []
        self.pending_video_clips = []

    def _stamp(self, item):
        now = datetime.now(timezone.utc)
        if getattr(item, "created_at", None) is None:
            item.created_at = now
        item.updated_at = now

    def _first_where_value(self, statement):
        for criterion in getattr(statement, "_where_criteria", ()):
            value = getattr(getattr(criterion, "right", None), "value", None)
            if value is not None:
                return value
        return None


class FakeResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


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
    monkeypatch.setattr(settings, "video_storage_root", str(tmp_path / "matches"))
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
async def test_real_style_mp4_only_zip_imports_from_filenames(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)
    content = zip_bytes(
        {
            "Veo highlights Tamworth FC vs. Ashby/.veo-zip": "",
            "Veo highlights Tamworth FC vs. Ashby/01 000124_-_Shot_on_goal.mp4": b"video",
            "Veo highlights Tamworth FC vs. Ashby/04 000659_-_Goal.mp4": b"video",
            "Veo highlights Tamworth FC vs. Ashby/16 010353_-_Shot_on_goal.mp4": b"video",
        }
    )

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("veo-real.zip", content))

    assert result.status == ImportStatus.COMPLETED
    assert result.imported_events_count == 3
    assert len(session.events) == 3
    assert len(session.video_clips) == 3
    assert result.summary is not None
    assert result.summary["parser_selected"] == "veo_highlights_mp4_filename"
    assert result.summary["selected_metadata_type"] == "mp4_filename"
    assert result.summary["total_parsed_provider_rows"] == 3
    assert result.summary["total_normalized_events"] == 3
    assert result.summary["video_clips_imported"] == 3
    assert result.summary["detected_mp4_highlight_files"] == [
        "Veo highlights Tamworth FC vs. Ashby/01 000124_-_Shot_on_goal.mp4",
        "Veo highlights Tamworth FC vs. Ashby/04 000659_-_Goal.mp4",
        "Veo highlights Tamworth FC vs. Ashby/16 010353_-_Shot_on_goal.mp4",
    ]

    first_event = session.events[0]
    assert first_event.match_id == MATCH_ID
    assert first_event.import_job_id == session.import_jobs[0].id
    assert first_event.video_clip_id == session.video_clips[0].id
    assert first_event.source == EventSource.IMPORT
    assert first_event.provider == EventProvider.VEO
    assert first_event.team_id is None
    assert first_event.team_id != HOME_TEAM_ID
    assert first_event.player_id is None
    assert first_event.event_type == "shot_on_goal"
    assert first_event.minute == 1
    assert first_event.second == 24
    assert first_event.period is None
    assert first_event.provider_event_id == "Veo highlights Tamworth FC vs. Ashby/01 000124_-_Shot_on_goal.mp4"
    assert first_event.raw_payload["filename"] == "01 000124_-_Shot_on_goal.mp4"
    assert first_event.raw_payload["relative_path"] == "Veo highlights Tamworth FC vs. Ashby/01 000124_-_Shot_on_goal.mp4"
    assert first_event.raw_payload["clip_index"] == 1
    assert first_event.raw_payload["veo_timestamp"] == "000124"
    assert first_event.raw_payload["clock_seconds"] == 84
    assert first_event.raw_payload["original_label"] == "Shot_on_goal"
    assert first_event.raw_payload["parsed_from"] == "mp4_filename"
    assert session.video_clips[0].match_id == MATCH_ID
    assert session.video_clips[0].import_job_id == session.import_jobs[0].id
    assert session.video_clips[0].source_provider == "veo"
    assert session.video_clips[0].original_filename == "01 000124_-_Shot_on_goal.mp4"
    assert session.video_clips[0].mime_type == "video/mp4"
    assert session.video_clips[0].file_size_bytes == 5

    goal_event = session.events[1]
    assert goal_event.video_clip_id == session.video_clips[1].id
    assert goal_event.event_type == "goal"
    assert goal_event.minute == 6
    assert goal_event.second == 59
    assert goal_event.raw_payload["clock_seconds"] == 419

    late_event = session.events[2]
    assert late_event.video_clip_id == session.video_clips[2].id
    assert late_event.event_type == "shot_on_goal"
    assert late_event.minute == 63
    assert late_event.second == 53
    assert late_event.raw_payload["clock_seconds"] == 3833


@pytest.mark.asyncio
async def test_mp4_filename_parser_records_unsupported_patterns_without_crashing(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)
    content = zip_bytes(
        {
            "clips/01 000124_-_Shot-on goal.mp4": b"video",
            "clips/random-highlight.mp4": b"video",
        }
    )

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("mixed-mp4.zip", content))

    assert result.status == ImportStatus.COMPLETED
    assert result.imported_events_count == 1
    assert len(session.events) == 1
    assert session.events[0].event_type == "shot_on_goal"
    assert result.summary is not None
    assert result.summary["unsupported_filename_patterns"] == [
        {"filename": "clips/random-highlight.mp4", "reason": "unsupported Veo MP4 highlight filename pattern"}
    ]
    assert result.summary["ignored_files"] == [
        {"filename": "clips/random-highlight.mp4", "reason": "unsupported Veo MP4 highlight filename pattern"}
    ]


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
async def test_json_metadata_without_team_does_not_fallback_to_home_team(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)
    rows = [{"id": "veo-1", "event_type": "shot", "minute": 7, "second": 8}]
    content = zip_bytes({"events.json": json.dumps(rows)})

    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("events.zip", content))

    assert result.status == ImportStatus.COMPLETED
    assert len(session.events) == 1
    assert session.events[0].team_id is None
    assert session.events[0].team_id != HOME_TEAM_ID
    assert session.events[0].player_id is None


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
    assert session.video_clips == []
    assert session.pending_video_clips == []
    assert session.rollback_count == 1


@pytest.mark.asyncio
async def test_delete_import_job_removes_imported_events_and_files_but_preserves_job(tmp_path, monkeypatch):
    session = FakeImportSession()
    importer = service(tmp_path, session, monkeypatch)
    content = zip_bytes(
        {
            "clips/01 000124_-_Shot_on_goal.mp4": b"video",
            "clips/02 000500_-_Goal.mp4": b"video",
        }
    )
    result = await importer.import_veo_highlights(match_id=MATCH_ID, file=upload("veo-real.zip", content))
    import_job_id = result.id
    manual_event = Event(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        match_id=MATCH_ID,
        team_id=HOME_TEAM_ID,
        event_type="manual_note",
        minute=90,
        second=0,
        source=EventSource.MANUAL,
        import_job_id=None,
    )
    session.events.append(manual_event)
    job_dir = tmp_path / "imports" / str(MATCH_ID) / str(import_job_id)

    deleted = await importer.delete_import_job(import_job_id)

    assert deleted.status == ImportStatus.DELETED
    assert deleted.deleted_at is not None
    assert deleted.id == import_job_id
    assert deleted.checksum_sha256 == result.checksum_sha256
    assert deleted.original_filename == "veo-real.zip"
    assert deleted.summary == result.summary
    assert session.import_jobs[0].status == ImportStatus.DELETED
    assert session.import_jobs[0].deleted_at is not None
    assert session.events == [manual_event]
    assert session.video_clips == []
    assert not job_dir.exists()
    assert not (tmp_path / "matches" / str(MATCH_ID) / "imports" / str(import_job_id)).exists()
