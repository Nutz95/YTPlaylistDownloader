(() => {
  async function applyAndAnnounce(jobId, trackId, youtubeUrl, onStatus) {
    if (typeof onStatus === "function") {
      onStatus("Applying YouTube override…");
    }
    const response = await fetch(
      `/api/jobs/${jobId}/tracks/${encodeURIComponent(trackId)}/youtube-override`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ youtube_url: youtubeUrl }),
      }
    );
    const body = await response.json();
    const result = { ok: response.ok, body };
    if (!result.ok) {
      if (typeof onStatus === "function") {
        onStatus(result.body.error || "YouTube override failed.");
      }
      return result;
    }
    const shortId =
      window.YtpdJobSelection && window.YtpdJobSelection.shortId
        ? window.YtpdJobSelection.shortId(result.body.job_id)
        : result.body.job_id.slice(0, 8);
    if (typeof onStatus === "function") {
      onStatus(`Override applied — ${shortId} · pipeline restarted`);
    }
    window.dispatchEvent(
      new CustomEvent("ytpd-pipeline-started", { detail: { jobId: result.body.job_id } })
    );
    return result;
  }

  window.YtpdYoutubeOverrideApi = {
    applyAndAnnounce,
  };
})();
