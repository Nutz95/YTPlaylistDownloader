import subprocess
from collections.abc import Sequence


class SubprocessTextRunner:
    """Run a subprocess capturing stdout/stderr as text with resilient decoding."""

    def run(
        self,
        argv: Sequence[str],
        timeout_sec: float,
    ) -> subprocess.CompletedProcess[str]:
        """Run ``argv``; replace undecodable bytes so Windows cp1252 never crashes."""
        return subprocess.run(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
