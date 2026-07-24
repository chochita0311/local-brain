let schemaRequest = null;

const currentExplorer = () => document.querySelector("[data-schema-explorer]");
const SCHEMA_ZOOM_MIN = 0.1;
const SCHEMA_ZOOM_MAX = 3;
const SCHEMA_ZOOM_BUTTON_FACTOR = 1.25;
const SCHEMA_ZOOM_WHEEL_SENSITIVITY = 0.002;

export function clampSchemaZoom(value) {
  if (!Number.isFinite(value)) return 1;
  return Math.min(SCHEMA_ZOOM_MAX, Math.max(SCHEMA_ZOOM_MIN, value));
}

export function schemaZoomFromWheel(scale, deltaY) {
  const boundedDelta = Math.min(120, Math.max(-120, Number(deltaY) || 0));
  return clampSchemaZoom(scale * Math.exp(-boundedDelta * SCHEMA_ZOOM_WHEEL_SENSITIVITY));
}

export function schemaAnchoredScroll(scrollOffset, pointerOffset, previousScale, nextScale) {
  if (!Number.isFinite(previousScale) || previousScale <= 0) return scrollOffset;
  return (scrollOffset + pointerOffset) * (nextScale / previousScale) - pointerOffset;
}

function setSchemaZoomControlsAvailable(controls, available) {
  controls?.querySelectorAll("button").forEach((button) => {
    button.disabled = !available;
  });
}

function setupSchemaDiagramZoom(panel) {
  const controls = panel?.querySelector("[data-schema-zoom-controls]");
  const viewport = panel?.querySelector("[data-schema-diagram-viewport]");
  const diagram = viewport?.querySelector(".schema-diagram");
  const rendered = diagram?.querySelector("[data-localbrain-mermaid-rendered]");
  if (!controls || !viewport || !diagram || !rendered) {
    setSchemaZoomControlsAvailable(controls, false);
    return;
  }

  const zoomOut = controls.querySelector("[data-schema-zoom-out]");
  const zoomReset = controls.querySelector("[data-schema-zoom-reset]");
  const zoomIn = controls.querySelector("[data-schema-zoom-in]");
  const zoomFit = controls.querySelector("[data-schema-zoom-fit]");
  const baseWidth = rendered.getBoundingClientRect().width;
  if (!baseWidth) {
    setSchemaZoomControlsAvailable(controls, false);
    return;
  }

  let scale = 1;
  rendered.style.width = `${baseWidth}px`;
  rendered.style.minWidth = "0px";
  setSchemaZoomControlsAvailable(controls, true);

  const updateControls = () => {
    const percentage = `${Math.round(scale * 100)}%`;
    zoomReset.textContent = percentage;
    zoomReset.setAttribute(
      "aria-label",
      `현재 배율 ${percentage}, 100%로 재설정`,
    );
    zoomOut.disabled = scale <= SCHEMA_ZOOM_MIN;
    zoomIn.disabled = scale >= SCHEMA_ZOOM_MAX;
  };

  const applyZoom = (requestedScale, clientX, clientY) => {
    const nextScale = clampSchemaZoom(requestedScale);
    if (Math.abs(nextScale - scale) < 0.0001) {
      updateControls();
      return;
    }

    const viewportRect = viewport.getBoundingClientRect();
    const pointerX = Number.isFinite(clientX)
      ? Math.min(viewport.clientWidth, Math.max(0, clientX - viewportRect.left))
      : viewport.clientWidth / 2;
    const pointerY = Number.isFinite(clientY)
      ? Math.min(viewport.clientHeight, Math.max(0, clientY - viewportRect.top))
      : viewport.clientHeight / 2;
    const nextScrollLeft = schemaAnchoredScroll(
      viewport.scrollLeft,
      pointerX,
      scale,
      nextScale,
    );
    const nextScrollTop = schemaAnchoredScroll(
      viewport.scrollTop,
      pointerY,
      scale,
      nextScale,
    );

    scale = nextScale;
    rendered.style.width = `${baseWidth * scale}px`;
    updateControls();
    window.requestAnimationFrame(() => {
      viewport.scrollLeft = nextScrollLeft;
      viewport.scrollTop = nextScrollTop;
    });
  };

  zoomOut.addEventListener("click", () => {
    applyZoom(scale / SCHEMA_ZOOM_BUTTON_FACTOR);
  });
  zoomReset.addEventListener("click", () => {
    applyZoom(1);
  });
  zoomIn.addEventListener("click", () => {
    applyZoom(scale * SCHEMA_ZOOM_BUTTON_FACTOR);
  });
  zoomFit.addEventListener("click", () => {
    const viewportStyle = window.getComputedStyle(viewport);
    const horizontalPadding =
      (Number.parseFloat(viewportStyle.paddingLeft) || 0)
      + (Number.parseFloat(viewportStyle.paddingRight) || 0);
    const availableWidth = Math.max(
      1,
      viewport.clientWidth - horizontalPadding,
    );
    applyZoom(Math.min(1, availableWidth / baseWidth));
  });
  viewport.addEventListener(
    "wheel",
    (event) => {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      applyZoom(
        schemaZoomFromWheel(scale, event.deltaY),
        event.clientX,
        event.clientY,
      );
    },
    { passive: false },
  );

  updateControls();
}

