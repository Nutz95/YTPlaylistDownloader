from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.ports.track_artifact_probe import TrackArtifactProbe


class TrackPhaseHealer:
    """Advance stuck track phases when artefacts already exist on disk."""

    def __init__(self, artifact_probe: TrackArtifactProbe) -> None:
        self._artifact_probe = artifact_probe

    def heal(self, job: JobSnapshot) -> JobSnapshot:
        """Return ``job`` with healed tracks, or the same snapshot when unchanged."""
        changed = False
        tracks: list[TrackRef] = []
        for track in job.tracks:
            healed = self._heal_one(job, track)
            tracks.append(healed)
            if healed is not track:
                changed = True
        if not changed:
            return job
        return replace(job, tracks=tracks)

    def _heal_one(self, job: JobSnapshot, track: TrackRef) -> TrackRef:
        if track.phase in {TrackPhase.SKIPPED, TrackPhase.DONE}:
            return track
        flags = self._artifact_probe.flags_for(job, track)
        if flags.mp3_present:
            return replace(track, phase=TrackPhase.DONE, error_message=None)
        if track.phase is TrackPhase.TRANSCODING and flags.download_complete:
            return replace(track, phase=TrackPhase.DOWNLOADED, error_message=None)
        if (
            flags.download_complete
            and track.phase is not TrackPhase.DOWNLOADED
            and track.phase is not TrackPhase.TRANSCODING
        ):
            return replace(track, phase=TrackPhase.DOWNLOADED, error_message=None)
        return track
