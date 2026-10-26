# Plan — YTPlaylistDownloader

Application Python locale : serveur web minimal (127.0.0.1), résolution de playlists Deezer / YouTube, matching YouTube (statique puis LLM via LM Studio), téléchargement et transcodage MP3 avec pipeline parallèle et workers GPU (NVIDIA CUDA / Intel Arc QSV) + CPU (N = nombre de cœurs).

## Contraintes non négociables

| Règle | Détail |
|-------|--------|
| Python | **3.14** free-threaded (`python3.14t` / build `nogil`) — vrai parallélisme threads pour resolve/match/download/transcode |
| SOLID + DI | Interfaces (`Protocol`) ; composition root unique ; fakes sous `tests/fakes/` |
| Guardrails | `solid-python` : ≤400 lignes/fichier, ≤60 lignes/fonction, ≤30 méthodes/classe, **1 type = 1 fichier**, pas de nested class/def, pas de `object`/`Any`, pas de `tuple` métier |
| Typage | `dataclass` / `Enum` / `TypedDict` concrets ; collections `list[T]` / `dict[str, T]` uniquement |
| Tests | **Unitaires à chaque lot** (offline) + guardrails verts |
| HTML | Templates **modulaires par onglet** (includes Jinja), JS/CSS segmentés |
| Portable | Script de packaging ZIP + wheelhouse (`ops-portable-python-package`) |

Skills / tools déjà déployés : `.cursor/skills`, `.cursor/rules`, `tools/python_guardrails`.

---

## 1. Objectif produit

| Entrée | Comportement |
|--------|----------------|
| Lien playlist Deezer (`link.deezer.com/...` ou URL Deezer longue) | Résoudre → liste (artiste, titre, durée) → match YouTube officiel → DL → MP3 destination |
| Lien playlist YouTube (`list=...`) | Lister chaque entrée (titre, durée, **URL**) → DL → MP3 |
| Lien vidéo YouTube seule | Conserver le lien → DL → MP3 |

### UI

- Onglets séparés (fichiers HTML distincts) : **Job**, **Progression**, **Config**, **Catalogue** (évent. **Logs**).
- Barre de progression **globale** du job + **une barre par média en cours** (download et/ou transcode) avec détail (%, phase, vitesse, ETA si dispo).
- Reprise automatique des jobs incomplets au démarrage.

---

## 2. Architecture cible

```text
┌──────────────────────────────────────────────────────────────────┐
│  Browser (onglets HTML modulaires)                               │
│  Job | Progression | Config | Catalogue                          │
│  progress: barre globale + barres médias actifs (SSE/poll)       │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼─────────────────────────────────────┐
│  FastAPI composition root (app_factory) — 127.0.0.1              │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  JobOrchestrator  +  JobCheckpointStore (persist / resume)       │
│                                                                  │
│   ResolveMatchPool (threads 3.14) ──▶ DownloadPool (threads)     │
│         │                                │                       │
│         │ track matched                  │ fichier DL ready      │
│         ▼                                ▼                       │
│   (Deezer only)                    TranscodeScheduler            │
│   StaticMatcher → LlmMatcher*        │                           │
│                                      ├─ NvidiaWorker (1)         │
│                                      ├─ ArcWorker (1)            │
│                                      └─ CpuWorkers (N = cores)   │
│                                                                  │
│   * LLM sous GpuResourceGate (jamais // au transcode GPU)        │
└──────────────────────────────────────────────────────────────────┘
```

### Pipeline (plus de phases globales bloquantes)

Ancien modèle « tout resolve → tout match → tout download → tout transcode » **abandonné**.

Nouveau modèle **streaming par track** :

1. **Resolve playlist** (une fois) → produit `list[TrackRef]` persistée.
2. **ResolveMatchPool** : pour chaque track Deezer non matché, match **en parallèle** (statique ; LLM sérialisé via gate). Tracks YouTube déjà « matched ».
3. Dès qu’un track a une URL YouTube → enfilé dans **DownloadPool** (parallèle).
4. Dès qu’un download est **complet** → enfilé dans **TranscodeScheduler** (GPU d’abord, CPU = `os.cpu_count()`).
5. Checkpoint après chaque transition d’état track (voir §4.8).

