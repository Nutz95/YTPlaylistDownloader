from fastapi.responses import JSONResponse

from ytpd.ports.output_catalog import OutputCatalog
from ytpd.web.catalog_entry_codec import CatalogEntryCodec


class CatalogApiHandler:
    """HTTP handlers for the finished MP3 catalogue."""

    def __init__(self, catalog: OutputCatalog) -> None:
        self._catalog = catalog
        self._codec = CatalogEntryCodec()

    def list_catalog(self) -> JSONResponse:
        """Return all catalogue entries."""
        entries = [self._codec.to_payload(item) for item in self._catalog.list_entries()]
        return JSONResponse(content={"entries": entries})
