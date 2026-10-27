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

  function failureHeadline(media) {
    return `${media.artist} — ${media.title}`;
  }

  function failureMeta(media) {
    return media.detail
      ? `${media.phase_label} — ${media.detail}`
      : media.phase_label || "";
  }

  function failureLine(media) {
    const detail = media.detail || media.phase_label || "";
    return detail ? `${failureHeadline(media)}: ${detail}` : failureHeadline(media);
  }

  function syncRowMedia(item, media) {
    item.dataset.trackId = media.track_id || "";
    item.dataset.artist = media.artist || "";
    item.dataset.title = media.title || "";
  }

  function createCopyButton(row) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "failure-copy-btn";
    button.title = "Copy artist + title";
    button.setAttribute("aria-label", "Copy artist and title for YouTube");
    button.innerHTML = COPY_ICON;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const text = `${row.dataset.artist || ""} ${row.dataset.title || ""}`.trim();
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

  function createOverridePanel(trackId, onYoutubeOverride) {
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
      if (!youtubeUrl || !trackId || !onYoutubeOverride) {
        return;
      }
      onYoutubeOverride(trackId, youtubeUrl);
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

  function createOverrideButton(panel) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "failure-override-btn";
    button.title = "Coller une URL YouTube";
    button.setAttribute("aria-label", "Ouvrir le champ URL YouTube");
    button.innerHTML = LINK_ICON;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      panel.hidden = !panel.hidden;
      if (!panel.hidden) {
        const input = panel.querySelector(".failure-override-input");
        if (input) {
          input.focus();
          input.select();
        }
        button.classList.add("is-open");
      } else {
        button.classList.remove("is-open");
      }
    });
    return button;
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

  function createCandidateList(trackId, candidates, onYoutubeOverride) {
    if (!Array.isArray(candidates) || candidates.length === 0 || !onYoutubeOverride) {
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
        if (!trackId || !candidate.youtube_url) {
          return;
        }
        onYoutubeOverride(trackId, candidate.youtube_url);
      });
      item.append(meta, useButton);
      list.appendChild(item);
    });
    return list;
  }

  function updateFailureLabels(item, media, useCard) {
    syncRowMedia(item, media);
    if (useCard) {
      const title = item.querySelector("strong");
      const meta = item.querySelector(".meta");
      if (title) {
        title.textContent = failureHeadline(media);
      }
      if (meta) {
        meta.textContent = failureMeta(media);
      }
      return;
    }
    const line = item.querySelector(".failure-row-body > span");
    if (line) {
      line.textContent = failureLine(media);
    }
  }

  function replaceCandidates(item, media, onYoutubeOverride) {
    const body = item.querySelector(".failure-row-body");
    if (!body) {
      return;
    }
    const previous = body.querySelector(".failure-candidate-list");
    if (previous) {
      previous.remove();
    }
    const candidates = createCandidateList(
      media.track_id,
      media.candidates,
      onYoutubeOverride
    );
    if (candidates) {
      body.append(candidates);
    }
  }

  function buildFailureItem(media, options) {
    const useCard = Boolean(options && options.card);
    const onYoutubeOverride = options && options.onYoutubeOverride;
    const item = document.createElement(useCard ? "div" : "li");
    item.className = useCard
      ? "progress-media-card is-failed failure-row"
      : "is-failed failure-row";
    syncRowMedia(item, media);
    const actions = document.createElement("div");
    actions.className = "failure-row-actions";
    actions.append(createCopyButton(item));
    const body = document.createElement("div");
    body.className = "failure-row-body";
    if (useCard) {
      const title = document.createElement("strong");
      title.textContent = failureHeadline(media);
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = failureMeta(media);
      body.append(title, meta);
    } else {
      const line = document.createElement("span");
      line.textContent = failureLine(media);
      body.append(line);
    }
    if (onYoutubeOverride && media.track_id) {
      const panel = createOverridePanel(media.track_id, onYoutubeOverride);
      actions.append(createOverrideButton(panel));
      body.append(panel);
    }
    const candidates = createCandidateList(
      media.track_id,
      media.candidates,
      onYoutubeOverride
    );
    if (candidates) {
      body.append(candidates);
    }
    item.append(actions, body);
    return item;
  }

  function paintFailureList(container, medias, options) {
    const useCard = Boolean(options && options.card);
    const onYoutubeOverride = options && options.onYoutubeOverride;
    const emptyText = (options && options.emptyText) || "No failures yet.";
    const limit = options && options.limit != null ? options.limit : medias.length;
    const items = Array.isArray(medias) ? medias.slice(0, limit) : [];
    if (items.length === 0) {
      container.innerHTML = "";
      const empty = document.createElement(useCard ? "div" : "li");
      empty.className = "hint";
      empty.textContent = emptyText;
      container.appendChild(empty);
      return;
    }
    const seen = new Set();
    const existing = new Map();
    Array.from(container.querySelectorAll(".failure-row[data-track-id]")).forEach(
      (row) => {
        existing.set(row.dataset.trackId, row);
      }
    );
    container.querySelectorAll(".hint").forEach((node) => node.remove());
    items.forEach((media) => {
      if (!media.track_id) {
        return;
      }
      seen.add(media.track_id);
      const row = existing.get(media.track_id);
      if (row) {
        updateFailureLabels(row, media, useCard);
        replaceCandidates(row, media, onYoutubeOverride);
        container.appendChild(row);
        return;
      }
      container.appendChild(buildFailureItem(media, options));
    });
    existing.forEach((row, trackId) => {
      if (!seen.has(trackId)) {
        row.remove();
      }
    });
  }

  window.YtpdFailureCopy = {
    paintFailureList,
  };
})();
