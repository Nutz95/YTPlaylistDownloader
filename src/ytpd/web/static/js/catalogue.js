(() => {
  const refreshButton = document.getElementById("catalogue-refresh");
  const status = document.getElementById("catalogue-status");
  const list = document.getElementById("catalogue-list");
  const i18n = window.YtpdI18n;
  if (!refreshButton || !status || !list) {
    return;
  }

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

  async function refreshCatalogue() {
    showStatus("catalogue.status.loading");
    const response = await fetch("/api/catalog");
    if (!response.ok) {
      showStatus("catalogue.status.failed");
      return;
    }
    const body = await response.json();
    const entries = Array.isArray(body.entries) ? body.entries : [];
    list.innerHTML = "";
    if (entries.length === 0) {
      const empty = document.createElement("li");
      empty.className = "hint";
      empty.textContent = t("catalogue.empty");
      list.appendChild(empty);
      showStatus("catalogue.status.empty");
      return;
    }
    entries.forEach((entry) => {
      const item = document.createElement("li");
      item.textContent = `${entry.artist} — ${entry.title} → ${entry.output_path}`;
      list.appendChild(item);
    });
    showStatus("catalogue.status.count", { count: entries.length });
  }

  refreshButton.addEventListener("click", () => {
    refreshCatalogue();
  });

  window.addEventListener("ytpd-tab-changed", (event) => {
    if (event.detail && event.detail.tab === "catalogue") {
      refreshCatalogue();
    }
  });

  window.addEventListener("ytpd-locale-changed", () => {
    if (list.children.length > 0) {
      refreshCatalogue();
      return;
    }
    showStatus("catalogue.status.idle");
  });
})();
