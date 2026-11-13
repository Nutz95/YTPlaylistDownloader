(() => {
  const select = document.getElementById("ui-locale");
  const i18n = window.YtpdI18n;
  if (!select || !i18n) {
    return;
  }

  const initial = i18n.normalizeLocale(select.value || "en");
  i18n.setLocale(initial);
  select.value = initial;

  async function persistLocale(code) {
    const response = await fetch("/api/config/ui-locale", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ui_locale: code }),
    });
    if (!response.ok) {
      select.value = i18n.getLocale();
    }
  }

  select.addEventListener("change", () => {
    const code = i18n.normalizeLocale(select.value);
    select.value = code;
    i18n.setLocale(code);
    persistLocale(code);
  });
})();
