(() => {
  const urlInput = document.getElementById("job-url");
  const createButton = document.getElementById("job-create");
  const cancelButton = document.getElementById("job-cancel");
  const resumeButton = document.getElementById("job-resume");
  const retryFailedButton = document.getElementById("job-retry-failed");
  const refreshButton = document.getElementById("job-refresh-list");
  const deleteCompletedButton = document.getElementById("job-delete-completed");
  const status = document.getElementById("job-status");
  const trackList = document.getElementById("job-track-list");
  const jobList = document.getElementById("job-list");
  const selection = window.YtpdJobSelection;
  const livePanel = window.YtpdJobLivePanel;
  if (
    !urlInput ||
    !createButton ||
    !cancelButton ||
    !resumeButton ||
    !retryFailedButton ||
    !refreshButton ||
    !deleteCompletedButton ||
    !status ||
    !trackList ||
    !jobList ||
    !selection ||
    !livePanel
  ) {
    return;
  }

  let latestJobs = [];
  let statusOverride = "";
  let lastProgressKey = "";
  const terminalStatuses = new Set(["completed", "failed", "cancelled"]);

  function canDeleteJob(job) {
    return job && job.status !== "running";
  }

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
      item.className = "job-list-row";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "job-list-item";
      if (job.job_id === selectedId) {
        button.classList.add("is-selected");
      }
      const title = document.createElement("div");
      const sourceTitle = (job.source_title || "").trim();
      title.textContent = sourceTitle || job.source_url;
      const meta = document.createElement("div");
      meta.className = "meta";
      const stage = job.pipeline_stage ? ` · ${job.pipeline_stage}` : "";
      meta.textContent = `${selection.shortId(job.job_id)} · ${job.status}${stage} · ${job.source_kind} · ${job.track_count} tracks`;
      if (sourceTitle) {
        const urlLine = document.createElement("div");
        urlLine.className = "meta";
        urlLine.textContent = job.source_url;
        button.append(title, urlLine, meta);
      } else {
        button.append(title, meta);
      }
      button.addEventListener("click", () => {
        statusOverride = "";
        selection.setSelectedJobId(job.job_id);
      });
      item.appendChild(button);
      if (canDeleteJob(job)) {
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "job-list-delete";
        remove.textContent = "Supprimer";
        remove.title = "Supprimer ce job";
        remove.setAttribute("aria-label", `Supprimer le job ${selection.shortId(job.job_id)}`);
        remove.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          deleteJob(job.job_id);
        });
        item.appendChild(remove);
      }
      jobList.appendChild(item);
    });
  }

  function clearSelectionIfDeleted(deletedIds) {
    const selectedId = selection.getSelectedJobId();
    if (!selectedId || !deletedIds.includes(selectedId)) {
      return;
    }
    selection.clearSelectedJobId();
    urlInput.value = "";
    trackList.innerHTML = "";
    livePanel.clearLive();
  }

  async function readJsonBody(response) {
    try {
      return await response.json();
    } catch (_error) {
      return {};
    }
  }

  async function deleteJob(jobId) {
    if (!jobId) {
      return;
    }
    statusOverride = "";
    status.textContent = "Deleting job…";
    const response = await fetch(`/api/jobs/${jobId}`, { method: "DELETE" });
    const body = await readJsonBody(response);
    if (!response.ok) {
      status.textContent = body.error || "Delete failed.";
      await refreshJobList(false);
      return;
    }
    clearSelectionIfDeleted([jobId]);
    statusOverride = `Deleted — ${selection.shortId(jobId)}`;
    status.textContent = statusOverride;
    await refreshJobList(false);
  }

  async function deleteCompletedJobs() {
    if (deleteCompletedButton.disabled) {
      return;
    }
    const confirmed = window.confirm(
      "Supprimer tous les jobs terminés (completed) ? Les MP3 restent dans le dossier de sortie."
    );
    if (!confirmed) {
      return;
    }
    deleteCompletedButton.disabled = true;
    statusOverride = "";
    status.textContent = "Deleting completed jobs…";
    try {
      const response = await fetch("/api/jobs/completed", { method: "DELETE" });
      const body = await readJsonBody(response);
      if (!response.ok) {
        status.textContent = body.error || "Delete completed failed.";
        return;
      }
      const deletedIds = Array.isArray(body.deleted_job_ids) ? body.deleted_job_ids : [];
      clearSelectionIfDeleted(deletedIds);
      const count = typeof body.deleted_count === "number" ? body.deleted_count : deletedIds.length;
      statusOverride = count === 0
        ? "No completed jobs to delete."
        : `Deleted ${count} completed job${count === 1 ? "" : "s"}`;
      status.textContent = statusOverride;
    } finally {
      deleteCompletedButton.disabled = false;
      await refreshJobList(false);
    }
  }

  function paintTracks(job) {
    trackList.innerHTML = "";
    const preview = (job.tracks || []).slice(0, 40);
    preview.forEach((track) => {
      const item = document.createElement("li");
      if (track.phase === "matching" || track.phase === "downloading" || track.phase === "transcoding") {
        item.classList.add("is-active");
      }
      if (track.phase === "match_failed" || track.phase === "error") {
        item.classList.add("is-failed");
      }
      const err = track.error_message ? ` — ${track.error_message}` : "";
      item.textContent = `${track.artist} — ${track.title} (${track.phase})${err}`;
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
    lastProgressKey = "";
    loadJobDetail(jobId);
    livePanel.startLiveWatch();
  });

  window.addEventListener("ytpd-progress-tick", async (event) => {
    const detail = event.detail || {};
    const jobId = detail.jobId || "";
    const jobStatus = detail.jobStatus || "";
    const stage = detail.stage || "idle";
    if (!jobId) {
      return;
    }
    const progressKey = `${jobId}|${jobStatus}|${stage}`;
    if (progressKey === lastProgressKey) {
      return;
    }
    lastProgressKey = progressKey;
    if (terminalStatuses.has(jobStatus)) {
      statusOverride = "";
    }
    await refreshJobList(false);
    if (selection.getSelectedJobId() === jobId) {
      await loadJobDetail(jobId);
    }
  });

  createButton.addEventListener("click", async () => {
    statusOverride = "";
    status.textContent = "Creating job…";
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
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
    if (body.started) {
      statusOverride = `Pipeline running — ${selection.shortId(body.job_id)} · open Progression for live stage / track`;
      status.textContent = statusOverride;
      window.dispatchEvent(
        new CustomEvent("ytpd-pipeline-started", { detail: { jobId: body.job_id } })
      );
    } else {
      statusOverride = `Queued — ${selection.shortId(body.job_id)} · starts when the current job finishes`;
      status.textContent = statusOverride;
    }
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
    statusOverride = `Cancelled — ${selection.shortId(body.job_id)} · in-flight work stopped; pending tracks can be resumed`;
    status.textContent = statusOverride;
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
    livePanel.startLiveWatch();
  });

  retryFailedButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select a job first.";
      return;
    }
    statusOverride = "";
    status.textContent = "Retrying failed tracks…";
    const response = await fetch(`/api/jobs/${jobId}/retry-failed`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Retry failed.";
      return;
    }
    statusOverride = `Retrying failures — ${selection.shortId(body.job_id)} · watch Progression / failures.log`;
    status.textContent = statusOverride;
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
    window.dispatchEvent(
      new CustomEvent("ytpd-pipeline-started", { detail: { jobId: body.job_id } })
    );
  });

  resumeButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      status.textContent = "Select a job first.";
      return;
    }
    statusOverride = "";
    status.textContent = "Resuming pipeline…";
    const response = await fetch(`/api/jobs/${jobId}/resume`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Resume failed.";
      return;
    }
    const actionCounts = {};
    (body.decisions || []).forEach((decision) => {
      if (!decision.action || decision.action === "none") {
        return;
      }
      actionCounts[decision.action] = (actionCounts[decision.action] || 0) + 1;
    });
    if (body.job_action && body.job_action !== "none") {
      actionCounts[body.job_action] = (actionCounts[body.job_action] || 0) + 1;
    }
    const summary = Object.keys(actionCounts)
      .map((key) => `${actionCounts[key]} ${key}`)
      .join(", ");
    statusOverride = body.started
      ? `Pipeline resumed — ${summary || "pending work"} · watch Progression`
      : `Resume plan ready but pipeline already running — ${summary || "no actions"}`;
    status.textContent = statusOverride;
    await refreshJobList(false);
    paintList();
    window.dispatchEvent(
      new CustomEvent("ytpd-pipeline-started", { detail: { jobId } })
    );
  });

  refreshButton.addEventListener("click", () => {
    statusOverride = "";
    refreshJobList(true);
  });

  deleteCompletedButton.addEventListener("click", () => {
    deleteCompletedJobs();
  });

  refreshJobList(true);
})();
