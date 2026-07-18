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

document.querySelectorAll("[data-local-time]").forEach((element) => {
  element.textContent = formatLocalTime(element.getAttribute("datetime") || element.textContent);
});

document.querySelectorAll("[data-local-epoch]").forEach((element) => {
  const milliseconds = Number(element.getAttribute("datetime"));
  if (Number.isFinite(milliseconds)) {
    element.textContent = formatLocalTime(new Date(milliseconds).toISOString());
  }
});

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
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const imported = Object.values(data.report).reduce(
        (sum, source) => sum + source.imported,
        0,
      );
      result.textContent = `${imported}개 변경 항목을 반영했습니다. 화면을 갱신합니다.`;
      result.className = "scan-result success";
      result.setAttribute("role", "status");
      result.hidden = false;
      window.setTimeout(() => window.location.reload(), 700);
    } catch (error) {
      result.textContent = `${actionLabel}에 실패했습니다: ${error.message}`;
      result.className = "scan-result error";
      result.setAttribute("role", "alert");
      result.hidden = false;
      button.disabled = false;
      button.removeAttribute("aria-busy");
      idle.hidden = false;
      working.hidden = true;
    }
  });
}

bindScanAction(
  document.querySelector("#scan-button"),
  document.querySelector("#scan-result"),
  "/api/scan",
  "스캔",
);
bindScanAction(
  document.querySelector("#session-sync-button"),
  document.querySelector("#session-sync-result"),
  "/api/sessions/sync",
  "동기화",
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
  const treePane = contextExplorer.querySelector(".source-tree-pane");
  const previewStatus = contextExplorer.querySelector("[data-context-preview-status]");
  const sourceId = contextExplorer.dataset.contextSourceId;
  let previewRequest = null;

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
}

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

document.querySelectorAll("[data-maintenance-run]").forEach((button) => {
  button.addEventListener("click", async () => {
    const container = button.parentElement;
    const marker = container.querySelector("[data-maintenance-marker]");
    const copyButton = container.querySelector("[data-copy-marker]");
    button.disabled = true;
    try {
      const workstreamId = button.dataset.maintenanceRun || null;
      const data = await requestJson("/api/maintenance-runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workstream_id: workstreamId }),
      });
      marker.textContent = data.marker;
      marker.hidden = false;
      copyButton.hidden = false;
      button.textContent = "새 마커 생성";
    } catch (error) {
      showNotice(error.message);
    } finally {
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-copy-marker]").forEach((button) => {
  button.addEventListener("click", async () => {
    const marker = button.parentElement.querySelector("[data-maintenance-marker]");
    button.disabled = true;
    try {
      await navigator.clipboard.writeText(marker.textContent);
      button.textContent = "복사됨";
      window.setTimeout(() => {
        button.textContent = "마커 복사";
        button.disabled = false;
      }, 1000);
    } catch (error) {
      showNotice(`마커를 복사하지 못했습니다: ${error.message}`);
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
      status.textContent = current.status;
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

  if (activeStatuses.has(status.textContent.trim())) {
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
