from typing import Literal

TrackPhaseName = Literal[
    "pending",
    "resolved",
    "matched",
    "match_failed",
    "downloading",
    "downloaded",
    "transcoding",
    "done",
    "skipped",
    "error",
]