### Principes SOLID / modules

- **1 fichier = 1 classe** (ou 1 Enum / 1 Protocol / 1 exception) — rule `python-one-type-per-file`.
- Aucun `tuple` de retour : toujours un dataclass résultat (`MatchResult`, `DownloadResult`, …).
- Aucun `object` / `Any` / `dict` nu aux frontières publiques.
- Orchestrateur **ne connaît pas** FFmpeg ni Deezer : il parle à des Protocols injectés.
- Workers I/O et CPU : **threads** sur interpréteur 3.14 free-threaded (pas de multiprocessing forcé ; subprocess FFmpeg/yt-dlp restent des process enfants).

### Arborescence proposée

```text
YTPlaylistDownloader/
  plan/
  .cursor/
  tools/python_guardrails/
  config/default.yaml
  src/ytpd/
    __init__.py
    __main__.py
    app_factory.py                 # composition root uniquement
    runtime/
      python_version_guard.py      # exige 3.14 (+ warn si GIL actif)
    config/
      app_config.py                # dataclass AppConfig
      config_store.py
      path_validator.py
    domain/
      source_kind.py               # Enum
      track_phase.py               # Enum
      track_ref.py
      track_progress.py
      job_status.py
      job_snapshot.py
      progress_snapshot.py
      global_progress.py
      media_progress.py
    ports/                         # Protocols (1 Protocol / fichier)
      playlist_resolver.py
      youtube_matcher.py
      media_downloader.py
      transcode_backend.py
      job_checkpoint_store.py
      output_catalog.py
      progress_publisher.py
      resource_gate.py
    resolve/
      url_classifier.py
      deezer_resolver.py
      youtube_resolver.py
      resolve_match_pool.py
    match/
      static_youtube_matcher.py
      match_score.py
      match_candidate.py
      llm_youtube_matcher.py
    lmstudio/
      lm_studio_client.py
      lm_studio_model_loader.py
      lm_studio_error.py
    download/
      ytdlp_downloader.py
      download_pool.py
      download_resume_policy.py
    transcode/
      ffmpeg_probe.py
      backend_detect.py
      worker_nvidia.py
      worker_arc.py
      worker_cpu.py
      transcode_scheduler.py
      gpu_resource_gate.py
      cpu_parallelism.py           # N = os.cpu_count()
    catalog/
      sqlite_output_catalog.py
      dest_dir_scanner.py
    jobs/
      job_orchestrator.py
      job_store.py
      sqlite_job_checkpoint_store.py
      job_resume_service.py
      track_state_machine.py
    web/
      routes_jobs.py
      routes_config.py
      routes_progress.py
      templates/
        base.html
        index.html                 # shell + includes onglets
        tabs/
          tab_job.html
          tab_progress.html
          tab_config.html
          tab_catalogue.html
      static/
        css/
          app.css
          progress.css
        js/
          tabs.js
          job_form.js
          progress_bars.js         # barre globale + barres médias
          config_form.js
  tests/
    fakes/                         # 1 fake / port
    unit/                          # miroir des packages, 1 lot → tests
    quality/
      test_guardrails.py
  requirements.txt
  Start-App.ps1
  Package-Portable.ps1             # packaging ZIP (ops-portable)
  README.md
```

---

## 3. Décisions techniques figées

| Sujet | Choix |
|-------|--------|
| Python | **3.14 free-threaded** ; `Start-App.ps1` refuse de démarrer sous autre minor ; log si build encore avec GIL |
| Serveur | **FastAPI** + Uvicorn, bind `127.0.0.1` |
| UI HTML | Jinja2 : `base` + `tabs/*.html` inclus ; **1 fichier = 1 onglet** |
| Progression | SSE `GET /api/jobs/{id}/events` (+ poll fallback) ; payloads typés `ProgressSnapshot` |
| Config | YAML + API ; écriture atomique |
| Deezer | API publique après resolve short-link |
| YouTube | **yt-dlp** |
| Match | ytsearch heuristique puis LLM LM Studio |
| LLM | `http://127.0.0.1:1234/v1`, modèle `qwen3.8-27b-gsq-rco` |
| Audio | **MP3 CBR 192 kbps** |
| Vidéo intermédiaire | audio-first ; sinon ≤1080p (préf. 720p) puis extract |
| GPU | NVIDIA + Arc workers dédiés ; encode MP3 = `libmp3lame` (CPU) ; GPU pour decode/demux parallèle |
| CPU parallel | `max_parallel_cpu = os.cpu_count()` (override config possible) |
| Checkpoint | SQLite job + tracks (métadonnées API / match **persistées**) |
| Catalogue sorties | SQLite + scan `dest_dir` |
| Portable | `Package-Portable.ps1` → ZIP wheelhouse Python 3.14 |
| Lanceur | `Start-App.ps1` |

