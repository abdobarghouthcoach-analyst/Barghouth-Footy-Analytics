from enum import Enum


class ImportProvider(str, Enum):
    VEO = "veo"
    CSV = "csv"
    OTHER = "other"


class ImportStatus(str, Enum):
    CREATED = "created"
    PENDING = "created"
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    PARSING = "parsing"
    RUNNING = "parsing"
    NORMALIZING = "normalizing"
    PERSISTING = "persisting"
    COMPLETED = "completed"
    FAILED = "failed"
