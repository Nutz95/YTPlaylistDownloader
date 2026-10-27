import imageio_ffmpeg


class ImageioFfmpegExeLocator:
    """Locate the ffmpeg binary bundled by the ``imageio-ffmpeg`` wheel."""

    def locate(self) -> str | None:
        """Return the bundled exe path, or ``None`` when empty."""
        path = imageio_ffmpeg.get_ffmpeg_exe()
        if path is None or str(path).strip() == "":
            return None
        return str(path)
