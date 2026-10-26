from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for bind address, directories, and LM Studio."""

    host: str
    port: int
    work_dir: Path
    dest_dir: Path
    lm_base_url: str
    lm_model: str
    lm_timeout_sec: float