function markDiagramFailure(root, message) {
  root.querySelectorAll("[data-schema-diagram-fallback]").forEach((fallback) => {
    fallback.textContent = message;
    fallback.closest("[data-schema-diagram-mode]")?.setAttribute(
      "data-schema-mermaid-state",
      "unavailable",
    );
  });
}

async function renderSchemaDiagrams(root) {
  const diagramNodes = [...root.querySelectorAll('[data-localbrain-mermaid="owned"]')];
  if (!diagramNodes.length) return;
  try {
    diagramNodes.forEach((node) => {
      const source = node.querySelector("[data-schema-source-json]");
      if (source) {
        source.textContent = JSON.parse(source.textContent);
        source.removeAttribute("data-schema-source-json");
      }
    });
  } catch (_error) {
    markDiagramFailure(root, "다이어그램 정의를 읽을 수 없습니다. 주제 및 테이블 링크를 이용하세요.");
    return;
  }
  const adapterUrl = root.dataset.mermaidAdapterUrl;
  if (!adapterUrl) {
    markDiagramFailure(root, "다이어그램 자산을 찾을 수 없습니다. 주제 및 테이블 링크를 이용하세요.");
    return;
  }

  try {
    const { renderLocalBrainMermaid } = await import(adapterUrl);
    for (const node of diagramNodes) {
      const panel = node.closest("[data-schema-diagram-mode]");
      const result = await renderLocalBrainMermaid(node);
      panel?.setAttribute(
        "data-schema-mermaid-state",
        result.ok ? "rendered" : "unavailable",
      );
      if (result.ok) {
        setupSchemaDiagramZoom(panel);
      } else {
        node.querySelector("[data-schema-diagram-fallback]").textContent =
          "다이어그램을 렌더링할 수 없습니다. 주제 및 테이블 링크를 이용하세요.";
      }
    }
  } catch (_error) {
    markDiagramFailure(root, "다이어그램을 불러올 수 없습니다. 주제 및 테이블 링크를 이용하세요.");
  }
}

function schemaFocusTarget(destination) {
  return destination.searchParams.has("table") ? "table" : "area";
}

function focusSchemaDestination(root, target, { scroll = true } = {}) {
  const heading = root.querySelector(`[data-schema-focus="${target}"]`)
    || root.querySelector('[data-schema-focus="area"]')
    || root.querySelector('[data-schema-focus="page"]');
  if (!heading) return;
  heading.focus({ preventScroll: true });
  if (scroll) heading.scrollIntoView({ block: "start", inline: "nearest" });
}

function announceSchemaState(root) {
  const status = root.querySelector("[data-schema-status]");
  const heading = root.querySelector("[data-schema-focus]");
  const currentArea = root.querySelector('.schema-subject-link[aria-current="page"] strong');
  const currentTable = root.querySelector('.schema-table-link[aria-current="page"] code');
  if (!status || !heading) return;
  status.textContent = [currentArea?.textContent, currentTable?.textContent]
    .filter(Boolean)
    .join(" · ") + " Schema 보기로 이동했습니다.";
}

async function loadSchema(destination, { pushHistory = false, scroll = true } = {}) {
  schemaRequest?.abort();
  const controller = new AbortController();
  schemaRequest = controller;
  const outgoing = currentExplorer();
  outgoing?.setAttribute("aria-busy", "true");

  try {
    const response = await fetch(destination.href, {
      credentials: "same-origin",
      headers: { "X-Requested-With": "LocalBrain-Schema-Explorer" },
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
    const incoming = parsed.querySelector("[data-schema-explorer]");
    if (!incoming || !outgoing) throw new Error("Schema 영역을 찾을 수 없습니다.");

    const adopted = document.importNode(incoming, true);
    outgoing.replaceWith(adopted);
    document.title = parsed.title || document.title;
    if (pushHistory) {
      window.history.pushState({ schemaExplorer: true }, "", destination.href);
    }
    await renderSchemaDiagrams(adopted);
    focusSchemaDestination(adopted, schemaFocusTarget(destination), { scroll });
    announceSchemaState(adopted);
  } catch (error) {
    if (error.name === "AbortError") return;
    window.location.assign(destination.href);
  } finally {
    if (schemaRequest === controller) {
      schemaRequest = null;
      currentExplorer()?.setAttribute("aria-busy", "false");
    }
  }
}

if (typeof document !== "undefined") {
  document.addEventListener("click", (event) => {
    const link = event.target.closest("[data-schema-link]");
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
    if (destination.origin !== window.location.origin || destination.pathname !== "/schema") return;
    event.preventDefault();
    if (destination.href === window.location.href) {
      focusSchemaDestination(currentExplorer(), schemaFocusTarget(destination));
      return;
    }
    loadSchema(destination, { pushHistory: true });
  });

  window.addEventListener("popstate", () => {
    const destination = new URL(window.location.href);
    if (destination.pathname !== "/schema") {
      window.location.reload();
      return;
    }
    loadSchema(destination);
  });

  const initialExplorer = currentExplorer();
  if (initialExplorer) {
    window.history.replaceState({ ...window.history.state, schemaExplorer: true }, "");
    renderSchemaDiagrams(initialExplorer).then(() => {
      const destination = new URL(window.location.href);
      if (destination.search) {
        focusSchemaDestination(initialExplorer, schemaFocusTarget(destination), { scroll: false });
      }
    });
  }
}
