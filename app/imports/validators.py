from uuid import UUID

from pydantic import ValidationError

from app.domain.event import EventPeriod, EventProvider, EventSource, SourceProvider
from app.imports.providers.base import ParsedProviderEvent
from app.schemas.event import EventCreate


def validate_imported_events(
    *,
    match_id: UUID,
    import_job_id: UUID,
    parsed_events: list[ParsedProviderEvent],
) -> tuple[list[EventCreate], list[str]]:
    events: list[EventCreate] = []
    warnings: list[str] = []
    supported_periods = {item.value for item in EventPeriod}
    for index, parsed in enumerate(parsed_events, start=1):
        try:
            period = parsed.period if parsed.period in supported_periods else None
            events.append(
                EventCreate.model_validate(
                    {
                        "match_id": match_id,
                        "import_job_id": import_job_id,
                        "team_id": parsed.team_id,
                        "player_id": parsed.player_id,
                        "event_type": parsed.event_type,
                        "minute": parsed.minute,
                        "second": parsed.second,
                        "period": period,
                        "x_coordinate": parsed.x_coordinate,
                        "y_coordinate": parsed.y_coordinate,
                        "notes": parsed.notes,
                        "source_provider": SourceProvider.VEO,
                        "source_event_id": parsed.provider_event_id,
                        "source": EventSource.IMPORT,
                        "provider": EventProvider.VEO,
                        "provider_event_id": parsed.provider_event_id,
                        "raw_payload": parsed.raw_payload,
                    }
                )
            )
        except ValidationError as exc:
            warnings.append(f"Row {index}: {exc.errors()[0]['msg']}")
    return events, warnings