### Clarification free-threading 3.14

- Exiger un interpréteur **3.14** ; préférer le binaire free-threaded (`python3.14t` / install « free-threaded ») quand disponible.
- Au boot : `sys._is_gil_enabled()` si présent — si GIL encore actif → warning visible (perf dégradée) mais démarrage OK si 3.14.
- Les pools (`ResolveMatchPool`, `DownloadPool`, workers transcode) utilisent `threading` + files thread-safe.
- yt-dlp / FFmpeg restent des **subprocess** (naturellement parallèles) ; les threads orchestrent l’I/O et l’état.

### Clarification transcodage GPU

Pour du MP3 final, l’encode audio est CPU. Les backends GPU :

1. Accélèrent le decode vidéo (NVDEC / QSV).
2. Permettent de traiter **plusieurs médias en //** (1 file NVIDIA + 1 file Arc + N files CPU).
3. Restent exclusifs vs LLM via `GpuResourceGate`.

---

## 4. Flux métier détaillé

### 4.1 Classification URL

1. `link.deezer.com` / `deezer.com` → Deezer
2. YouTube + `list=` → playlist
3. YouTube / youtu.be → vidéo
4. Sinon → erreur claire

### 4.2 Resolve Deezer / YouTube

Inchangé fonctionnellement (API Deezer / yt-dlp flat-playlist), mais résultat **écrit immédiatement** dans le checkpoint (pas de re-fetch au resume).

### 4.3 Matching (parallèle)

Pool de threads : chaque track Deezer `resolved` sans `youtube_url` est matché indépendamment.

- Statique d’abord (parallélisable).
- LLM : **au plus 1 à la fois**, derrière `GpuResourceGate.acquire_llm()` ; si LM Studio down → erreur claire, track reste `match_failed` (reprise possible plus tard).

### 4.4 Download (parallèle + resume)

- Pool borné (`max_parallel_downloads`, défaut configurable).
- yt-dlp : tenter **reprise** (`continuedl` / fichiers partiels `.part`) si artefact incomplet présent.
- Si reprise échoue → supprimer partiel + **retry download complet** (N tentatives).
- À la fin → événement `download_ready` → file transcode (sans attendre la fin de toute la playlist).

### 4.5 Transcode → MP3 192k (pipeline)

- Dès qu’un media est ready → scheduler.
- Priorité : NVIDIA idle → Arc idle → CPU (jusqu’à `os.cpu_count()` workers).
- Transcodes **non** checkpointés comme « précieux » : au resume, si MP3 absent → **relancer** transcode depuis le fichier DL (s’il est complet) ; si DL incomplet → politique §4.4.
- Écriture atomique vers `dest_dir` + catalogue.

### 4.6 Skip catalogue

Clés : `youtube_video_id`, `deezer_track_id`, clé normalisée artiste|titre.

Si MP3 destination + catalogue OK → `skipped` (ni DL ni transcode).

### 4.7 Progression (UI)

`ProgressSnapshot` agrège :

| Champ | Rôle |
|-------|------|
| `GlobalProgress` | % job = f(tracks done+skipped / total) + phase dominante + ETA globale si estimable |
| `list[MediaProgress]` | Uniquement médias **actifs** (downloading / transcoding) : %, bytes, vitesse, backend, titre |
| `list[TrackProgress]` | Tableau résumé (phase, erreur courte) pour l’onglet Progression |

Barres :

1. **Barre globale** (onglet Progression + bandeau sticky optionnel).
2. **Barres médias** (une carte/barre par download ou transcode en cours, détail texte sous la barre).

