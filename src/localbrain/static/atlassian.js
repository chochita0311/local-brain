const atlassianRegistration = document.querySelector("[data-atlassian-registration]");

if (atlassianRegistration) {
  const registrationUrl = atlassianRegistration.querySelector("#atlassian-url");
  const siteSelect = atlassianRegistration.querySelector("[data-atlassian-site-select]");
  const newConnection = atlassianRegistration.querySelector("[data-atlassian-new-connection]");
  const preview = atlassianRegistration.querySelector("[data-atlassian-url-preview]");
  const siteName = atlassianRegistration.querySelector("[data-atlassian-site-name]");
  const targetSelect = atlassianRegistration.querySelector("[data-atlassian-target-select]");
  const connectionSelect = atlassianRegistration.querySelector("[data-atlassian-connection-select]");
  let previewTimer = null;
  let previewRequest = null;

  const syncConnectionMode = () => {
    if (!siteSelect || !newConnection) return;
    const creating = siteSelect.value === "new";
    newConnection.dataset.active = creating ? "true" : "false";
    if (creating) newConnection.open = true;
  };

  const setPreview = (message, state = "neutral") => {
    if (!preview) return;
    preview.classList.remove("neutral", "success", "warning", "error");
    preview.classList.add(state);
    preview.textContent = message;
  };

  const previewUrl = async () => {
    if (!registrationUrl || !preview) return;
    const value = registrationUrl.value.trim();
    if (!value) {
      setPreview("URL을 입력하면 Jira/Confluence, Site 도메인, Item 또는 Space 식별자를 로컬에서 확인합니다.");
      return;
    }
    previewRequest?.abort();
    const controller = new AbortController();
    previewRequest = controller;
    setPreview("URL을 로컬에서 확인하는 중입니다.");
    const service = atlassianRegistration.querySelector('input[name="service"]')?.value || "";
    try {
      const params = new URLSearchParams({ url: value, service });
      const response = await fetch(`/api/atlassian/registration-preview?${params}`, {
        credentials: "same-origin",
        headers: { "X-Requested-With": "LocalBrain-Atlassian-Preview" },
        signal: controller.signal,
      });
      const payload = await response.json();
      if (!response.ok) {
        const detail = payload?.detail;
        throw new Error(detail?.message || "지원되는 Atlassian URL인지 확인해 주세요.");
      }
      const serviceLabel = payload.service === "jira" ? "Jira" : "Confluence";
      const kindLabel = payload.kind === "item" ? "Item" : "Space";
      const identifier = payload.identifier ? ` · ${payload.identifier}` : "";
      const enabledMatches = payload.matches.filter((match) => match.enabled);
      if (enabledMatches.length === 1) {
        if (siteSelect) siteSelect.value = String(enabledMatches[0].site_id);
        setPreview(
          `${serviceLabel} · ${payload.normalized_domain} · ${kindLabel}${identifier} · ${enabledMatches[0].provider_label} 연결 재사용`,
          "success",
        );
      } else if (enabledMatches.length > 1) {
        if (siteSelect) siteSelect.value = "";
        setPreview(
          `${serviceLabel} · ${payload.normalized_domain} · ${kindLabel}${identifier} · 일치하는 연결 ${enabledMatches.length}개 중 하나를 선택하세요.`,
          "warning",
        );
      } else {
        if (siteSelect) siteSelect.value = "new";
        if (siteName && !siteName.value) siteName.value = payload.suggested_site_name || "";
        setPreview(
          `${serviceLabel} · ${payload.normalized_domain} · ${kindLabel}${identifier} · 새 MCP 연결을 선택하세요.`,
          "warning",
        );
      }
      syncConnectionMode();
    } catch (error) {
      if (error.name === "AbortError") return;
      setPreview(error.message, "error");
    } finally {
      if (previewRequest === controller) previewRequest = null;
    }
  };

  siteSelect?.addEventListener("change", syncConnectionMode);
  registrationUrl?.addEventListener("input", () => {
    window.clearTimeout(previewTimer);
    previewTimer = window.setTimeout(previewUrl, 350);
  });
  registrationUrl?.addEventListener("blur", () => {
    window.clearTimeout(previewTimer);
    previewUrl();
  });
  syncConnectionMode();
  if (registrationUrl?.value.trim()) previewUrl();

  const syncDiscoveryConnections = () => {
    if (!targetSelect || !connectionSelect) return;
    const targetDomain = targetSelect.value;
    const current = connectionSelect.selectedOptions[0];
    for (const option of connectionSelect.options) {
      if (!option.dataset.domain) continue;
      option.hidden = Boolean(targetDomain && option.dataset.domain !== targetDomain);
    }
    if (current?.dataset.domain && current.dataset.domain !== targetDomain) {
      connectionSelect.value = "";
    }
    connectionSelect.disabled = !targetDomain;
  };

  targetSelect?.addEventListener("change", syncDiscoveryConnections);
  syncDiscoveryConnections();

  const focusDestination = () => {
    if (!window.location.hash) return;
    let id = window.location.hash.slice(1);
    try {
      id = decodeURIComponent(id);
    } catch (_error) {
      return;
    }
    const target = document.getElementById(id);
    if (!target) return;
    window.requestAnimationFrame(() => {
      target.focus({ preventScroll: true });
      target.scrollIntoView({ block: "center" });
    });
  };

  focusDestination();
  atlassianRegistration
    .querySelector("[data-registration-notice]")
    ?.focus({ preventScroll: true });

  const catalog = atlassianRegistration.querySelector("[data-catalog-run]");
  const activeStates = new Set(["queued", "running", "cancelling"]);
  if (catalog && activeStates.has(catalog.dataset.catalogStatus)) {
    const runId = catalog.dataset.catalogRun;
    let stopped = false;

    const poll = async () => {
      try {
        const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`, {
          credentials: "same-origin",
          headers: { "X-Requested-With": "LocalBrain-Atlassian-Catalog" },
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (!activeStates.has(payload.run?.status)) {
          stopped = true;
          window.location.reload();
        }
      } catch (_error) {
        stopped = true;
      }
      if (!stopped) window.setTimeout(poll, 1500);
    };

    window.setTimeout(poll, 1500);
  }
}
