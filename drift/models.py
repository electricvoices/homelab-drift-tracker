from datetime import datetime
from enum import Enum

from dataclasses import dataclass

class DriftKind(Enum):
# IMAGE_UPDATED, RESTARTED, MEM_MISMATCH, MISSING, UNEXPECTED (values = readable labels).
    IMAGE_UPDATED = "Image Updated"
    RESTARTED = "Restarted"
    MEM_MISMATCH = "Memory Mismatch"
    MISSING = "Missing"
    UNEXPECTED = "Unexpected"

@dataclass
class ContainerSnapshot:
    name: str
    image: str
    image_id: str
    restart_count: int
    started_at: datetime
    mem_bytes: int
    taken_at: datetime

    def __post_init__(self):
        if self.name.startswith("/"):
            self.name = self.name.lstrip("/")
