(() => {
  const form = document.getElementById("config-form");
  const status = document.getElementById("config-status");
  if (!form || !status) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "Saving…";
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
      status.textContent = body.error || "Save failed";
      return;
    }
    document.getElementById("bind_host").value = body.bind_host;
    document.getElementById("bind_port").value = body.bind_port;
    document.getElementById("work_dir").value = body.work_dir;
    document.getElementById("dest_dir").value = body.dest_dir;
    status.textContent = "Saved.";
  });
})();
