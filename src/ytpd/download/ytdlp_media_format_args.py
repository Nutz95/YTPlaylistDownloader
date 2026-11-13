from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.domain.job_media_mode_policy import JobMediaModePolicy


class YtdlpMediaFormatArgs:
    """Build yt-dlp format argv fragments from the job media-mode policy."""

    def for_mode(self, mode: JobMediaMode) -> list[str]:
        """Return format flags for the given media mode."""
        return list(JobMediaModePolicy.for_mode(mode).ytdlp_format_args)
