from ytpd.domain.catalog_entry import CatalogEntry


class MemoryOutputCatalog:
    """In-memory catalogue used by offline unit tests."""

    def __init__(self) -> None:
        self._entries: dict[str, CatalogEntry] = {}

    def upsert(self, entry: CatalogEntry) -> None:
        """Insert or replace one entry by track id."""
        self._entries[entry.track_id] = entry

    def list_entries(self) -> list[CatalogEntry]:
        """Return catalogue entries sorted by track id."""
        return [self._entries[key] for key in sorted(self._entries)]
