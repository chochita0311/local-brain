function formatLocalTime(value) {
  if (!value || value === "대기 중" || value === "-") return value;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatLocalTimes(root = document) {
  root.querySelectorAll("[data-local-time]").forEach((element) => {
    element.textContent = formatLocalTime(element.getAttribute("datetime") || element.textContent);
  });

  root.querySelectorAll("[data-local-epoch]").forEach((element) => {
    const milliseconds = Number(element.getAttribute("datetime"));
    if (Number.isFinite(milliseconds)) {
      element.textContent = formatLocalTime(new Date(milliseconds).toISOString());
    }
  });
}

formatLocalTimes();

const usageDashboardStatus = document.querySelector("[data-usage-dashboard-status]");

if (usageDashboardStatus) {
  let usageDashboardRequest = null;

  const currentUsageDashboard = () => document.querySelector("[data-usage-dashboard]");
  const usageScrollFallbackKey = "localbrain:usage-dashboard-scroll";

  const restoreUsageScroll = (scrollY) => {
    const top = Number.isFinite(scrollY) ? scrollY : 0;
    window.scrollTo(0, top);
    window.requestAnimationFrame(() => window.scrollTo(0, top));
  };

  const announceUsageScope = (dashboard) => {
    const source = dashboard.querySelector('[data-usage-control="source"][aria-current="page"]')?.textContent.trim();
    const metric = dashboard.querySelector('[data-usage-control="metric"][aria-current="page"]')?.textContent.trim();
    const breakdown = dashboard.querySelector('[data-usage-control="breakdown"][aria-current="page"]')?.textContent.trim();
    usageDashboardStatus.textContent = [source, metric, breakdown].filter(Boolean).join(" · ")
      + " 보기로 전환했습니다.";
  };

  const loadUsageDashboard = async (
    destination,
    {
      pushHistory = false,
      scrollY = window.scrollY,
      focusControl = null,
      focusValue = null,
    } = {},
  ) => {
    usageDashboardRequest?.abort();
    const controller = new AbortController();
    usageDashboardRequest = controller;
    currentUsageDashboard()?.setAttribute("aria-busy", "true");

    try {
      const response = await fetch(destination.href, {
        credentials: "same-origin",
        headers: { "X-Requested-With": "LocalBrain-Usage-Dashboard" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
      const incomingDashboard = parsed.querySelector("[data-usage-dashboard]");
      const outgoingDashboard = currentUsageDashboard();
      if (!incomingDashboard || !outgoingDashboard) {
        throw new Error("사용량 대시보드 영역을 찾을 수 없습니다.");
      }

      const adoptedDashboard = document.importNode(incomingDashboard, true);
      adoptedDashboard.setAttribute("aria-busy", "false");
      outgoingDashboard.replaceWith(adoptedDashboard);
      document.title = parsed.title || document.title;
      formatLocalTimes(adoptedDashboard);

      if (pushHistory) {
        window.history.pushState(
          { usageDashboard: true, usageScrollY: scrollY },
          "",
          destination.href,
        );
      }

      if (focusControl && focusValue) {
        adoptedDashboard
          .querySelector(`[data-usage-control="${focusControl}"][data-usage-value="${focusValue}"]`)
          ?.focus({ preventScroll: true });
      }
      announceUsageScope(adoptedDashboard);
      restoreUsageScroll(scrollY);
    } catch (error) {
      if (error.name === "AbortError") return;
      window.sessionStorage.setItem(
        usageScrollFallbackKey,
        JSON.stringify({ href: destination.href, scrollY }),
      );
      window.location.assign(destination.href);
    } finally {
      if (usageDashboardRequest === controller) {
        usageDashboardRequest = null;
        currentUsageDashboard()?.setAttribute("aria-busy", "false");
      }
    }
  };

  document.addEventListener("click", (event) => {
    const link = event.target.closest("[data-usage-scope-link]");
    if (
      !link
      || event.defaultPrevented
      || event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
      || link.target
    ) return;

    const destination = new URL(link.href, window.location.href);
    if (destination.origin !== window.location.origin) return;
    event.preventDefault();
    if (destination.href === window.location.href) return;

    const scrollY = window.scrollY;
    window.history.replaceState(
      { ...window.history.state, usageDashboard: true, usageScrollY: scrollY },
      "",
    );
    loadUsageDashboard(destination, {
      pushHistory: true,
      scrollY,
      focusControl: link.dataset.usageControl,
      focusValue: link.dataset.usageValue,
    });
  });

  window.addEventListener("popstate", (event) => {
    const destination = new URL(window.location.href);
    if (destination.pathname !== "/sessions-dashboard") {
      window.location.reload();
      return;
    }
    const storedScrollY = Number(event.state?.usageScrollY);
    loadUsageDashboard(destination, {
      scrollY: Number.isFinite(storedScrollY) ? storedScrollY : window.scrollY,
    });
  });

  try {
    const fallback = JSON.parse(window.sessionStorage.getItem(usageScrollFallbackKey));
    if (fallback?.href === window.location.href) {
      window.sessionStorage.removeItem(usageScrollFallbackKey);
      restoreUsageScroll(Number(fallback.scrollY));
    }
  } catch (_error) {
    window.sessionStorage.removeItem(usageScrollFallbackKey);
  }
}

const inventorySwitch = document.querySelector("[data-inventory-switch]");

if (inventorySwitch) {
  const inventoryStatus = document.querySelector("[data-inventory-status]");
  const inventoryLinks = [
    ...inventorySwitch.querySelectorAll("[data-inventory-view]"),
  ];
  const inventoryPanels = [
    ...document.querySelectorAll("[data-inventory-panel]"),
  ];

  const syncInventoryIndicator = () => {
    const selectedLink = inventoryLinks.find(
      (link) => link.getAttribute("aria-current") === "page",
    );
    if (!selectedLink) return;
    inventorySwitch.style.setProperty(
      "--inventory-indicator-left",
      `${selectedLink.offsetLeft}px`,
    );
    inventorySwitch.style.setProperty(
      "--inventory-indicator-width",
      `${selectedLink.offsetWidth}px`,
    );
    inventorySwitch.dataset.indicatorReady = "true";
  };

  const inventoryFromPath = () => (
    window.location.pathname === "/projects" ? "projects" : "sessions"
  );

  const selectInventory = (inventory, { pushHistory = false } = {}) => {
    const selectedInventory = inventory === "projects" ? "projects" : "sessions";
    inventorySwitch.dataset.selected = selectedInventory;

    inventoryLinks.forEach((link) => {
      const isSelected = link.dataset.inventoryView === selectedInventory;
      if (isSelected) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
    inventoryPanels.forEach((panel) => {
      panel.hidden = panel.dataset.inventoryPanel !== selectedInventory;
    });
    syncInventoryIndicator();

    const destination = selectedInventory === "projects" ? "/projects" : "/sessions";
    document.title = `${selectedInventory === "projects" ? "Projects" : "Sessions"} · LocalBrain`;
    if (pushHistory) window.history.pushState({ inventory: selectedInventory }, "", destination);
    inventoryStatus.textContent = `${selectedInventory === "projects" ? "Projects" : "Sessions"} 보기를 표시했습니다.`;
  };

  inventorySwitch.addEventListener("click", (event) => {
    const link = event.target.closest("[data-inventory-view]");
    if (
      !link
      || event.defaultPrevented
      || event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
    ) return;

    const selectedInventory = link.dataset.inventoryView;
    if (selectedInventory === inventorySwitch.dataset.selected) return;
    event.preventDefault();
    selectInventory(selectedInventory, { pushHistory: true });
  });

  window.addEventListener("popstate", () => selectInventory(inventoryFromPath()));
  window.addEventListener("resize", syncInventoryIndicator);
  syncInventoryIndicator();
  document.fonts?.ready.then(syncInventoryIndicator);
}

const subsessionMenus = [...document.querySelectorAll("[data-subsession-menu]")];

if (subsessionMenus.length) {
  const closeSubsessionMenu = (menu, { restoreFocus = false } = {}) => {
    const trigger = menu.querySelector("[data-subsession-trigger]");
    const dropdown = menu.querySelector("[data-subsession-dropdown]");
    trigger.setAttribute("aria-expanded", "false");
    dropdown.hidden = true;
    menu.closest(".session-row")?.classList.remove("disclosure-open");
    if (restoreFocus) trigger.focus();
  };

  const closeSubsessionMenus = (except = null) => {
    subsessionMenus.forEach((menu) => {
      if (menu !== except) closeSubsessionMenu(menu);
    });
  };

  subsessionMenus.forEach((menu) => {
    const trigger = menu.querySelector("[data-subsession-trigger]");
    const dropdown = menu.querySelector("[data-subsession-dropdown]");

    trigger.addEventListener("click", () => {
      const willOpen = trigger.getAttribute("aria-expanded") !== "true";
      closeSubsessionMenus(willOpen ? menu : null);
      trigger.setAttribute("aria-expanded", String(willOpen));
      dropdown.hidden = !willOpen;
      menu.closest(".session-row")?.classList.toggle("disclosure-open", willOpen);
    });

    menu.querySelectorAll("[data-subsession-link]").forEach((link) => {
      link.addEventListener("click", () => closeSubsessionMenu(menu));
    });
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-subsession-menu]")) closeSubsessionMenus();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const openMenu = subsessionMenus.find(
      (menu) => menu.querySelector("[data-subsession-trigger]").getAttribute("aria-expanded") === "true",
    );
    if (!openMenu) return;
    event.preventDefault();
    closeSubsessionMenu(openMenu, { restoreFocus: true });
  });
}

document.addEventListener("submit", async (event) => {
  const form = event.target.closest?.("[data-session-pin-form]");
  if (!form) return;

  const returnInput = form.querySelector("[data-session-pin-return]");
  if (returnInput) returnInput.value = `${window.location.pathname}${window.location.search}`;
  if (!window.fetch || !window.DOMParser) return;

  event.preventDefault();
  const control = form.querySelector("[data-session-pin-control]");
  const controlId = control?.id;
  const windowScrollY = window.scrollY;
  const pinnedListScrollTop = document.querySelector(".pinned-session-list")?.scrollTop || 0;
  if (!controlId) {
    HTMLFormElement.prototype.submit.call(form);
    return;
  }
  control.disabled = true;

  try {
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      credentials: "same-origin",
      headers: { "X-Requested-With": "LocalBrain-Session-Pin" },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
    const incomingControl = parsed.getElementById(controlId);
    const incomingForm = incomingControl?.closest("[data-session-pin-form]");
    if (!incomingForm) throw new Error("핀 상태를 갱신할 수 없습니다.");

    const currentPanel = document.querySelector("[data-pinned-sessions-panel]");
    const incomingPanel = parsed.querySelector("[data-pinned-sessions-panel]");
    if (currentPanel && incomingPanel) {
      const adoptedPanel = document.importNode(incomingPanel, true);
      formatLocalTimes(adoptedPanel);
      currentPanel.replaceWith(adoptedPanel);
      const adoptedList = adoptedPanel.querySelector(".pinned-session-list");
      if (adoptedList) adoptedList.scrollTop = pinnedListScrollTop;
    }

    const adoptedForm = document.importNode(incomingForm, true);
    form.replaceWith(adoptedForm);
    const adoptedControl = adoptedForm.querySelector("[data-session-pin-control]");
    const restoreScroll = () => {
      window.scrollTo(0, windowScrollY);
      const pinnedList = document.querySelector(".pinned-session-list");
      if (pinnedList) pinnedList.scrollTop = pinnedListScrollTop;
    };
    restoreScroll();
    adoptedControl?.focus({ preventScroll: true });
    window.requestAnimationFrame(restoreScroll);

    const inventoryStatus = document.querySelector("[data-inventory-status]");
    if (inventoryStatus && adoptedControl) {
      inventoryStatus.textContent = adoptedControl.getAttribute("aria-pressed") === "true"
        ? "Session을 핀으로 고정했습니다."
        : "Session 핀을 해제했습니다.";
    }
  } catch (error) {
    control.disabled = false;
    HTMLFormElement.prototype.submit.call(form);
  }
});

if (/^#session-pin-\d+$/.test(window.location.hash)) {
  const pinControl = document.querySelector(window.location.hash);
  if (pinControl) {
    window.requestAnimationFrame(() => pinControl.focus({ preventScroll: true }));
  }
}

function showNotice(message, tone = "error") {
  const region = document.querySelector("[data-toast-region]");
  if (!region) return;
  const notice = document.createElement("div");
  notice.className = `toast-notice ${tone}`;
  notice.setAttribute("role", tone === "error" ? "alert" : "status");
  notice.textContent = message;
  region.replaceChildren(notice);
  window.setTimeout(() => notice.remove(), 5000);
}

const scanStatusLabels = {
  completed: "완료",
  empty: "비어 있음",
  unavailable: "경로 확인 필요",
  configuration_error: "설정 확인 필요",
  scan_failed: "동기화 실패",
};

function renderScanReport(result, report, actionLabel) {
  if (!report || !Array.isArray(report.sources)) {
    throw new Error("invalid-report");
  }
  const outcome = ["complete", "partial", "failed"].includes(report.outcome)
    ? report.outcome
    : "failed";
  const heading = document.createElement("strong");
  heading.textContent = outcome === "complete"
    ? `${actionLabel}를 완료했습니다.`
    : outcome === "partial"
      ? `${actionLabel} 결과 중 확인이 필요한 소스가 있습니다.`
      : `${actionLabel}를 완료하지 못했습니다.`;
  const summary = document.createElement("span");
  const changed = Number(report.summary?.imported || 0);
  const unchanged = Number(report.summary?.unchanged || 0);
  summary.textContent = `${changed}개 처리 · ${unchanged}개 변경 없음`;
  const list = document.createElement("div");
  list.className = "scan-source-results";
  report.sources.forEach((source) => {
    const row = document.createElement("div");
    row.className = `scan-source-result ${source.status || "scan_failed"}`;
    const identity = document.createElement("span");
    const label = document.createElement("strong");
    label.textContent = source.display_label || source.source_key || "Session source";
    const state = document.createElement("small");
    state.textContent = scanStatusLabels[source.status] || "확인 필요";
    identity.append(label, state);
    const counts = document.createElement("span");
    counts.textContent = `${Number(source.eligible_sessions || 0)} Sessions · ${Number(source.tracked_files || 0)} files`;
    row.append(identity, counts);
    if (source.error_message) {
      const consequence = document.createElement("p");
      consequence.textContent = source.error_message;
      row.append(consequence);
    }
    list.append(row);
  });
  result.replaceChildren(heading, summary, list);
  result.className = `scan-result scan-report ${outcome === "complete" ? "success" : outcome === "partial" ? "warning" : "error"}`;
  result.setAttribute("role", outcome === "complete" ? "status" : "alert");
  result.hidden = false;
  return outcome;
}

function bindScanAction(button, result, endpoint, actionLabel) {
  if (!button || !result) return;
  const eventTarget = button.form || button;
  const eventName = button.form ? "submit" : "click";
  eventTarget.addEventListener(eventName, async (event) => {
    event.preventDefault();
    const idle = button.querySelector(".button-idle");
    const working = button.querySelector(".button-working");
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    idle.hidden = true;
    working.hidden = false;
    result.textContent = `${actionLabel} 중...`;
    result.className = "scan-result working";
    result.setAttribute("role", "status");
    result.hidden = false;

    try {
      const response = await fetch(endpoint, { method: "POST" });
      if (!response.ok) throw new Error("request-failed");
      const data = await response.json();
      const outcome = renderScanReport(result, data.report, actionLabel);
      if (outcome === "complete") {
        window.setTimeout(() => window.location.reload(), 900);
        return;
      }
      button.disabled = false;
      button.removeAttribute("aria-busy");
      idle.hidden = false;
      working.hidden = true;
      button.focus({ preventScroll: true });
    } catch (_error) {
      result.textContent = `${actionLabel} 요청을 처리하지 못했습니다. 기존 데이터는 유지됩니다. 다시 시도하거나 소스 설정을 확인하세요.`;
      result.className = "scan-result scan-report error";
      result.setAttribute("role", "alert");
      result.hidden = false;
      button.disabled = false;
      button.removeAttribute("aria-busy");
      idle.hidden = false;
      working.hidden = true;
      button.focus({ preventScroll: true });
    }
  });
}

function restoreScanAction(button, idle, working) {
  button.disabled = false;
  button.removeAttribute("aria-busy");
  idle.hidden = false;
  working.hidden = true;
  button.focus({ preventScroll: true });
}

function bindSessionSyncAction(button, result) {
  if (!button || !result) return;
  const eventTarget = button.form || button;
  const eventName = button.form ? "submit" : "click";
  eventTarget.addEventListener(eventName, async (event) => {
    event.preventDefault();
    const idle = button.querySelector(".button-idle");
    const working = button.querySelector(".button-working");
    const plans = new Map();
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    idle.hidden = true;
    working.hidden = false;
    result.textContent = "동기화 준비 중...";
    result.className = "scan-result working";
    result.setAttribute("role", "status");
    result.hidden = false;

    const renderProgress = (message) => {
      result.textContent = message;
      result.className = "scan-result working";
      result.setAttribute("role", "status");
      result.hidden = false;
    };

    const consumeEvent = (payload) => {
      const label = payload.display_label || payload.source_key || "Session source";
      if (payload.type === "source_started") {
        renderProgress(`${label} 준비 중...`);
      } else if (payload.type === "source_plan") {
        plans.set(payload.source_key, payload);
        const repairLabels = { session: "Session", usage: "Usage", reference: "참조" };
        const repairs = Array.isArray(payload.repair_kinds)
          ? payload.repair_kinds.map((kind) => repairLabels[kind]).filter(Boolean)
          : [];
        const activity = repairs.length
          ? `${repairs.join(" · ")} 계약 업그레이드`
          : payload.mode === "forced"
            ? "전체 다시 처리"
            : "변경 확인";
        renderProgress(`${label} ${activity} · 0/${Number(payload.total_files || 0)}`);
      } else if (payload.type === "source_progress") {
        const plan = plans.get(payload.source_key);
        const repair = plan && Array.isArray(plan.repair_kinds) && plan.repair_kinds.length;
        const activity = repair ? "계약 업그레이드" : "동기화";
        renderProgress(
          `${label} ${activity} · ${Number(payload.processed_files || 0)}/${Number(payload.total_files || 0)}`,
        );
      } else if (payload.type === "source_result") {
        renderProgress(
          `${label} 완료 · ${Number(payload.imported || 0)}개 처리 · ${Number(payload.unchanged || 0)}개 변경 없음`,
        );
      } else if (payload.type === "sync_complete") {
        renderProgress("동기화 결과를 정리하는 중...");
      }
    };

    try {
      const supportsStreaming = Boolean(window.ReadableStream && window.TextDecoder);
      const response = await fetch(
        supportsStreaming ? "/api/sessions/sync/stream" : "/api/sessions/sync",
        { method: "POST" },
      );
      if (!response.ok) throw new Error("request-failed");

      let report = null;
      if (!supportsStreaming) {
        const data = await response.json();
        report = data.report;
      } else {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let terminalError = false;
        const consumeLine = (line) => {
          if (!line.trim()) return;
          const payload = JSON.parse(line);
          if (payload.type === "result" && payload.ok) {
            report = payload.report;
          } else if (payload.type === "error") {
            terminalError = true;
          } else {
            consumeEvent(payload);
          }
        };
        while (true) {
          const { value, done } = await reader.read();
          buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          lines.forEach(consumeLine);
          if (done) break;
        }
        consumeLine(buffer);
        if (terminalError || !report) throw new Error("sync-failed");
      }

      const outcome = renderScanReport(result, report, "동기화");
      if (outcome === "complete") {
        window.setTimeout(() => window.location.reload(), 900);
        return;
      }
      restoreScanAction(button, idle, working);
    } catch (_error) {
      result.textContent = "동기화 요청을 처리하지 못했습니다. 기존 데이터는 유지됩니다. 다시 시도하거나 소스 설정을 확인하세요.";
      result.className = "scan-result scan-report error";
      result.setAttribute("role", "alert");
      result.hidden = false;
      restoreScanAction(button, idle, working);
    }
  });
}

bindScanAction(
  document.querySelector("#scan-button"),
  document.querySelector("#scan-result"),
  "/api/scan",
  "스캔",
);
bindSessionSyncAction(
  document.querySelector("#session-sync-button"),
  document.querySelector("#session-sync-result"),
);

async function requestJson(endpoint, options = {}) {
  const response = await fetch(endpoint, options);
  let data = {};
  try {
    data = await response.json();
  } catch (_error) {
    data = {};
  }
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join(", ")
      : data.detail;
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return data;
}

function splitReference(value) {
  const separator = value.indexOf(":");
  if (separator < 1) return ["", ""];
  return [value.slice(0, separator), value.slice(separator + 1)];
}

const contextExplorer = document.querySelector("[data-context-explorer]");

if (contextExplorer) {
  const sourceScrollKey = "localbrain:context-source-window-scroll";
  const treePane = contextExplorer.querySelector(".source-tree-pane");
  const explorerBody = contextExplorer.querySelector("[data-context-split]");
  const paneSeparator = contextExplorer.querySelector("[data-context-pane-separator]");
  const previewStatus = contextExplorer.querySelector("[data-context-preview-status]");
  const sourceId = contextExplorer.dataset.contextSourceId;
  let previewRequest = null;

  document.addEventListener("click", (event) => {
    const link = event.target.closest("[data-context-folder-source-link]");
    if (
      !link
      || event.defaultPrevented
      || event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
    ) return;

    const destination = new URL(link.href, window.location.href);
    if (destination.href === window.location.href) return;
    try {
      window.sessionStorage.setItem(
        sourceScrollKey,
        JSON.stringify({
          href: destination.href,
          scrollY: window.scrollY,
          createdAt: Date.now(),
        }),
      );
    } catch (_error) {
      // Storage denial must not block ordinary source-link navigation.
    }
  });

  try {
    const savedSourceScroll = JSON.parse(
      window.sessionStorage.getItem(sourceScrollKey) || "null",
    );
    window.sessionStorage.removeItem(sourceScrollKey);
    if (
      savedSourceScroll?.href === window.location.href
      && Number.isFinite(savedSourceScroll.scrollY)
      && Date.now() - savedSourceScroll.createdAt < 15000
    ) {
      const restoreSourceScroll = () => window.scrollTo(0, savedSourceScroll.scrollY);
      window.requestAnimationFrame(() => {
        restoreSourceScroll();
        window.requestAnimationFrame(restoreSourceScroll);
      });
    }
  } catch (_error) {
    try {
      window.sessionStorage.removeItem(sourceScrollKey);
    } catch (_storageError) {
      // Storage denial must not block ordinary source-link navigation.
    }
  }

  if (explorerBody && paneSeparator) {
    const compactSplit = window.matchMedia("(max-width: 700px)");
    const defaultSize = Number(paneSeparator.dataset.defaultSize) || 300;
    const configuredMin = Number(paneSeparator.dataset.minSize) || 220;
    const configuredMax = Number(paneSeparator.dataset.maxSize) || 480;
    const keyboardStep = Number(paneSeparator.dataset.keyboardStep) || 16;
    let preferredSize = defaultSize;
    let activePointer = null;
    let pointerStart = 0;
    let sizeStart = defaultSize;

    const splitterBounds = () => {
      const bodyWidth = explorerBody.getBoundingClientRect().width;
      if (bodyWidth <= 0) return { min: configuredMin, max: configuredMax };
      const separatorWidth = paneSeparator.getBoundingClientRect().width;
      const treeFloor = Math.min(
        configuredMin,
        Math.max(160, Math.floor(bodyWidth * 0.35)),
      );
      const previewFloor = Math.min(
        360,
        Math.max(180, Math.floor(bodyWidth * 0.42)),
      );
      const treeCeiling = Math.max(
        treeFloor,
        Math.min(
          configuredMax,
          Math.floor(bodyWidth - separatorWidth - previewFloor),
        ),
      );
      return { min: treeFloor, max: treeCeiling };
    };

    const applySplitSize = (value, { updatePreferred = true } = {}) => {
      const bounds = splitterBounds();
      const nextSize = Math.round(Math.min(bounds.max, Math.max(bounds.min, value)));
      if (updatePreferred) preferredSize = nextSize;
      explorerBody.style.setProperty("--context-tree-width", `${nextSize}px`);
      paneSeparator.setAttribute("aria-valuemin", String(bounds.min));
      paneSeparator.setAttribute("aria-valuemax", String(bounds.max));
      paneSeparator.setAttribute("aria-valuenow", String(nextSize));
      paneSeparator.setAttribute("aria-valuetext", `Source tree ${nextSize} pixels`);
      return nextSize;
    };

    const finishPointerResize = () => {
      if (activePointer === null) return;
      const pointerId = activePointer;
      activePointer = null;
      contextExplorer.classList.remove("is-resizing");
      if (paneSeparator.hasPointerCapture(pointerId)) {
        paneSeparator.releasePointerCapture(pointerId);
      }
    };

    const syncSplitterMode = () => {
      if (compactSplit.matches) {
        finishPointerResize();
        explorerBody.style.removeProperty("--context-tree-width");
        paneSeparator.tabIndex = -1;
        paneSeparator.setAttribute("aria-hidden", "true");
        paneSeparator.setAttribute("aria-disabled", "true");
        return;
      }
      paneSeparator.tabIndex = 0;
      paneSeparator.removeAttribute("aria-hidden");
      paneSeparator.removeAttribute("aria-disabled");
      applySplitSize(preferredSize, { updatePreferred: false });
    };

    paneSeparator.addEventListener("pointerdown", (event) => {
      if (compactSplit.matches || event.button !== 0) return;
      event.preventDefault();
      activePointer = event.pointerId;
      pointerStart = event.clientX;
      sizeStart = Number(paneSeparator.getAttribute("aria-valuenow")) || preferredSize;
      paneSeparator.setPointerCapture(event.pointerId);
      contextExplorer.classList.add("is-resizing");
    });

    paneSeparator.addEventListener("pointermove", (event) => {
      if (event.pointerId !== activePointer) return;
      event.preventDefault();
      applySplitSize(sizeStart + event.clientX - pointerStart);
    });

    paneSeparator.addEventListener("pointerup", (event) => {
      if (event.pointerId !== activePointer) return;
      finishPointerResize();
    });
    paneSeparator.addEventListener("pointercancel", finishPointerResize);
    paneSeparator.addEventListener("lostpointercapture", finishPointerResize);

    paneSeparator.addEventListener("keydown", (event) => {
      if (compactSplit.matches || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const current = Number(paneSeparator.getAttribute("aria-valuenow")) || preferredSize;
      applySplitSize(current + (event.key === "ArrowRight" ? keyboardStep : -keyboardStep));
    });

    compactSplit.addEventListener("change", syncSplitterMode);
    window.addEventListener("resize", () => {
      if (!compactSplit.matches) applySplitSize(preferredSize, { updatePreferred: false });
    });
    syncSplitterMode();
  }

  const documentLinks = () => [
    ...treePane.querySelectorAll("[data-context-document-link]"),
  ];

  const destinationKey = (destination) => {
    const url = new URL(destination, window.location.href);
    return [url.searchParams.get("root"), url.searchParams.get("document")].join(":");
  };

  const revealDocumentLink = (link) => {
    let ancestor = link.parentElement.closest("details");
    while (ancestor && treePane.contains(ancestor)) {
      ancestor.open = true;
      ancestor = ancestor.parentElement.closest("details");
    }

    const paneBounds = treePane.getBoundingClientRect();
    const linkBounds = link.getBoundingClientRect();
    if (linkBounds.top < paneBounds.top) {
      treePane.scrollTop -= paneBounds.top - linkBounds.top;
    } else if (linkBounds.bottom > paneBounds.bottom) {
      treePane.scrollTop += linkBounds.bottom - paneBounds.bottom;
    }
  };

  const selectDocumentLink = (destination, fallbackLink = null) => {
    const key = destinationKey(destination);
    const selected = documentLinks().find((link) => destinationKey(link.href) === key)
      || fallbackLink;

    documentLinks().forEach((link) => {
      const isSelected = link === selected;
      link.classList.toggle("active", isSelected);
      if (isSelected) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });

    if (selected) revealDocumentLink(selected);
    return selected;
  };

  const destinationUsesCurrentSource = (destination) => {
    const root = destination.searchParams.get("root") || sourceId;
    return root === sourceId;
  };

  const scrollPreviewFragment = (destination) => {
    if (!destination.hash) return;
    let anchorId = destination.hash.slice(1);
    try {
      anchorId = decodeURIComponent(anchorId);
    } catch (_error) {
      return;
    }
    window.requestAnimationFrame(() => {
      const preview = contextExplorer.querySelector("[data-context-preview]");
      const target = preview?.querySelector(`#${CSS.escape(anchorId)}`);
      const heading = preview?.querySelector(".context-preview-heading");
      if (!preview || !target) return;
      const previewBounds = preview.getBoundingClientRect();
      const targetBounds = target.getBoundingClientRect();
      preview.scrollTop += targetBounds.top - previewBounds.top - (heading?.offsetHeight || 0);
    });
  };

  const loadDocumentPreview = async (
    destination,
    { pushHistory = false, focusSelection = false } = {},
  ) => {
    previewRequest?.abort();
    const controller = new AbortController();
    previewRequest = controller;
    const currentPreview = contextExplorer.querySelector("[data-context-preview]");
    currentPreview.setAttribute("aria-busy", "true");

    try {
      const response = await fetch(destination.href, {
        credentials: "same-origin",
        headers: { "X-Requested-With": "LocalBrain-Context-Preview" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
      const incomingPreview = parsed.querySelector("[data-context-preview]");
      if (!incomingPreview) throw new Error("미리보기 영역을 찾을 수 없습니다.");

      const incomingSelected = parsed.querySelector("[data-context-document-link].active");
      const selectedDestination = incomingSelected?.href || destination.href;
      const adoptedPreview = document.importNode(incomingPreview, true);
      adoptedPreview.setAttribute("aria-busy", "false");
      currentPreview.replaceWith(adoptedPreview);
      const selectedLink = selectDocumentLink(selectedDestination);
      if (focusSelection && selectedLink) selectedLink.focus({ preventScroll: true });

      if (pushHistory) {
        window.history.pushState({ contextDocument: true }, "", destination.href);
      }
      scrollPreviewFragment(destination);

      const title = adoptedPreview.querySelector(".context-preview-heading h2")?.textContent.trim();
      previewStatus.textContent = title
        ? `${title} 문서를 미리보기에 표시했습니다.`
        : "선택된 문서가 없습니다.";
    } catch (error) {
      if (error.name === "AbortError") return;
      window.location.assign(destination.href);
    } finally {
      if (previewRequest === controller) {
        previewRequest = null;
        contextExplorer.querySelector("[data-context-preview]")?.setAttribute("aria-busy", "false");
      }
    }
  };

  treePane.addEventListener("click", (event) => {
    const link = event.target.closest("[data-context-document-link]");
    if (
      !link
      || event.defaultPrevented
      || event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
    ) return;

    const destination = new URL(link.href, window.location.href);
    if (!destinationUsesCurrentSource(destination)) return;
    event.preventDefault();
    if (destination.href === window.location.href) return;
    loadDocumentPreview(destination, { pushHistory: true });
  });

  contextExplorer.addEventListener("click", (event) => {
    const reference = event.target.closest(
      "[data-context-preview] a.markdown-reference-internal[href^='/documents/']",
    );
    if (
      !reference
      || event.defaultPrevented
      || event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
    ) return;

    const referenceDestination = new URL(reference.href, window.location.href);
    const match = referenceDestination.pathname.match(/^\/documents\/(\d+)$/);
    if (!match) return;
    const targetLink = documentLinks().find((link) => {
      const candidate = new URL(link.href, window.location.href);
      return candidate.searchParams.get("document") === match[1];
    });
    if (!targetLink) return;

    event.preventDefault();
    const destination = new URL(targetLink.href, window.location.href);
    destination.hash = referenceDestination.hash;
    if (destinationKey(destination) === destinationKey(window.location.href)) {
      selectDocumentLink(destination, targetLink);
      if (destination.href !== window.location.href) {
        window.history.pushState({ contextDocument: true }, "", destination.href);
      }
      scrollPreviewFragment(destination);
      return;
    }
    loadDocumentPreview(destination, { pushHistory: true, focusSelection: true });
  });

  window.addEventListener("popstate", () => {
    const destination = new URL(window.location.href);
    if (!destinationUsesCurrentSource(destination)) {
      window.location.reload();
      return;
    }
    loadDocumentPreview(destination, { focusSelection: true });
  });

  const initialSelection = treePane.querySelector("[data-context-document-link].active");
  if (initialSelection) selectDocumentLink(initialSelection.href, initialSelection);
  scrollPreviewFragment(new URL(window.location.href));
}

const documentReader = document.querySelector("[data-document-reader]");

if (documentReader) {
  const treePane = documentReader.querySelector("[data-document-reader-tree]");
  const returnLink = documentReader.querySelector("[data-document-reader-return]");
  const readerStatus = documentReader.querySelector("[data-document-reader-status]");
  let readerRequest = null;

  if (treePane) {
    const documentLinks = () => [
      ...treePane.querySelectorAll("[data-document-reader-link]"),
    ];

    const documentId = (destination) => {
      const url = new URL(destination, window.location.href);
      return url.pathname.match(/^\/documents\/(\d+)$/)?.[1] || null;
    };

    const revealDocumentLink = (link) => {
      let ancestor = link.parentElement.closest("details");
      while (ancestor && treePane.contains(ancestor)) {
        ancestor.open = true;
        ancestor = ancestor.parentElement.closest("details");
      }

      const paneBounds = treePane.getBoundingClientRect();
      const linkBounds = link.getBoundingClientRect();
      if (linkBounds.top < paneBounds.top) {
        treePane.scrollTop -= paneBounds.top - linkBounds.top;
      } else if (linkBounds.bottom > paneBounds.bottom) {
        treePane.scrollTop += linkBounds.bottom - paneBounds.bottom;
      }
    };

    const selectDocumentLink = (destination, fallbackLink = null) => {
      const selectedId = documentId(destination);
      const selected = documentLinks().find((link) => documentId(link.href) === selectedId)
        || fallbackLink;

      documentLinks().forEach((link) => {
        const isSelected = link === selected;
        link.classList.toggle("active", isSelected);
        if (isSelected) {
          link.setAttribute("aria-current", "page");
        } else {
          link.removeAttribute("aria-current");
        }
      });

      if (selected) {
        revealDocumentLink(selected);
        if (returnLink && selected.dataset.contextHref) {
          returnLink.href = selected.dataset.contextHref;
        }
      }
      return selected;
    };

    const scrollReaderDestination = (destination) => {
      window.requestAnimationFrame(() => {
        const content = documentReader.querySelector("[data-document-reader-content]");
        if (!content) return;
        if (!destination.hash) {
          content.scrollIntoView({ block: "start" });
          return;
        }
        let anchorId = destination.hash.slice(1);
        try {
          anchorId = decodeURIComponent(anchorId);
        } catch (_error) {
          return;
        }
        content.querySelector(`#${CSS.escape(anchorId)}`)?.scrollIntoView({ block: "start" });
      });
    };

    const loadDocumentReader = async (
      destination,
      { pushHistory = false, focusSelection = false } = {},
    ) => {
      readerRequest?.abort();
      const controller = new AbortController();
      readerRequest = controller;
      const currentContent = documentReader.querySelector("[data-document-reader-content]");
      currentContent.setAttribute("aria-busy", "true");

      try {
        const response = await fetch(destination.href, {
          credentials: "same-origin",
          headers: { "X-Requested-With": "LocalBrain-Document-Reader" },
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
        const incomingContent = parsed.querySelector("[data-document-reader-content]");
        if (!incomingContent) throw new Error("문서 읽기 영역을 찾을 수 없습니다.");

        const incomingSelected = parsed.querySelector(
          "[data-document-reader-link][aria-current='page']",
        );
        const selectedDestination = incomingSelected?.href || destination.href;
        const adoptedContent = document.importNode(incomingContent, true);
        adoptedContent.setAttribute("aria-busy", "false");
        currentContent.replaceWith(adoptedContent);
        const selectedLink = selectDocumentLink(selectedDestination);
        if (focusSelection && selectedLink) selectedLink.focus({ preventScroll: true });

        if (pushHistory) {
          window.history.pushState({ documentReader: true }, "", destination.href);
        }
        document.title = parsed.title;
        scrollReaderDestination(destination);

        const title = adoptedContent.querySelector(".document-heading h1")?.textContent.trim();
        readerStatus.textContent = title
          ? `${title} 문서를 전체 읽기에 표시했습니다.`
          : "문서를 전체 읽기에 표시했습니다.";
      } catch (error) {
        if (error.name === "AbortError") return;
        window.location.assign(destination.href);
      } finally {
        if (readerRequest === controller) {
          readerRequest = null;
          documentReader.querySelector("[data-document-reader-content]")
            ?.setAttribute("aria-busy", "false");
        }
      }
    };

    treePane.addEventListener("click", (event) => {
      const link = event.target.closest("[data-document-reader-link]");
      if (
        !link
        || event.defaultPrevented
        || event.button !== 0
        || event.metaKey
        || event.ctrlKey
        || event.shiftKey
        || event.altKey
      ) return;

      const destination = new URL(link.href, window.location.href);
      if (!documentId(destination)) return;
      event.preventDefault();
      if (destination.href === window.location.href) return;
      loadDocumentReader(destination, { pushHistory: true });
    });

    documentReader.addEventListener("click", (event) => {
      const reference = event.target.closest(
        "[data-document-reader-content] a.markdown-reference-internal[href^='/documents/']",
      );
      if (
        !reference
        || event.defaultPrevented
        || event.button !== 0
        || event.metaKey
        || event.ctrlKey
        || event.shiftKey
        || event.altKey
      ) return;

      const referenceDestination = new URL(reference.href, window.location.href);
      const targetLink = documentLinks().find(
        (link) => documentId(link.href) === documentId(referenceDestination),
      );
      if (!targetLink) return;

      event.preventDefault();
      const destination = new URL(targetLink.href, window.location.href);
      destination.hash = referenceDestination.hash;
      if (documentId(destination) === documentId(window.location.href)) {
        selectDocumentLink(destination, targetLink);
        if (destination.href !== window.location.href) {
          window.history.pushState({ documentReader: true }, "", destination.href);
        }
        scrollReaderDestination(destination);
        return;
      }
      loadDocumentReader(destination, { pushHistory: true, focusSelection: true });
    });

    window.addEventListener("popstate", () => {
      const destination = new URL(window.location.href);
      const targetLink = documentLinks().find(
        (link) => documentId(link.href) === documentId(destination),
      );
      if (!targetLink) {
        window.location.reload();
        return;
      }
      loadDocumentReader(destination, { focusSelection: true });
    });

    const initialSelection = treePane.querySelector(
      "[data-document-reader-link][aria-current='page']",
    );
    if (initialSelection) selectDocumentLink(initialSelection.href, initialSelection);
    scrollReaderDestination(new URL(window.location.href));
  }
}

document.querySelectorAll("[data-task-run-form]").forEach((form) => {
  const taskSelect = form.querySelector("[data-runner-task-select]");
  const baseRequest = form.querySelector("[data-runner-base-request-text]");
  if (!taskSelect || !baseRequest) return;

  const syncBaseRequest = () => {
    baseRequest.textContent = taskSelect.selectedOptions[0]?.dataset.baseRequest || "";
  };
  taskSelect.addEventListener("change", syncBaseRequest);
  syncBaseRequest();
});

document.querySelectorAll("[data-api-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector("button[type='submit']");
    const result = form.querySelector("[data-form-result]");
    const payload = Object.fromEntries(new FormData(form).entries());

    if (form.hasAttribute("data-split-entity")) {
      [payload.scope_type, payload.scope_id] = splitReference(payload.scope_ref || "");
      [payload.entity_type, payload.entity_id] = splitReference(payload.entity_ref || "");
      delete payload.scope_ref;
      delete payload.entity_ref;
    } else if (form.hasAttribute("data-split-scope")) {
      [payload.scope_type, payload.scope_id] = splitReference(payload.scope_ref || "");
      delete payload.scope_ref;
    }

    submitButton.disabled = true;
    if (result) result.hidden = true;
    try {
      const data = await requestJson(form.dataset.endpoint, {
        method: form.dataset.method || "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (data.redirect) {
        window.location.assign(data.redirect);
        return;
      }
      if (result) {
        result.textContent = "저장했습니다.";
        result.className = "form-result success";
        result.setAttribute("role", "status");
        result.hidden = false;
      }
      window.setTimeout(() => window.location.reload(), 350);
    } catch (error) {
      if (result) {
        result.textContent = error.message;
        result.className = "form-result error";
        result.setAttribute("role", "alert");
        result.hidden = false;
      }
      submitButton.disabled = false;
    }
  });
});

document.querySelectorAll("[data-delete-link]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!window.confirm("이 연결을 제거할까요?")) return;
    button.disabled = true;
    try {
      await requestJson(button.dataset.deleteLink, { method: "DELETE" });
      window.location.reload();
    } catch (error) {
      showNotice(error.message);
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-delete-context-root], [data-delete-context-source]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!window.confirm("이 Source를 Local Contexts 인덱스에서 제거할까요? 실제 파일과 Apple Notes는 삭제되지 않습니다.")) return;
    button.disabled = true;
    try {
      const sourceId = button.dataset.deleteContextSource || button.dataset.deleteContextRoot;
      await requestJson(`/api/context-sources/${sourceId}`, {
        method: "DELETE",
      });
      window.location.assign("/context");
    } catch (error) {
      showNotice(error.message);
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-suggestion-run]").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    const original = button.textContent;
    button.textContent = "분석 중";
    try {
      const data = await requestJson(
        `/api/workstreams/${button.dataset.suggestionRun}/suggestions`,
        { method: "POST" },
      );
      button.textContent = `${data.created}개 제안`;
      window.setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      showNotice(error.message);
      button.disabled = false;
      button.textContent = original;
    }
  });
});

document.querySelectorAll("[data-suggestion-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      await requestJson(button.dataset.suggestionAction, { method: "POST" });
      window.location.reload();
    } catch (error) {
      showNotice(error.message);
      button.disabled = false;
    }
  });
});

