from ytpd.transcode.imageio_ffmpeg_exe_locator import ImageioFfmpegExeLocator
from ytpd.transcode.path_ffmpeg_exe_locator import PathFfmpegExeLocator


class FfmpegPathResolver:
    """Resolve the ffmpeg executable: config, then imageio-ffmpeg, then PATH."""

    def __init__(
        self,
        configured_path: str = "",
        imageio_locator: ImageioFfmpegExeLocator | None = None,
        path_locator: PathFfmpegExeLocator | None = None,
    ) -> None:
        self._configured_path = configured_path.strip()
        self._imageio_locator = imageio_locator or ImageioFfmpegExeLocator()
        self._path_locator = path_locator or PathFfmpegExeLocator()

    def resolve(self) -> str:
        """Return an absolute or command path usable as ffmpeg argv[0]."""
        if self._configured_path != "":
            return self._configured_path
        bundled = self._imageio_locator.locate()
        if bundled is not None and bundled.strip() != "":
            return bundled
        found = self._path_locator.locate()
        if found is not None and found.strip() != "":
            return found
        return "ffmpeg"
