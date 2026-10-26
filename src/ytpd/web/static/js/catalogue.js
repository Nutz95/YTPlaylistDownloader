(() => {
  const refreshButton = document.getElementById("catalogue-refresh");
  const status = document.getElementById("catalogue-status");
  const list = document.getElementById("catalogue-list");
  if (!refreshButton || !status || !list) {
    return;
  }

  async function refreshCatalogue() {
    status.textContent = "Loading catalogue…";
    const response = await fetch("/api/catalog");
    if (!response.ok) {
      status.textContent = "Failed to load catalogue.";
      return;
    }
    const body = await response.json();
    const entries = Array.isArray(body.entries) ? body.entries : [];
    list.innerHTML = "";
    if (entries.length === 0) {
      const empty = document.createElement("li");
      empty.className = "hint";
      empty.textContent = "No finished MP3 files yet.";
      list.appendChild(empty);
      status.textContent = "Catalogue empty.";
      return;
    }
    entries.forEach((entry) => {
      const item = document.createElement("li");
      item.textContent = `${entry.artist} — ${entry.title} → ${entry.mp3_path}`;
      list.appendChild(item);
    });
    status.textContent = `${entries.length} catalogue entries.`;
  }

  refreshButton.addEventListener("click", () => {
    refreshCatalogue();
  });

  window.addEventListener("ytpd-tab-changed", (event) => {
    if (event.detail && event.detail.tab === "catalogue") {
      refreshCatalogue();
    }
  });
})();
