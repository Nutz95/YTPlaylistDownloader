import subprocess


class TaskkillProcessKiller:
    """Force-terminate a Windows process tree with ``taskkill /T /F``."""

    def kill(self, pid: int) -> None:
        """Kill ``pid`` and its child processes; ignore missing-process errors."""
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15.0,
            )
        except OSError:
            return
        except subprocess.TimeoutExpired:
            return
