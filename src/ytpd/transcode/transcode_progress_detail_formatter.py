from ytpd.domain.transcode_progress_snapshot import TranscodeProgressSnapshot


class TranscodeProgressDetailFormatter:
    """Format a live encode snapshot for progress UI detail text."""

    def format(self, snapshot: TranscodeProgressSnapshot) -> str:
        """Return a short human-readable encode progress line."""
        backend = snapshot.backend_label
        if snapshot.status == "starting":
            return f"{backend} · starting…"
        if snapshot.status == "complete":
            return f"{backend} · done"
        if snapshot.status == "failed":
            return f"{backend} · failed — {snapshot.message}"
        if snapshot.percent is not None:
            return f"{backend} · {snapshot.percent:.0f}%"
        return f"{backend} · {snapshot.message or 'encoding…'}"
