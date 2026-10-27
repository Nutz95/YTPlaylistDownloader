from ytpd.domain.download_progress_snapshot import DownloadProgressSnapshot


class DownloadProgressDetailFormatter:
    """Format a live download snapshot for progress UI detail text."""

    def format(self, snapshot: DownloadProgressSnapshot) -> str:
        """Return a short human-readable progress line."""
        if snapshot.status == "waiting":
            return "waiting for audio download slot (shared media)"
        if snapshot.status == "starting":
            return "starting audio download (bestaudio)…"
        if snapshot.status == "complete":
            size_text = self._size_text(snapshot)
            if size_text != "":
                return f"audio download complete · {size_text}"
            return "audio download complete (not full video)"
        if snapshot.status == "failed":
            return f"failed — {snapshot.message}"
        if snapshot.percent is not None:
            size_text = self._size_text(snapshot)
            if size_text != "":
                return f"audio {snapshot.percent:.1f}% · {size_text}"
            return f"audio {snapshot.percent:.1f}%"
        return snapshot.message or "audio downloading…"

    def _size_text(self, snapshot: DownloadProgressSnapshot) -> str:
        if snapshot.downloaded_bytes is None:
            return ""
        downloaded = self._human_bytes(snapshot.downloaded_bytes)
        if snapshot.total_bytes is None:
            return downloaded
        return f"{downloaded}/{self._human_bytes(snapshot.total_bytes)}"

    def _human_bytes(self, size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024.0 or unit == "GB":
                if unit == "B":
                    return f"{int(value)} {unit}"
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{size} B"
