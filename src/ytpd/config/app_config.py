from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for bind address and working directories."""

    host: str
    port: int
    work_dir: Path
    dest_dir: Path
