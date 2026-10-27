from importlib import resources
from pathlib import Path

import yaml

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_document import AppConfigDocument
from ytpd.config.app_config_document_parser import AppConfigDocumentParser
from ytpd.config.app_config_yaml_loader import AppConfigYamlLoader
from ytpd.config.invalid_app_config_error import InvalidAppConfigError
from ytpd.config.path_validator import PathValidator


class AppConfigStore:
    """Load and atomically persist application config YAML."""

    def __init__(self, writable_path: Path, path_validator: PathValidator) -> None:
        self._writable_path = writable_path
        self._path_validator = path_validator
        self._yaml_loader = AppConfigYamlLoader()
        self._document_parser = AppConfigDocumentParser()

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
            lm_base_url=config.lm_base_url,
            lm_model=config.lm_model,
            lm_timeout_sec=config.lm_timeout_sec,
        )
        self._writable_path.parent.mkdir(parents=True, exist_ok=True)
        document = self.to_document(normalized)
        text = yaml.safe_dump(dict(document), sort_keys=False)
        temporary_path = self._writable_path.with_suffix(".yaml.tmp")
        temporary_path.write_text(text, encoding="utf-8")
        temporary_path.replace(self._writable_path)
        return normalized

    def load_text(self, text: str) -> AppConfig:
        """Parse YAML text into a validated ``AppConfig``."""
        defaults = self._yaml_loader.load_text(self._read_packaged_default())
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise InvalidAppConfigError("Config root must be a mapping")
        document = self._yaml_loader.merge_with_defaults(loaded, defaults)
        return self._document_parser.parse(document)

    def to_document(self, config: AppConfig) -> AppConfigDocument:
        """Serialize runtime settings into a structured config document."""
        return {
            "bind_host": config.host,
            "bind_port": config.port,
            "work_dir": config.work_dir.as_posix(),
            "dest_dir": config.dest_dir.as_posix(),
            "lm_base_url": config.lm_base_url,
            "lm_model": config.lm_model,
            "lm_timeout_sec": config.lm_timeout_sec,
        }

    def _read_packaged_default(self) -> str:
        config_root = resources.files("ytpd.config")
        return (config_root / "default.yaml").read_text(encoding="utf-8")
