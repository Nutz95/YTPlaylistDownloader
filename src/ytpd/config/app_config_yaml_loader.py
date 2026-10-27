import yaml

from ytpd.config.app_config_document import AppConfigDocument
from ytpd.config.invalid_app_config_error import InvalidAppConfigError


class AppConfigYamlLoader:
    """Load a YAML string into a typed ``AppConfigDocument``."""

    def load_text(self, text: str) -> AppConfigDocument:
        """Parse YAML into a structured config document."""
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise InvalidAppConfigError("Config root must be a mapping")
        return self._document_from_mapping(loaded)

    def merge_with_defaults(
        self,
        partial: dict[str, str | int | float],
        defaults: AppConfigDocument,
    ) -> AppConfigDocument:
        """Fill missing keys from ``defaults`` then validate types."""
        merged: dict[str, str | int | float] = dict(defaults)
        merged.update(partial)
        return self._document_from_mapping(merged)

    def _document_from_mapping(
        self,
        loaded: dict[str, str | int | float],
    ) -> AppConfigDocument:
        bind_host = loaded.get("bind_host")
        if not isinstance(bind_host, str):
            raise InvalidAppConfigError("bind_host must be a non-empty string")
        bind_port = loaded.get("bind_port")
        if isinstance(bind_port, bool) or not isinstance(bind_port, int):
            raise InvalidAppConfigError("bind_port must be an integer")
        work_dir = loaded.get("work_dir")
        if not isinstance(work_dir, str):
            raise InvalidAppConfigError("work_dir must be a non-empty string")
        dest_dir = loaded.get("dest_dir")
        if not isinstance(dest_dir, str):
            raise InvalidAppConfigError("dest_dir must be a non-empty string")
        lm_base_url = loaded.get("lm_base_url")
        if not isinstance(lm_base_url, str):
            raise InvalidAppConfigError("lm_base_url must be a non-empty string")
        lm_model = loaded.get("lm_model")
        if not isinstance(lm_model, str):
            raise InvalidAppConfigError("lm_model must be a non-empty string")
        lm_timeout_sec = loaded.get("lm_timeout_sec")
        if isinstance(lm_timeout_sec, bool) or not isinstance(
            lm_timeout_sec, (int, float)
        ):
            raise InvalidAppConfigError("lm_timeout_sec must be a number")
        cookies_browser = loaded.get("youtube_cookies_from_browser", "")
        if not isinstance(cookies_browser, str):
            raise InvalidAppConfigError(
                "youtube_cookies_from_browser must be a string"
            )
        cookies_file = loaded.get("youtube_cookies_file", "")
        if not isinstance(cookies_file, str):
            raise InvalidAppConfigError("youtube_cookies_file must be a string")
        ffmpeg_path = loaded.get("ffmpeg_path", "")
        if not isinstance(ffmpeg_path, str):
            raise InvalidAppConfigError("ffmpeg_path must be a string")
        return {
            "bind_host": bind_host,
            "bind_port": bind_port,
            "work_dir": work_dir,
            "dest_dir": dest_dir,
            "lm_base_url": lm_base_url,
            "lm_model": lm_model,
            "lm_timeout_sec": float(lm_timeout_sec),
            "youtube_cookies_from_browser": cookies_browser,
            "youtube_cookies_file": cookies_file,
            "ffmpeg_path": ffmpeg_path,
        }
