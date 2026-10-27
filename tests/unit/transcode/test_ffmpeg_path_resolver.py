from ytpd.transcode.ffmpeg_path_resolver import FfmpegPathResolver
from tests.fakes.fake_imageio_ffmpeg_exe_locator import FakeImageioFfmpegExeLocator


def test_configured_path_wins_over_imageio() -> None:
    resolver = FfmpegPathResolver(
        configured_path=r"C:\Tools\ffmpeg.exe",
        imageio_locator=FakeImageioFfmpegExeLocator(r"C:\bundled\ffmpeg.exe"),
    )
    assert resolver.resolve() == r"C:\Tools\ffmpeg.exe"


def test_imageio_used_when_config_empty() -> None:
    resolver = FfmpegPathResolver(
        configured_path="",
        imageio_locator=FakeImageioFfmpegExeLocator(r"C:\bundled\ffmpeg.exe"),
    )
    assert resolver.resolve() == r"C:\bundled\ffmpeg.exe"


def test_falls_back_to_path_name_when_imageio_missing() -> None:
    resolver = FfmpegPathResolver(
        configured_path="",
        imageio_locator=FakeImageioFfmpegExeLocator(None),
    )
    assert resolver.resolve() == "ffmpeg"
