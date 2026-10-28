(() => {
  const liveLabel = document.getElementById("job-live-label");
  const liveList = document.getElementById("job-live-list");
  const failList = document.getElementById("job-fail-list");
  const status = document.getElementById("job-status");
  const selection = window.YtpdJobSelection;
  const overrideApi = window.YtpdYoutubeOverrideApi;
  const failureCopy = window.YtpdFailureCopy;
  if (
    !liveLabel ||
    !liveList ||
    !failList ||
    !selection ||
    !overrideApi ||
    !failureCopy
  ) {
    return;
  }

  let liveTimerId = 0;

  async function overrideFailedTrackYoutube(trackId, youtubeUrl) {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      if (status) {
        status.textContent = "Select a job first.";
      }
      return;
    }
    const result = await overrideApi.applyAndAnnounce(
      jobId,
      trackId,
      youtubeUrl,
      (message) => {
        if (status) {
          status.textContent = message;
        }
      }
    );
    if (!result.ok) {
      return;
    }
    window.dispatchEvent(
      new CustomEvent("ytpd-job-selected", { detail: { jobId: result.body.job_id } })
    );
    startLiveWatch();
  }

  function paintLive(snapshot) {
    liveLabel.textContent = snapshot.label || "No active work.";
    liveList.innerHTML = "";
    (snapshot.active_media || []).forEach((media) => {
      const item = document.createElement("li");
      item.className = "is-active";
      const detail = media.detail ? ` · ${media.detail}` : "";
      item.textContent = `${media.phase_label}: ${media.artist} — ${media.title}${detail}`;
      liveList.appendChild(item);
    });
    if ((snapshot.active_media || []).length === 0) {
      const empty = document.createElement("li");
      empty.className = "hint";
      empty.textContent = "No track in flight right now.";
      liveList.appendChild(empty);
    }
    failureCopy.paintFailureList(failList, snapshot.failed_media || [], {
      card: false,
      limit: 12,
      emptyText: "No failures yet.",
      onYoutubeOverride: overrideFailedTrackYoutube,
    });
  }

  async function pollLiveOnce() {
    const jobId = selection.getSelectedJobId();
    if (!jobId) {
      liveLabel.textContent = "No active work.";
      liveList.innerHTML = "";
      failList.innerHTML = "";
      return;
    }
    const response = await fetch(`/api/jobs/${jobId}/progress`);
    if (!response.ok) {
      return;
    }
    const snapshot = await response.json();
    paintLive(snapshot);
    window.dispatchEvent(
      new CustomEvent("ytpd-progress-tick", {
        detail: {
          jobId: snapshot.job_id || jobId,
          jobStatus: snapshot.job_status || "",
          stage: snapshot.stage || "idle",
        },
      })
    );
  }

  function startLiveWatch() {
    if (liveTimerId) {
      window.clearInterval(liveTimerId);
    }
    pollLiveOnce();
    liveTimerId = window.setInterval(pollLiveOnce, 1000);
  }

  function clearLive() {
    liveLabel.textContent = "No active work.";
    liveList.innerHTML = "";
    failList.innerHTML = "";
  }

  window.YtpdJobLivePanel = {
    startLiveWatch,
    clearLive,
  };

  window.addEventListener("ytpd-pipeline-started", () => {
    startLiveWatch();
  });
  window.addEventListener("ytpd-job-selected", () => {
    startLiveWatch();
  });
})();
