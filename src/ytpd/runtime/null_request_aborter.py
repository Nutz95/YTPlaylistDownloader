class NullRequestAborter:
    """No-op aborter used when no abortable HTTP client is wired."""

    def abort(self) -> None:
        """Do nothing."""
