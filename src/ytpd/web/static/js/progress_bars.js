(() => {
  const jobSelect = document.getElementById("progress-job-select");
  const watchButton = document.getElementById("progress-watch");
  const label = document.getElementById("progress-global-label");
  const fill = document.getElementById("progress-global-fill");
  const mediaList = document.getElementById("progress-media-list");
  const selection = window.YtpdJobSelection;
  if (!jobSelect || !watchButton || !label || !fill || !mediaList || !selection) {
    return;
  }

  let timerId = 0;

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
      option.textContent = `${selection.shortId(job.job_id)} · ${job.status} · ${job.track_count} tracks · ${job.source_url}`;
      jobSelect.appendChild(option);
    });
    jobSelect.value = selectedId || "";
  }

  function render(snapshot) {
    label.textContent = `${snapshot.label}: ${snapshot.completed_tracks}/${snapshot.total_tracks} (${snapshot.percent.toFixed(1)}%)`;
    fill.style.width = `${snapshot.percent}%`;
    mediaList.innerHTML = "";
    snapshot.active_media.forEach((media) => {
      const card = document.createElement("div");
      card.className = "progress-media-card";
      const title = document.createElement("strong");
      title.textContent = media.title;
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = media.detail
        ? `${media.phase_label} — ${media.detail}`
        : media.phase_label;
      card.append(title, meta);
      mediaList.appendChild(card);
    });
  }

  async function pollOnce() {
    const jobId = jobSelect.value.trim() || selection.getSelectedJobId();
    if (!jobId) {
      label.textContent = "Select a saved job first.";
      fill.style.width = "0%";
      mediaList.innerHTML = "";
      return;
    }
    const response = await fetch(`/api/jobs/${jobId}/progress`);
    if (!response.ok) {
      label.textContent = "Job not found.";
      fill.style.width = "0%";
      mediaList.innerHTML = "";
      return;
    }
    render(await response.json());
  }

  watchButton.addEventListener("click", () => {
    if (timerId) {
      window.clearInterval(timerId);
    }
    pollOnce();
    timerId = window.setInterval(pollOnce, 1000);
  });

  jobSelect.addEventListener("change", () => {
    if (jobSelect.value) {
      selection.setSelectedJobId(jobSelect.value);
      pollOnce();
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
    pollOnce();
  });
})();
