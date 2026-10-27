import json
from typing import cast

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.persisted_match_candidate import PersistedMatchCandidate
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.match_candidate_payload_parser import MatchCandidatePayloadParser
from ytpd.jobs.track_chapter_payload_parser import TrackChapterPayloadParser
from ytpd.web.job_json_payload import JobJsonPayload
from ytpd.web.job_status_name import JobStatusName
from ytpd.web.match_candidate_json_payload import MatchCandidateJsonPayload
from ytpd.web.pipeline_stage_name import PipelineStageName
from ytpd.web.source_kind_name import SourceKindName
from ytpd.web.track_json_payload import TrackJsonPayload
from ytpd.web.track_phase_name import TrackPhaseName


class JobSnapshotCodec:
    """Convert job snapshots to/from the shared JSON payload contract."""

    def __init__(self) -> None:
        self._chapter_parser = TrackChapterPayloadParser()
        self._candidate_parser = MatchCandidatePayloadParser()

    def to_payload(self, snapshot: JobSnapshot) -> JobJsonPayload:
        """Serialize a snapshot into the API/checkpoint JSON shape."""
        stage = (
            cast(PipelineStageName, snapshot.pipeline_stage.value)
            if snapshot.pipeline_stage is not None
            else None
        )
        return {
            "job_id": snapshot.job_id,
            "source_url": snapshot.source_url,
            "source_kind": cast(SourceKindName, snapshot.source_kind.value),
            "status": cast(JobStatusName, snapshot.status.value),
            "error_message": snapshot.error_message,
            "tracks": [self._track_to_payload(track) for track in snapshot.tracks],
            "pipeline_stage": stage,
        }

    def from_json_text(self, text: str) -> JobSnapshot:
        """Deserialize a JSON text blob into a typed snapshot."""
        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise InvalidJobError("job payload must be a JSON object")
        job_id = loaded.get("job_id")
        source_url = loaded.get("source_url")
        source_kind = loaded.get("source_kind")
        status = loaded.get("status")
        error_message = loaded.get("error_message")
        tracks_raw = loaded.get("tracks")
        pipeline_stage = loaded.get("pipeline_stage")
        if not isinstance(job_id, str) or not isinstance(source_url, str):
            raise InvalidJobError("job_id/source_url must be strings")
        if not isinstance(source_kind, str) or not isinstance(status, str):
            raise InvalidJobError("source_kind/status must be strings")
        if error_message is not None and not isinstance(error_message, str):
            raise InvalidJobError("error_message must be a string or null")
        if not isinstance(tracks_raw, list):
            raise InvalidJobError("tracks must be a list")
        if pipeline_stage is not None and not isinstance(pipeline_stage, str):
            raise InvalidJobError("pipeline_stage must be a string or null")
        try:
            SourceKind(source_kind)
            JobStatus(status)
            if pipeline_stage is not None:
                PipelineStage(pipeline_stage)
        except ValueError as error:
            raise InvalidJobError(str(error)) from error
        tracks_payload = [self._parse_track_mapping(item) for item in tracks_raw]
        payload: JobJsonPayload = {
            "job_id": job_id,
            "source_url": source_url,
            "source_kind": cast(SourceKindName, source_kind),
            "status": cast(JobStatusName, status),
            "error_message": error_message,
            "tracks": tracks_payload,
            "pipeline_stage": (
                cast(PipelineStageName, pipeline_stage)
                if pipeline_stage is not None
                else None
            ),
        }
        return self.from_payload(payload)

    def from_payload(self, payload: JobJsonPayload) -> JobSnapshot:
        """Deserialize a JSON payload into a typed snapshot."""
        tracks = [self._track_from_payload(item) for item in payload["tracks"]]
        stage_raw = payload.get("pipeline_stage")
        stage = PipelineStage(stage_raw) if stage_raw is not None else None
        return JobSnapshot(
            job_id=payload["job_id"],
            source_url=payload["source_url"],
            source_kind=SourceKind(payload["source_kind"]),
            status=JobStatus(payload["status"]),
            tracks=tracks,
            error_message=payload["error_message"],
            pipeline_stage=stage,
        )

    def _parse_track_mapping(self, item: TrackJsonPayload) -> TrackJsonPayload:
        if not isinstance(item, dict):
            raise InvalidJobError("track payload must be an object")
        track_id = item.get("track_id")
        title = item.get("title")
        artist = item.get("artist")
        duration_sec = item.get("duration_sec")
        source_kind = item.get("source_kind")
        phase = item.get("phase")
        youtube_url = item.get("youtube_url")
        deezer_id = item.get("deezer_id")
        error_message = item.get("error_message")
        chapter_fields = self._chapter_parser.parse(item)
        match_candidates = self._candidate_parser.parse(item.get("match_candidates"))
        if not isinstance(track_id, str) or not isinstance(title, str) or not isinstance(artist, str):
            raise InvalidJobError("track_id/title/artist must be strings")
        if duration_sec is not None and (
            isinstance(duration_sec, bool) or not isinstance(duration_sec, int)
        ):
            raise InvalidJobError("duration_sec must be an int or null")
        if not isinstance(source_kind, str) or not isinstance(phase, str):
            raise InvalidJobError("track source_kind/phase must be strings")
        if youtube_url is not None and not isinstance(youtube_url, str):
            raise InvalidJobError("youtube_url must be a string or null")
        if deezer_id is not None and not isinstance(deezer_id, str):
            raise InvalidJobError("deezer_id must be a string or null")
        if error_message is not None and not isinstance(error_message, str):
            raise InvalidJobError("track error_message must be a string or null")
        try:
            SourceKind(source_kind)
            TrackPhase(phase)
        except ValueError as error:
            raise InvalidJobError(str(error)) from error
        candidates_payload = [
            self._candidate_to_payload(candidate) for candidate in match_candidates
        ]
        return {
            "track_id": track_id,
            "title": title,
            "artist": artist,
            "duration_sec": duration_sec,
            "source_kind": cast(SourceKindName, source_kind),
            "phase": cast(TrackPhaseName, phase),
            "youtube_url": youtube_url,
            "deezer_id": deezer_id,
            "error_message": error_message,
            "chapter_start_sec": chapter_fields.chapter_start_sec,
            "chapter_end_sec": chapter_fields.chapter_end_sec,
            "parent_video_id": chapter_fields.parent_video_id,
            "chapter_index": chapter_fields.chapter_index,
            "match_candidates": candidates_payload,
        }

    def _track_to_payload(self, track: TrackRef) -> TrackJsonPayload:
        return {
            "track_id": track.track_id,
            "title": track.title,
            "artist": track.artist,
            "duration_sec": track.duration_sec,
            "source_kind": cast(SourceKindName, track.source_kind.value),
            "phase": cast(TrackPhaseName, track.phase.value),
            "youtube_url": track.youtube_url,
            "deezer_id": track.deezer_id,
            "error_message": track.error_message,
            "chapter_start_sec": track.chapter_start_sec,
            "chapter_end_sec": track.chapter_end_sec,
            "parent_video_id": track.parent_video_id,
            "chapter_index": track.chapter_index,
            "match_candidates": [
                self._candidate_to_payload(candidate)
                for candidate in track.match_candidates
            ],
        }

    def _candidate_to_payload(
        self,
        candidate: PersistedMatchCandidate,
    ) -> MatchCandidateJsonPayload:
        return {
            "youtube_url": candidate.youtube_url,
            "title": candidate.title,
            "channel": candidate.channel,
            "duration_sec": candidate.duration_sec,
        }

    def _track_from_payload(self, item: TrackJsonPayload) -> TrackRef:
        return TrackRef(
            track_id=item["track_id"],
            title=item["title"],
            artist=item["artist"],
            duration_sec=item["duration_sec"],
            source_kind=SourceKind(item["source_kind"]),
            phase=TrackPhase(item["phase"]),
            youtube_url=item["youtube_url"],
            deezer_id=item["deezer_id"],
            error_message=item["error_message"],
            chapter_start_sec=item.get("chapter_start_sec"),
            chapter_end_sec=item.get("chapter_end_sec"),
            parent_video_id=item.get("parent_video_id"),
            chapter_index=item.get("chapter_index"),
            match_candidates=self._candidate_parser.parse(
                item.get("match_candidates")
            ),
        )
