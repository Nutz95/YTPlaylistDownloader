from pathlib import Path

from ytpd.config.invalid_app_config_error import InvalidAppConfigError


class PathValidator:
    """Validate and materialize directory paths used by the application."""

    def ensure_directory(self, raw_path: str | Path) -> Path:
        """Resolve ``raw_path`` under cwd, jail it, and create it when missing."""
        text = raw_path if isinstance(raw_path, str) else raw_path.as_posix()
        if text.strip() == "":
            raise InvalidAppConfigError("directory path must be a non-empty string")
        resolved = Path(text).expanduser()
        if not resolved.is_absolute():
            resolved = Path.cwd() / resolved
        resolved = resolved.resolve()
        self._require_under_cwd(resolved)
        try:
            resolved.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise InvalidAppConfigError(
                f"cannot create directory {resolved}: {error}"
            ) from error
        if not resolved.is_dir():
            raise InvalidAppConfigError(f"path is not a directory: {resolved}")
        return resolved

    def to_storage_path(self, absolute_path: Path) -> Path:
        """Return a cwd-relative path suitable for config files (no machine roots)."""
        resolved = absolute_path.resolve()
        self._require_under_cwd(resolved)
        return resolved.relative_to(Path.cwd().resolve())

    def _require_under_cwd(self, resolved: Path) -> None:
        cwd = Path.cwd().resolve()
        try:
            resolved.relative_to(cwd)
        except ValueError as error:
            raise InvalidAppConfigError(
                "directory must stay under the working directory "
                f"({cwd.as_posix()})"
            ) from error
