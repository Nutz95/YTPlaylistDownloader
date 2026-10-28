from ytpd.jobs.invalid_job_error import InvalidJobError


class DuplicateSourceUrlError(InvalidJobError):
    """Raised when create is asked for a source URL that already has a job."""