### 4.8 Checkpoint & reprise (critique)

Persisté sous `{work_dir}/jobs/{job_id}/checkpoint.sqlite` (ou DB centrale jobs) :

| Donnée | Persister ? | Au resume |
|--------|-------------|-----------|
| URL source, kind, job id | oui | recharger |
| Liste tracks + métadonnées API (artiste, titre, durée, ids) | **oui** | **ne pas** re-appeler Deezer/YT list API |
| Résultat match + youtube_url + scores | **oui** | skip match si déjà matched |
| Chemins artefacts DL partiels / complets | oui | reprise DL ou skip |
| État phase par track | oui | reprendre à la phase manquante |
| Progression volatile (%, vitesse) | non (recalcul) | — |
| Transcode en cours | non obligatoire | **relancer** transcode si MP3 manquant |

**Au lancement app** : `JobResumeService` scanne les jobs `running` / `paused` / `interrupted` → propose reprise auto (ou bouton « Reprendre »).

Crash / kill process → au prochain start, statut `interrupted` → reprise.

---

## 5. API web

| Méthode | Chemin | Rôle |
|---------|--------|------|
| GET | `/` | Shell UI (onglets) |
| GET | `/api/config` | Lire config |
| PUT | `/api/config` | Écrire config |
| POST | `/api/jobs` | `{ "url": "..." }` → job |
| GET | `/api/jobs` | Liste jobs (dont incomplets) |
| GET | `/api/jobs/{id}` | Snapshot typé |
| GET | `/api/jobs/{id}/progress` | `ProgressSnapshot` |
| GET | `/api/jobs/{id}/events` | SSE progression |
| POST | `/api/jobs/{id}/cancel` | Cancel |
| POST | `/api/jobs/{id}/resume` | Reprise manuelle |
| GET | `/api/catalog` | Entrées déjà produites |

---

## 6. Config (`config/default.yaml`)

```yaml
# Packaged defaults (ytpd/config/default.yaml); user overrides in config/app.yaml
bind_host: "127.0.0.1"
bind_port: 8765
work_dir: "_work"
dest_dir: "_out"
# Later lots add:
# catalog_db, jobs_db, mp3_bitrate_kbps, youtube heights, parallelism,
# lmstudio, transcode backends, resume policy
```

---

## 7. Lanceurs

### `Start-App.ps1`

1. `#Requires -Version 5.1` ; `$ErrorActionPreference = "Stop"`.
2. Vérifier **Python 3.14** (préférer free-threaded) — sinon erreur actionnable.
3. Créer `.venv` avec ce Python si absent.
4. `pip install -r requirements.txt` si besoin.
5. Vérifier `ffmpeg` (PATH) + message NVENC/QSV.
6. `python -m ytpd` → URL 127.0.0.1.

### `Package-Portable.ps1` (skill `ops-portable-python-package`)

1. Whitelist `src/ytpd`, `config`, templates/static, launchers, `requirements.txt`.
2. `pip download --only-binary=:all:` → `wheelhouse/` (tag cp314 / plateforme).
3. `Setup-Venv.ps1` offline + `Run-App.ps1`.
4. ZIP final sans `.venv`, tests, `_work`, secrets.

---

## 8. Lots de réalisation

Chaque lot = code + **tests unitaires offline** + guardrails. Critère transverse : **1 type / fichier**, DI, pas de tuples métier.

### Lot 0 — Socle Python 3.14 + hello web — DONE

- [x] `pyproject` / `requirements.txt` ; package `src/ytpd`.
- [x] `PythonVersionGuard` (3.14).
- [x] `Start-App.ps1` (venv 3.14 + run) + `Run-Tests.ps1` + `Ensure-Python314Venv.ps1`.
- [x] FastAPI hello + `base.html` (puis remplacé par shell onglets au Lot 1).
- [x] `tests/quality/test_guardrails.py` (+ PublicDocstringGuard).
- [x] Tests version guard / composer.

**Done** : page OK sur 127.0.0.1 sous Python 3.14.

---

### Lot 1 — Config + UI onglets modulaires — DONE

