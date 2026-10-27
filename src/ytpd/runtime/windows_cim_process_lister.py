import json
import subprocess

from ytpd.runtime.os_process_ref import OsProcessRef

_POWERSHELL = [
    "powershell",
    "-NoProfile",
    "-Command",
    (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='python' "
        "OR Name='ytpd.exe'\" | "
        "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    ),
]


class WindowsCimProcessLister:
    """List Python / ytpd processes via Windows CIM (PowerShell)."""

    def list_processes(self) -> list[OsProcessRef]:
        """Return python/ytpd process rows; empty list when the query fails."""
        try:
            completed = subprocess.run(
                _POWERSHELL,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15.0,
            )
        except OSError:
            return []
        except subprocess.TimeoutExpired:
            return []
        if completed.returncode != 0:
            return []
        return self._parse_json(completed.stdout.strip())

    def _parse_json(self, text: str) -> list[OsProcessRef]:
        if text == "":
            return []
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            return []
        rows = loaded if isinstance(loaded, list) else [loaded]
        processes: list[OsProcessRef] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            pid_raw = row.get("ProcessId")
            command_raw = row.get("CommandLine")
            if not isinstance(pid_raw, int):
                continue
            command = command_raw if isinstance(command_raw, str) else ""
            processes.append(OsProcessRef(pid=pid_raw, command_line=command))
        return processes
