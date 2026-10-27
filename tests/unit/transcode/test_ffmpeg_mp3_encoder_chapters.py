from pathlib import Path

from ytpd.domain.ffmpeg_encode_request import FfmpegEncodeRequest
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.transcode.ffmpeg_mp3_encoder import FfmpegMp3Encoder
from tests.fakes.recording_ffmpeg_runner import RecordingFfmpegRunner


def test_encoder_adds_ss_and_t_for_chapter_slice(tmp_path: Path) -> None:
    source = tmp_path / "src.media"
    source.write_bytes(b"audio")
    destination = tmp_path / "out.mp3"
    request = FfmpegEncodeRequest(
        track_id="vid__ch00",
        source=source,
        destination=destination,
        backend=TranscodeBackendKind.CPU,
        chapter_start_sec=10.0,
        chapter_duration_sec=20.0,
        metadata_title="Chapter Title",
        metadata_artist="Channel",
        expected_duration_sec=20.0,
    )
    runner = RecordingFfmpegRunner()
    result = FfmpegMp3Encoder(runner, "ffmpeg").encode(request)
    assert result.success is True
    assert destination.is_file()
    assert "-ss" in runner.last_argv
    assert "10.000" in runner.last_argv
    assert "-t" in runner.last_argv
    assert "20.000" in runner.last_argv
    assert "title=Chapter Title" in runner.last_argv
    assert "artist=Channel" in runner.last_argv
    assert runner.last_argv[-3:-1] == ["-f", "mp3"]
    assert runner.last_argv[-1].endswith(".vid__ch00.mp3.tmp") or ".vid__ch00.mp3.tmp" in runner.last_argv[-1]


def test_encoder_omits_slice_flags_without_chapter(tmp_path: Path) -> None:
    source = tmp_path / "src.media"
    source.write_bytes(b"audio")
    destination = tmp_path / "out.mp3"
    request = FfmpegEncodeRequest(
        track_id="plain",
        source=source,
        destination=destination,
        backend=TranscodeBackendKind.CPU,
        chapter_start_sec=None,
        chapter_duration_sec=None,
        metadata_title="Solo",
        metadata_artist="A",
        expected_duration_sec=None,
    )
    runner = RecordingFfmpegRunner()
    result = FfmpegMp3Encoder(runner, "ffmpeg").encode(request)
    assert result.success is True
    assert "-ss" not in runner.last_argv
    assert "-t" not in runner.last_argv
