(() => {
  async function applyYoutubeOverride(jobId, trackId, youtubeUrl) {
    const response = await fetch(
      `/api/jobs/${jobId}/tracks/${encodeURIComponent(trackId)}/youtube-override`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ youtube_url: youtubeUrl }),
      }
    );
    const body = await response.json();
    return { ok: response.ok, body };
  }

  window.YtpdYoutubeOverrideApi = {
    applyYoutubeOverride,
  };
})();
