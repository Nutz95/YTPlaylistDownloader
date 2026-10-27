from ytpd.domain.track_phase import TrackPhase

TRACK_PHASE_WEIGHTS: dict[TrackPhase, float] = {
    TrackPhase.PENDING: 0.0,
    TrackPhase.RESOLVED: 0.05,
    TrackPhase.MATCHING: 0.15,
    TrackPhase.MATCHED: 0.4,
    TrackPhase.MATCH_FAILED: 0.4,
    TrackPhase.DOWNLOADING: 0.55,
    TrackPhase.DOWNLOADED: 0.7,
    TrackPhase.TRANSCODING: 0.85,
    TrackPhase.DONE: 1.0,
    TrackPhase.SKIPPED: 1.0,
    TrackPhase.ERROR: 1.0,
}
