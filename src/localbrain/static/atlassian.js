const atlassianRegistration = document.querySelector("[data-atlassian-registration]");

const clearAddFieldError = (input) => {
  const content = input?.closest("[data-atlassian-add-content]");
  const error = content?.querySelector("[data-atlassian-add-error]");
  if (!input || !error) return;
  const errorId = error.id;
  error.remove();
  input.removeAttribute("aria-invalid");
  const describedBy = (input.getAttribute("aria-describedby") || "")
    .split(/\s+/)
    .filter((token) => token && token !== errorId);
  if (describedBy.length) input.setAttribute("aria-describedby", describedBy.join(" "));
  else input.removeAttribute("aria-describedby");
  input.closest("form")?.removeAttribute("aria-describedby");
};

if (atlassianRegistration) {
  const registrationUrl = atlassianRegistration.querySelector("#atlassian-url");
  const preview = atlassianRegistration.querySelector("[data-atlassian-url-preview]");
  const targetSelect = atlassianRegistration.querySelector("[data-atlassian-target-select]");
  const connectionSelect = atlassianRegistration.querySelector("[data-atlassian-connection-select]");
  let previewTimer = null;
  let previewRequest = null;
  let previewGeneration = 0;

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
      setPreview("URL을 입력하면 Jira/Wiki, 도메인, 링크/문서 또는 Project/Space 식별자를 로컬에서 확인합니다.");
      return;
    }
    previewRequest?.abort();
    const controller = new AbortController();
    const generation = ++previewGeneration;
    previewRequest = controller;
    setPreview("URL을 로컬에서 확인하는 중입니다.");
    try {
      const params = new URLSearchParams({ url: value });
      const response = await fetch(`/api/atlassian/registration-preview?${params}`, {
        credentials: "same-origin",
        headers: { "X-Requested-With": "LocalBrain-Atlassian-Preview" },
        signal: controller.signal,
      });
      const payload = await response.json();
      if (generation !== previewGeneration || registrationUrl.value.trim() !== value) return;
      if (!response.ok) {
        const detail = payload?.detail;
        throw new Error(detail?.message || "지원되는 Atlassian URL인지 확인해 주세요.");
      }
      const serviceLabel = payload.service === "jira" ? "Jira" : "Wiki";
      const kindLabel = payload.kind === "item"
        ? (payload.service === "jira" ? "링크" : "문서")
        : (payload.service === "jira" ? "Project" : "Space");
      const identifier = payload.identifier ? ` · ${payload.identifier}` : "";
      setPreview(
        `${serviceLabel} · ${payload.normalized_domain} · ${kindLabel}${identifier} · 로컬 등록 준비됨`,
        "success",
      );
    } catch (error) {
      if (error.name === "AbortError" || generation !== previewGeneration) return;
      setPreview(error.message, "error");
    } finally {
      if (previewRequest === controller) previewRequest = null;
    }
  };

  registrationUrl?.addEventListener("input", () => {
    clearAddFieldError(registrationUrl);
    previewRequest?.abort();
    previewRequest = null;
    previewGeneration += 1;
    window.clearTimeout(previewTimer);
    previewTimer = window.setTimeout(previewUrl, 350);
  });
  registrationUrl?.addEventListener("blur", () => {
    window.clearTimeout(previewTimer);
    previewUrl();
  });
  if (registrationUrl?.value.trim()) previewUrl();

  const syncDiscoveryConnections = () => {
    if (!targetSelect || !connectionSelect) return;
    const targetSiteId = targetSelect.value;
    const current = connectionSelect.selectedOptions[0];
    for (const option of connectionSelect.options) {
      if (!option.dataset.siteId) continue;
      option.hidden = Boolean(targetSiteId && option.dataset.siteId !== targetSiteId);
    }
    if (current?.dataset.siteId && current.dataset.siteId !== targetSiteId) {
      connectionSelect.value = "";
    }
    connectionSelect.disabled = !targetSiteId;
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

  const owningError = atlassianRegistration.querySelector("[data-atlassian-form-error]");
  if (owningError) {
    const errorTarget = owningError.querySelector('[role="alert"]') || owningError;
    window.requestAnimationFrame(() => errorTarget.focus({ preventScroll: true }));
  } else if (window.location.hash) {
    focusDestination();
  } else if (!atlassianRegistration.hasAttribute("data-atlassian-explorer")) {
    atlassianRegistration.querySelector("[data-registration-notice]")?.focus({ preventScroll: true });
  }

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

let syncAtlassianExplorerModal = () => false;
const atlassianAddDialog = document.querySelector("[data-atlassian-add-dialog]");

const bindReplacementAddPreview = (surface) => {
  const input = surface?.querySelector("#atlassian-url");
  const output = surface?.querySelector("[data-atlassian-url-preview]");
  if (!input || !output) return;
  let timer = null;
  let request = null;
  let generation = 0;
  const render = (message, state = "neutral") => {
    output.classList.remove("neutral", "success", "warning", "error");
    output.classList.add(state);
    output.textContent = message;
  };
  const preview = async () => {
    const value = input.value.trim();
    if (!value) {
      render("URL을 입력하면 인식된 Atlassian identity를 로컬에서 확인합니다.");
      return;
    }
    request?.abort();
    const controller = new AbortController();
    const currentGeneration = ++generation;
    request = controller;
    render("URL을 로컬에서 확인하는 중입니다.");
    try {
      const params = new URLSearchParams({ url: value });
      const response = await fetch(`/api/atlassian/registration-preview?${params}`, {
        credentials: "same-origin",
        headers: { "X-Requested-With": "LocalBrain-Atlassian-Preview" },
        signal: controller.signal,
      });
      const payload = await response.json();
      if (currentGeneration !== generation || input.value.trim() !== value) return;
      if (!response.ok) throw new Error(payload?.detail?.message || "지원되는 Atlassian URL인지 확인해 주세요.");
      const service = payload.service === "jira" ? "Jira" : "Wiki";
      const kind = payload.kind === "item"
        ? (payload.service === "jira" ? "링크" : "문서")
        : (payload.service === "jira" ? "Project" : "Space");
      render(`${service} · ${payload.normalized_domain} · ${kind}${payload.identifier ? ` · ${payload.identifier}` : ""} · 로컬 등록 준비됨`, "success");
    } catch (error) {
      if (error.name === "AbortError" || currentGeneration !== generation) return;
      render(error.message, "error");
    } finally {
      if (request === controller) request = null;
    }
  };
  input.addEventListener("input", () => {
    clearAddFieldError(input);
    request?.abort();
    request = null;
    generation += 1;
    window.clearTimeout(timer);
    timer = window.setTimeout(preview, 350);
  });
  input.addEventListener("blur", () => {
    window.clearTimeout(timer);
    preview();
  });
  if (input.value.trim()) preview();
};

if (atlassianAddDialog) {
  let restoreTrigger = null;
  let pending = false;

  const syncAddSheetOffset = () => {
    const shellHeader = document.querySelector(".workspace-header");
    const headerBottom = shellHeader?.getBoundingClientRect().bottom || 0;
    const offset = Math.max(0, Math.min(window.innerHeight, Math.ceil(headerBottom)));
    atlassianAddDialog.style.setProperty("--atlassian-add-sheet-top", `${offset}px`);
  };

  const focusableInAdd = () => [...atlassianAddDialog.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )].filter((element) => !element.hidden && element.getAttribute("aria-hidden") !== "true");

  const setPending = (form, value) => {
    pending = value;
    atlassianAddDialog.dataset.atlassianAddBusy = value ? "true" : "false";
    form?.setAttribute("aria-busy", value ? "true" : "false");
    const submit = form?.querySelector("[data-atlassian-add-submit]");
    if (submit) submit.disabled = value;
    if (value) {
      const status = form?.querySelector("[data-atlassian-url-preview]");
      if (status) {
        status.classList.remove("success", "warning", "error");
        status.classList.add("neutral");
        status.textContent = "URL reference를 로컬에 등록하는 중입니다.";
      }
    }
  };

  const closeDialog = () => {
    if (!pending && atlassianAddDialog.open) atlassianAddDialog.close("cancel");
  };

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-atlassian-add-trigger]");
    if (!trigger || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (typeof atlassianAddDialog.showModal !== "function") return;
    event.preventDefault();
    restoreTrigger = trigger;
    syncAddSheetOffset();
    atlassianAddDialog.showModal();
    syncAtlassianExplorerModal();
    window.requestAnimationFrame(() => atlassianAddDialog.querySelector("#atlassian-url")?.focus());
  });

  window.addEventListener("resize", () => {
    if (atlassianAddDialog.open) syncAddSheetOffset();
  });

  atlassianAddDialog.addEventListener("click", (event) => {
    if (event.target.closest("[data-atlassian-add-close], [data-atlassian-add-cancel]")) {
      event.preventDefault();
      closeDialog();
    }
  });
  atlassianAddDialog.addEventListener("cancel", (event) => {
    if (pending) event.preventDefault();
  });
  atlassianAddDialog.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    const focusable = focusableInAdd();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && (document.activeElement === first || !atlassianAddDialog.contains(document.activeElement))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !atlassianAddDialog.contains(document.activeElement))) {
      event.preventDefault();
      first.focus();
    }
  });
  atlassianAddDialog.addEventListener("close", () => {
    const sheetRestored = syncAtlassianExplorerModal({ focus: true });
    if (!sheetRestored) {
      const target = restoreTrigger?.isConnected
        ? restoreTrigger
        : document.querySelector("[data-atlassian-explorer-heading]");
      window.requestAnimationFrame(() => target?.focus({ preventScroll: true }));
    }
  });

  atlassianAddDialog.addEventListener("submit", async (event) => {
    const form = event.target.closest("[data-atlassian-add-form]");
    if (!form || pending || !atlassianAddDialog.open || typeof window.fetch !== "function") return;
    event.preventDefault();
    setPending(form, true);
    try {
      const body = new URLSearchParams();
      for (const [key, value] of new FormData(form).entries()) body.append(key, String(value));
      const response = await fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-LocalBrain-Partial": "atlassian-add",
        },
        body,
      });
      if (response.redirected) {
        window.location.assign(response.url);
        return;
      }
      if (response.status === 422) {
        const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
        const incoming = parsed.querySelector("[data-atlassian-add-content]");
        const current = atlassianAddDialog.querySelector("[data-atlassian-add-content]");
        if (!incoming || !current) throw new Error("Invalid Add response");
        const adopted = document.importNode(incoming, true);
        current.replaceWith(adopted);
        setPending(adopted.querySelector("form"), false);
        bindReplacementAddPreview(adopted);
        const focusTarget = adopted.querySelector('[aria-invalid="true"]') || adopted.querySelector('[role="alert"]');
        window.requestAnimationFrame(() => focusTarget?.focus({ preventScroll: true }));
        return;
      }
      throw new Error(`Unexpected Add response ${response.status}`);
    } catch (_error) {
      setPending(form, false);
      form.submit();
    }
  });
}

