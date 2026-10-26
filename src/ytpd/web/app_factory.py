from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from ytpd.web.home_handler import HomeHandler


class AppFactory:
    """Build the FastAPI application and register HTTP routes."""

    def __init__(self, templates_dir: Path) -> None:
        self._templates_dir = templates_dir

    def build(self) -> FastAPI:
        """Create the app with Jinja templates and the home page route."""
        templates = Jinja2Templates(directory=str(self._templates_dir))
        home_handler = HomeHandler(templates)
        app = FastAPI(title="YTPlaylistDownloader")
        app.add_api_route("/", home_handler.handle, methods=["GET"])
        return app
