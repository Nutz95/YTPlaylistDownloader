from typing import cast

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.web.job_list_item_json_payload import JobListItemJsonPayload
from ytpd.web.job_status_name import JobStatusName
from ytpd.web.pipeline_stage_name import PipelineStageName
from ytpd.web.source_kind_name import SourceKindName


class JobListItemCodec:
    """Convert job snapshots to lightweight list-row payloads."""

    def to_payload(self, snapshot: JobSnapshot) -> JobListItemJsonPayload:
        """Serialize a job summary without embedding track bodies."""
        stage = (
            cast(PipelineStageName, snapshot.pipeline_stage.value)
            if snapshot.pipeline_stage is not None
            else None
        )
        return {
            "job_id": snapshot.job_id,
            "source_url": snapshot.source_url,
            "source_kind": cast(SourceKindName, snapshot.source_kind.value),
            "status": cast(JobStatusName, snapshot.status.value),
            "track_count": len(snapshot.tracks),
            "error_message": snapshot.error_message,
            "pipeline_stage": stage,
        }
