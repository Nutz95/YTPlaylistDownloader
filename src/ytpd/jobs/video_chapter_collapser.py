from dataclasses import replace

from ytpd.domain.track_ref import TrackRef


class VideoChapterCollapser:
    """Collapse chapter-expanded tracks into one full-video track per parent."""

    def collapse(
        self,
        tracks: list[TrackRef],
        fallback_title: str | None,
    ) -> list[TrackRef]:
        """Return full-video tracks only (no chapter slice metadata)."""
        plain: list[TrackRef] = []
        by_parent: dict[str, list[TrackRef]] = {}
        for track in tracks:
            parent = self._parent_id(track)
            if parent is None:
                plain.append(self._without_chapters(track))
                continue
            group = by_parent.get(parent)
            if group is None:
                by_parent[parent] = [track]
            else:
                group.append(track)
        collapsed = list(plain)
        for parent_id, group in by_parent.items():
            collapsed.append(self._full_from_group(group, parent_id, fallback_title))
        return collapsed

    def _parent_id(self, track: TrackRef) -> str | None:
        if track.parent_video_id is None:
            return None
        cleaned = track.parent_video_id.strip()
        if cleaned == "":
            return None
        return cleaned

    def _full_from_group(
        self,
        group: list[TrackRef],
        parent_id: str,
        fallback_title: str | None,
    ) -> TrackRef:
        first = group[0]
        title = fallback_title.strip() if fallback_title is not None else ""
        if title == "":
            title = first.title
        starts = [
            track.chapter_start_sec
            for track in group
            if track.chapter_start_sec is not None
        ]
        ends = [
            track.chapter_end_sec
            for track in group
            if track.chapter_end_sec is not None
        ]
        duration_sec: int | None = None
        if len(starts) > 0 and len(ends) > 0:
            duration_sec = int(round(max(ends) - min(starts)))
        return TrackRef(
            track_id=parent_id,
            title=title,
            artist=first.artist,
            duration_sec=duration_sec,
            source_kind=first.source_kind,
            phase=first.phase,
            youtube_url=first.youtube_url,
            deezer_id=first.deezer_id,
            error_message=None,
        )

    def _without_chapters(self, track: TrackRef) -> TrackRef:
        if (
            track.chapter_start_sec is None
            and track.chapter_end_sec is None
            and track.parent_video_id is None
            and track.chapter_index is None
        ):
            return track
        return replace(
            track,
            chapter_start_sec=None,
            chapter_end_sec=None,
            parent_video_id=None,
            chapter_index=None,
        )
