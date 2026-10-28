from ytpd.jobs.invalid_job_error import InvalidJobError


class PipelineBusyError(InvalidJobError):
    """Raised when a pipeline start is refused because another job is running."""

    def __init__(self) -> None:
        super().__init__("a pipeline is already running")
