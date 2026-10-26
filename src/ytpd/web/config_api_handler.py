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

    def _to_payload(self, config: AppConfig) -> dict[str, str | int | float]:
        return {
            "bind_host": config.host,
            "bind_port": config.port,
            "work_dir": config.work_dir.as_posix(),
            "dest_dir": config.dest_dir.as_posix(),
            "lm_base_url": config.lm_base_url,
            "lm_model": config.lm_model,
            "lm_timeout_sec": config.lm_timeout_sec,
        }

    def _parse_body(self, body: Mapping[str, str | int | float]) -> AppConfig:
        current = self._store.load()
        raw_host = body.get("bind_host", current.host)
        raw_port = body.get("bind_port", current.port)
        raw_work = body.get("work_dir", current.work_dir.as_posix())
        raw_dest = body.get("dest_dir", current.dest_dir.as_posix())
        raw_lm_url = body.get("lm_base_url", current.lm_base_url)
        raw_lm_model = body.get("lm_model", current.lm_model)
        raw_lm_timeout = body.get("lm_timeout_sec", current.lm_timeout_sec)
        if not isinstance(raw_host, str):
            raise InvalidAppConfigError("bind_host must be a string")
        if isinstance(raw_port, bool) or not isinstance(raw_port, int):
            raise InvalidAppConfigError("bind_port must be an integer")
        if not isinstance(raw_work, str):
            raise InvalidAppConfigError("work_dir must be a string")
        if not isinstance(raw_dest, str):
            raise InvalidAppConfigError("dest_dir must be a string")
        if not isinstance(raw_lm_url, str):
            raise InvalidAppConfigError("lm_base_url must be a string")
        if not isinstance(raw_lm_model, str):
            raise InvalidAppConfigError("lm_model must be a string")
        if isinstance(raw_lm_timeout, bool) or not isinstance(
            raw_lm_timeout, (int, float)
        ):
            raise InvalidAppConfigError("lm_timeout_sec must be a number")
        return AppConfig(
            host=raw_host,
            port=raw_port,
            work_dir=Path(raw_work),
            dest_dir=Path(raw_dest),
            lm_base_url=raw_lm_url,
            lm_model=raw_lm_model,
            lm_timeout_sec=float(raw_lm_timeout),
        )
