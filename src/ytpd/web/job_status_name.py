from typing import Literal

JobStatusName = Literal[
    "queued",
    "running",
    "paused",
    "interrupted",
    "completed",
    "failed",
    "cancelled",
]
