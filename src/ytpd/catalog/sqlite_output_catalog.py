from pathlib import Path

from sqlalchemy import Column, MetaData, String, Table, create_engine, select, text
from sqlalchemy.engine import Engine

from ytpd.domain.catalog_entry import CatalogEntry


class SqliteOutputCatalog:
    """SQLite-backed catalogue of finished destination output files."""

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
            Column("output_path", String, nullable=False),
            Column("youtube_url", String, nullable=True),
            Column("deezer_id", String, nullable=True),
        )
        self._metadata.create_all(self._engine)
        self._migrate_legacy_mp3_path_column()

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
                    output_path=entry.output_path,
                    youtube_url=entry.youtube_url,
                    deezer_id=entry.deezer_id,
                )
            )

    def delete(self, track_id: str) -> None:
        """Remove one catalogue row by track id when present."""
        with self._engine.begin() as connection:
            connection.execute(
                self._table.delete().where(self._table.c.track_id == track_id)
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
                    output_path=row["output_path"],
                    youtube_url=row["youtube_url"],
                    deezer_id=row["deezer_id"],
                )
                for row in rows
            ]

    def _migrate_legacy_mp3_path_column(self) -> None:
        with self._engine.begin() as connection:
            columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(catalog_entries)"))
            }
            if "mp3_path" in columns and "output_path" not in columns:
                connection.execute(
                    text(
                        "ALTER TABLE catalog_entries RENAME COLUMN mp3_path TO output_path"
                    )
                )
