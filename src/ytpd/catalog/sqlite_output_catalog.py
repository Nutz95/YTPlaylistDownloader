from pathlib import Path

from sqlalchemy import Column, MetaData, String, Table, create_engine, select
from sqlalchemy.engine import Engine

from ytpd.domain.catalog_entry import CatalogEntry


class SqliteOutputCatalog:
    """SQLite-backed catalogue of finished destination MP3 files."""

    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine: Engine = create_engine(f"sqlite:///{database_path}")
        self._metadata = MetaData()
        self._table = Table(
            "catalog_entries",
            self._metadata,
            Column("track_id", String, primary_key=True),
            Column("title", String, nullable=False),
            Column("artist", String, nullable=False),
            Column("mp3_path", String, nullable=False),
            Column("youtube_url", String, nullable=True),
            Column("deezer_id", String, nullable=True),
        )
        self._metadata.create_all(self._engine)

    def upsert(self, entry: CatalogEntry) -> None:
        """Insert or replace one catalogue row."""
        with self._engine.begin() as connection:
            connection.execute(
                self._table.delete().where(self._table.c.track_id == entry.track_id)
            )
            connection.execute(
                self._table.insert().values(
                    track_id=entry.track_id,
                    title=entry.title,
                    artist=entry.artist,
                    mp3_path=entry.mp3_path,
                    youtube_url=entry.youtube_url,
                    deezer_id=entry.deezer_id,
                )
            )

    def list_entries(self) -> list[CatalogEntry]:
        """Return all catalogue rows ordered by track id."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(self._table).order_by(self._table.c.track_id)
            ).mappings()
            return [
                CatalogEntry(
                    track_id=row["track_id"],
                    title=row["title"],
                    artist=row["artist"],
                    mp3_path=row["mp3_path"],
                    youtube_url=row["youtube_url"],
                    deezer_id=row["deezer_id"],
                )
                for row in rows
            ]
