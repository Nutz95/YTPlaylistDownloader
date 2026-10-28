from ytpd.domain.job_snapshot import JobSnapshot


class JobDisplayTitle:
    """Derive a human-facing source title for job list and progress labels."""

    def for_snapshot(self, snapshot: JobSnapshot) -> str | None:
        """Prefer persisted ``source_title``, else a single-track artist/title line."""
        if snapshot.source_title is not None and snapshot.source_title.strip() != "":
            return snapshot.source_title.strip()
        if len(snapshot.tracks) != 1:
            return None
        track = snapshot.tracks[0]
        if track.artist.strip() == "":
            return track.title
        return f"{track.artist} — {track.title}"
