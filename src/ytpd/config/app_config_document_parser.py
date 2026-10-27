from pathlib import Path

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_document import AppConfigDocument
from ytpd.config.invalid_app_config_error import InvalidAppConfigError


class AppConfigDocumentParser:
    """Validate a typed config document into ``AppConfig``."""

    def parse(self, document: AppConfigDocument) -> AppConfig:
        """Convert a structured document into runtime settings."""
        host = document["bind_host"].strip()
        if host == "":
            raise InvalidAppConfigError("bind_host must be a non-empty string")
        port = document["bind_port"]
        if port < 1 or port > 65535:
            raise InvalidAppConfigError("bind_port must be between 1 and 65535")
        work_dir = document["work_dir"].strip()
        if work_dir == "":
            raise InvalidAppConfigError("work_dir must be a non-empty string")
        dest_dir = document["dest_dir"].strip()
        if dest_dir == "":
            raise InvalidAppConfigError("dest_dir must be a non-empty string")
        if "lm_base_url" not in document or document["lm_base_url"].strip() == "":
            raise InvalidAppConfigError("lm_base_url must be a non-empty string")
        if "lm_model" not in document or document["lm_model"].strip() == "":
            raise InvalidAppConfigError("lm_model must be a non-empty string")
        if "lm_timeout_sec" not in document:
            raise InvalidAppConfigError("lm_timeout_sec must be a number")
        lm_timeout_sec = float(document["lm_timeout_sec"])
        if lm_timeout_sec <= 0:
            raise InvalidAppConfigError("lm_timeout_sec must be positive")
        return AppConfig(
            host=host,
            port=port,
            work_dir=Path(work_dir),
            dest_dir=Path(dest_dir),
            lm_base_url=document["lm_base_url"].strip(),
            lm_model=document["lm_model"].strip(),
            lm_timeout_sec=lm_timeout_sec,
        )
