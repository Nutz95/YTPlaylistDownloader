from typing import Protocol

from ytpd.domain.catalog_entry import CatalogEntry


class OutputCatalog(Protocol):
    """Persist and list finished destination MP3 catalogue entries."""

    def upsert(self, entry: CatalogEntry) -> None:
        """Insert or update one catalogue entry."""

    def list_entries(self) -> list[CatalogEntry]:
        """Return all catalogue entries."""
