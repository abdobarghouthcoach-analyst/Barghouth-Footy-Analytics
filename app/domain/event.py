from enum import Enum


class EventPeriod(str, Enum):
    FIRST_HALF = "1H"
    SECOND_HALF = "2H"
    EXTRA_TIME = "ET"
    PENALTIES = "P"


class SourceProvider(str, Enum):
    MANUAL = "manual"
    VEO = "veo"
    OTHER = "other"


class EventSource(str, Enum):
    MANUAL = "manual"
    IMPORT = "import"


class EventProvider(str, Enum):
    VEO = "veo"
    OTHER = "other"


class EventConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"
