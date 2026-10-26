(() => {
  const jobInput = document.getElementById("progress-job-id");
  const watchButton = document.getElementById("progress-watch");
  const label = document.getElementById("progress-global-label");
  const fill = document.getElementById("progress-global-fill");
  const mediaList = document.getElementById("progress-media-list");
  if (!jobInput || !watchButton || !label || !fill || !mediaList) {
    return;
  }

  let timerId = 0;

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
    const jobId = jobInput.value.trim();
    if (!jobId) {
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
})();
