(() => {
  const urlInput = document.getElementById("job-url");
  const createButton = document.getElementById("job-create");
  const resolveButton = document.getElementById("job-resolve");
  const status = document.getElementById("job-status");
  const trackList = document.getElementById("job-track-list");
  if (!urlInput || !createButton || !resolveButton || !status || !trackList) {
    return;
  }

  let currentJobId = "";

  function renderJob(job) {
    currentJobId = job.job_id;
    status.textContent = `Job ${job.job_id} — ${job.status} — ${job.source_kind} — ${job.tracks.length} tracks`;
    trackList.innerHTML = "";
    job.tracks.forEach((track) => {
      const item = document.createElement("li");
      item.textContent = `${track.artist} — ${track.title} (${track.phase})`;
      trackList.appendChild(item);
    });
    const progressInput = document.getElementById("progress-job-id");
    if (progressInput) {
      progressInput.value = job.job_id;
    }
  }

  createButton.addEventListener("click", async () => {
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
    renderJob(body);
  });

  resolveButton.addEventListener("click", async () => {
    if (!currentJobId) {
      status.textContent = "Create a job first.";
      return;
    }
    const response = await fetch(`/api/jobs/${currentJobId}/resolve`, {
      method: "POST",
    });
    const body = await response.json();
    if (!response.ok) {
      status.textContent = body.error || "Resolve failed.";
      return;
    }
    renderJob(body);
  });
})();
