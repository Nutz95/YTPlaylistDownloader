(() => {
  const form = document.getElementById("config-form");
  const status = document.getElementById("config-status");
  const i18n = window.YtpdI18n;
  if (!form || !status) {
    return;
  }

  const statusBind = i18n ? i18n.bindStatus(status) : null;

  function t(key) {
    return i18n ? i18n.t(key) : key;
  }

  function showStatus(key) {
    if (statusBind) {
      statusBind.set(key);
      return;
    }
    status.textContent = t(key);
  }

  function showRawStatus(text) {
    if (statusBind) {
      statusBind.clear();
    }
    status.textContent = text;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    showStatus("config.saving");
    const payload = {
      bind_host: document.getElementById("bind_host").value,
      bind_port: Number(document.getElementById("bind_port").value),
      work_dir: document.getElementById("work_dir").value,
      dest_dir: document.getElementById("dest_dir").value,
    };
    const response = await fetch("/api/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      showRawStatus(body.error || t("config.save.failed"));
      return;
    }
    document.getElementById("bind_host").value = body.bind_host;
    document.getElementById("bind_port").value = body.bind_port;
    document.getElementById("work_dir").value = body.work_dir;
    document.getElementById("dest_dir").value = body.dest_dir;
    showStatus("config.saved");
  });
})();
