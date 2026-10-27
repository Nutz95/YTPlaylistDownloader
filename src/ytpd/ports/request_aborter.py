from typing import Protocol


class RequestAborter(Protocol):
    """Abort in-flight outbound HTTP so cooperative cancel can unblock."""

    def abort(self) -> None:
        """Cancel outstanding requests; safe to call repeatedly."""
