from enum import Enum


class ImportProvider(str, Enum):
    VEO = "veo"
    CSV = "csv"
    OTHER = "other"


class ImportStatus(str, Enum):
    CREATED = "created"
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    PARSING = "parsing"
    NORMALIZING = "normalizing"
    PERSISTING = "persisting"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"
