import csv
import json
import re
from pathlib import Path
from typing import Any

from app.imports.providers.base import ParsedProviderEvent, ProviderParseResult


SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
MP4_FILENAME_PATTERN = re.compile(r"^(?P<clip_index>\d+)\s+(?P<timestamp>\d{6})_-_(?P<label>.+)\.mp4$", re.IGNORECASE)
NORMALIZED_FIELD_NAMES = {
    "id",
    "event_id",
    "eventId",
    "clip_id",
    "highlight_id",
    "event_type",
    "eventType",
    "type",
    "event",
    "action",
    "label",
    "minute",
    "min",
    "second",
    "sec",
    "timestamp",
    "time",
    "start_time",
    "startTime",
    "period",
    "half",
    "team_id",
    "teamId",
    "team",
    "player_id",
    "playerId",
    "player",
    "x_coordinate",
    "x",
    "xCoordinate",
    "y_coordinate",
    "y",
    "yCoordinate",
    "notes",
    "description",
    "title",
    "provider_version",
    "providerVersion",
    "version",
    "export_version",
    "exportVersion",
}

class VeoHighlightsAdapter:
    def parse(self, extracted_dir: Path, filenames: list[str]) -> ProviderParseResult:
        json_candidates = sorted(name for name in filenames if Path(name).suffix.lower() == ".json")
        csv_candidates = sorted(name for name in filenames if Path(name).suffix.lower() == ".csv")
        mp4_candidates = sorted(name for name in filenames if Path(name).suffix.lower() == ".mp4")
        detected_metadata_files = [
            *({"filename": name, "type": "json"} for name in json_candidates),
            *({"filename": name, "type": "csv"} for name in csv_candidates),
        ]
        ignored_files = self._ignored_files(filenames, json_candidates, csv_candidates, mp4_candidates)
        raw_metadata: dict[str, Any] = {
            "filenames": filenames,
            "zip_file_list": filenames,
            "candidate_json_files": json_candidates,
            "candidate_csv_files": csv_candidates,
            "candidate_mp4_files": mp4_candidates,
            "ignored_video_files": sorted(
                name for name in filenames if Path(name).suffix.lower() in SUPPORTED_VIDEO_SUFFIXES
            ),
            "detected_metadata_files": detected_metadata_files,
            "ignored_files": ignored_files,
        }

        for filename in json_candidates:
            rows, provider_version = self._load_json_rows(extracted_dir / filename)
            events, warnings = self._normalise_rows(rows)
            diagnostics = self._diagnostics(
                filenames=filenames,
                detected_metadata_files=detected_metadata_files,
                ignored_files=ignored_files,
                parser_selected="veo_highlights_json",
                selected_metadata_file=filename,
                selected_metadata_type="json",
                provider_version=provider_version,
                rows=rows,
                events=events,
            )
            raw_metadata.update(diagnostics)
            return ProviderParseResult(raw_metadata=raw_metadata, events=events, warnings=warnings, diagnostics=diagnostics)

        for filename in csv_candidates:
            rows = self._load_csv_rows(extracted_dir / filename)
            events, warnings = self._normalise_rows(rows)
            diagnostics = self._diagnostics(
                filenames=filenames,
                detected_metadata_files=detected_metadata_files,
                ignored_files=ignored_files,
                parser_selected="veo_highlights_csv",
                selected_metadata_file=filename,
                selected_metadata_type="csv",
                provider_version=self._detect_provider_version_from_rows(rows),
                rows=rows,
                events=events,
            )
            raw_metadata.update(diagnostics)
            return ProviderParseResult(raw_metadata=raw_metadata, events=events, warnings=warnings, diagnostics=diagnostics)

        if mp4_candidates:
            rows, unsupported_filename_patterns = self._load_mp4_filename_rows(mp4_candidates)
            if rows:
                events = self._normalise_mp4_filename_rows(rows)
                mp4_detected_metadata_files = [
                    {"filename": row["relative_path"], "type": "mp4_filename"} for row in rows
                ]
                mp4_ignored_files = [
                    *ignored_files,
                    *(
                        {
                            "filename": item["filename"],
                            "reason": "unsupported Veo MP4 highlight filename pattern",
                        }
                        for item in unsupported_filename_patterns
                    ),
                ]
                diagnostics = self._diagnostics(
                    filenames=filenames,
                    detected_metadata_files=mp4_detected_metadata_files,
                    ignored_files=mp4_ignored_files,
                    parser_selected="veo_highlights_mp4_filename",
                    selected_metadata_file="; ".join(row["relative_path"] for row in rows),
                    selected_metadata_type="mp4_filename",
                    provider_version=None,
                    rows=rows,
                    events=events,
                    unsupported_fields=[],
                )
                diagnostics["detected_mp4_highlight_files"] = [row["relative_path"] for row in rows]
                diagnostics["unsupported_filename_patterns"] = unsupported_filename_patterns
                raw_metadata.update(diagnostics)
                return ProviderParseResult(
                    raw_metadata=raw_metadata,
                    events=events,
                    warnings=[],
                    diagnostics=diagnostics,
                )

        raise ValueError("No supported Veo event metadata file found.")

    def _load_json_rows(self, path: Path) -> tuple[list[dict[str, Any]], str | None]:
        data = json.loads(path.read_text(encoding="utf-8"))
        provider_version = self._detect_provider_version(data)
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)], provider_version
        if isinstance(data, dict):
            for key in ("events", "highlights", "clips", "rows"):
                rows = data.get(key)
                if isinstance(rows, list):
                    return [row for row in rows if isinstance(row, dict)], provider_version
        return [], provider_version

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
                    team_id=self._first_text(row, "team_id", "teamId", "team"),
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

    def _load_mp4_filename_rows(self, filenames: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        rows: list[dict[str, Any]] = []
        unsupported: list[dict[str, str]] = []
        for relative_path in filenames:
            filename = Path(relative_path).name
            match = MP4_FILENAME_PATTERN.match(filename)
            if match is None:
                unsupported.append({"filename": relative_path, "reason": "unsupported Veo MP4 highlight filename pattern"})
                continue

            veo_timestamp = match.group("timestamp")
            original_label = match.group("label")
            clock_seconds = self._hhmmss_to_seconds(veo_timestamp)
            rows.append(
                {
                    "filename": filename,
                    "relative_path": relative_path,
                    "clip_index": int(match.group("clip_index")),
                    "veo_timestamp": veo_timestamp,
                    "clock_seconds": clock_seconds,
                    "original_label": original_label,
                    "parsed_from": "mp4_filename",
                }
            )
        return rows, unsupported

    def _normalise_mp4_filename_rows(self, rows: list[dict[str, Any]]) -> list[ParsedProviderEvent]:
        events: list[ParsedProviderEvent] = []
        for row in rows:
            clock_seconds = int(row["clock_seconds"])
            events.append(
                ParsedProviderEvent(
                    provider_event_id=str(row["relative_path"]),
                    event_type=self._normalise_label(str(row["original_label"])),
                    minute=clock_seconds // 60,
                    second=clock_seconds % 60,
                    period=None,
                    team_id=None,
                    raw_payload=row,
                )
            )
        return events

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

    def _ignored_files(
        self,
        filenames: list[str],
        json_candidates: list[str],
        csv_candidates: list[str],
        mp4_candidates: list[str] | None = None,
    ) -> list[dict[str, str]]:
        metadata_files = {*json_candidates, *csv_candidates, *(mp4_candidates or [])}
        ignored: list[dict[str, str]] = []
        for filename in sorted(name for name in filenames if name not in metadata_files):
            suffix = Path(filename).suffix.lower()
            reason = "video file ignored" if suffix in SUPPORTED_VIDEO_SUFFIXES else "unsupported metadata format"
            ignored.append({"filename": filename, "reason": reason})
        return ignored

    def _diagnostics(
        self,
        *,
        filenames: list[str],
        detected_metadata_files: list[dict[str, str]],
        ignored_files: list[dict[str, str]],
        parser_selected: str,
        selected_metadata_file: str,
        selected_metadata_type: str,
        provider_version: str | None,
        rows: list[dict[str, Any]],
        events: list[ParsedProviderEvent],
        unsupported_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "zip_file_list": filenames,
            "detected_metadata_files": detected_metadata_files,
            "ignored_files": ignored_files,
            "parser_selected": parser_selected,
            "selected_metadata_file": selected_metadata_file,
            "selected_metadata_type": selected_metadata_type,
            "provider_version": provider_version,
            "total_parsed_provider_rows": len(rows),
            "total_normalized_events": len(events),
            "unsupported_fields_encountered": unsupported_fields if unsupported_fields is not None else self._unsupported_fields(rows),
        }

    def _unsupported_fields(self, rows: list[dict[str, Any]]) -> list[str]:
        return sorted({key for row in rows for key in row if key not in NORMALIZED_FIELD_NAMES})

    def _detect_provider_version(self, data: Any) -> str | None:
        if isinstance(data, dict):
            return self._first_text(data, "provider_version", "providerVersion", "version", "export_version", "exportVersion")
        return None

    def _detect_provider_version_from_rows(self, rows: list[dict[str, Any]]) -> str | None:
        for row in rows:
            version = self._first_text(row, "provider_version", "providerVersion", "version", "export_version", "exportVersion")
            if version:
                return version
        return None

    def _hhmmss_to_seconds(self, timestamp: str) -> int:
        hours = int(timestamp[0:2])
        minutes = int(timestamp[2:4])
        seconds = int(timestamp[4:6])
        return (hours * 3600) + (minutes * 60) + seconds

    def _normalise_label(self, label: str) -> str:
        value = label.strip().lower()
        value = re.sub(r"[\s-]+", "_", value)
        value = re.sub(r"[^a-z0-9_]+", "_", value)
        value = re.sub(r"_+", "_", value)
        return value.strip("_") or "highlight"
