import hashlib
import shutil
import zipfile
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile


class ImportStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def job_dir(self, match_id: UUID, import_job_id: UUID) -> Path:
        return self.root / str(match_id) / str(import_job_id)

    def delete_job_files(self, *, match_id: UUID, import_job_id: UUID) -> None:
        root = self.root.resolve()
        directory = self.job_dir(match_id, import_job_id).resolve()
        if root != directory and root not in directory.parents:
            raise ValueError("Import storage path is outside the configured root.")
        if directory.exists():
            shutil.rmtree(directory)

    async def store_original_zip(self, *, match_id: UUID, import_job_id: UUID, file: UploadFile) -> tuple[Path, int, str]:
        directory = self.job_dir(match_id, import_job_id)
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / "original.zip"
        digest = hashlib.sha256()
        size = 0
        with destination.open("wb") as handle:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
                handle.write(chunk)
        return destination, size, digest.hexdigest()

    def safe_extract_zip(self, zip_path: Path, *, match_id: UUID, import_job_id: UUID) -> tuple[Path, list[str]]:
        extracted_dir = self.job_dir(match_id, import_job_id) / "extracted"
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir)
        extracted_dir.mkdir(parents=True, exist_ok=True)
        extracted_root = extracted_dir.resolve()
        filenames: list[str] = []

        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.infolist():
                member_name = member.filename.replace("\\", "/")
                member_path = Path(member_name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ValueError("ZIP contains an unsafe path.")
                if member.is_dir():
                    continue
                destination = (extracted_dir / member_path).resolve()
                if extracted_root not in destination.parents:
                    raise ValueError("ZIP contains an unsafe path.")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
                filenames.append(member_name)

        return extracted_dir, sorted(filenames)
