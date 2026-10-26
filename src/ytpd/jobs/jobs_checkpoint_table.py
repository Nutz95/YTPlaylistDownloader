from sqlalchemy import Column, MetaData, Table, Text
from sqlalchemy.engine import Engine


class JobsCheckpointTable:
    """SQLAlchemy table definition for persisted job JSON payloads."""

    def __init__(self) -> None:
        self._metadata = MetaData()
        self.table = Table(
            "jobs",
            self._metadata,
            Column("job_id", Text, primary_key=True),
            Column("payload_json", Text, nullable=False),
        )

    def create_all(self, engine: Engine) -> None:
        """Create the jobs table when missing."""
        self._metadata.create_all(engine)
