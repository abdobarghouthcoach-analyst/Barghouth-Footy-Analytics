from enum import Enum


class ImportProvider(str, Enum):
    VEO = "veo"
    CSV = "csv"
    OTHER = "other"


class ImportStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
