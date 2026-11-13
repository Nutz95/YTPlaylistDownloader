from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.download.ytdlp_media_format_args import YtdlpMediaFormatArgs


def test_audio_mode_uses_bestaudio() -> None:
    args = YtdlpMediaFormatArgs().for_mode(JobMediaMode.AUDIO)
    assert args == ["-f", "bestaudio/best"]


def test_video_mode_merges_best_streams_to_mp4() -> None:
    args = YtdlpMediaFormatArgs().for_mode(JobMediaMode.VIDEO)
    assert args == [
        "-f",
        "bestvideo*+bestaudio/best",
        "--merge-output-format",
        "mp4",
    ]
