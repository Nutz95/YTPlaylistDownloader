# YTPlaylistDownloader

Local web app bound to `127.0.0.1`. Current UI has modular tabs (Job, Progression, Config, Catalogue). Config paths (`work_dir`, `dest_dir`) and bind settings are editable and persisted to `config/app.yaml`. Playlist resolve / download / MP3 pipeline comes in later work.

## Requirements

- Python **3.14** (free-threaded build preferred when available)

## Run

```powershell
.\Start-App.ps1
```

Open the URL printed in the console (default `http://127.0.0.1:8765`).

## Tests

```powershell
.\Run-Tests.ps1
```
