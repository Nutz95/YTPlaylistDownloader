import os
import time

from ytpd.ports.process_killer import ProcessKiller
from ytpd.ports.process_lister import ProcessLister
from ytpd.runtime.sibling_process_termination_report import (
    SiblingProcessTerminationReport,
)
from ytpd.runtime.ytpd_server_command_matcher import YtpdServerCommandMatcher


class SiblingYtpdProcessGuard:
    """Terminate other ytpd server processes so only this instance remains."""

    def __init__(
        self,
        process_lister: ProcessLister,
        process_killer: ProcessKiller,
        command_matcher: YtpdServerCommandMatcher | None = None,
        current_pid: int | None = None,
        parent_pid: int | None = None,
        settle_sec: float = 0.4,
    ) -> None:
        self._process_lister = process_lister
        self._process_killer = process_killer
        self._command_matcher = command_matcher or YtpdServerCommandMatcher()
        self._current_pid = os.getpid() if current_pid is None else current_pid
        self._parent_pid = os.getppid() if parent_pid is None else parent_pid
        self._settle_sec = max(0.0, settle_sec)

    def terminate_siblings(self) -> SiblingProcessTerminationReport:
        """Kill every other matching ytpd server and return their PIDs."""
        protected = {self._current_pid, self._parent_pid}
        killed: list[int] = []
        for process in self._process_lister.list_processes():
            if process.pid in protected:
                continue
            if not self._command_matcher.matches(process.command_line):
                continue
            self._process_killer.kill(process.pid)
            killed.append(process.pid)
        if killed and self._settle_sec > 0:
            time.sleep(self._settle_sec)
        return SiblingProcessTerminationReport(killed_pids=killed)
