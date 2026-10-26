from pathlib import Path

from ytpd.config.invalid_app_config_error import InvalidAppConfigError


class PathValidator:
    """Validate and materialize directory paths used by the application."""

    def ensure_directory(self, raw_path: str | Path) -> Path:
        """Resolve ``raw_path`` and create the directory when missing."""
        text = raw_path if isinstance(raw_path, str) else raw_path.as_posix()
        if text.strip() == "":
            raise InvalidAppConfigError("directory path must be a non-empty string")
        resolved = Path(text).expanduser()
        if not resolved.is_absolute():
            resolved = (Path.cwd() / resolved).resolve()
        else:
            resolved = resolved.resolve()
        try:
            resolved.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise InvalidAppConfigError(
                f"cannot create directory {resolved}: {error}"
            ) from error
        if not resolved.is_dir():
            raise InvalidAppConfigError(f"path is not a directory: {resolved}")
        return resolved
