from collections.abc import Mapping

from ytpd.domain.job_create_request import JobCreateRequest
from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.jobs.invalid_job_error import InvalidJobError


class JobCreateRequestParser:
    """Parse a JSON object into a typed job-create request."""

    def parse(self, body: Mapping[str, str | bool | None]) -> JobCreateRequest:
        """Validate ``body`` and return a create request."""
        raw_url = body.get("url")
        if not isinstance(raw_url, str):
            raise InvalidJobError("url must be a non-empty string")
        raw_mode = body.get("media_mode")
        raw_force = body.get("force_reprocess")
        return JobCreateRequest(
            source_url=raw_url,
            media_mode=self._parse_media_mode(raw_mode),
            force_reprocess=self._parse_force(raw_force),
        )

    def _parse_media_mode(self, raw_mode: str | bool | None) -> JobMediaMode:
        if raw_mode is None:
            return JobMediaMode.AUDIO
        if not isinstance(raw_mode, str):
            raise InvalidJobError("media_mode must be 'audio' or 'video'")
        try:
            return JobMediaMode(raw_mode.strip().lower())
        except ValueError as error:
            raise InvalidJobError("media_mode must be 'audio' or 'video'") from error

    def _parse_force(self, raw_force: str | bool | None) -> bool:
        if raw_force is None:
            return False
        if not isinstance(raw_force, bool):
            raise InvalidJobError("force_reprocess must be a boolean")
        return raw_force
