from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_snapshot_codec import JobSnapshotCodec


def test_codec_round_trips_chapter_fields() -> None:
    snapshot = JobSnapshot(
        job_id="job-1",
        source_url="https://youtu.be/vid",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.QUEUED,
        tracks=[
            TrackRef(
                track_id="vid__ch00",
                title="Intro",
                artist="Channel",
                duration_sec=30,
                source_kind=SourceKind.YOUTUBE_VIDEO,
                phase=TrackPhase.MATCHED,
                youtube_url="https://youtu.be/vid",
                deezer_id=None,
                error_message=None,
                chapter_start_sec=0.0,
                chapter_end_sec=30.5,
                parent_video_id="vid",
                chapter_index=0,
            )
        ],
        error_message=None,
    )
    codec = JobSnapshotCodec()
    payload = codec.to_payload(snapshot)
    restored = codec.from_payload(payload)
    track = restored.tracks[0]
    assert track.chapter_start_sec == 0.0
    assert track.chapter_end_sec == 30.5
    assert track.parent_video_id == "vid"
    assert track.chapter_index == 0


def test_codec_accepts_legacy_track_without_chapter_keys() -> None:
    codec = JobSnapshotCodec()
    text = """
    {
      "job_id": "job-1",
      "source_url": "https://youtu.be/abc",
      "source_kind": "youtube_video",
      "status": "queued",
      "error_message": null,
      "pipeline_stage": null,
      "tracks": [
        {
          "track_id": "t1",
          "title": "Song",
          "artist": "Artist",
          "duration_sec": 120,
          "source_kind": "youtube_video",
          "phase": "resolved",
          "youtube_url": "https://youtu.be/abc",
          "deezer_id": null,
          "error_message": null
        }
      ]
    }
    """
    snapshot = codec.from_json_text(text)
    assert snapshot.tracks[0].parent_video_id is None
    assert snapshot.tracks[0].chapter_index is None
