from ytpd.runtime.os_process_ref import OsProcessRef
from ytpd.runtime.sibling_ytpd_process_guard import SiblingYtpdProcessGuard
from tests.fakes.fake_process_killer import FakeProcessKiller
from tests.fakes.fake_process_lister import FakeProcessLister


def test_terminates_other_ytpd_servers_not_self_or_ytdlp() -> None:
    killer = FakeProcessKiller()
    guard = SiblingYtpdProcessGuard(
        FakeProcessLister(
            [
                OsProcessRef(100, r"python.exe -m ytpd"),
                OsProcessRef(200, r"python.exe -m yt_dlp https://x"),
                OsProcessRef(300, r"python.exe -m ytpd"),
                OsProcessRef(999, r"python.exe -m ytpd"),
            ]
        ),
        killer,
        current_pid=999,
        parent_pid=1,
        settle_sec=0.0,
    )
    report = guard.terminate_siblings()
    assert report.killed_pids == [100, 300]
    assert killer.killed_pids == [100, 300]


def test_does_not_kill_windows_python_parent_wrapper() -> None:
    killer = FakeProcessKiller()
    guard = SiblingYtpdProcessGuard(
        FakeProcessLister(
            [
                OsProcessRef(50, r"python.exe -m ytpd"),
                OsProcessRef(100, r"python.exe -m ytpd"),
            ]
        ),
        killer,
        current_pid=100,
        parent_pid=50,
        settle_sec=0.0,
    )
    report = guard.terminate_siblings()
    assert report.killed_pids == []
    assert killer.killed_pids == []
