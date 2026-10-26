from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef


class TrackStateMachine:
    """Decision table for the next resume action of one track."""

    def decide(self, track: TrackRef, artifacts: TrackArtifactFlags) -> ResumeAction:
        """Choose the next action from phase, YouTube URL, and artefact flags."""
        phase = track.phase
        if phase is TrackPhase.SKIPPED or phase is TrackPhase.DONE:
            return ResumeAction.NONE
        if artifacts.mp3_present:
            return ResumeAction.NONE
        if track.youtube_url is None or track.youtube_url.strip() == "":
            return ResumeAction.MATCH
        if not artifacts.download_complete:
            return ResumeAction.DOWNLOAD
        return ResumeAction.TRANSCODE
