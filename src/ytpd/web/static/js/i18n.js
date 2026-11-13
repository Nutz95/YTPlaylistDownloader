(() => {
  const catalogs = {
    en: window.YtpdI18nMessagesEn || {},
    fr: window.YtpdI18nMessagesFr || {},
  };
  const supported = Object.keys(catalogs);
  let locale = "en";

  function normalizeLocale(code) {
    const raw = String(code || "").toLowerCase();
    if (supported.includes(raw)) {
      return raw;
    }
    return "en";
  }

  function catalogFor(code) {
    return catalogs[normalizeLocale(code)] || catalogs.en || {};
  }

  function format(template, vars) {
    if (!vars) {
      return template;
    }
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      if (Object.prototype.hasOwnProperty.call(vars, key)) {
        return String(vars[key]);
      }
      return match;
    });
  }

  function t(key, vars) {
    const primary = catalogFor(locale)[key];
    const fallback = catalogFor("en")[key];
    const template = primary || fallback || key;
    return format(template, vars);
  }

  function applyNode(node) {
    const key = node.getAttribute("data-i18n");
    if (key) {
      node.textContent = t(key);
    }
    const htmlKey = node.getAttribute("data-i18n-html");
    if (htmlKey) {
      node.innerHTML = t(htmlKey);
    }
    const titleKey = node.getAttribute("data-i18n-title");
    if (titleKey) {
      node.setAttribute("title", t(titleKey));
    }
    const placeholderKey = node.getAttribute("data-i18n-placeholder");
    if (placeholderKey) {
      node.setAttribute("placeholder", t(placeholderKey));
    }
    const ariaKey = node.getAttribute("data-i18n-aria-label");
    if (ariaKey) {
      node.setAttribute("aria-label", t(ariaKey));
    }
  }

  function applyDom(root) {
    const scope = root || document;
    scope.querySelectorAll(
      "[data-i18n], [data-i18n-html], [data-i18n-title], [data-i18n-placeholder], [data-i18n-aria-label]"
    ).forEach(applyNode);
    document.documentElement.lang = locale;
  }

  function refreshStatus(element) {
    const key = element.dataset.i18nStatusKey;
    if (!key) {
      return;
    }
    let vars;
    if (element.dataset.i18nStatusVars) {
      try {
        vars = JSON.parse(element.dataset.i18nStatusVars);
      } catch (_error) {
        vars = undefined;
      }
    }
    element.textContent = t(key, vars);
  }

  function refreshBoundStatuses(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-i18n-status-key]").forEach(refreshStatus);
  }

  function bindStatus(element) {
    return {
      set(key, vars) {
        element.dataset.i18nStatusKey = key;
        if (vars) {
          element.dataset.i18nStatusVars = JSON.stringify(vars);
        } else {
          delete element.dataset.i18nStatusVars;
        }
        element.textContent = t(key, vars);
      },
      clear() {
        delete element.dataset.i18nStatusKey;
        delete element.dataset.i18nStatusVars;
      },
      refresh() {
        refreshStatus(element);
      },
    };
  }

  function setLocale(code) {
    const next = normalizeLocale(code);
    if (next === locale) {
      applyDom();
      refreshBoundStatuses();
      return;
    }
    locale = next;
    applyDom();
    refreshBoundStatuses();
    window.dispatchEvent(
      new CustomEvent("ytpd-locale-changed", { detail: { locale } })
    );
  }

  function getLocale() {
    return locale;
  }

  window.YtpdI18n = {
    t,
    setLocale,
    getLocale,
    applyDom,
    bindStatus,
    normalizeLocale,
    supportedLocales: () => supported.slice(),
  };
})();
