from ytpd.domain.track_phase import TrackPhase

ACTIVE_TRACK_PHASES = frozenset(
    {
        TrackPhase.MATCHING,
        TrackPhase.DOWNLOADING,
        TrackPhase.TRANSCODING,
    }
)

DONE_TRACK_PHASES = frozenset({TrackPhase.DONE, TrackPhase.SKIPPED})

FAILED_TRACK_PHASES = frozenset(
    {
        TrackPhase.MATCH_FAILED,
        TrackPhase.ERROR,
    }
)

MATCH_DONE_TRACK_PHASES = frozenset(
    {
        TrackPhase.MATCHED,
        TrackPhase.MATCH_FAILED,
        TrackPhase.DOWNLOADING,
        TrackPhase.DOWNLOADED,
        TrackPhase.TRANSCODING,
        TrackPhase.DONE,
        TrackPhase.SKIPPED,
        TrackPhase.ERROR,
    }
)

DOWNLOAD_DONE_TRACK_PHASES = frozenset(
    {
        TrackPhase.DOWNLOADED,
        TrackPhase.TRANSCODING,
        TrackPhase.DONE,
        TrackPhase.SKIPPED,
    }
)

TRANSCODE_DONE_TRACK_PHASES = frozenset({TrackPhase.DONE, TrackPhase.SKIPPED})

MEDIA_DONE_TRACK_PHASES = frozenset({TrackPhase.DONE, TrackPhase.SKIPPED})
