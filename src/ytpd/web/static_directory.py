from importlib import resources
from pathlib import Path


class StaticDirectory:
    """Resolve the packaged static assets directory for the web UI."""

    def resolve(self) -> Path:
        """Return a filesystem path to ``ytpd.web`` static files."""
        static_root = resources.files("ytpd.web") / "static"
        return Path(str(static_root))
