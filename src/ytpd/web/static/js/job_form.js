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
  const i18n = window.YtpdI18n;
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
  let statusOverride = null;
  let lastProgressKey = "";
  const terminalStatuses = new Set(["completed", "failed", "cancelled"]);
  const statusBind = i18n ? i18n.bindStatus(status) : null;

  function t(key, vars) {
    return i18n ? i18n.t(key, vars) : key;
  }

  function showStatus(key, vars) {
    if (statusBind) {
      statusBind.set(key, vars);
      return;
    }
    status.textContent = t(key, vars);
  }

  function showRawStatus(text) {
    statusOverride = null;
    if (statusBind) {
      statusBind.clear();
    }
    status.textContent = text;
  }

  function setStatusOverride(key, vars) {
    statusOverride = { key, vars: vars || null };
    showStatus(key, vars);
  }

  function clearStatusOverride() {
    statusOverride = null;
    if (statusBind) {
      statusBind.clear();
    }
  }

  function canDeleteJob(job) {
    return job && job.status !== "running";
  }

  function selectedMediaMode() {
    const checked = document.querySelector('input[name="job-media-mode"]:checked');
    return checked && checked.value === "video" ? "video" : "audio";
  }

  function mediaModeLabel(mode) {
    return mode === "video" ? "video" : "audio";
  }

  function forceReprocessSelected() {
    const box = document.getElementById("job-force-reprocess");
    return !!(box && box.checked);
  }

  function paintList() {
    jobList.innerHTML = "";
    if (latestJobs.length === 0) {
      const empty = document.createElement("li");
      empty.className = "hint";
      empty.textContent = t("job.empty");
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
      const mode = mediaModeLabel(job.media_mode);
      meta.textContent = `${selection.shortId(job.job_id)} · ${job.status}${stage} · ${mode} · ${job.source_kind} · ${job.track_count} tracks`;
      if (sourceTitle) {
        const urlLine = document.createElement("div");
        urlLine.className = "meta";
        urlLine.textContent = job.source_url;
        button.append(title, urlLine, meta);
      } else {
        button.append(title, meta);
      }
      button.addEventListener("click", () => {
        clearStatusOverride();
        selection.setSelectedJobId(job.job_id);
      });
      item.appendChild(button);
      if (canDeleteJob(job)) {
        const shortId = selection.shortId(job.job_id);
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "job-list-delete";
        remove.textContent = t("job.delete");
        remove.title = t("job.delete.title");
        remove.setAttribute("aria-label", t("job.delete.aria", { id: shortId }));
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
    if (!statusOverride) {
      showStatus("job.status.none");
    }
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
    clearStatusOverride();
    showStatus("job.status.deleting");
    const response = await fetch(`/api/jobs/${jobId}`, { method: "DELETE" });
    const body = await readJsonBody(response);
    if (!response.ok) {
      showRawStatus(body.error || t("job.status.delete.failed"));
      await refreshJobList(false);
      return;
    }
    clearSelectionIfDeleted([jobId]);
    setStatusOverride("job.status.deleted", { id: selection.shortId(jobId) });
    await refreshJobList(false);
  }

  async function deleteCompletedJobs() {
    if (deleteCompletedButton.disabled) {
      return;
    }
    const confirmed = window.confirm(t("job.confirm.delete.completed"));
    if (!confirmed) {
      return;
    }
    deleteCompletedButton.disabled = true;
    clearStatusOverride();
    showStatus("job.status.deleting.completed");
    try {
      const response = await fetch("/api/jobs/completed", { method: "DELETE" });
      const body = await readJsonBody(response);
      if (!response.ok) {
        showRawStatus(body.error || t("job.status.delete.completed.failed"));
        return;
      }
      const deletedIds = Array.isArray(body.deleted_job_ids) ? body.deleted_job_ids : [];
      clearSelectionIfDeleted(deletedIds);
      const count = typeof body.deleted_count === "number" ? body.deleted_count : deletedIds.length;
      if (count === 0) {
        setStatusOverride("job.status.none.completed");
      } else {
        setStatusOverride("job.status.deleted.completed", { count });
      }
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
      more.textContent = t("job.status.more.tracks", {
        count: job.tracks.length - preview.length,
      });
      trackList.appendChild(more);
    }
  }

  function paintSelectedSummary(job) {
    urlInput.value = job.source_url;
    if (statusOverride) {
      showStatus(statusOverride.key, statusOverride.vars || undefined);
      return;
    }
    const trackCount = job.track_count != null ? job.track_count : (job.tracks || []).length;
    showStatus("job.status.selected", {
      id: selection.shortId(job.job_id),
      status: job.status,
      kind: job.source_kind,
      count: trackCount,
    });
  }

  async function loadJobDetail(jobId) {
    const response = await fetch(`/api/jobs/${jobId}`);
    if (!response.ok) {
      showStatus("job.status.load.detail.failed");
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
      showStatus("job.status.load.failed");
      return;
    }
    const body = await response.json();
    if (!Array.isArray(body.jobs)) {
      showStatus("job.status.invalid");
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
      clearStatusOverride();
    }
    await refreshJobList(false);
    if (selection.getSelectedJobId() === jobId) {
      await loadJobDetail(jobId);
    }
  });

  window.addEventListener("ytpd-locale-changed", () => {
    paintList();
    if (statusOverride) {
      showStatus(statusOverride.key, statusOverride.vars || undefined);
      return;
    }
    const jobId = selection.getSelectedJobId();
    if (jobId) {
      loadJobDetail(jobId);
      return;
    }
    showStatus("job.status.none");
  });

  createButton.addEventListener("click", async () => {
    clearStatusOverride();
    showStatus("job.status.creating");
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: urlInput.value,
        media_mode: selectedMediaMode(),
        force_reprocess: forceReprocessSelected(),
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      showRawStatus(body.error || t("job.status.create.failed"));
      return;
    }
    selection.setSelectedJobId(body.job_id);
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
    if (body.started) {
      setStatusOverride("job.status.running", { id: selection.shortId(body.job_id) });
      window.dispatchEvent(
        new CustomEvent("ytpd-pipeline-started", { detail: { jobId: body.job_id } })
      );
    } else {
      setStatusOverride("job.status.queued", { id: selection.shortId(body.job_id) });
    }
  });

  cancelButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      showStatus("job.status.select.first");
      return;
    }
    const response = await fetch(`/api/jobs/${jobId}/cancel`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      showRawStatus(body.error || t("job.status.cancel.failed"));
      return;
    }
    setStatusOverride("job.status.cancelled", { id: selection.shortId(body.job_id) });
    paintSelectedSummary(body);
    paintTracks(body);
    await refreshJobList(false);
    livePanel.startLiveWatch();
  });

  retryFailedButton.addEventListener("click", async () => {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      showStatus("job.status.select.first");
      return;
    }
    clearStatusOverride();
    showStatus("job.status.retrying");
    const response = await fetch(`/api/jobs/${jobId}/retry-failed`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      showRawStatus(body.error || t("job.status.retry.failed"));
      return;
    }
    setStatusOverride("job.status.retrying.ok", { id: selection.shortId(body.job_id) });
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
      showStatus("job.status.select.first");
      return;
    }
    clearStatusOverride();
    showStatus("job.status.resuming");
    const response = await fetch(`/api/jobs/${jobId}/resume`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) {
      showRawStatus(body.error || t("job.status.resume.failed"));
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
    const summaryText = summary
      || t(
        body.started
          ? "job.status.resume.summary.pending"
          : "job.status.resume.summary.none"
      );
    if (body.started) {
      setStatusOverride("job.status.resumed", { summary: summaryText });
    } else {
      setStatusOverride("job.status.resume.busy", { summary: summaryText });
    }
    await refreshJobList(false);
    paintList();
    window.dispatchEvent(
      new CustomEvent("ytpd-pipeline-started", { detail: { jobId } })
    );
  });

  refreshButton.addEventListener("click", () => {
    clearStatusOverride();
    refreshJobList(true);
  });

  deleteCompletedButton.addEventListener("click", () => {
    deleteCompletedJobs();
  });

  refreshJobList(true);
})();
