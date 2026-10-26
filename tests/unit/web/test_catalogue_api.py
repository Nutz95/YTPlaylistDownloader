from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.fakes.build_test_app import BuildTestApp


def test_catalogue_endpoint_returns_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    app = BuildTestApp().build(tmp_path)
    client = TestClient(app)
    response = client.get("/api/catalog")
    assert response.status_code == 200
    body = response.json()
    assert "entries" in body
    assert body["entries"] == []
