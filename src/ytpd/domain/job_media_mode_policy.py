from dataclasses import dataclass

from ytpd.domain.job_media_mode import JobMediaMode


@dataclass(frozen=True)
class JobMediaModePolicy:
    """Canonical behaviour for one job media mode (paths, yt-dlp, resolve)."""

    download_suffix: str
    destination_extension: str
    ytdlp_format_args: list[str]
    collapse_chapters: bool

    @staticmethod
    def for_mode(mode: JobMediaMode) -> "JobMediaModePolicy":
        """Return the fixed policy for ``mode``."""
        if mode is JobMediaMode.VIDEO:
            return JobMediaModePolicy(
                download_suffix=".mp4",
                destination_extension="mp4",
                ytdlp_format_args=[
                    "-f",
                    "bestvideo*+bestaudio/best",
                    "--merge-output-format",
                    "mp4",
                ],
                collapse_chapters=True,
            )
        return JobMediaModePolicy(
            download_suffix=".media",
            destination_extension="mp3",
            ytdlp_format_args=["-f", "bestaudio/best"],
            collapse_chapters=False,
        )
