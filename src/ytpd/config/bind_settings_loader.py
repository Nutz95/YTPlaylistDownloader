from collections.abc import Mapping
from importlib import resources

import yaml

from ytpd.config.bind_settings import BindSettings
from ytpd.config.invalid_bind_settings_error import InvalidBindSettingsError


class BindSettingsLoader:
    """Load and validate HTTP bind settings from packaged or inline YAML."""

    def load_default(self) -> BindSettings:
        """Load ``default.yaml`` shipped inside the ``ytpd.config`` package."""
        config_root = resources.files("ytpd.config")
        text = (config_root / "default.yaml").read_text(encoding="utf-8")
        return self.load_text(text)

    def load_text(self, text: str) -> BindSettings:
        """Parse YAML text into validated bind settings."""
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, Mapping):
            raise InvalidBindSettingsError("Config root must be a mapping")
        raw_host = loaded.get("bind_host")
        if not isinstance(raw_host, str):
            raise InvalidBindSettingsError("bind_host must be a non-empty string")
        raw_port = loaded.get("bind_port")
        if isinstance(raw_port, bool) or not isinstance(raw_port, int):
            raise InvalidBindSettingsError("bind_port must be an integer")
        return BindSettings(
            host=self._normalize_host(raw_host),
            port=self._normalize_port(raw_port),
        )

    def _normalize_host(self, raw_host: str) -> str:
        if raw_host.strip() == "":
            raise InvalidBindSettingsError("bind_host must be a non-empty string")
        return raw_host.strip()

    def _normalize_port(self, raw_port: int) -> int:
        if raw_port < 1 or raw_port > 65535:
            raise InvalidBindSettingsError("bind_port must be between 1 and 65535")
        return raw_port
