from importlib import resources
from pathlib import Path


class TemplateDirectory:
    """Resolve the packaged Jinja templates directory for the web UI."""

    def resolve(self) -> Path:
        """Return a filesystem path to ``ytpd.web`` templates."""
        templates_root = resources.files("ytpd.web") / "templates"
        return Path(str(templates_root))
