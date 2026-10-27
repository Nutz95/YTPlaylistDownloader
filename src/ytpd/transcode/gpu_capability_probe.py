import shutil
import subprocess

from ytpd.runtime.subprocess_text_runner import SubprocessTextRunner


class GpuCapabilityProbe:
    """Detect NVIDIA / Intel Arc availability from local tooling."""

    def __init__(self) -> None:
        self._runner = SubprocessTextRunner()

    def has_nvidia(self) -> bool:
        """True when ``nvidia-smi`` reports at least one GPU."""
        if shutil.which("nvidia-smi") is None:
            return False
        try:
            completed = self._runner.run(["nvidia-smi", "-L"], 5.0)
        except OSError:
            return False
        except subprocess.TimeoutExpired:
            return False
        return completed.returncode == 0 and "GPU" in completed.stdout

    def has_arc(self) -> bool:
        """True when ffmpeg advertises QSV and an Intel GPU name is visible."""
        if shutil.which("ffmpeg") is None:
            return False
        try:
            completed = self._runner.run(
                ["ffmpeg", "-hide_banner", "-hwaccels"],
                5.0,
            )
        except OSError:
            return False
        except subprocess.TimeoutExpired:
            return False
        text = f"{completed.stdout}\n{completed.stderr}".casefold()
        return "qsv" in text
