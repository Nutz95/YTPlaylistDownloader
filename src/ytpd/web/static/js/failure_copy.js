(() => {
  const COPY_ICON =
    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  const LINK_ICON =
    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
    return Promise.resolve();
  }

  function artistTitleText(media) {
    return `${media.artist || ""} ${media.title || ""}`.trim();
  }

  function formatDuration(seconds) {
    if (seconds == null || Number.isNaN(Number(seconds))) {
      return "?";
    }
    const total = Math.max(0, Math.floor(Number(seconds)));
    const minutes = Math.floor(total / 60);
    const rem = total % 60;
    return `${minutes}:${String(rem).padStart(2, "0")}`;
  }

  function createCopyButton(media) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "failure-copy-btn";
    button.title = "Copy artist + title";
    button.setAttribute("aria-label", "Copy artist and title for YouTube");
    button.innerHTML = COPY_ICON;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const text = artistTitleText(media);
      if (!text) {
        return;
      }
      copyText(text).then(() => {
        button.classList.add("is-copied");
        window.setTimeout(() => button.classList.remove("is-copied"), 900);
      });
    });
    return button;
  }

  function createOverridePanel(media, onYoutubeOverride) {
    const panel = document.createElement("div");
    panel.className = "failure-override-panel";
    panel.hidden = true;
    const input = document.createElement("input");
    input.type = "url";
    input.className = "failure-override-input";
    input.placeholder = "https://www.youtube.com/watch?v=…";
    input.setAttribute("aria-label", "YouTube URL override");
    const apply = document.createElement("button");
    apply.type = "button";
    apply.className = "failure-override-apply";
    apply.textContent = "Appliquer";
    const submit = () => {
      const youtubeUrl = input.value.trim();
      if (!youtubeUrl || !media.track_id || !onYoutubeOverride) {
        return;
      }
      onYoutubeOverride(media.track_id, youtubeUrl);
    };
    apply.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      submit();
    });
    input.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      submit();
    });
    panel.append(input, apply);
    return panel;
  }

  function createOverrideButton(media, onYoutubeOverride, panel) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "failure-override-btn";
    button.title = "Coller une URL YouTube";
    button.setAttribute("aria-label", "Ouvrir le champ URL YouTube");
    button.innerHTML = LINK_ICON;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (!media.track_id || !onYoutubeOverride || !panel) {
        return;
      }
      panel.hidden = !panel.hidden;
      if (!panel.hidden) {
        const input = panel.querySelector(".failure-override-input");
        if (input) {
          input.focus();
          input.select();
        }
        button.classList.add("is-applied");
      } else {
        button.classList.remove("is-applied");
      }
    });
    return button;
  }

  function createCandidateList(media, onYoutubeOverride) {
    const candidates = Array.isArray(media.candidates) ? media.candidates : [];
    if (candidates.length === 0 || !onYoutubeOverride) {
      return null;
    }
    const list = document.createElement("ul");
    list.className = "failure-candidate-list";
    candidates.forEach((candidate) => {
      const item = document.createElement("li");
      item.className = "failure-candidate-item";
      const meta = document.createElement("div");
      meta.className = "failure-candidate-meta";
      const title = candidate.title || "(no title)";
      const channel = candidate.channel || "?";
      const duration = formatDuration(candidate.duration_sec);
      meta.textContent = `${title} · ${channel} · ${duration}`;
      const useButton = document.createElement("button");
      useButton.type = "button";
      useButton.className = "failure-candidate-use";
      useButton.textContent = "Utiliser";
      useButton.title = candidate.youtube_url || "";
      useButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (!media.track_id || !candidate.youtube_url) {
          return;
        }
        onYoutubeOverride(media.track_id, candidate.youtube_url);
      });
      item.append(meta, useButton);
      list.appendChild(item);
    });
    return list;
  }

  function appendFailureItem(container, media, options) {
    const useCard = Boolean(options && options.card);
    const onYoutubeOverride = options && options.onYoutubeOverride;
    const item = document.createElement(useCard ? "div" : "li");
    item.className = useCard
      ? "progress-media-card is-failed failure-row"
      : "is-failed failure-row";
    const actions = document.createElement("div");
    actions.className = "failure-row-actions";
    actions.append(createCopyButton(media));
    const body = document.createElement("div");
    body.className = "failure-row-body";
    const title = document.createElement(useCard ? "strong" : "span");
    title.className = useCard ? "" : "failure-row-title";
    title.textContent = `${media.artist} — ${media.title}`;
    const detail = media.detail || media.phase_label || "";
    if (useCard) {
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = media.detail
        ? `${media.phase_label} — ${media.detail}`
        : media.phase_label || "";
      body.append(title, meta);
    } else {
      const line = document.createElement("span");
      line.textContent = detail
        ? `${media.artist} — ${media.title}: ${detail}`
        : `${media.artist} — ${media.title}`;
      body.append(line);
    }
    if (onYoutubeOverride) {
      const panel = createOverridePanel(media, onYoutubeOverride);
      actions.append(createOverrideButton(media, onYoutubeOverride, panel));
      body.append(panel);
    }
    const candidates = createCandidateList(media, onYoutubeOverride);
    if (candidates) {
      body.append(candidates);
    }
    item.append(actions, body);
    container.appendChild(item);
  }

  window.YtpdFailureCopy = {
    appendFailureItem,
    artistTitleText,
  };
})();
