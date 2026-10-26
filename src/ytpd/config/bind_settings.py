from dataclasses import dataclass


@dataclass(frozen=True)
class BindSettings:
    """Local HTTP bind host and port for the web UI."""

    host: str
    port: int
