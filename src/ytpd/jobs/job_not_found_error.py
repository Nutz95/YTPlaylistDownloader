from ytpd.jobs.invalid_job_error import InvalidJobError


class JobNotFoundError(InvalidJobError):
    """Raised when a job id is missing from the checkpoint store."""

    def __init__(self) -> None:
        super().__init__("job not found")
