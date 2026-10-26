from pathlib import Path


class WritableConfigPath:
    """Resolve the user-writable ``config/app.yaml`` path under the process cwd."""

    def resolve(self) -> Path:
        """Return ``<cwd>/config/app.yaml``."""
        return Path.cwd() / "config" / "app.yaml"
