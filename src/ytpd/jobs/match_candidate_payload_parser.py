from ytpd.domain.persisted_match_candidate import PersistedMatchCandidate
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.web.match_candidate_json_payload import MatchCandidateJsonPayload


class MatchCandidatePayloadParser:
    """Parse persisted match-candidate list fields from track JSON."""

    def parse(self, raw: list[MatchCandidateJsonPayload] | None) -> list[PersistedMatchCandidate]:
        """Return typed candidates; empty when ``raw`` is missing."""
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise InvalidJobError("match_candidates must be a list")
        return [self._parse_one(item, index) for index, item in enumerate(raw)]

    def _parse_one(
        self,
        item: MatchCandidateJsonPayload,
        index: int,
    ) -> PersistedMatchCandidate:
        if not isinstance(item, dict):
            raise InvalidJobError(f"match_candidates[{index}] must be an object")
        youtube_url = item.get("youtube_url")
        title = item.get("title")
        channel = item.get("channel")
        duration_sec = item.get("duration_sec")
        if not isinstance(youtube_url, str) or youtube_url.strip() == "":
            raise InvalidJobError(f"match_candidates[{index}].youtube_url invalid")
        if not isinstance(title, str) or not isinstance(channel, str):
            raise InvalidJobError(f"match_candidates[{index}] title/channel must be strings")
        if duration_sec is not None and (
            isinstance(duration_sec, bool) or not isinstance(duration_sec, int)
        ):
            raise InvalidJobError(f"match_candidates[{index}].duration_sec invalid")
        return PersistedMatchCandidate(
            youtube_url=youtube_url,
            title=title,
            channel=channel,
            duration_sec=duration_sec,
        )
