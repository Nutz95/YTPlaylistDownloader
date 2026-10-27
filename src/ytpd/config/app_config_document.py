from typing import TypedDict


class AppConfigDocument(TypedDict):
    """Structured YAML/JSON document for application settings."""

    bind_host: str
    bind_port: int
    work_dir: str
    dest_dir: str
    lm_base_url: str
    lm_model: str
    lm_timeout_sec: float
    youtube_cookies_from_browser: str
    youtube_cookies_file: str
    ffmpeg_path: str
