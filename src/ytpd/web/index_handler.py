from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ytpd.config.app_config import AppConfig


class IndexHandler:
    """Serve the tabbed shell page for the local web UI."""

    def __init__(self, templates: Jinja2Templates, config: AppConfig) -> None:
        self._templates = templates
        self._config = config

    async def handle(self, request: Request) -> HTMLResponse:
        """Render ``index.html`` with the current config values for forms."""
        return self._templates.TemplateResponse(
            request,
            name="index.html",
            context={
                "page_title": "YTPlaylistDownloader",
                "bind_host": self._config.host,
                "bind_port": self._config.port,
                "work_dir": self._config.work_dir,
                "dest_dir": self._config.dest_dir,
            },
        )
