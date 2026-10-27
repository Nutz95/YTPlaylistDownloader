(() => {
  const jobSelect = document.getElementById("progress-job-select");
  const watchButton = document.getElementById("progress-watch");
  const stageLine = document.getElementById("progress-stage-line");
  const label = document.getElementById("progress-global-label");
  const fill = document.getElementById("progress-global-fill");
  const mediaList = document.getElementById("progress-media-list");
  const failList = document.getElementById("progress-fail-list");
  const selection = window.YtpdJobSelection;
  if (
    !jobSelect ||
    !watchButton ||
    !stageLine ||
    !label ||
    !fill ||
    !mediaList ||
    !failList ||
    !selection
  ) {
    return;
  }

  let timerId = 0;

  async function overrideFailedTrackYoutube(trackId, youtubeUrl) {
    const jobId = jobSelect.value.trim() || selection.getSelectedJobId();
    const overrideApi = window.YtpdYoutubeOverrideApi;
    if (!jobId) {
      label.textContent = "Select a saved job first.";
      return;
    }
    if (!overrideApi) {
      label.textContent = "YouTube override API unavailable.";
      return;
    }
    label.textContent = "Applying YouTube override…";
    const result = await overrideApi.applyYoutubeOverride(jobId, trackId, youtubeUrl);
    if (!result.ok) {
      label.textContent = result.body.error || "YouTube override failed.";
      return;
    }
    label.textContent = `Override applied · pipeline restarted for ${selection.shortId(result.body.job_id)}`;
    window.dispatchEvent(
      new CustomEvent("ytpd-pipeline-started", { detail: { jobId: result.body.job_id } })
    );
    pollOnce();
  }

  function fillSelect(jobs) {
    const selectedId = selection.getSelectedJobId();
    jobSelect.innerHTML = "";
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "— select a saved job —";
    jobSelect.appendChild(placeholder);
    jobs.forEach((job) => {
      const option = document.createElement("option");
      option.value = job.job_id;
      const stage = job.pipeline_stage ? ` · ${job.pipeline_stage}` : "";
      option.textContent = `${selection.shortId(job.job_id)} · ${job.status}${stage} · ${job.track_count} tracks · ${job.source_url}`;
      jobSelect.appendChild(option);
    });
    jobSelect.value = selectedId || "";
  }

  function appendCards(container, items, emptyText, failed) {
    container.innerHTML = "";
    if (!items || items.length === 0) {
      const empty = document.createElement("div");
      empty.className = "hint";
      empty.textContent = emptyText;
      container.appendChild(empty);
      return;
    }
    const failureCopy = window.YtpdFailureCopy;
    items.forEach((media) => {
      if (failed && failureCopy) {
        failureCopy.appendFailureItem(container, media, {
          card: true,
          onYoutubeOverride: overrideFailedTrackYoutube,
        });
        return;
      }
      const card = document.createElement("div");
      card.className = failed
        ? "progress-media-card is-failed"
        : "progress-media-card";
      const title = document.createElement("strong");
      title.textContent = `${media.artist} — ${media.title}`;
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = media.detail
        ? `${media.phase_label} — ${media.detail}`
        : media.phase_label;
      card.append(title, meta);
      container.appendChild(card);
    });
  }

  function render(snapshot) {
    const stage = snapshot.stage || "idle";
    stageLine.textContent =
      stage === "idle"
        ? `Stage: idle · finished ${snapshot.completed_tracks}/${snapshot.total_tracks}`
        : `Stage: ${stage} · ${snapshot.stage_done}/${snapshot.stage_total}`;
    label.textContent = snapshot.label;
    fill.style.width = `${snapshot.percent}%`;
    appendCards(
      mediaList,
      snapshot.active_media,
      stage === "idle" ? "No active media." : "Waiting for the next track checkpoint…",
      false
    );
    appendCards(
      failList,
      snapshot.failed_media,
      "No failures yet.",
      true
    );
  }

  async function pollOnce() {
    const jobId = jobSelect.value.trim() || selection.getSelectedJobId();
    if (!jobId) {
      stageLine.textContent = "No active stage.";
      label.textContent = "Select a saved job first.";
      fill.style.width = "0%";
      mediaList.innerHTML = "";
      failList.innerHTML = "";
      return;
    }
    const response = await fetch(`/api/jobs/${jobId}/progress`);
    if (!response.ok) {
      stageLine.textContent = "No active stage.";
      label.textContent = "Job not found.";
      fill.style.width = "0%";
      mediaList.innerHTML = "";
      failList.innerHTML = "";
      return;
    }
    render(await response.json());
  }

  function startWatch() {
    if (timerId) {
      window.clearInterval(timerId);
    }
    pollOnce();
    timerId = window.setInterval(pollOnce, 1000);
  }

  watchButton.addEventListener("click", () => {
    startWatch();
  });

  jobSelect.addEventListener("change", () => {
    if (jobSelect.value) {
      selection.setSelectedJobId(jobSelect.value);
      startWatch();
    }
  });

  window.addEventListener("ytpd-jobs-refreshed", (event) => {
    fillSelect((event.detail && event.detail.jobs) || []);
  });

  window.addEventListener("ytpd-job-selected", (event) => {
    const jobId = event.detail && event.detail.jobId;
    if (!jobId) {
      return;
    }
    if (jobSelect.value !== jobId) {
      jobSelect.value = jobId;
    }
    startWatch();
  });

  window.addEventListener("ytpd-pipeline-started", (event) => {
    const jobId = event.detail && event.detail.jobId;
    if (jobId && jobSelect.value !== jobId) {
      jobSelect.value = jobId;
    }
    startWatch();
  });
})();
