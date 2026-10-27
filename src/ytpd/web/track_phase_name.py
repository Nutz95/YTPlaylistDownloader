from typing import Literal

TrackPhaseName = Literal[
    "pending",
    "resolved",
    "matching",
    "matched",
    "match_failed",
    "downloading",
    "downloaded",
    "transcoding",
    "done",
    "skipped",
    "error",
]
