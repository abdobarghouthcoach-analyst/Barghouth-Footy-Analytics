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
