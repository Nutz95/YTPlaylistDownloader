(() => {
  const urlInput = document.getElementById("job-url");
  const createButton = document.getElementById("job-create");
  const runButton = document.getElementById("job-run");
  const cancelButton = document.getElementById("job-cancel");
  const resolveButton = document.getElementById("job-resolve");
  const matchButton = document.getElementById("job-match");
  const downloadButton = document.getElementById("job-download");
  const transcodeButton = document.getElementById("job-transcode");
  const resumeButton = document.getElementById("job-resume");
  const refreshButton = document.getElementById("job-refresh-list");
  const status = document.getElementById("job-status");
  const trackList = document.getElementById("job-track-list");
  const jobList = document.getElementById("job-list");
  const selection = window.YtpdJobSelection;
  if (
    !urlInput ||
    !createButton ||
    !runButton ||
    !cancelButton ||
    !resolveButton ||
    !matchButton ||
    !downloadButton ||
    !transcodeButton ||
    !resumeButton ||
    !refreshButton ||
    !status ||
    !trackList ||
    !jobList ||
    !selection
  ) {
    return;
  }

  let latestJobs = [];
  let statusOverride = "";

  function paintList() {
    jobList.innerHTML = "";
    if (latestJobs.length === 0) {
      const empty = document.createElement("li");
      empty.className = "hint";
      empty.textContent = "No saved jobs yet.";
      jobList.appendChild(empty);
      return;
    }
    const selectedId = selection.getSelectedJobId();
    latestJobs.forEach((job) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "job-list-item";
      if (job.job_id === selectedId) {
        button.classList.add("is-selected");
      }
      const title = document.createElement("div");
      title.textContent = job.source_url;
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = `${selection.shortId(job.job_id)} · ${job.status} · ${job.source_kind} · ${job.track_count} tracks`;
      button.append(title, meta);
      button.addEventListener("click", () => {
        statusOverride = "";
        selection.setSelectedJobId(job.job_id);
      });
      item.appendChild(button);
      jobList.appendChild(item);
    });
  }

  function paintTracks(job) {
    trackList.innerHTML = "";
    const preview = (job.tracks || []).slice(0, 40);
    preview.forEach((track) => {
      const item = document.createElement("li");
      item.textContent = `${track.artist} — ${track.title} (${track.phase})`;
      trackList.appendChild(item);
    });
    if ((job.tracks || []).length > preview.length) {
      const more = document.createElement("li");
      more.textContent = `… +${job.tracks.length - preview.length} more tracks`;
      trackList.appendChild(more);
    }
  }

  function paintSelectedSummary(job) {
    urlInput.value = job.source_url;
    if (statusOverride) {
      status.textContent = statusOverride;
      return;
    }
    const trackCount = job.track_count != null ? job.track_count : (job.tracks || []).length;
    status.textContent = `Selected ${selection.shortId(job.job_id)} — ${job.status} — ${job.source_kind} — ${trackCount} tracks`;
  }

  async function loadJobDetail(jobId) {
    const response = await fetch(`/api/jobs/${jobId}`);
    if (!response.ok) {
      status.textContent = "Failed to load job detail.";
      return;
    }
    const job = await response.json();
    paintSelectedSummary(job);
    paintTracks(job);
    paintList();
  }

  async function refreshJobList(autoSelect) {
    const response = await fetch("/api/jobs");
    if (!response.ok) {
      status.textContent = "Failed to load jobs.";
      return;
    }
    const body = await response.json();
    if (!Array.isArray(body.jobs)) {
      status.textContent = "Jobs API returned an invalid payload.";
      return;
    }
    latestJobs = body.jobs;
    paintList();
    window.dispatchEvent(
      new CustomEvent("ytpd-jobs-refreshed", { detail: { jobs: latestJobs } })
    );
    if (!selection.getSelectedJobId() && autoSelect) {
      const preferred = selection.pickPreferredJob(latestJobs);
      if (preferred) {
        selection.setSelectedJobId(preferred.job_id);
      }
    }
  }

  window.addEventListener("ytpd-job-selected", (event) => {
    const jobId = event.detail && event.detail.jobId;
    if (!jobId) {
      return;
    }
    loadJobDetail(jobId);
  });

  createButton.addEventListener("click", async () => {
    statusOverride = "";
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: urlInput.value }),
    });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Create failed.";
      return;
    }
    selection.setSelectedJobId(body.job_id);
    await refreshJobList(false);
  });

  runButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select or create a job first.";
      return;
    }
    statusOverride = "";
    status.textContent = "Running pipeline…";
    const response = await fetch(`/api/jobs/${jobId}/run`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Pipeline failed.";
      return;
    }
    statusOverride = body.cancelled
      ? `Pipeline cancelled — ${selection.shortId(body.job_id)}`
      : `Pipeline completed — ${selection.shortId(body.job_id)}`;
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
  });

  cancelButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select a job first.";
      return;
    }
    const response = await fetch(`/api/jobs/${jobId}/cancel`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Cancel failed.";
      return;
    }
    statusOverride = "Cancel requested — waiting for the current stage to finish.";
    status.textContent = statusOverride;
  });

  resolveButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select or create a job first.";
      return;
    }
    statusOverride = "";
    const response = await fetch(`/api/jobs/${jobId}/resolve`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Resolve failed.";
      return;
    }
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
  });

  matchButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select a job first.";
      return;
    }
    statusOverride = "";
    status.textContent = "Matching YouTube…";
    const response = await fetch(`/api/jobs/${jobId}/match`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Match failed.";
      return;
    }
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
  });

  downloadButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select a job first.";
      return;
    }
    statusOverride = "";
    status.textContent = "Downloading…";
    const response = await fetch(`/api/jobs/${jobId}/download`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Download failed.";
      return;
    }
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
  });

  transcodeButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select a job first.";
      return;
    }
    statusOverride = "";
    status.textContent = "Transcoding…";
    const response = await fetch(`/api/jobs/${jobId}/transcode`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Transcode failed.";
      return;
    }
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
  });

  resumeButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select a job first.";
      return;
    }
    const response = await fetch(`/api/jobs/${jobId}/resume`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Resume failed.";
      return;
    }
    statusOverride = `Resume plan: ${body.job_action} · ${body.decisions.length} track actions`;
    status.textContent = statusOverride;
    await refreshJobList(false);
    paintList();
  });

  refreshButton.addEventListener("click", () => {
    statusOverride = "";
    refreshJobList(true);
  });

  refreshJobList(true);
})();