const runConsole = document.querySelector("[data-run-console]");

if (runConsole) {
  const runId = runConsole.dataset.runId;
  const output = runConsole.querySelector("[data-run-output]");
  const status = document.querySelector("[data-run-status]");
  const pid = document.querySelector("[data-run-pid]");
  const suggestions = document.querySelector("[data-run-suggestions]");
  const mcpCalls = document.querySelector("[data-run-mcp]");
  const updated = runConsole.querySelector("[data-run-updated]");
  const errorPanel = runConsole.querySelector("[data-run-error]");
  const cancelButton = document.querySelector("[data-cancel-run]");
  const activeStatuses = new Set(["queued", "running", "cancelling"]);

  const refreshRun = async () => {
    try {
      const data = await requestJson(`/api/runs/${runId}`);
      const current = data.run;
      status.textContent = current.status_label;
      status.className = `run-status large ${current.status}`;
      pid.textContent = current.pid || "-";
      if (suggestions) suggestions.textContent = current.suggestions_created || 0;
      if (mcpCalls) {
        mcpCalls.textContent = `${current.mcp_calls_used || 0} / ${current.mcp_call_budget}`;
        mcpCalls.classList.toggle("missing", Boolean(current.mcp_budget_exceeded));
      }
      updated.textContent = formatLocalTime(current.updated_at);
      if (current.output) output.textContent = current.output;
      if (current.error) {
        errorPanel.textContent = current.error;
        errorPanel.hidden = false;
      }
      cancelButton.hidden = !activeStatuses.has(current.status);
      if (activeStatuses.has(current.status)) {
        window.setTimeout(refreshRun, 1000);
      }
    } catch (error) {
      errorPanel.textContent = error.message;
      errorPanel.hidden = false;
    }
  };

  if (activeStatuses.has(runConsole.dataset.runStatus)) {
    window.setTimeout(refreshRun, 500);
  }

  cancelButton.addEventListener("click", async () => {
    cancelButton.disabled = true;
    try {
      await requestJson(`/api/runs/${runId}/cancel`, { method: "POST" });
      status.textContent = "cancelling";
      status.className = "run-status large cancelling";
      window.setTimeout(refreshRun, 300);
    } catch (error) {
      errorPanel.textContent = error.message;
      errorPanel.hidden = false;
      cancelButton.disabled = false;
    }
  });
}
