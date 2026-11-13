from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ytpd.config.app_config_store import AppConfigStore
from ytpd.domain.ui_locale import UiLocale


class IndexHandler:
    """Serve the tabbed shell page for the local web UI."""

    def __init__(self, templates: Jinja2Templates, config_store: AppConfigStore) -> None:
        self._templates = templates
        self._config_store = config_store

    async def handle(self, request: Request) -> HTMLResponse:
        """Render ``index.html`` with the current config values for forms."""
        config = self._config_store.load()
        return self._templates.TemplateResponse(
            request,
            name="index.html",
            context={
                "page_title": "YTPlaylistDownloader",
                "bind_host": config.host,
                "bind_port": config.port,
                "work_dir": config.work_dir.as_posix(),
                "dest_dir": config.dest_dir.as_posix(),
                "ui_locale": config.ui_locale.value,
                "ui_locales": UiLocale.codes(),
            },
        )
