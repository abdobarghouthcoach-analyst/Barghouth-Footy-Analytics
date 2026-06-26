import csv
import json
from pathlib import Path
from typing import Any

from app.imports.providers.base import ParsedProviderEvent, ProviderParseResult


SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


class VeoHighlightsAdapter:
    def parse(self, extracted_dir: Path, filenames: list[str]) -> ProviderParseResult:
        json_candidates = sorted(name for name in filenames if Path(name).suffix.lower() == ".json")
        csv_candidates = sorted(name for name in filenames if Path(name).suffix.lower() == ".csv")
        ignored_video_files = sorted(name for name in filenames if Path(name).suffix.lower() in SUPPORTED_VIDEO_SUFFIXES)
        raw_metadata: dict[str, Any] = {
            "filenames": filenames,
            "candidate_json_files": json_candidates,
            "candidate_csv_files": csv_candidates,
            "ignored_video_files": ignored_video_files,
        }

        for filename in json_candidates:
            rows = self._load_json_rows(extracted_dir / filename)
            raw_metadata["selected_metadata_file"] = filename
            raw_metadata["selected_metadata_type"] = "json"
            events, warnings = self._normalise_rows(rows)
            return ProviderParseResult(raw_metadata=raw_metadata, events=events, warnings=warnings)

        for filename in csv_candidates:
            rows = self._load_csv_rows(extracted_dir / filename)
            raw_metadata["selected_metadata_file"] = filename
            raw_metadata["selected_metadata_type"] = "csv"
            events, warnings = self._normalise_rows(rows)
            return ProviderParseResult(raw_metadata=raw_metadata, events=events, warnings=warnings)

        raise ValueError("No supported Veo event metadata file found.")

    def _load_json_rows(self, path: Path) -> list[dict[str, Any]]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            for key in ("events", "highlights", "clips", "rows"):
                rows = data.get(key)
                if isinstance(rows, list):
                    return [row for row in rows if isinstance(row, dict)]
        return []

    def _load_csv_rows(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    def _normalise_rows(self, rows: list[dict[str, Any]]) -> tuple[list[ParsedProviderEvent], list[str]]:
        events: list[ParsedProviderEvent] = []
        warnings: list[str] = []
        for index, row in enumerate(rows, start=1):
            try:
                minute, second = self._parse_time(row)
                event = ParsedProviderEvent(
                    provider_event_id=self._first_text(row, "id", "event_id", "eventId", "clip_id", "highlight_id"),
                    event_type=self._first_text(row, "event_type", "eventType", "type", "event", "action", "label") or "highlight",
                    minute=minute,
                    second=second,
                    period=self._first_text(row, "period", "half"),
                    team_id=self._first_text(row, "team_id", "teamId", "team") or "",
                    player_id=self._first_text(row, "player_id", "playerId", "player"),
                    x_coordinate=self._optional_float(row, "x_coordinate", "x", "xCoordinate"),
                    y_coordinate=self._optional_float(row, "y_coordinate", "y", "yCoordinate"),
                    notes=self._first_text(row, "notes", "description", "title"),
                    raw_payload=row,
                )
                events.append(event)
            except ValueError as exc:
                warnings.append(f"Row {index}: {exc}")
        return events, warnings

    def _parse_time(self, row: dict[str, Any]) -> tuple[int, int]:
        minute = self._optional_int(row, "minute", "min")
        second = self._optional_int(row, "second", "sec")
        if minute is not None:
            return minute, second or 0

        timestamp = self._first_text(row, "timestamp", "time", "start_time", "startTime")
        if timestamp:
            if ":" in timestamp:
                parts = [int(part) for part in timestamp.split(":")]
                if len(parts) == 2:
                    return parts[0], parts[1]
                if len(parts) == 3:
                    return (parts[0] * 60) + parts[1], parts[2]
            total_seconds = int(float(timestamp))
            return total_seconds // 60, total_seconds % 60

        raise ValueError("missing event time")

    def _first_text(self, row: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = row.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return None

    def _optional_int(self, row: dict[str, Any], *keys: str) -> int | None:
        value = self._first_text(row, *keys)
        return int(float(value)) if value is not None else None

    def _optional_float(self, row: dict[str, Any], *keys: str) -> float | None:
        value = self._first_text(row, *keys)
        return float(value) if value is not None else None
