from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


class HomeHandler:
    """Serve the home page HTML response."""

    def __init__(self, templates: Jinja2Templates) -> None:
        self._templates = templates

    async def handle(self, request: Request) -> HTMLResponse:
        """Render ``home.html`` with a simple OK status payload."""
        return self._templates.TemplateResponse(
            request,
            name="home.html",
            context={"page_title": "YTPlaylistDownloader", "status_message": "OK"},
        )
