import mimetypes
import shutil
from pathlib import Path
from uuid import UUID


VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


class VideoClipStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def clips_dir(self, *, match_id: UUID, import_job_id: UUID) -> Path:
        return self.root / str(match_id) / "imports" / str(import_job_id) / "clips"

    def delete_import_clips(self, *, match_id: UUID, import_job_id: UUID) -> None:
        root = self.root.resolve()
        directory = self.clips_dir(match_id=match_id, import_job_id=import_job_id).resolve()
        if root != directory and root not in directory.parents:
            raise ValueError("Video storage path is outside the configured root.")
        if directory.exists():
            shutil.rmtree(directory)
        import_directory = directory.parent
        if import_directory.exists() and not any(import_directory.iterdir()):
            import_directory.rmdir()

    def delete_match_video(self, *, match_id: UUID) -> None:
        root = self.root.resolve()
        directory = (self.root / str(match_id)).resolve()
        if root != directory and root not in directory.parents:
            raise ValueError("Video storage path is outside the configured root.")
        if directory.exists():
            shutil.rmtree(directory)

    def store_clip(self, *, match_id: UUID, import_job_id: UUID, source_path: Path, original_filename: str) -> tuple[Path, int, str]:
        directory = self.clips_dir(match_id=match_id, import_job_id=import_job_id)
        directory.mkdir(parents=True, exist_ok=True)
        destination = self._unique_destination(directory, original_filename)
        shutil.copy2(source_path, destination)
        mime_type = mimetypes.guess_type(destination.name)[0] or "application/octet-stream"
        return destination, destination.stat().st_size, mime_type

    def resolve_clip_path(self, storage_path: str) -> Path:
        root = self.root.resolve()
        path = Path(storage_path).resolve()
        if root != path and root not in path.parents:
            raise ValueError("Video storage path is outside the configured root.")
        return path

    def _unique_destination(self, directory: Path, filename: str) -> Path:
        candidate = directory / Path(filename).name
        if not candidate.exists():
            return candidate
        stem = candidate.stem
        suffix = candidate.suffix
        counter = 2
        while True:
            next_candidate = directory / f"{stem}-{counter}{suffix}"
            if not next_candidate.exists():
                return next_candidate
            counter += 1


def is_video_filename(filename: str) -> bool:
    return Path(filename).suffix.lower() in VIDEO_SUFFIXES
