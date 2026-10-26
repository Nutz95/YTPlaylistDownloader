from collections.abc import Mapping
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.invalid_app_config_error import InvalidAppConfigError


class ConfigApiHandler:
    """HTTP handlers for reading and updating application config."""

    def __init__(self, store: AppConfigStore) -> None:
        self._store = store

    async def get_config(self) -> JSONResponse:
        """Return the current config as JSON."""
        config = self._store.load()
        return JSONResponse(content=self._to_payload(config))

    async def put_config(self, request: Request) -> JSONResponse:
        """Validate JSON body, persist config, and return the saved payload."""
        body = await request.json()
        if not isinstance(body, Mapping):
            return JSONResponse(
                status_code=400,
                content={"error": "JSON body must be an object"},
            )
        try:
            config = self._store.save(self._parse_body(body))
        except InvalidAppConfigError as error:
            return JSONResponse(status_code=400, content={"error": str(error)})
        return JSONResponse(content=self._to_payload(config))

    def _to_payload(self, config: AppConfig) -> dict[str, str | int]:
        return {
            "bind_host": config.host,
            "bind_port": config.port,
            "work_dir": config.work_dir.as_posix(),
            "dest_dir": config.dest_dir.as_posix(),
        }

    def _parse_body(self, body: Mapping[str, str | int]) -> AppConfig:
        raw_host = body.get("bind_host")
        raw_port = body.get("bind_port")
        raw_work = body.get("work_dir")
        raw_dest = body.get("dest_dir")
        if not isinstance(raw_host, str):
            raise InvalidAppConfigError("bind_host must be a string")
        if isinstance(raw_port, bool) or not isinstance(raw_port, int):
            raise InvalidAppConfigError("bind_port must be an integer")
        if not isinstance(raw_work, str):
            raise InvalidAppConfigError("work_dir must be a string")
        if not isinstance(raw_dest, str):
            raise InvalidAppConfigError("dest_dir must be a string")
        return AppConfig(
            host=raw_host,
            port=raw_port,
            work_dir=Path(raw_work),
            dest_dir=Path(raw_dest),
        )
