from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for bind address and working directories."""

    host: str
    port: int
    work_dir: str
    dest_dir: str
