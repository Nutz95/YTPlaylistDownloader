from typing import Protocol

from ytpd.domain.catalog_entry import CatalogEntry


class OutputCatalog(Protocol):
    """Persist and list finished destination files in the output catalogue."""

    def upsert(self, entry: CatalogEntry) -> None:
        """Insert or update one catalogue entry."""

    def delete(self, track_id: str) -> None:
        """Remove one catalogue entry by track id when present."""

    def list_entries(self) -> list[CatalogEntry]:
        """Return all catalogue entries."""
