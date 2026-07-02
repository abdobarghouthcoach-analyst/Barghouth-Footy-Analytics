from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.models.match import Match
from app.models.video_clip import MatchVideoClip
from app.services.video_clip import VideoClipNotFoundError, VideoClipService


MATCH_ID = UUID("11111111-1111-1111-1111-111111111111")
CLIP_ID = UUID("22222222-2222-2222-2222-222222222222")
IMPORT_JOB_ID = UUID("33333333-3333-3333-3333-333333333333")


class FakeVideoSession:
    def __init__(self, *, storage_path: str) -> None:
        now = datetime.now(timezone.utc)
        self.match = Match(
            id=MATCH_ID,
            competition_id=UUID(int=1),
            season_id=UUID(int=2),
            home_team_id=UUID(int=3),
            away_team_id=UUID(int=4),
            kickoff_datetime=now,
            venue="Test Ground",
        )
        self.clip = MatchVideoClip(
            id=CLIP_ID,
            match_id=MATCH_ID,
            import_job_id=IMPORT_JOB_ID,
            source_provider="veo",
            original_filename="01 000124_-_Shot_on_goal.mp4",
            storage_path=storage_path,
            mime_type="video/mp4",
            file_size_bytes=5,
        )
        self.clip.created_at = now
        self.clip.updated_at = now

    async def get(self, model, item_id):
        if model is Match and item_id == MATCH_ID:
            return self.match
        if model is MatchVideoClip and item_id == CLIP_ID:
            return self.clip
        return None

    async def execute(self, statement):
        entity = statement.column_descriptions[0].get("entity")
        if entity is MatchVideoClip:
            return FakeResult([self.clip])
        return FakeResult([])


class FakeResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


@pytest.mark.asyncio
async def test_list_match_clips_returns_metadata_only(tmp_path, monkeypatch):
    from app.config import settings

    clip_path = tmp_path / "matches" / str(MATCH_ID) / "imports" / str(IMPORT_JOB_ID) / "clips" / "clip.mp4"
    clip_path.parent.mkdir(parents=True)
    clip_path.write_bytes(b"video")
    monkeypatch.setattr(settings, "video_storage_root", str(tmp_path / "matches"))
    service = VideoClipService(FakeVideoSession(storage_path=str(clip_path)))  # type: ignore[arg-type]

    clips = await service.list_match_clips(MATCH_ID)

    assert len(clips) == 1
    assert clips[0].id == CLIP_ID
    assert clips[0].match_id == MATCH_ID
    assert clips[0].original_filename == "01 000124_-_Shot_on_goal.mp4"
    assert not hasattr(clips[0], "storage_path")


@pytest.mark.asyncio
async def test_stream_clip_returns_file_response(tmp_path, monkeypatch):
    from app.config import settings

    clip_path = tmp_path / "matches" / str(MATCH_ID) / "imports" / str(IMPORT_JOB_ID) / "clips" / "clip.mp4"
    clip_path.parent.mkdir(parents=True)
    clip_path.write_bytes(b"video")
    monkeypatch.setattr(settings, "video_storage_root", str(tmp_path / "matches"))
    service = VideoClipService(FakeVideoSession(storage_path=str(clip_path)))  # type: ignore[arg-type]

    response = await service.stream_clip(CLIP_ID)

    assert response.media_type == "video/mp4"
    assert str(response.path) == str(clip_path)


@pytest.mark.asyncio
async def test_stream_clip_rejects_missing_file(tmp_path, monkeypatch):
    from app.config import settings

    clip_path = tmp_path / "matches" / str(MATCH_ID) / "imports" / str(IMPORT_JOB_ID) / "clips" / "missing.mp4"
    monkeypatch.setattr(settings, "video_storage_root", str(tmp_path / "matches"))
    service = VideoClipService(FakeVideoSession(storage_path=str(clip_path)))  # type: ignore[arg-type]

    with pytest.raises(VideoClipNotFoundError):
        await service.stream_clip(CLIP_ID)


@pytest.mark.asyncio
async def test_stream_clip_rejects_storage_path_outside_video_root(tmp_path, monkeypatch):
    from app.config import settings

    video_root = tmp_path / "matches"
    outside_file = tmp_path / "outside.mp4"
    outside_file.write_bytes(b"video")
    monkeypatch.setattr(settings, "video_storage_root", str(video_root))
    service = VideoClipService(FakeVideoSession(storage_path=str(outside_file)))  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        await service.stream_clip(CLIP_ID)
