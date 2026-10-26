from collections.abc import Mapping
from importlib import resources
from pathlib import Path

import yaml

from ytpd.config.app_config import AppConfig
from ytpd.config.invalid_app_config_error import InvalidAppConfigError
from ytpd.config.path_validator import PathValidator


class AppConfigStore:
    """Load and atomically persist application config YAML."""

    def __init__(self, writable_path: Path, path_validator: PathValidator) -> None:
        self._writable_path = writable_path
        self._path_validator = path_validator

    def load(self) -> AppConfig:
        """Load writable config when present, otherwise seed from the package default."""
        if self._writable_path.is_file():
            return self.load_text(self._writable_path.read_text(encoding="utf-8"))
        config = self.load_text(self._read_packaged_default())
        self.save(config)
        return config

    def save(self, config: AppConfig) -> AppConfig:
        """Validate directories, persist cwd-relative paths, and return the saved config."""
        work_absolute = self._path_validator.ensure_directory(config.work_dir)
        dest_absolute = self._path_validator.ensure_directory(config.dest_dir)
        normalized = AppConfig(
            host=config.host,
            port=config.port,
            work_dir=self._path_validator.to_storage_path(work_absolute),
            dest_dir=self._path_validator.to_storage_path(dest_absolute),
        )
        self._writable_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "bind_host": normalized.host,
            "bind_port": normalized.port,
            "work_dir": normalized.work_dir.as_posix(),
            "dest_dir": normalized.dest_dir.as_posix(),
        }
        text = yaml.safe_dump(payload, sort_keys=False)
        temporary_path = self._writable_path.with_suffix(".yaml.tmp")
        temporary_path.write_text(text, encoding="utf-8")
        temporary_path.replace(self._writable_path)
        return normalized

    def load_text(self, text: str) -> AppConfig:
        """Parse YAML text into a validated ``AppConfig``."""
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, Mapping):
            raise InvalidAppConfigError("Config root must be a mapping")
        raw_host = loaded.get("bind_host")
        if not isinstance(raw_host, str) or raw_host.strip() == "":
            raise InvalidAppConfigError("bind_host must be a non-empty string")
        raw_port = loaded.get("bind_port")
        if isinstance(raw_port, bool) or not isinstance(raw_port, int):
            raise InvalidAppConfigError("bind_port must be an integer")
        if raw_port < 1 or raw_port > 65535:
            raise InvalidAppConfigError("bind_port must be between 1 and 65535")
        raw_work = loaded.get("work_dir")
        if not isinstance(raw_work, str) or raw_work.strip() == "":
            raise InvalidAppConfigError("work_dir must be a non-empty string")
        raw_dest = loaded.get("dest_dir")
        if not isinstance(raw_dest, str) or raw_dest.strip() == "":
            raise InvalidAppConfigError("dest_dir must be a non-empty string")
        return AppConfig(
            host=raw_host.strip(),
            port=raw_port,
            work_dir=Path(raw_work.strip()),
            dest_dir=Path(raw_dest.strip()),
        )

    def _read_packaged_default(self) -> str:
        config_root = resources.files("ytpd.config")
        return (config_root / "default.yaml").read_text(encoding="utf-8")