if (!atlassianAddDialog) {
  const directAdd = document.querySelector("[data-atlassian-add-form]");
  if (directAdd) {
    const target = directAdd.querySelector('[aria-invalid="true"]') || directAdd.querySelector("#atlassian-url");
    window.requestAnimationFrame(() => target?.focus({ preventScroll: true }));
  }
}

const atlassianExplorer = document.querySelector("[data-atlassian-explorer]");

if (atlassianExplorer) {
  const compactQuery = window.matchMedia("(max-width: 920px)");
  let previewRequest = null;
  let requestGeneration = 0;

  const currentPreview = () => atlassianExplorer.querySelector("[data-atlassian-preview]");
  const resultList = () => atlassianExplorer.querySelector("[data-atlassian-result-list]");
  const resultHeading = () => atlassianExplorer.querySelector("[data-atlassian-results-heading]");
  const entryLinks = () => [...atlassianExplorer.querySelectorAll("[data-atlassian-entry-link]")];
  const selectedKind = () => currentPreview()?.dataset.selectionKind || "";
  const selectedId = () => currentPreview()?.dataset.selectedId || "";
  const selectedKey = () => currentPreview()?.dataset.selectedKey
    || (selectedKind() && selectedId() ? `${selectedKind()}:${selectedId()}` : "");
  const selectedState = () => currentPreview()?.dataset.previewState || "empty";
  const rowForKey = (entryKey) => entryLinks()
    .find((link) => link.dataset.atlassianEntryKey === String(entryKey));
  const selectionKeyFromUrl = (value) => {
    const destination = new URL(value, window.location.href);
    const referenceId = destination.searchParams.get("reference");
    if (referenceId) return `reference:${referenceId}`;
    const itemId = destination.searchParams.get("item");
    return itemId ? `item:${itemId}` : "";
  };
  const clearLink = () => currentPreview()?.querySelector('a[data-atlassian-detail-close]');
  const modalBackground = () => [
    document.querySelector(".skip-link"),
    document.querySelector(".lnb"),
    document.querySelector(".workspace-header"),
    document.querySelector(".toast-region"),
    ...atlassianExplorer.querySelectorAll("[data-atlassian-modal-background]"),
  ].filter(Boolean);

  const destinationFor = (value) => {
    const destination = new URL(value, window.location.href);
    if (destination.origin !== window.location.origin || destination.pathname !== "/atlassian") {
      return null;
    }
    return destination;
  };

  const baseDestinationKey = (value) => {
    const destination = new URL(value, window.location.href);
    destination.searchParams.delete("item");
    destination.searchParams.delete("reference");
    destination.searchParams.delete("sync_receipt");
    const requestedView = (destination.searchParams.get("view") || "all").toLowerCase();
    destination.searchParams.set(
      "view",
      requestedView === "confluence"
        ? "wiki"
        : (["all", "jira", "wiki"].includes(requestedView) ? requestedView : "all"),
    );
    for (const [key, parameter] of [...destination.searchParams.entries()]) {
      if (parameter === "") destination.searchParams.delete(key);
    }
    destination.hash = "";
    destination.searchParams.sort();
    return destination.href;
  };
  let explorerBaseKey = baseDestinationKey(window.location.href);

  const syncForm = () => atlassianExplorer.querySelector("[data-atlassian-sync-form]");
  const syncButton = () => atlassianExplorer.querySelector("[data-atlassian-sync-button]");
  const syncStatus = () => atlassianExplorer.querySelector("[data-atlassian-sync-status]");
  const syncContent = () => syncStatus()?.querySelector("[data-atlassian-sync-content]");
  const syncAnnouncement = () => syncStatus()?.querySelector("[data-atlassian-sync-announcement]");
  const syncCandidateKeys = [
    "key_only",
    "unsafe_url",
    "unsupported_locator",
    "unconfigured_domain",
    "ambiguous_site",
    "invalid_location",
  ];
  const syncReasonLabels = {
    "ineligible-session": "대상 외 Session",
    "disabled-document": "비활성 Local Context",
    "session-projection-missing": "Session 참조 투영 없음",
    "session-projection-stale": "Session 참조 투영 갱신 필요",
    "session-projection-error": "Session 참조 투영 오류",
    "session-projection-partial": "Session 참조 투영 일부만 보존됨",
    "context-unavailable": "Local Context 문서 확인 불가",
    "document-url-limit": "문서 URL 보존 한도 초과",
    "invalid-location": "근거 위치 확인 불가",
    "unsafe-url": "안전하지 않은 URL",
    "unsupported-locator": "지원하지 않는 Atlassian URL",
    "unconfigured-domain": "등록되지 않은 도메인 URL",
    "ambiguous-site": "도메인을 하나로 정할 수 없음",
    "identity-collision": "구조 identity 충돌",
    "reconciliation-error": "로컬 근거 정리 실패",
  };
  const syncCandidateLabels = {
    key_only: "URL 없이 언급된 Jira key",
    unsafe_url: "안전하지 않은 URL",
    unsupported_locator: "지원하지 않는 Atlassian URL",
    unconfigured_domain: "등록되지 않은 도메인 URL",
    ambiguous_site: "도메인을 하나로 정할 수 없는 URL",
    invalid_location: "근거 위치 확인 불가",
  };
  const syncOutcomeLabels = {
    complete: "완료",
    partial: "일부 완료",
    excluded: "제외",
    unavailable: "확인 불가",
    failed: "실패",
  };
  const syncOutcomeTones = {
    complete: "success",
    partial: "warning",
    excluded: "neutral",
    unavailable: "warning",
    failed: "danger",
  };
  let pendingSyncAnnouncement = "";

  const syncNumber = (value) => (
    Number.isSafeInteger(value) && value >= 0 ? value : 0
  );

  const syncNode = (tag, className = "", text = "") => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== "") node.textContent = text;
    return node;
  };

  const currentSyncReturnTo = () => {
    const destination = new URL(window.location.href);
    destination.searchParams.delete("sync_receipt");
    destination.hash = "";
    return `${destination.pathname}${destination.search}`;
  };

  const syncModalOwnerActive = () => (
    Boolean(atlassianAddDialog?.open)
    || atlassianExplorer.classList.contains("is-sheet-open")
  );

  const announceSync = (message) => {
    const announcement = syncAnnouncement();
    if (!announcement || !message) return;
    if (syncModalOwnerActive()) {
      pendingSyncAnnouncement = message;
      announcement.setAttribute("aria-live", "off");
      return;
    }
    pendingSyncAnnouncement = "";
    announcement.setAttribute(
      "aria-live",
      announcement.dataset.atlassianSyncUrgency || "polite",
    );
    announcement.textContent = "";
    window.requestAnimationFrame(() => {
      if (announcement.isConnected) announcement.textContent = message;
    });
  };

  const flushSyncAnnouncement = () => {
    if (!pendingSyncAnnouncement || syncModalOwnerActive()) return;
    const message = pendingSyncAnnouncement;
    pendingSyncAnnouncement = "";
    announceSync(message);
  };

  const setSyncSurfaceState = (state, { alert = false, busy = false } = {}) => {
    const status = syncStatus();
    if (!status) return null;
    status.classList.remove(
      "state-idle",
      "state-working",
      "state-complete",
      "state-partial",
      "state-failed",
      "state-busy",
    );
    status.classList.add(`state-${state}`);
    status.setAttribute("aria-busy", busy ? "true" : "false");
    const announcement = syncAnnouncement();
    if (announcement) {
      announcement.setAttribute("role", alert ? "alert" : "status");
      announcement.dataset.atlassianSyncUrgency = alert ? "assertive" : "polite";
      announcement.setAttribute(
        "aria-live",
        syncModalOwnerActive() ? "off" : announcement.dataset.atlassianSyncUrgency,
      );
    }
    return status;
  };

  const renderSyncMessage = (state, title, detail, { alert = false, busy = false } = {}) => {
    const status = setSyncSurfaceState(state, { alert, busy });
    if (!status) return;
    const summary = syncNode("div", "atlassian-sync-summary");
    summary.id = "atlassian-sync-scope";
    summary.dataset.atlassianSyncSummary = "";
    const copy = syncNode("div");
    copy.append(syncNode("strong", "", title), syncNode("span", "", detail));
    summary.append(copy);
    syncContent()?.replaceChildren(summary);
    announceSync(`${title}. ${detail}`);
  };

  const syncBadge = (label, value, tone) => (
    syncNode("span", `status-badge ${tone}`, `${label} ${syncNumber(value)}`)
  );

  const renderSyncReport = (report) => {
    const allowedStatuses = new Set(["complete", "partial", "failed", "busy"]);
    const state = allowedStatuses.has(report?.status) ? report.status : "failed";
    const titles = {
      complete: "로컬 근거 동기화 완료",
      partial: "로컬 근거 일부 동기화",
      failed: "로컬 근거 동기화 실패",
      busy: "다른 탭에서 동기화 중",
    };
    const title = titles[state];
    if (state === "busy") {
      renderSyncMessage(
        "busy",
        title,
        "진행 중인 로컬 Sync가 끝난 뒤 같은 Sync를 다시 실행해 주세요. 새 작업이나 remote read는 시작하지 않았습니다.",
      );
      return;
    }
    const status = setSyncSurfaceState(state, {
      alert: state === "partial" || state === "failed",
    });
    if (!status) return;

    const sources = report?.sources || {};
    const items = report?.items || {};
    const evidence = report?.evidence || {};
    const structureReferences = report?.structure_references || {};
    const structureEvidence = report?.structure_evidence || {};
    const siteOnly = syncNumber(report?.site_only);
    const skips = report?.candidate_skips || {};
    const limits = report?.scope_limits || {};
    const skippedTotal = syncCandidateKeys.reduce(
      (total, key) => total + syncNumber(skips[key]),
      0,
    );

    const summary = syncNode("div", "atlassian-sync-summary");
    summary.id = "atlassian-sync-scope";
    summary.dataset.atlassianSyncSummary = "";
    const copy = syncNode("div");
    copy.append(
      syncNode("strong", "", title),
      syncNode("span", "", "저장된 Session 및 Local Context만 확인했으며 remote read는 실행하지 않았습니다."),
    );
    const outcomes = syncNode("div", "atlassian-sync-outcomes");
    outcomes.setAttribute("aria-label", "동기화 집계");
    const outcomeBadges = [
      syncBadge("새 링크/문서", items.new, "success"),
      syncBadge("기존 링크/문서", items.reused, "info"),
    ];
    if (syncNumber(structureReferences.new)) {
      outcomeBadges.push(syncBadge("새 구조 참조", structureReferences.new, "success"));
    }
    if (syncNumber(structureReferences.reused)) {
      outcomeBadges.push(syncBadge("기존 구조 참조", structureReferences.reused, "info"));
    }
    if (siteOnly) outcomeBadges.push(syncBadge("도메인/서비스만 확인", siteOnly, "neutral"));
    outcomeBadges.push(
      syncBadge("후보 건너뜀", skippedTotal, "neutral"),
      syncBadge("소스 확인 불가", sources.unavailable, "warning"),
      syncBadge("소스 실패", sources.failed, "danger"),
    );
    outcomes.append(...outcomeBadges);
    const evidenceSummary = [
      `소스 ${syncNumber(sources.scanned)}/${syncNumber(sources.considered)}개 확인`,
      `제외 ${syncNumber(sources.excluded)}개`,
      `링크/문서 근거 새 ${syncNumber(evidence.new)}개`,
      `기존 ${syncNumber(evidence.reused)}개`,
    ];
    if (syncNumber(evidence.removed)) evidenceSummary.push(`정리 ${syncNumber(evidence.removed)}개`);
    evidenceSummary.push(
      `구조 근거 새 ${syncNumber(structureEvidence.new)}개`,
      `기존 ${syncNumber(structureEvidence.reused)}개`,
    );
    if (syncNumber(structureEvidence.removed)) {
      evidenceSummary.push(`정리 ${syncNumber(structureEvidence.removed)}개`);
    }
    const overflow = syncNumber(limits.session_reference_overflow)
      + syncNumber(limits.document_url_overflow);
    if (overflow) evidenceSummary.push(`투영 한도 밖 참조 ${overflow}개`);
    summary.append(copy, outcomes, syncNode("p", "", evidenceSummary.join(" · ")));
    if (syncNumber(limits.session_projection_sources)) {
      summary.append(syncNode(
        "p",
        "atlassian-sync-disclosure",
        `Session ${syncNumber(limits.session_projection_sources)}개는 저장된 안전 URL 투영만 확인했습니다. 원본 Session이나 투영 전에 제외된 후보 수는 재구성하지 않습니다.`,
      ));
    }
    const noChanges = state === "complete"
      && syncNumber(items.new) === 0
      && syncNumber(evidence.new) === 0
      && syncNumber(evidence.removed) === 0
      && syncNumber(structureReferences.new) === 0
      && syncNumber(structureEvidence.new) === 0
      && syncNumber(structureEvidence.removed) === 0;
    if (noChanges) {
      const recovery = syncNode(
        "p",
        "atlassian-sync-recovery",
        "새로 반영할 로컬 근거가 없습니다. Session·Local Context 원본을 먼저 동기화하거나 ",
      );
      const addLink = syncNode("a", "", "Add");
      addLink.href = atlassianExplorer.querySelector("[data-atlassian-add-trigger]")?.href || "/atlassian/add";
      addLink.dataset.atlassianAddTrigger = "";
      recovery.append(addLink, document.createTextNode("에서 링크/문서 URL 하나를 직접 등록할 수 있습니다."));
      summary.append(recovery);
    }
    if (state === "partial" || state === "failed") {
      summary.append(syncNode(
        "p",
        "atlassian-sync-recovery",
        "현재 결과와 기존 인벤토리는 유지됩니다. Retry는 실패한 소스만 고르지 않고 같은 Sync로 전체 로컬 범위를 다시 확인합니다.",
      ));
    }
    const content = syncContent();
    content?.replaceChildren(summary);

    const sourceOutcomes = Array.isArray(report?.source_outcomes)
      ? report.source_outcomes
      : [];
    if (sourceOutcomes.length) {
      const details = syncNode("details", "atlassian-sync-details");
      details.dataset.atlassianSyncDetails = "";
      details.append(syncNode("summary", "", "소스별 결과와 건너뜀 이유"));
      const scroll = syncNode("div", "atlassian-sync-detail-scroll");
      const reasons = syncNode("ul", "atlassian-sync-reasons");
      reasons.setAttribute("aria-label", "후보 건너뜀 집계");
      syncCandidateKeys.forEach((key) => {
        const value = syncNumber(skips[key]);
        if (!value) return;
        const row = syncNode("li");
        row.append(
          syncNode("span", "", syncCandidateLabels[key]),
          syncNode("strong", "", String(value)),
        );
        reasons.append(row);
      });
      const sourceList = syncNode("ul", "atlassian-sync-sources");
      sourceList.setAttribute("aria-label", "소스별 동기화 결과");
      sourceOutcomes.forEach((source) => {
        const row = syncNode("li");
        const heading = syncNode("div");
        heading.append(
          syncNode(
            "strong",
            "",
            `${source?.kind === "session" ? "Session" : "Local Context"} #${syncNumber(source?.local_id)}`,
          ),
          syncNode(
            "span",
            `status-badge ${syncOutcomeTones[source?.outcome] || "neutral"}`,
            syncOutcomeLabels[source?.outcome] || "확인됨",
          ),
        );
        const counts = source?.counts || {};
        const countParts = [
          `URL ${syncNumber(counts.urls)}`,
          `링크/문서 새 ${syncNumber(counts.new_items)}`,
          `기존 ${syncNumber(counts.reused_items)}`,
          `근거 새 ${syncNumber(counts.new_evidence)}`,
          `기존 ${syncNumber(counts.reused_evidence)}`,
        ];
        if (syncNumber(counts.removed_evidence)) {
          countParts.push(`정리 ${syncNumber(counts.removed_evidence)}`);
        }
        if (
          syncNumber(counts.new_structure_references)
          || syncNumber(counts.reused_structure_references)
        ) {
          countParts.push(
            `구조 참조 새 ${syncNumber(counts.new_structure_references)}`,
            `기존 ${syncNumber(counts.reused_structure_references)}`,
          );
        }
        if (
          syncNumber(counts.new_structure_evidence)
          || syncNumber(counts.reused_structure_evidence)
          || syncNumber(counts.removed_structure_evidence)
        ) {
          countParts.push(
            `구조 근거 새 ${syncNumber(counts.new_structure_evidence)}`,
            `기존 ${syncNumber(counts.reused_structure_evidence)}`,
          );
          if (syncNumber(counts.removed_structure_evidence)) {
            countParts.push(`정리 ${syncNumber(counts.removed_structure_evidence)}`);
          }
        }
        if (syncNumber(counts.site_only)) {
          countParts.push(`도메인/서비스만 확인 ${syncNumber(counts.site_only)}`);
        }
        if (syncNumber(counts.skipped)) countParts.push(`건너뜀 ${syncNumber(counts.skipped)}`);
        row.append(heading, syncNode("span", "", countParts.join(" · ")));
        const codes = Array.isArray(source?.reason_codes) ? source.reason_codes : [];
        if (codes.length) {
          const sourceReasons = syncNode("ul", "atlassian-sync-source-reasons");
          codes.forEach((code) => sourceReasons.append(syncNode(
            "li",
            "",
            syncReasonLabels[code] || "분류되지 않은 로컬 결과",
          )));
          row.append(sourceReasons);
        }
        sourceList.append(row);
      });
      scroll.append(reasons, sourceList);
      details.append(scroll);
      content?.append(details);
    }
    announceSync(`${title}. 새 링크/문서 ${syncNumber(items.new)}개, 기존 링크/문서 ${syncNumber(items.reused)}개, 새 구조 참조 ${syncNumber(structureReferences.new)}개, 기존 구조 참조 ${syncNumber(structureReferences.reused)}개, 도메인/서비스만 확인 ${siteOnly}개, 후보 건너뜀 ${skippedTotal}개, 소스 확인 불가 ${syncNumber(sources.unavailable)}개, 소스 실패 ${syncNumber(sources.failed)}개.`);
  };

  const renderSyncRefreshWarning = () => {
    const content = syncContent();
    if (!content || content.querySelector("[data-atlassian-sync-refresh-warning]")) return;
    const warning = syncNode(
      "p",
      "atlassian-sync-recovery atlassian-sync-refresh-warning",
      "로컬 Sync 결과는 저장했지만 Explorer 목록 업데이트를 확인하지 못했습니다. ",
    );
    warning.dataset.atlassianSyncRefreshWarning = "";
    const reload = syncNode("a", "", "현재 Explorer 다시 불러오기");
    reload.href = currentSyncReturnTo();
    warning.append(reload);
    content.append(warning);
    const announcement = syncAnnouncement();
    if (announcement) {
      announcement.setAttribute("role", "alert");
      announcement.dataset.atlassianSyncUrgency = "assertive";
    }
    announceSync("로컬 Sync 결과는 저장했지만 Explorer 목록 업데이트를 확인하지 못했습니다. 현재 Explorer를 다시 불러와 주세요.");
  };

  const setSyncPending = (pending) => {
    const button = syncButton();
    if (button) {
      button.disabled = pending;
      button.setAttribute("aria-busy", pending ? "true" : "false");
      const idle = button.querySelector("[data-atlassian-sync-idle]");
      const working = button.querySelector("[data-atlassian-sync-working]");
      if (idle) idle.hidden = pending;
      if (working) working.hidden = !pending;
    }
    if (pending) {
      renderSyncMessage(
        "working",
        "로컬 근거 동기화 중",
        "저장된 Session 및 Local Context URL에서 링크·문서와 구조 참조를 확인하고 있습니다. Explorer는 계속 사용할 수 있습니다.",
        { busy: true },
      );
    } else {
      syncStatus()?.setAttribute("aria-busy", "false");
    }
  };

  const focusPreview = () => {
    const target = currentPreview()?.querySelector("[data-atlassian-detail-focus]")
      || clearLink();
    target?.focus({ preventScroll: true });
  };

  const focusResultsAnchor = (entryKey) => {
    const target = entryKey ? rowForKey(entryKey) : null;
    (target || resultHeading())?.focus({ preventScroll: true });
  };

  const revealSelectedRow = (entryKey) => {
    const list = resultList();
    const row = rowForKey(entryKey);
    if (!list || !row) return;
    const listBounds = list.getBoundingClientRect();
    const rowBounds = row.getBoundingClientRect();
    if (rowBounds.top < listBounds.top || rowBounds.bottom > listBounds.bottom) {
      row.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  };

  const updateRows = (entryKey, state) => {
    entryLinks().forEach((link) => {
      const active = state === "selected" && link.dataset.atlassianEntryKey === entryKey;
      link.classList.toggle("selected", active);
      if (active) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });
    atlassianExplorer.dataset.atlassianSelectedKey = entryKey;
    atlassianExplorer.dataset.atlassianSelectedId = selectedId();
  };

  const focusableInPreview = () => [...(currentPreview()?.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  ) || [])].filter((element) => !element.hidden && element.getAttribute("aria-hidden") !== "true");

  const syncModal = ({ focus = false } = {}) => {
    const preview = currentPreview();
    const addOwnsModal = Boolean(atlassianAddDialog?.open);
    const open = Boolean(preview && compactQuery.matches && selectedState() !== "empty" && !addOwnsModal);
    atlassianExplorer.classList.toggle("is-sheet-open", open);
    document.body.classList.toggle("atlassian-modal-open", open || addOwnsModal);
    modalBackground().forEach((element) => {
      element.inert = open;
    });
    if (!preview) return open;
    if (open) {
      preview.setAttribute("role", "dialog");
      preview.setAttribute("aria-modal", "true");
      preview.setAttribute("aria-labelledby", "atlassian-preview-title");
      if (focus) window.requestAnimationFrame(focusPreview);
    } else {
      preview.removeAttribute("role");
      preview.removeAttribute("aria-modal");
      preview.removeAttribute("aria-labelledby");
    }
    if (!open && !addOwnsModal) window.requestAnimationFrame(flushSyncAnnouncement);
    return open;
  };
  syncAtlassianExplorerModal = syncModal;

  const historySnapshot = (overrides = {}) => ({
    ...window.history.state,
    atlassianExplorer: true,
    selectionKey: selectedKey(),
    itemId: selectedKind() === "item" ? selectedId() : "",
    referenceId: selectedKind() === "reference" ? selectedId() : "",
    listScroll: resultList()?.scrollTop || 0,
    pageScroll: window.scrollY,
    ...overrides,
  });
  let historyPositionFrame = null;

  const persistHistoryPosition = () => {
    if (historyPositionFrame !== null) return;
    historyPositionFrame = window.requestAnimationFrame(() => {
      historyPositionFrame = null;
      if (!window.history.state?.atlassianExplorer) return;
      if (selectionKeyFromUrl(window.location.href) !== selectedKey()) return;
      window.history.replaceState(historySnapshot(), "");
    });
  };

  let boundResultList = null;
  const bindResultListScroll = () => {
    const nextList = resultList();
    if (boundResultList === nextList) return;
    boundResultList?.removeEventListener("scroll", persistHistoryPosition);
    boundResultList = nextList;
    boundResultList?.addEventListener("scroll", persistHistoryPosition, {
      passive: true,
    });
  };

  const baseSyncFragmentSelectors = [
    "[data-atlassian-explorer-toolbar]",
    "[data-atlassian-hierarchy-rail]",
    "[data-atlassian-hierarchy-compact]",
    "[data-atlassian-results]",
  ];
  const syncFragmentSelectors = () => [
    ...baseSyncFragmentSelectors,
    ...(selectedKind() === "reference" ? ["[data-atlassian-preview-content]"] : []),
  ];

  const captureSyncContinuity = () => {
    const list = resultList();
    const listBounds = list?.getBoundingClientRect();
    const internalList = Boolean(list && list.scrollHeight > list.clientHeight + 1);
    const visibleTop = internalList ? listBounds.top : Math.max(0, listBounds?.top || 0);
    const visibleBottom = internalList ? listBounds.bottom : window.innerHeight;
    const anchorRow = entryLinks().find((row) => {
      const bounds = row.getBoundingClientRect();
      return bounds.bottom > visibleTop && bounds.top < visibleBottom;
    });
    const active = document.activeElement;
    const activeLink = active?.closest?.("a[href]");
    const replacements = syncFragmentSelectors()
      .map((selector) => atlassianExplorer.querySelector(selector))
      .filter(Boolean);
    return {
      pageScroll: window.scrollY,
      pageScrollX: window.scrollX,
      listScroll: list?.scrollTop || 0,
      previewScroll: currentPreview()?.querySelector("[data-atlassian-detail-scroll]")?.scrollTop || 0,
      hierarchyScroll: atlassianExplorer.querySelector("[data-atlassian-hierarchy-rail]")?.scrollTop || 0,
      compactOpen: Boolean(atlassianExplorer.querySelector("[data-atlassian-hierarchy-compact]")?.open),
      anchorKey: anchorRow?.dataset.atlassianEntryKey || "",
      anchorOffset: anchorRow
        ? anchorRow.getBoundingClientRect().top - (internalList ? listBounds.top : 0)
        : 0,
      anchorInList: internalList,
      activeWasReplaced: replacements.some((surface) => surface.contains(active))
        || Boolean(active?.closest?.("[data-atlassian-detail-close]")),
      activeInPreview: Boolean(currentPreview()?.contains(active)),
      activeEntryKey: active?.closest?.("[data-atlassian-entry-link]")?.dataset.atlassianEntryKey || "",
      activeHref: activeLink?.href || "",
      activeFocusKey: active?.closest?.("[data-atlassian-sync-focus-key]")?.dataset.atlassianSyncFocusKey || "",
    };
  };

  const restoreSyncContinuity = (continuity) => {
    const compact = atlassianExplorer.querySelector("[data-atlassian-hierarchy-compact]");
    if (compact) compact.open = continuity.compactOpen;
    const hierarchy = atlassianExplorer.querySelector("[data-atlassian-hierarchy-rail]");
    if (hierarchy) hierarchy.scrollTop = continuity.hierarchyScroll;
    const list = resultList();
    if (list) list.scrollTop = continuity.listScroll;
    const previewScroll = currentPreview()?.querySelector("[data-atlassian-detail-scroll]");
    if (previewScroll) previewScroll.scrollTop = continuity.previewScroll;
    window.scrollTo(continuity.pageScrollX, continuity.pageScroll);

    const anchor = continuity.anchorKey ? rowForKey(continuity.anchorKey) : null;
    if (anchor && list) {
      const anchorTop = anchor.getBoundingClientRect().top;
      if (continuity.anchorInList) {
        const listTop = list.getBoundingClientRect().top;
        list.scrollTop += anchorTop - listTop - continuity.anchorOffset;
      } else {
        window.scrollBy(0, anchorTop - continuity.anchorOffset);
      }
    }
    if (continuity.activeWasReplaced) {
      let focusTarget = continuity.activeFocusKey
        ? [...atlassianExplorer.querySelectorAll("[data-atlassian-sync-focus-key]")]
          .find((element) => element.dataset.atlassianSyncFocusKey === continuity.activeFocusKey)
        : null;
      if (!focusTarget && continuity.activeEntryKey) focusTarget = rowForKey(continuity.activeEntryKey);
      if (!focusTarget && continuity.activeHref) {
        focusTarget = [...atlassianExplorer.querySelectorAll("a[href]")]
          .find((link) => link.href === continuity.activeHref);
      }
      if (!focusTarget && continuity.activeInPreview) {
        focusTarget = currentPreview()?.querySelector("[data-atlassian-detail-focus]")
          || clearLink();
      }
      (focusTarget || resultHeading())?.focus({ preventScroll: true });
    }
  };

  const patchSyncInventory = (parsed, continuity, canonicalPath = "") => {
    previewRequest?.abort();
    previewRequest = null;
    requestGeneration += 1;
    if (historyPositionFrame !== null) {
      window.cancelAnimationFrame(historyPositionFrame);
      historyPositionFrame = null;
    }
    const fragments = syncFragmentSelectors().map((selector) => ({
      selector,
      current: atlassianExplorer.querySelector(selector),
      incoming: parsed.querySelector(selector),
    }));
    const missing = fragments.find(({ current, incoming }) => !current || !incoming);
    if (missing) throw new Error(`Missing Sync fragment ${missing.selector}`);
    fragments.forEach(({ current, incoming }) => {
      current.replaceWith(document.importNode(incoming, true));
    });
    if (selectedKind() === "reference") {
      const current = currentPreview();
      const incoming = parsed.querySelector("[data-atlassian-preview]");
      if (current && incoming) {
        current.className = incoming.className;
        ["previewState", "selectionKind", "selectedKey", "selectedId", "documentTitle"]
          .forEach((key) => {
            current.dataset[key] = incoming.dataset[key] || "";
          });
        const currentClose = current.querySelector("a[data-atlassian-detail-close]");
        const incomingClose = incoming.querySelector("a[data-atlassian-detail-close]");
        if (currentClose && incomingClose) {
          currentClose.href = incomingClose.href;
        } else if (currentClose) {
          currentClose.remove();
        } else if (incomingClose) {
          const panel = current.querySelector(".atlassian-preview-panel");
          const content = current.querySelector("[data-atlassian-preview-content]");
          if (panel && content) {
            panel.insertBefore(document.importNode(incomingClose, true), content);
          }
        }
        current.setAttribute("aria-busy", "false");
        document.title = current.dataset.documentTitle || "Atlassian · LocalBrain";
      }
    }
    bindResultListScroll();
    updateRows(selectedKey(), selectedState());
    restoreSyncContinuity(continuity);
    syncModal({ focus: false });
    window.history.replaceState(historySnapshot(), "", canonicalPath || window.location.href);
    explorerBaseKey = baseDestinationKey(window.location.href);
  };

  const fetchCurrentExplorerDocument = async (canonicalPath = "") => {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const requestedPath = canonicalPath || currentSyncReturnTo();
      const response = await fetch(requestedPath, {
        credentials: "same-origin",
        headers: { Accept: "text/html" },
      });
      if (!response.ok) throw new Error(`Explorer refresh ${response.status}`);
      const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
      if (canonicalPath || requestedPath === currentSyncReturnTo()) return parsed;
    }
    throw new Error("Explorer state changed during Sync refresh");
  };

  const announceLoading = () => {
    const status = atlassianExplorer.querySelector("[data-atlassian-detail-status]");
    if (status) status.textContent = "Atlassian 항목 preview를 불러오는 중입니다.";
  };

  const loadPreview = async (
    destination,
    {
      pushHistory = false,
      focusHeading = false,
      restoreFocusKey = "",
      fallbackHref = null,
      failureMode = "row",
      historyState = null,
    } = {},
  ) => {
    const target = destinationFor(destination);
    if (!target) {
      if (fallbackHref) window.location.assign(fallbackHref);
      return;
    }
    if (baseDestinationKey(target) !== explorerBaseKey) {
      window.location.assign(target.href);
      return;
    }

    const previousKey = selectedKey();
    const expectedKey = selectionKeyFromUrl(target);
    const [expectedKind = "", expectedId = ""] = expectedKey.split(":", 2);
    const listScroll = resultList()?.scrollTop || 0;
    const pageScroll = window.scrollY;
    if (pushHistory) {
      window.history.replaceState(
        historySnapshot({ focusEntryKey: restoreFocusKey || expectedKey || previousKey }),
        "",
      );
    }

    previewRequest?.abort();
    const controller = new AbortController();
    const generation = ++requestGeneration;
    previewRequest = controller;
    currentPreview()?.setAttribute("aria-busy", "true");
    announceLoading();

    try {
      const response = await fetch(target.href, {
        credentials: "same-origin",
        headers: { "X-LocalBrain-Partial": "atlassian-selection-preview" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
      const incoming = parsed.querySelector("[data-atlassian-preview]");
      if (!incoming || (incoming.dataset.selectedKey || "") !== expectedKey) {
        throw new Error("Preview identity mismatch");
      }
      if (generation !== requestGeneration) return;

      const adopted = document.importNode(incoming, true);
      adopted.setAttribute("aria-busy", "false");
      currentPreview()?.replaceWith(adopted);
      const incomingState = adopted.dataset.previewState || "empty";
      updateRows(expectedKey, incomingState);
      document.title = adopted.dataset.documentTitle || "Atlassian · LocalBrain";
      if (typeof formatLocalTimes === "function") formatLocalTimes(adopted);
      const detailScroll = adopted.querySelector("[data-atlassian-detail-scroll]");
      if (detailScroll) detailScroll.scrollTop = 0;

      const targetListScroll = Number.isFinite(historyState?.listScroll)
        ? historyState.listScroll
        : listScroll;
      if (resultList()) resultList().scrollTop = targetListScroll;
      if (Number.isFinite(historyState?.pageScroll)) {
        window.scrollTo(0, historyState.pageScroll);
      } else {
        window.scrollTo(0, pageScroll);
      }

      if (pushHistory) {
        window.history.pushState(
          historySnapshot({
            selectionKey: expectedKey,
            itemId: expectedKind === "item" ? expectedId : "",
            referenceId: expectedKind === "reference" ? expectedId : "",
            selectionKind: expectedKind,
            focusEntryKey: restoreFocusKey || previousKey || expectedKey,
            listScroll: targetListScroll,
          }),
          "",
          target.href,
        );
      }
      syncModal({ focus: compactQuery.matches && incomingState !== "empty" });

      window.requestAnimationFrame(() => {
        if (incomingState !== "empty" && focusHeading) {
          focusPreview();
        } else if (incomingState === "empty") {
          focusResultsAnchor(restoreFocusKey || historyState?.focusEntryKey || previousKey);
        }
      });
      const status = atlassianExplorer.querySelector("[data-atlassian-detail-status]");
      if (status) {
        const title = adopted.querySelector("[data-atlassian-detail-focus]")?.textContent.trim();
        status.textContent = incomingState === "empty"
          ? "Atlassian 항목 선택을 지웠습니다."
          : `${title || "Atlassian 항목"} preview를 표시했습니다.`;
      }
    } catch (error) {
      if (error.name === "AbortError" || generation !== requestGeneration) return;
      if (failureMode === "popstate") {
        window.location.reload();
      } else {
        window.location.assign(fallbackHref || target.href);
      }
    } finally {
      if (previewRequest === controller) {
        previewRequest = null;
        currentPreview()?.setAttribute("aria-busy", "false");
      }
    }
  };

  const unmodifiedPrimaryClick = (event) => (
    !event.defaultPrevented
    && event.button === 0
    && !event.metaKey
    && !event.ctrlKey
    && !event.shiftKey
    && !event.altKey
  );

  atlassianExplorer.addEventListener("click", (event) => {
    const entryLink = event.target.closest("[data-atlassian-entry-link]");
    if (entryLink && unmodifiedPrimaryClick(event) && !entryLink.target) {
      const destination = destinationFor(entryLink.dataset.atlassianSelectionUrl);
      if (!destination) return;
      event.preventDefault();
      const entryKey = entryLink.dataset.atlassianEntryKey || "";
      if (selectedState() === "selected" && selectedKey() === entryKey) {
        syncModal({ focus: compactQuery.matches });
        if (!compactQuery.matches) focusPreview();
        return;
      }
      loadPreview(destination, {
        pushHistory: true,
        focusHeading: true,
        restoreFocusKey: entryKey,
        fallbackHref: entryLink.href,
        failureMode: "row",
      });
      return;
    }

    const closeControl = event.target.closest("[data-atlassian-detail-close]");
    if (!closeControl || !unmodifiedPrimaryClick(event)) return;
    const ordinaryClear = clearLink();
    const destination = destinationFor(ordinaryClear?.href);
    if (!destination) return;
    event.preventDefault();
    const entryKey = selectedKey();
    loadPreview(destination, {
      pushHistory: true,
      restoreFocusKey: entryKey,
      fallbackHref: ordinaryClear.href,
      failureMode: "close",
    });
  });

  document.addEventListener("keydown", (event) => {
    if (!atlassianExplorer.classList.contains("is-sheet-open")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      const ordinaryClear = clearLink();
      const destination = destinationFor(ordinaryClear?.href);
      if (!destination) return;
      const entryKey = selectedKey();
      loadPreview(destination, {
        pushHistory: true,
        restoreFocusKey: entryKey,
        fallbackHref: ordinaryClear.href,
        failureMode: "close",
      });
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = focusableInPreview();
    if (!focusable.length) {
      event.preventDefault();
      focusPreview();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  document.addEventListener("focusin", (event) => {
    if (!atlassianExplorer.classList.contains("is-sheet-open")) return;
    const preview = currentPreview();
    if (preview && !preview.contains(event.target)) {
      window.requestAnimationFrame(focusPreview);
    }
  });

  window.addEventListener("popstate", (event) => {
    if (historyPositionFrame !== null) {
      window.cancelAnimationFrame(historyPositionFrame);
      historyPositionFrame = null;
    }
    const destination = destinationFor(window.location.href);
    if (!destination || baseDestinationKey(destination) !== explorerBaseKey) {
      window.location.reload();
      return;
    }
    loadPreview(destination, {
      focusHeading: Boolean(selectionKeyFromUrl(destination)),
      restoreFocusKey: event.state?.focusEntryKey || "",
      failureMode: "popstate",
      historyState: event.state,
    });
  });

  compactQuery.addEventListener("change", () => {
    const becomingModal = compactQuery.matches && selectedState() !== "empty";
    syncModal({ focus: becomingModal });
  });

  let syncInFlight = false;
  syncForm()?.addEventListener("submit", async (event) => {
    const form = event.currentTarget;
    if (syncInFlight || typeof window.fetch !== "function") return;
    event.preventDefault();
    syncInFlight = true;
    const button = syncButton();
    const restoreButtonFocus = document.activeElement === button;
    const syncStartReturnTo = currentSyncReturnTo();
    const returnInput = form.querySelector('input[name="return_to"]');
    if (returnInput) returnInput.value = syncStartReturnTo;
    setSyncPending(true);

    try {
      const body = new URLSearchParams();
      for (const [key, value] of new FormData(form).entries()) {
        body.append(key, String(value));
      }
      const response = await fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-LocalBrain-Partial": "atlassian-local-evidence-sync",
        },
        body,
      });
      const payload = await response.json();
      if (response.status === 422) {
        renderSyncMessage(
          "failed",
          "동기화 요청을 확인할 수 없음",
          "Explorer 상태를 다시 확인한 뒤 Sync를 실행해 주세요. 로컬 근거는 변경하지 않았습니다.",
          { alert: true },
        );
        return;
      }
      if (![200, 409].includes(response.status) || !payload?.report) {
        throw new Error(`Unexpected Sync response ${response.status}`);
      }

      const refreshInventory = payload.report.status !== "busy";
      const returnedDestination = typeof payload.return_to === "string"
        ? destinationFor(payload.return_to)
        : null;
      const refreshSourcePath = currentSyncReturnTo();
      const canonicalPath = returnedDestination && refreshSourcePath === syncStartReturnTo
        ? `${returnedDestination.pathname}${returnedDestination.search}`
        : refreshSourcePath;
      const refreshGeneration = requestGeneration;
      let parsed = null;
      if (refreshInventory) {
        try {
          parsed = await fetchCurrentExplorerDocument(canonicalPath);
        } catch (_error) {
          parsed = null;
        }
      }
      const continuity = captureSyncContinuity();
      renderSyncReport(payload.report);
      const refreshStillCurrent = (
        requestGeneration === refreshGeneration
        && previewRequest === null
        && currentSyncReturnTo() === refreshSourcePath
      );
      if (!refreshInventory) {
        restoreSyncContinuity(continuity);
        syncModal({ focus: false });
      } else if (parsed && refreshStillCurrent) {
        try {
          patchSyncInventory(parsed, continuity, canonicalPath);
        } catch (_error) {
          restoreSyncContinuity(continuity);
          syncModal({ focus: false });
          renderSyncRefreshWarning();
        }
      } else if (!parsed) {
        restoreSyncContinuity(continuity);
        syncModal({ focus: false });
        renderSyncRefreshWarning();
      } else {
        restoreSyncContinuity(continuity);
        syncModal({ focus: false });
        renderSyncRefreshWarning();
      }
    } catch (_error) {
      renderSyncMessage(
        "failed",
        "동기화 결과를 확인할 수 없음",
        "자동 재실행하지 않았습니다. 현재 Explorer를 유지한 채 준비가 되면 Sync를 다시 실행해 주세요.",
        { alert: true },
      );
      syncModal({ focus: false });
    } finally {
      syncInFlight = false;
      setSyncPending(false);
      const active = document.activeElement;
      if (
        restoreButtonFocus
        && (active === document.body || active === document.documentElement)
        && !syncModalOwnerActive()
      ) {
        button?.focus({ preventScroll: true });
      }
    }
  });

  atlassianExplorer.classList.add("atlassian-explorer-enhanced");
  window.history.replaceState(historySnapshot(), "");
  bindResultListScroll();
  window.addEventListener("scroll", persistHistoryPosition, { passive: true });
  updateRows(selectedKey(), selectedState());
  if (selectedState() === "selected") revealSelectedRow(selectedKey());
  syncModal({ focus: compactQuery.matches && selectedState() !== "empty" });
  if (atlassianExplorer.querySelector("[data-registration-notice]")) {
    window.requestAnimationFrame(() => {
      if (selectedState() !== "empty") {
        focusPreview();
      } else {
        resultHeading()?.focus({ preventScroll: true });
      }
    });
  }
}
