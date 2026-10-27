from fastapi import Request
from fastapi.responses import JSONResponse

from ytpd.config.app_config_document_parser import AppConfigDocumentParser
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.app_config_yaml_loader import AppConfigYamlLoader
from ytpd.config.invalid_app_config_error import InvalidAppConfigError


class ConfigApiHandler:
    """HTTP handlers for reading and updating application config."""

    def __init__(self, store: AppConfigStore) -> None:
        self._store = store
        self._parser = AppConfigDocumentParser()
        self._yaml_loader = AppConfigYamlLoader()

    async def get_config(self) -> JSONResponse:
        """Return the current config as JSON."""
        return JSONResponse(content=self._store.to_document(self._store.load()))

    async def put_config(self, request: Request) -> JSONResponse:
        """Validate JSON body, persist config, and return the saved payload."""
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse(
                status_code=400,
                content={"error": "JSON body must be an object"},
            )
        try:
            defaults = self._store.to_document(self._store.load())
            document = self._yaml_loader.merge_with_defaults(body, defaults)
            config = self._store.save(self._parser.parse(document))
        except InvalidAppConfigError as error:
            return JSONResponse(status_code=400, content={"error": str(error)})
        return JSONResponse(content=self._store.to_document(config))
