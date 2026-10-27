import shutil
import subprocess


class GpuCapabilityProbe:
    """Detect NVIDIA / Intel Arc availability from local tooling."""

    def has_nvidia(self) -> bool:
        """True when ``nvidia-smi`` reports at least one GPU."""
        if shutil.which("nvidia-smi") is None:
            return False
        try:
            completed = subprocess.run(
                ["nvidia-smi", "-L"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5.0,
            )
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
            completed = subprocess.run(
                ["ffmpeg", "-hide_banner", "-hwaccels"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5.0,
            )
        except OSError:
            return False
        except subprocess.TimeoutExpired:
            return False
        text = f"{completed.stdout}\n{completed.stderr}".casefold()
        return "qsv" in text
