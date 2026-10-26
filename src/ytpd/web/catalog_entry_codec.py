from ytpd.domain.catalog_entry import CatalogEntry
from ytpd.web.catalog_entry_json_payload import CatalogEntryJsonPayload


class CatalogEntryCodec:
    """Encode catalogue entries for JSON responses."""

    def to_payload(self, entry: CatalogEntry) -> CatalogEntryJsonPayload:
        """Convert one catalogue entry into a JSON-friendly mapping."""
        return {
            "track_id": entry.track_id,
            "title": entry.title,
            "artist": entry.artist,
            "mp3_path": entry.mp3_path,
            "youtube_url": entry.youtube_url,
            "deezer_id": entry.deezer_id,
        }
