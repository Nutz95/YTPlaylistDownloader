(() => {
  const liveLabel = document.getElementById("job-live-label");
  const liveList = document.getElementById("job-live-list");
  const failList = document.getElementById("job-fail-list");
  const status = document.getElementById("job-status");
  const selection = window.YtpdJobSelection;
  const overrideApi = window.YtpdYoutubeOverrideApi;
  if (!liveLabel || !liveList || !failList || !selection || !overrideApi) {
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
    if (status) {
      status.textContent = "Applying YouTube override…";
    }
    const result = await overrideApi.applyYoutubeOverride(jobId, trackId, youtubeUrl);
    if (!result.ok) {
      if (status) {
        status.textContent = result.body.error || "YouTube override failed.";
      }
      return;
    }
    if (status) {
      status.textContent = `Override applied — ${selection.shortId(result.body.job_id)} · pipeline restarted`;
    }
    window.dispatchEvent(
      new CustomEvent("ytpd-pipeline-started", { detail: { jobId: result.body.job_id } })
    );
    window.dispatchEvent(
      new CustomEvent("ytpd-job-selected", { detail: { jobId: result.body.job_id } })
    );
    startLiveWatch();
  }

  function paintLive(snapshot) {
    liveLabel.textContent = snapshot.label || "No active work.";
    liveList.innerHTML = "";
    failList.innerHTML = "";
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
    const failureCopy = window.YtpdFailureCopy;
    (snapshot.failed_media || []).slice(0, 12).forEach((media) => {
      if (failureCopy) {
        failureCopy.appendFailureItem(failList, media, {
          card: false,
          onYoutubeOverride: overrideFailedTrackYoutube,
        });
        return;
      }
      const item = document.createElement("li");
      item.className = "is-failed";
      item.textContent = `${media.artist} — ${media.title}: ${media.detail || media.phase_label}`;
      failList.appendChild(item);
    });
    if ((snapshot.failed_media || []).length === 0) {
      const empty = document.createElement("li");
      empty.className = "hint";
      empty.textContent = "No failures yet.";
      failList.appendChild(empty);
    }
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
    paintLive(await response.json());
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
