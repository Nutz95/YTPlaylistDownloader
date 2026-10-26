from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.web.config_api_handler import ConfigApiHandler
from ytpd.web.index_handler import IndexHandler


class AppFactory:
    """Build the FastAPI application and register HTTP routes."""

    def __init__(
        self,
        templates_dir: Path,
        static_dir: Path,
        config: AppConfig,
        config_store: AppConfigStore,
    ) -> None:
        self._templates_dir = templates_dir
        self._static_dir = static_dir
        self._config = config
        self._config_store = config_store

    def build(self) -> FastAPI:
        """Create the app with templates, static assets, pages, and config API."""
        templates = Jinja2Templates(directory=str(self._templates_dir))
        index_handler = IndexHandler(templates, self._config)
        config_handler = ConfigApiHandler(self._config_store)
        app = FastAPI(title="YTPlaylistDownloader")
        app.mount("/static", StaticFiles(directory=str(self._static_dir)), name="static")
        app.add_api_route("/", index_handler.handle, methods=["GET"])
        app.add_api_route("/api/config", config_handler.get_config, methods=["GET"])
        app.add_api_route("/api/config", config_handler.put_config, methods=["PUT"])
        return app