- [x] `AppConfig` + `AppConfigStore` + `PathValidator` + `WritableConfigPath`.
- [x] GET/PUT `/api/config` (persistance atomique `config/app.yaml`).
- [x] Templates : `index.html` + `tabs/tab_job.html`, `tab_progress.html`, `tab_config.html`, `tab_catalogue.html`.
- [x] `tabs.js` + `config_form.js` + `app.css`.
- [x] Tests unitaires store / paths / API / onglets.

**Done** : 4 onglets séparés en fichiers ; chemins persistés.

---

### Lot 2 — Domaine typé + JobStore + Checkpoint

- [ ] Enums / dataclasses domaine (1/fichier) : phases, snapshots, progress.
- [ ] Ports Protocols checkpoint / catalog / publisher.
- [ ] `SqliteJobCheckpointStore` + `JobStore`.
- [ ] POST/GET jobs stub.
- [ ] Tests : sérialisation track, save/load checkpoint sans perte métadonnées.

**Done** : job créé → persisté → relisible après « restart » simulé.

---

### Lot 3 — Progress model + barres UI (SSE)

- [ ] `GlobalProgress`, `MediaProgress`, `ProgressSnapshot`, `ProgressPublisher`.
- [ ] Endpoint progress + SSE.
- [ ] `progress_bars.js` : barre globale + barres dynamiques par média actif.
- [ ] Tests : agrégation % global ; filtrage médias actifs.

**Done** : UI affiche barre globale + N barres fictives via publisher fake.

---

### Lot 4 — Resume service

- [ ] `JobResumeService` + `TrackStateMachine`.
- [ ] Auto-resume startup (config).
- [ ] Politique : skip re-resolve si tracks présentes ; skip rematch si URL YT ; DL resume/retry ; transcode always-retry si MP3 absent.
- [ ] Tests unitaires table de décisions resume (fakes).

**Done** : scénarios resume couverts par tests (API data jamais re-fetchée si checkpoint OK).

---

### Lot 5 — UrlClassifier + Resolve YouTube (+ tests)

- [ ] `UrlClassifier`, `YoutubeResolver`.
- [ ] Persistence tracks après resolve.
- [ ] Affichage onglet Job/Progression.
- [ ] Tests classifier + parser JSON yt-dlp (fixtures fichiers, pas réseau).

**Done** : playlist/vidéo YT → tracks checkpointées.

---

### Lot 6 — Resolve Deezer (+ tests)

- [ ] Short-link + API Deezer (client injectable).
- [ ] Pagination.
- [ ] Tests avec réponses HTTP fake (`httpx` mock / fake port).

**Done** : short-link exemple → liste artiste/titre/durée persistée.

---

### Lot 7 — ResolveMatchPool parallèle + match statique

- [ ] `ResolveMatchPool` (threads 3.14).
- [ ] `StaticYoutubeMatcher` + scoring (`MatchScore`, `MatchCandidate`).
- [ ] Enfile vers download dès match (hook).
- [ ] Tests scoring + pool avec matcher fake (ordre / concurrence).

**Done** : N tracks matchées en // ; unmatched restants explicites.

---

### Lot 8 — LM Studio matcher + ResourceGate

- [ ] `LmStudioClient` / `ModelLoader` / erreurs typées.
- [ ] `LlmYoutubeMatcher`.
- [ ] `GpuResourceGate` (LLM ⊕ GPU exclusifs).
- [ ] Tests : down → erreur claire ; gate bloque transcode pendant LLM (fakes).

**Done** : fallback LLM testé ; pas de LLM si serveur off (message FR).

---

### Lot 9 — DownloadPool parallèle + resume fichiers

- [ ] `YtdlpDownloader` + `DownloadResumePolicy`.
- [ ] `DownloadPool` ; push transcode à `download_complete`.
- [ ] Progression bytes → `MediaProgress`.
- [ ] Tests policy resume/fail→full retry (FS tmp).

**Done** : multi-DL // ; partiel → reprise ou retry full.

---

### Lot 10 — TranscodeScheduler GPU×2 + CPU×cores

- [ ] `BackendDetect`, workers nvidia/arc/cpu.
- [ ] `CpuParallelism` → `os.cpu_count()`.
- [ ] Scheduler priorité GPU→CPU ; gate LLM.
- [ ] MP3 192k atomique + catalogue.
- [ ] Tests scheduler (backends fake) : priorité, parallélisme CPU N, exclusion LLM.

