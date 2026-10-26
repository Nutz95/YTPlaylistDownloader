from fastapi.testclient import TestClient

from ytpd.web.app_factory import AppFactory
from ytpd.web.template_directory import TemplateDirectory


def test_home_page_returns_ok() -> None:
    app = AppFactory(TemplateDirectory().resolve()).build()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "OK" in response.text
    assert "YTPlaylistDownloader" in response.text
