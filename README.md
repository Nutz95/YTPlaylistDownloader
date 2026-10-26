# YTPlaylistDownloader

Local web app on `127.0.0.1` that resolves Deezer / YouTube playlists, matches
tracks to YouTube, downloads media, and transcodes to MP3 (192 kbps).

## Requirements

- Python **3.14** (free-threaded build preferred)
- `ffmpeg` on `PATH` for transcoding
- Optional: [LM Studio](https://lmstudio.ai/) on `http://127.0.0.1:1234/v1` for
  LLM match fallback when static scoring is weak

## Run

```powershell
.\Start-App.ps1
```

Open the URL printed in the console (default `http://127.0.0.1:8765`).

## Daily usage

1. **Config** tab — set relative `work_dir` / `dest_dir` (and LM Studio settings).
2. **Job** tab — paste a Deezer playlist, YouTube playlist, or single video URL.
3. **Create job**, then either:
   - **Run pipeline** for resolve → match → download → transcode, or
   - step with Resolve / Match / Download / Transcode.
4. After restart, pick a saved job from the list (no need to copy a job id).
5. **Resume** rebuilds the next actions from checkpoints; **Cancel** stops the
   active pipeline between stages.
6. **Catalogue** tab lists finished MP3 paths.

Progress lives under the **Progression** tab (poll-based bars).

## Tests

```powershell
.\Run-Tests.ps1
```