**Done** : fichier DL ready → MP3 ; 2 GPU + N CPU simulés.

---

### Lot 11 — Orchestrateur pipeline bout-en-bout

- [ ] `JobOrchestrator` : resolve → pool match → pool DL → scheduler (streaming).
- [ ] Cancel cooperative.
- [ ] Scan dest + skip catalogue.
- [ ] Tests orchestration avec **tous** ports fake (pipeline 3 tracks).

**Done** : un job fake traverse toutes les phases sans I/O réel.

---

### Lot 12 — UX polish + catalogue onglet

- [ ] Onglet Catalogue branché.
- [ ] Cancel / Resume boutons.
- [ ] README usage (sans « Lot N »).
- [ ] Tests smoke UI optionnels hors CI stricte.

**Done** : usage quotidien sans console.

---

### Lot 13 — Packaging portable

- [ ] `Package-Portable.ps1` (whitelist, wheelhouse cp314, Setup/Run).
- [ ] Doc Python 3.14 + ffmpeg externe.
- [ ] Test script WhatIf / dry-list fichiers inclus.

**Done** : ZIP portable généré ; install offline documentée.

---

### Lot 14 — Durcissement tests & parallel suites

- [ ] Compléter fakes manquants.
- [ ] `@pytest.mark.online` isolé.
- [ ] `ops-parallel-test-suites` si volume élevé.
- [ ] Guardrails `assert_roots_clean` sur `src/ytpd`.

**Done** : `pytest` offline vert ; guardrails verts.

---

## 9. Dépendances Python prévues

```text
fastapi
uvicorn[standard]
jinja2
httpx
pyyaml
yt-dlp
```

Pas de `Any` via pydantic non borné : préférer dataclasses domaine + validation explicite aux frontières HTTP (modèles dédiés 1/fichier si besoin).

Systèmes : **Python 3.14 (free-threaded)**, **FFmpeg**, LM Studio (utilisateur), drivers NVIDIA + Arc.

---

## 10. Risques & mitigations

| Risque | Mitigation |
|--------|------------|
| Wheels cp314 / free-threaded encore rares | Pin deps ; documenter ; CI locale ; fallback note si un paquet force GIL |
| yt-dlp non thread-safe | 1 instance/options par tâche ; pas d’état partagé mutable |
| FFmpeg QSV/NVENC absent | Detect + CPU `os.cpu_count()` |
| Checkpoint corrompu | Écritures atomiques ; job `corrupt` + bouton reset resolve |
| Re-fetch API évité | Tests resume dédiés (Lot 4) |
| LM Studio VRAM vs CUDA | `GpuResourceGate` |
| HTML monolithique | Onglets fichiers séparés dès Lot 1 |

---

## 11. Ordre d’exécution

```text
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14
                    └─5∥6─┘
```

`5 ∥ 6` après Lot 4. Lots 3–4 (progress/resume) avant les resolvers pour que chaque feature métier checkpoint/progress dès le premier resolve.

---

## 12. Hors scope

- Bind non-localhost / multi-user auth
- Validation manuelle des matchs (V2 utile)
- Téléchargement Deezer natif (DRM) — métadonnées seulement
- Multi-jobs running simultanés (V1 : 1 job actif ; autres en queue)

---

## 13. Définition de « terminé » produit

1. Python **3.14** + `Start-App.ps1` + UI onglets modulaires sur 127.0.0.1.
2. Barre **globale** + barres **par média actif**, détail phase/%.
3. Checkpoint : métadonnées API / match **jamais** re-fetchées inutilement ; DL reprise ou retry ; transcode relançable.
4. Pipeline // : match //, download //, transcode dès DL ready (GPU×2 + CPU×cores).
5. LLM jamais pendant transcode GPU ; erreur claire si LM Studio down.
6. MP3 192k dans `dest_dir` ; skip catalogue.
7. SOLID / 1 classe par fichier / DI / pas de tuples ni `object`.
8. Tests unitaires par lot + guardrails.
9. ZIP portable via `Package-Portable.ps1`.
)
