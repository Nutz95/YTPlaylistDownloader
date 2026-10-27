import sys

import uvicorn

from ytpd.application_composer import ApplicationComposer
from ytpd.runtime.sibling_ytpd_process_guard import SiblingYtpdProcessGuard
from ytpd.runtime.taskkill_process_killer import TaskkillProcessKiller
from ytpd.runtime.windows_cim_process_lister import WindowsCimProcessLister


def main() -> None:
    """Stop sibling ytpd servers, compose the app, and serve on localhost."""
    if sys.platform.startswith("win"):
        report = SiblingYtpdProcessGuard(
            WindowsCimProcessLister(),
            TaskkillProcessKiller(),
        ).terminate_siblings()
        if len(report.killed_pids) > 0:
            print(
                "Stopped previous ytpd instance(s): "
                + ", ".join(str(pid) for pid in report.killed_pids),
                flush=True,
            )
    composed = ApplicationComposer().compose()
    if composed.gil_warning is not None:
        print(composed.gil_warning, flush=True)
    settings = composed.settings
    print(f"Serving on http://{settings.host}:{settings.port}", flush=True)
    uvicorn.run(
        composed.app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
