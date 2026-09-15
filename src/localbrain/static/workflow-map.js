const WORKFLOW_ZOOM_MIN = 0.55;
const WORKFLOW_ZOOM_MAX = 1.8;
const WORKFLOW_ZOOM_BUTTON_FACTOR = 1.2;
const WORKFLOW_ZOOM_WHEEL_SENSITIVITY = 0.002;
const WORKFLOW_RESTORE_VERSION = "localbrain.workflow-correction-restore.v1";
const WORKFLOW_RESTORE_KEY = "localbrain.workflow-correction-restore";
const WORKFLOW_RESTORE_TTL_MS = 2 * 60 * 1000;
const WORKFLOW_SCROLL_MAX = 10_000_000;
const WORKFLOW_EPISODE_KEY = /^session:[0-9a-f]{64}$/;
const WORKFLOW_RELATION_ID = /^workflow-relation-[0-9a-f]{64}$/;
const WORKFLOW_PATH = /^\/sessions\/[1-9][0-9]*\/workflow$/;
const WORKFLOW_RESULT_MESSAGES = Object.freeze({
  "workflow-corrected": "작업 흐름 경계를 사용자 확인으로 반영했습니다.",
  "workflow-undone": "이전 경계를 되돌려 작업 흐름을 다시 투영했습니다.",
});

const DEFAULT_GEOMETRY = Object.freeze({
  nodeWidth: 228,
  nodeHeight: 144,
  columnGap: 104,
  laneGap: 56,
  stagePadding: 40,
  axisSize: 36,
});

function boundedScroll(value) {
  if (!Number.isFinite(value)) return 0;
  return Math.min(WORKFLOW_SCROLL_MAX, Math.max(0, value));
}

function validDisclosureKey(value) {
  return typeof value === "string"
    && value.length <= 160
    && /^evidence:session:[0-9a-f]{64}:[a-z0-9-]+$/.test(value);
}

export function sanitizeWorkflowRestorationSnapshot(
  value,
  pathname,
  now = Date.now(),
) {
  if (
    !value
    || value.version !== WORKFLOW_RESTORE_VERSION
    || value.pathname !== pathname
    || !WORKFLOW_PATH.test(pathname)
    || !Number.isFinite(value.createdAt)
    || value.createdAt > now + 5_000
    || now - value.createdAt > WORKFLOW_RESTORE_TTL_MS
    || !WORKFLOW_EPISODE_KEY.test(value.selectedEpisodeKey || "")
    || !Object.hasOwn(WORKFLOW_RESULT_MESSAGES, value.resultCode)
    || !Array.isArray(value.expandedBranchKeys)
    || !Array.isArray(value.openDisclosureKeys)
  ) {
    return null;
  }
  const expandedBranchKeys = [...new Set(value.expandedBranchKeys)]
    .filter((key) => WORKFLOW_EPISODE_KEY.test(key))
    .slice(0, 24);
  const openDisclosureKeys = [...new Set(value.openDisclosureKeys)]
    .filter(validDisclosureKey)
    .slice(0, 40);
  const focusKind = value.focusKind === "relation" ? "relation" : "lifecycle";
  const focusKey = focusKind === "relation"
    ? (WORKFLOW_RELATION_ID.test(value.focusKey || "") ? value.focusKey : null)
    : (WORKFLOW_EPISODE_KEY.test(value.focusKey || "") ? value.focusKey : null);
  if (!focusKey) return null;
  return {
    version: WORKFLOW_RESTORE_VERSION,
    pathname,
    createdAt: value.createdAt,
    selectedEpisodeKey: value.selectedEpisodeKey,
    expandedBranchKeys,
    scale: clampWorkflowZoom(value.scale),
    viewportScrollLeft: boundedScroll(value.viewportScrollLeft),
    viewportScrollTop: boundedScroll(value.viewportScrollTop),
    traceScrollTop: boundedScroll(value.traceScrollTop),
    outerScrollX: boundedScroll(value.outerScrollX),
    outerScrollY: boundedScroll(value.outerScrollY),
    openDisclosureKeys,
    focusKind,
    focusKey,
    resultCode: value.resultCode,
  };
}

export function consumeWorkflowRestorationSnapshot(
  storage,
  pathname,
  now = Date.now(),
) {
  let serialized = null;
  try {
    serialized = storage?.getItem(WORKFLOW_RESTORE_KEY);
    storage?.removeItem(WORKFLOW_RESTORE_KEY);
  } catch (_error) {
    return null;
  }
  if (!serialized || serialized.length > 8_192) return null;
  try {
    return sanitizeWorkflowRestorationSnapshot(
      JSON.parse(serialized), pathname, now,
    );
  } catch (_error) {
    return null;
  }
}

export function storeWorkflowRestorationSnapshot(storage, value) {
  const snapshot = sanitizeWorkflowRestorationSnapshot(
    value, value?.pathname, value?.createdAt,
  );
  if (!snapshot) return false;
  try {
    storage?.setItem(WORKFLOW_RESTORE_KEY, JSON.stringify(snapshot));
    return true;
  } catch (_error) {
    return false;
  }
}

function correctionResponse(payload, responseStatus, episodeKeys) {
  if (!payload || payload.status !== "ok" || responseStatus !== 200) return null;
  if (!Object.hasOwn(WORKFLOW_RESULT_MESSAGES, payload.code)) return null;
  if (!WORKFLOW_PATH.test(payload.reload_url || "")) return null;
  const boundary = payload.boundary;
  if (
    !boundary
    || !["relation", "lifecycle"].includes(boundary.kind)
    || !episodeKeys.has(boundary.source_episode_key)
  ) return null;
  if (boundary.kind === "relation") {
    if (
      !episodeKeys.has(boundary.target_episode_key)
      || !WORKFLOW_RELATION_ID.test(boundary.relation_id || "")
    ) return null;
  } else if (boundary.target_episode_key !== null) {
    return null;
  }
  return {
    code: payload.code,
    focusKind: boundary.kind,
    focusKey: boundary.kind === "relation"
      ? boundary.relation_id
      : boundary.source_episode_key,
  };
}

export function clampWorkflowZoom(value) {
  if (!Number.isFinite(value)) return 1;
  return Math.min(WORKFLOW_ZOOM_MAX, Math.max(WORKFLOW_ZOOM_MIN, value));
}

export function workflowZoomFromWheel(scale, deltaY) {
  const boundedDelta = Math.min(120, Math.max(-120, Number(deltaY) || 0));
  return clampWorkflowZoom(
    scale * Math.exp(-boundedDelta * WORKFLOW_ZOOM_WHEEL_SENSITIVITY),
  );
}

export function workflowAnchoredScroll(
  scrollOffset,
  pointerOffset,
  previousScale,
  nextScale,
) {
  if (!Number.isFinite(previousScale) || previousScale <= 0) return scrollOffset;
  return (scrollOffset + pointerOffset) * (nextScale / previousScale) - pointerOffset;
}

export function workflowWheelOwnsZoom(event) {
  return Boolean(event?.ctrlKey || event?.metaKey);
}

function observationValue(episode) {
  const value = Date.parse(
    episode.last_observed_at || episode.observed_start_at || "",
  );
  return Number.isFinite(value) ? value : Number.MAX_SAFE_INTEGER;
}

function validateProjection(payload) {
  if (
    !payload
    || payload.status !== "ready"
    || !Array.isArray(payload.episodes)
    || !Array.isArray(payload.relations)
    || !payload.episodes.length
    || typeof payload.selected_episode_key !== "string"
  ) {
    throw new Error("Invalid Workflow Focus payload");
  }
  const keys = new Set();
  payload.episodes.forEach((episode) => {
    if (!episode || typeof episode.episode_key !== "string" || keys.has(episode.episode_key)) {
      throw new Error("Invalid Workflow Episode");
    }
    keys.add(episode.episode_key);
  });
  if (!keys.has(payload.selected_episode_key)) {
    throw new Error("Selected Workflow Episode is absent");
  }
  payload.relations.forEach((relation) => {
    if (
      !relation
      || !keys.has(relation.source_episode_key)
      || !keys.has(relation.target_episode_key)
      || !["continues", "branches-from", "merged-into"].includes(relation.kind)
    ) {
      throw new Error("Invalid Workflow relation");
    }
  });
}

export function buildWorkflowLayout(
  payload,
  orientation = "wide",
  geometry = DEFAULT_GEOMETRY,
) {
  validateProjection(payload);
  const direction = orientation === "compact" ? "compact" : "wide";
  const dimensions = { ...DEFAULT_GEOMETRY, ...geometry };
  const episodes = [...payload.episodes].sort((first, second) => (
    observationValue(first) - observationValue(second)
    || first.episode_key.localeCompare(second.episode_key)
  ));
  const episodeOrder = new Map(
    episodes.map((episode, index) => [episode.episode_key, index]),
  );
  const incoming = new Map();
  [...payload.relations]
    .sort((first, second) => (
      (episodeOrder.get(first.target_episode_key) ?? Number.MAX_SAFE_INTEGER)
      - (episodeOrder.get(second.target_episode_key) ?? Number.MAX_SAFE_INTEGER)
      || first.source_episode_key.localeCompare(second.source_episode_key)
      || first.kind.localeCompare(second.kind)
    ))
    .forEach((relation) => {
      if (!incoming.has(relation.target_episode_key)) {
        incoming.set(relation.target_episode_key, relation);
      }
    });

  const lanes = new Map();
  const branchOwners = new Map();
  let nextLane = 0;
  episodes.forEach((episode) => {
    const relation = incoming.get(episode.episode_key);
    const sourceLane = relation ? lanes.get(relation.source_episode_key) : undefined;
    if (!relation || sourceLane === undefined) {
      lanes.set(episode.episode_key, nextLane);
      branchOwners.set(episode.episode_key, null);
      nextLane += 1;
      return;
    }
    if (relation.kind === "branches-from") {
      lanes.set(episode.episode_key, nextLane);
      branchOwners.set(episode.episode_key, episode.episode_key);
      nextLane += 1;
      return;
    }
    lanes.set(episode.episode_key, sourceLane);
    branchOwners.set(
      episode.episode_key,
      branchOwners.get(relation.source_episode_key) || null,
    );
  });

  const positionedEpisodes = episodes.map((episode, index) => {
    const lane = lanes.get(episode.episode_key) || 0;
    const wideX = dimensions.stagePadding
      + index * (dimensions.nodeWidth + dimensions.columnGap);
    const wideY = dimensions.stagePadding + dimensions.axisSize
      + lane * (dimensions.nodeHeight + dimensions.laneGap);
    const compactX = dimensions.stagePadding
      + lane * (dimensions.nodeWidth + dimensions.laneGap);
    const compactY = dimensions.stagePadding + dimensions.axisSize
      + index * (dimensions.nodeHeight + dimensions.columnGap);
    return {
      ...episode,
      index,
      lane,
      branchOwner: branchOwners.get(episode.episode_key) || null,
      x: direction === "wide" ? wideX : compactX,
      y: direction === "wide" ? wideY : compactY,
    };
  });
  const positionedByKey = new Map(
    positionedEpisodes.map((episode) => [episode.episode_key, episode]),
  );
  const relations = payload.relations.map((relation) => {
    const source = positionedByKey.get(relation.source_episode_key);
    const target = positionedByKey.get(relation.target_episode_key);
    const sourcePoint = direction === "wide"
      ? {
        x: source.x + dimensions.nodeWidth,
        y: source.y + dimensions.nodeHeight / 2,
      }
      : {
        x: source.x + dimensions.nodeWidth / 2,
        y: source.y + dimensions.nodeHeight,
      };
    const targetPoint = direction === "wide"
      ? { x: target.x, y: target.y + dimensions.nodeHeight / 2 }
      : { x: target.x + dimensions.nodeWidth / 2, y: target.y };
    const middle = direction === "wide"
      ? (sourcePoint.x + targetPoint.x) / 2
      : (sourcePoint.y + targetPoint.y) / 2;
    const path = direction === "wide"
      ? `M ${sourcePoint.x} ${sourcePoint.y} H ${middle} V ${targetPoint.y} H ${targetPoint.x}`
      : `M ${sourcePoint.x} ${sourcePoint.y} V ${middle} H ${targetPoint.x} V ${targetPoint.y}`;
    return {
      ...relation,
      path,
      labelX: direction === "wide" ? middle : (sourcePoint.x + targetPoint.x) / 2,
      labelY: direction === "wide" ? (sourcePoint.y + targetPoint.y) / 2 : middle,
    };
  });
  const laneCount = Math.max(1, nextLane);
  const width = direction === "wide"
    ? dimensions.stagePadding * 2
      + dimensions.nodeWidth * episodes.length
      + dimensions.columnGap * Math.max(0, episodes.length - 1)
    : dimensions.stagePadding * 2
      + dimensions.nodeWidth * laneCount
      + dimensions.laneGap * Math.max(0, laneCount - 1);
  const height = direction === "wide"
    ? dimensions.stagePadding * 2 + dimensions.axisSize
      + dimensions.nodeHeight * laneCount
      + dimensions.laneGap * Math.max(0, laneCount - 1)
    : dimensions.stagePadding * 2 + dimensions.axisSize
      + dimensions.nodeHeight * episodes.length
      + dimensions.columnGap * Math.max(0, episodes.length - 1);

  const branchGroups = {};
  positionedEpisodes.forEach((episode) => {
    if (!episode.branchOwner || episode.branchOwner === episode.episode_key) return;
    if (!branchGroups[episode.branchOwner]) branchGroups[episode.branchOwner] = [];
    branchGroups[episode.branchOwner].push(episode.episode_key);
  });
  return {
    orientation: direction,
    width,
    height,
    episodes: positionedEpisodes,
    relations,
    branchGroups,
  };
}

export function workflowPath(payload, selectedKey) {
  validateProjection(payload);
  if (!payload.episodes.some((episode) => episode.episode_key === selectedKey)) {
    return { episodeKeys: [], relationIds: [] };
  }
  const incoming = new Map();
  const outgoing = new Map();
  payload.relations.forEach((relation) => {
    const into = incoming.get(relation.target_episode_key) || [];
    into.push(relation);
    incoming.set(relation.target_episode_key, into);
    const out = outgoing.get(relation.source_episode_key) || [];
    out.push(relation);
    outgoing.set(relation.source_episode_key, out);
  });
  const episodeKeys = new Set([selectedKey]);
  const relationIds = new Set();
  const walk = (start, relationMap, neighborKey) => {
    const pending = [start];
    while (pending.length) {
      const current = pending.pop();
      (relationMap.get(current) || [])
        .slice()
        .sort((first, second) => first.relation_id.localeCompare(second.relation_id))
        .forEach((relation) => {
          const neighbor = relation[neighborKey];
          relationIds.add(relation.relation_id);
          if (!episodeKeys.has(neighbor)) {
            episodeKeys.add(neighbor);
            pending.push(neighbor);
          }
        });
    }
  };
  walk(selectedKey, incoming, "source_episode_key");
  walk(selectedKey, outgoing, "target_episode_key");
  return {
    episodeKeys: [...episodeKeys].sort(),
    relationIds: [...relationIds].sort(),
  };
}

function cssNumber(root, property, fallback) {
  const value = Number.parseFloat(
    window.getComputedStyle(root).getPropertyValue(property),
  );
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function geometryFromCss(root) {
  return {
    nodeWidth: cssNumber(root, "--workflow-node-width", DEFAULT_GEOMETRY.nodeWidth),
    nodeHeight: cssNumber(root, "--workflow-node-height", DEFAULT_GEOMETRY.nodeHeight),
    columnGap: cssNumber(root, "--workflow-column-gap", DEFAULT_GEOMETRY.columnGap),
    laneGap: cssNumber(root, "--workflow-lane-gap", DEFAULT_GEOMETRY.laneGap),
    stagePadding: cssNumber(root, "--workflow-stage-padding", DEFAULT_GEOMETRY.stagePadding),
    axisSize: cssNumber(root, "--workflow-axis-size", DEFAULT_GEOMETRY.axisSize),
  };
}

function svgNode(name, attributes = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
  return node;
}

function setControlsAvailable(controls, available) {
  controls?.querySelectorAll("button").forEach((button) => {
    button.disabled = !available;
  });
}

function failWorkflowMap(root, message) {
  root.classList.remove("is-enhanced");
  root.setAttribute("aria-busy", "false");
  const panel = root.querySelector(".workflow-map-panel");
  panel?.setAttribute("data-workflow-render-state", "unavailable");
  const status = root.querySelector("[data-workflow-render-message]");
  if (status) status.textContent = message;
  const label = root.querySelector("[data-workflow-layout-label]");
  if (label) label.textContent = "텍스트 흐름 사용 가능";
  const fallback = root.querySelector("[data-workflow-fallback]");
  if (fallback) fallback.open = true;
  setControlsAvailable(root.querySelector("[data-workflow-zoom-controls]"), false);
}

export function setupWorkflowMap(root) {
  const source = root.querySelector("[data-workflow-projection]");
  const viewport = root.querySelector("[data-workflow-viewport]");
  const scaler = root.querySelector("[data-workflow-scaler]");
  const stage = root.querySelector("[data-workflow-stage]");
  const edgeLayer = root.querySelector("[data-workflow-edge-layer]");
  const controls = root.querySelector("[data-workflow-zoom-controls]");
  const fallback = root.querySelector("[data-workflow-fallback]");
  if (!source || !viewport || !scaler || !stage || !edgeLayer || !controls || !fallback) {
    failWorkflowMap(root, "맵 구조를 읽을 수 없습니다. 아래 텍스트 흐름을 이용하세요.");
    return;
  }
  root.setAttribute("aria-busy", "true");
  root.querySelector(".workflow-map-panel")?.setAttribute(
    "data-workflow-render-state",
    "loading",
  );

  let payload;
  try {
    payload = JSON.parse(source.textContent);
    validateProjection(payload);
  } catch (_error) {
    failWorkflowMap(root, "작업 흐름 데이터를 읽을 수 없습니다. 아래 텍스트 흐름을 이용하세요.");
    return;
  }

  const zoomOut = controls.querySelector("[data-workflow-zoom-out]");
  const zoomReset = controls.querySelector("[data-workflow-zoom-reset]");
  const zoomIn = controls.querySelector("[data-workflow-zoom-in]");
  const zoomFit = controls.querySelector("[data-workflow-zoom-fit]");
  const liveStatus = root.querySelector("[data-workflow-live-status]");
  const layoutLabel = root.querySelector("[data-workflow-layout-label]");
  const renderMessage = root.querySelector("[data-workflow-render-message]");
  const returnButton = root.querySelector("[data-workflow-trace-return]");
  const traceScroll = root.querySelector(".workflow-trace-scroll");
  const correctionFeedback = root.querySelector(
    "[data-workflow-correction-feedback]",
  );
  const episodeByKey = new Map(
    payload.episodes.map((episode) => [episode.episode_key, episode]),
  );
  const episodeKeys = new Set(episodeByKey.keys());
  const restoration = consumeWorkflowRestorationSnapshot(
    window.sessionStorage,
    window.location.pathname,
  );
  let selectedKey = restoration && episodeKeys.has(restoration.selectedEpisodeKey)
    ? restoration.selectedEpisodeKey
    : payload.selected_episode_key;
  let inspectedRelationId = null;
  let layout;
  let scale = restoration?.scale || 1;
  let resizeFrame = null;
  const expandedBranches = new Set(
    (restoration?.expandedBranchKeys || []).filter((key) => episodeKeys.has(key)),
  );

  const isNarrow = () => window.matchMedia("(max-width: 700px)").matches;
  const orientation = () => (
    window.matchMedia("(max-width: 920px)").matches ? "compact" : "wide"
  );

  const updateScaleControls = () => {
    const percentage = `${Math.round(scale * 100)}%`;
    zoomReset.textContent = percentage;
    zoomReset.setAttribute(
      "aria-label",
      `현재 배율 ${percentage}, 100%로 재설정`,
    );
    zoomOut.disabled = isNarrow() || scale <= WORKFLOW_ZOOM_MIN;
    zoomIn.disabled = isNarrow() || scale >= WORKFLOW_ZOOM_MAX;
    zoomReset.disabled = isNarrow();
    zoomFit.disabled = isNarrow();
  };

  const applyScale = (requestedScale, clientX, clientY) => {
    if (isNarrow() || !layout) return;
    const nextScale = clampWorkflowZoom(requestedScale);
    const viewportRect = viewport.getBoundingClientRect();
    const pointerX = Number.isFinite(clientX)
      ? Math.min(viewport.clientWidth, Math.max(0, clientX - viewportRect.left))
      : viewport.clientWidth / 2;
    const pointerY = Number.isFinite(clientY)
      ? Math.min(viewport.clientHeight, Math.max(0, clientY - viewportRect.top))
      : viewport.clientHeight / 2;
    const nextScrollLeft = workflowAnchoredScroll(
      viewport.scrollLeft,
      pointerX,
      scale,
      nextScale,
    );
    const nextScrollTop = workflowAnchoredScroll(
      viewport.scrollTop,
      pointerY,
      scale,
      nextScale,
    );
    scale = nextScale;
    stage.style.transform = `scale(${scale})`;
    scaler.style.width = `${layout.width * scale}px`;
    scaler.style.height = `${layout.height * scale}px`;
    updateScaleControls();
    window.requestAnimationFrame(() => {
      viewport.scrollLeft = nextScrollLeft;
      viewport.scrollTop = nextScrollTop;
    });
  };

  const branchOwnerFor = (episodeKey) => (
    layout.episodes.find((episode) => episode.episode_key === episodeKey)?.branchOwner || null
  );

  const visibleKeys = () => new Set(
    layout.episodes
      .filter((episode) => (
        !episode.branchOwner
        || episode.branchOwner === episode.episode_key
        || expandedBranches.has(episode.branchOwner)
      ))
      .map((episode) => episode.episode_key),
  );

  const updateBranchVisibility = () => {
    const visible = visibleKeys();
    root.querySelectorAll("[data-workflow-episode-position]").forEach((node) => {
      node.hidden = !visible.has(node.dataset.episodeKey);
    });
    root.querySelectorAll("[data-workflow-relation]").forEach((node) => {
      node.hidden = !visible.has(node.dataset.sourceEpisodeKey)
        || !visible.has(node.dataset.targetEpisodeKey);
    });
    Object.entries(layout.branchGroups).forEach(([branchRoot, members]) => {
      const rootNode = root.querySelector(
        `[data-workflow-episode-position][data-episode-key="${CSS.escape(branchRoot)}"]`,
      );
      const toggle = rootNode?.querySelector("[data-workflow-branch-toggle]");
      if (!toggle) return;
      toggle.hidden = members.length === 0;
      const expanded = expandedBranches.has(branchRoot);
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.textContent = expanded
        ? `branch ${members.length}개 접기`
        : `branch ${members.length}개 펼치기`;
      const focusedInside = selectedKey !== branchRoot && members.includes(selectedKey);
      toggle.disabled = expanded && focusedInside;
      if (focusedInside) {
        toggle.setAttribute("aria-label", "선택한 Episode가 있어 branch를 접을 수 없습니다");
      } else {
        toggle.removeAttribute("aria-label");
      }
    });
  };

  const updatePath = () => {
    const path = workflowPath(payload, selectedKey);
    const activeEpisodes = new Set(path.episodeKeys);
    const activeRelations = new Set(path.relationIds);
    root.querySelectorAll("[data-workflow-episode-position]").forEach((position) => {
      const selected = position.dataset.episodeKey === selectedKey;
      const card = position.querySelector("[data-workflow-episode-card]");
      const button = position.querySelector("[data-workflow-episode]");
      const label = position.querySelector("[data-workflow-selected-label]");
      card?.classList.toggle("is-selected", selected);
      position.classList.toggle("is-related", activeEpisodes.has(position.dataset.episodeKey));
      position.classList.toggle("is-dimmed", !activeEpisodes.has(position.dataset.episodeKey));
      button?.setAttribute("aria-pressed", String(selected));
      if (label) label.hidden = !selected;
    });
    root.querySelectorAll("[data-workflow-relation]").forEach((relation) => {
      const active = activeRelations.has(relation.dataset.relationId);
      relation.classList.toggle("is-related", active);
      relation.classList.toggle("is-dimmed", !active);
    });
  };

  const showEpisodeTrace = () => {
    root.querySelectorAll("[data-workflow-episode-trace]").forEach((panel) => {
      panel.hidden = panel.dataset.workflowEpisodeTrace !== selectedKey;
    });
    root.querySelectorAll("[data-workflow-relation-trace]").forEach((panel) => {
      panel.hidden = true;
    });
    inspectedRelationId = null;
    returnButton.hidden = true;
  };

  const announceEpisode = () => {
    const episode = episodeByKey.get(selectedKey);
    if (liveStatus && episode) {
      liveStatus.textContent = `${episode.title} Episode를 선택했습니다.`;
    }
  };

  const selectEpisode = (
    episodeKey,
    { pushHistory = false, focusNode = false, announce = true } = {},
  ) => {
    const episode = episodeByKey.get(episodeKey);
    if (!episode) return false;
    const owner = branchOwnerFor(episodeKey);
    if (owner) expandedBranches.add(owner);
    selectedKey = episodeKey;
    root.dataset.selectedEpisodeKey = episodeKey;
    updateBranchVisibility();
    updatePath();
    showEpisodeTrace();
    if (pushHistory) {
      const destination = new URL(episode.workflow_destination, window.location.href);
      window.history.pushState(
        { ...window.history.state, workflowFocus: episodeKey },
        "",
        destination.pathname,
      );
    }
    if (focusNode) {
      const node = root.querySelector(
        `[data-workflow-episode-position][data-episode-key="${CSS.escape(episodeKey)}"] [data-workflow-episode]`,
      );
      node?.focus({ preventScroll: true });
      node?.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
    if (announce) announceEpisode();
    return true;
  };

  const inspectRelation = (relationId, { focus = false } = {}) => {
    const panel = root.querySelector(
      `[data-workflow-relation-trace="${CSS.escape(relationId)}"]`,
    );
    if (!panel) return;
    root.querySelectorAll("[data-workflow-episode-trace]").forEach((item) => {
      item.hidden = true;
    });
    root.querySelectorAll("[data-workflow-relation-trace]").forEach((item) => {
      item.hidden = item !== panel;
    });
    inspectedRelationId = relationId;
    returnButton.hidden = false;
    if (liveStatus) {
      liveStatus.textContent = `${panel.querySelector("h3")?.textContent || "관계"} 근거를 표시합니다.`;
    }
    if (focus) panel.querySelector("h3")?.setAttribute("tabindex", "-1");
    if (focus) panel.querySelector("h3")?.focus({ preventScroll: false });
  };

  const drawRelations = () => {
    edgeLayer.replaceChildren();
    edgeLayer.setAttribute("viewBox", `0 0 ${layout.width} ${layout.height}`);
    edgeLayer.setAttribute("width", String(layout.width));
    edgeLayer.setAttribute("height", String(layout.height));
    layout.relations.forEach((relation) => {
      const group = svgNode("g", {
        class: `workflow-relation-edge ${relation.kind} authority-${relation.authority}`,
        tabindex: "0",
        role: "button",
        "aria-label": `${relation.label}, ${relation.authority_label}, 관계 근거 보기`,
        "data-workflow-relation": "",
        "data-relation-id": relation.relation_id,
        "data-source-episode-key": relation.source_episode_key,
        "data-target-episode-key": relation.target_episode_key,
        "data-workflow-authority": relation.authority,
      });
      group.append(
        svgNode("path", { class: "workflow-edge-hit", d: relation.path }),
        svgNode("path", { class: "workflow-edge-line", d: relation.path }),
      );
      const label = svgNode("text", {
        class: "workflow-edge-label",
        x: String(relation.labelX),
        y: String(relation.labelY),
        "text-anchor": "middle",
      });
      const kind = svgNode("tspan", { x: String(relation.labelX), dy: "0" });
      kind.textContent = relation.label;
      const authority = svgNode("tspan", {
        x: String(relation.labelX),
        dy: "1.35em",
      });
      authority.textContent = relation.authority_label;
      label.append(kind, authority);
      group.append(label);
      group.addEventListener("click", () => inspectRelation(relation.relation_id, { focus: true }));
      group.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        inspectRelation(relation.relation_id, { focus: true });
      });
      edgeLayer.append(group);
    });
  };

  const renderLayout = () => {
    const nextOrientation = orientation();
    layout = buildWorkflowLayout(payload, nextOrientation, geometryFromCss(root));
    stage.dataset.orientation = nextOrientation;
    stage.style.width = `${layout.width}px`;
    stage.style.height = `${layout.height}px`;
    scaler.style.width = `${layout.width * scale}px`;
    scaler.style.height = `${layout.height * scale}px`;
    stage.style.transform = `scale(${scale})`;
    layout.episodes.forEach((episode) => {
      const position = root.querySelector(
        `[data-workflow-episode-position][data-episode-key="${CSS.escape(episode.episode_key)}"]`,
      );
      if (!position) throw new Error("Workflow Episode DOM is incomplete");
      position.style.transform = `translate(${episode.x}px, ${episode.y}px)`;
      position.dataset.workflowLane = String(episode.lane);
      position.dataset.workflowBranchOwner = episode.branchOwner || "";
    });
    drawRelations();
    const selectedOwner = branchOwnerFor(selectedKey);
    if (selectedOwner) expandedBranches.add(selectedOwner);
    if (layout.branchGroups[selectedKey]) expandedBranches.add(selectedKey);
    updateBranchVisibility();
    updatePath();
    layoutLabel.textContent = nextOrientation === "wide"
      ? "시간축 · 고정 branch lane"
      : "세로 시간축 · 고정 branch lane";
    fallback.open = isNarrow();
    fallback.dataset.workflowAutoOpen = isNarrow() ? "true" : "false";
    updateScaleControls();
  };

  const correctionSnapshot = () => ({
    version: WORKFLOW_RESTORE_VERSION,
    pathname: window.location.pathname,
    createdAt: Date.now(),
    selectedEpisodeKey: selectedKey,
    expandedBranchKeys: [...expandedBranches],
    scale,
    viewportScrollLeft: viewport.scrollLeft,
    viewportScrollTop: viewport.scrollTop,
    traceScrollTop: traceScroll?.scrollTop || 0,
    outerScrollX: window.scrollX,
    outerScrollY: window.scrollY,
    openDisclosureKeys: [...root.querySelectorAll(
      "[data-workflow-disclosure-key][open]",
    )].map((item) => item.dataset.workflowDisclosureKey),
  });

  const showCorrectionFailure = (form, response, status) => {
    const feedback = form.querySelector("[data-workflow-correction-form-feedback]");
    const reload = form.querySelector("[data-workflow-correction-reload]");
    const message = typeof response?.message === "string" && response.message.length <= 240
      ? response.message
      : "교정을 적용하지 못했습니다. 현재 흐름은 바뀌지 않았습니다.";
    if (feedback) {
      feedback.textContent = message;
      feedback.hidden = false;
    }
    if (
      reload
      && status === 409
      && WORKFLOW_PATH.test(response?.reload_url || "")
    ) {
      reload.href = response.reload_url;
      reload.hidden = false;
    }
  };

  root.addEventListener("change", (event) => {
    const select = event.target.closest("[data-workflow-close-reason]");
    if (!select) return;
    const preview = select.closest("[data-workflow-correction-action]")
      ?.querySelector("[data-workflow-close-reason-preview]");
    if (preview) {
      preview.textContent = select.selectedOptions[0]?.textContent
        ?.replace(/ \(현재\)$/, "") || "종료 사유";
    }
  });

  root.addEventListener("click", (event) => {
    const cancel = event.target.closest("[data-workflow-correction-cancel]");
    if (!cancel) return;
    const disclosure = cancel.closest("[data-workflow-correction-action]");
    if (!disclosure) return;
    disclosure.open = false;
    disclosure.querySelector(":scope > summary")?.focus({ preventScroll: false });
  });

  root.addEventListener("submit", async (event) => {
    const form = event.target.closest("[data-workflow-correction-form]");
    if (!form) return;
    event.preventDefault();
    const fieldset = form.querySelector("fieldset");
    const feedback = form.querySelector("[data-workflow-correction-form-feedback]");
    const reload = form.querySelector("[data-workflow-correction-reload]");
    if (!fieldset || fieldset.disabled) return;
    const formBody = new URLSearchParams(new FormData(form));
    const restorationSnapshot = correctionSnapshot();
    fieldset.disabled = true;
    form.setAttribute("aria-busy", "true");
    if (feedback) {
      feedback.hidden = true;
      feedback.textContent = "";
    }
    if (reload) reload.hidden = true;
    let response;
    let body;
    try {
      const correctionUrl = new URL(
        form.getAttribute("action"), window.location.href,
      );
      response = await window.fetch(correctionUrl.href, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-LocalBrain-Partial": "workflow-correction" },
        body: formBody,
      });
      body = await response.json();
    } catch (_error) {
      fieldset.disabled = false;
      form.setAttribute("aria-busy", "false");
      showCorrectionFailure(form, null, 0);
      return;
    }
    const result = correctionResponse(body, response.status, episodeKeys);
    if (result) {
      storeWorkflowRestorationSnapshot(
        window.sessionStorage,
        {
          ...restorationSnapshot,
          focusKind: result.focusKind,
          focusKey: result.focusKey,
          resultCode: result.code,
        },
      );
      window.location.reload();
      return;
    }
    fieldset.disabled = false;
    form.setAttribute("aria-busy", "false");
    showCorrectionFailure(form, body, response.status);
  });

  root.addEventListener("click", (event) => {
    const episodeButton = event.target.closest("[data-workflow-episode]");
    if (episodeButton) {
      const position = episodeButton.closest("[data-episode-key]");
      if (position && position.dataset.episodeKey !== selectedKey) {
        selectEpisode(position.dataset.episodeKey, { pushHistory: true, announce: true });
      }
      return;
    }
    const branchButton = event.target.closest("[data-workflow-branch-toggle]");
    if (branchButton) {
      const branchRoot = branchButton.closest("[data-episode-key]")?.dataset.episodeKey;
      if (!branchRoot || branchButton.disabled) return;
      if (expandedBranches.has(branchRoot)) expandedBranches.delete(branchRoot);
      else expandedBranches.add(branchRoot);
      updateBranchVisibility();
      updatePath();
      if (liveStatus) {
        liveStatus.textContent = expandedBranches.has(branchRoot)
          ? "bounded branch를 펼쳤습니다."
          : "bounded branch를 접었습니다.";
      }
      return;
    }
    const relationButton = event.target.closest("[data-workflow-relation-target]");
    if (relationButton) {
      inspectRelation(relationButton.dataset.workflowRelationTarget, { focus: true });
      return;
    }
    const episodeTarget = event.target.closest("[data-workflow-episode-target]");
    if (episodeTarget) {
      selectEpisode(episodeTarget.dataset.workflowEpisodeTarget, {
        pushHistory: true,
        focusNode: true,
      });
    }
  });

  returnButton.addEventListener("click", () => {
    if (!inspectedRelationId) return;
    showEpisodeTrace();
    root.querySelector(
      `[data-workflow-episode-position][data-episode-key="${CSS.escape(selectedKey)}"] [data-workflow-episode]`,
    )?.focus({ preventScroll: false });
  });

  viewport.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
    const order = layout.episodes.map((episode) => episode.episode_key);
    const current = order.indexOf(selectedKey);
    const delta = event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 1;
    const next = Math.min(order.length - 1, Math.max(0, current + delta));
    if (next === current) return;
    event.preventDefault();
    selectEpisode(order[next], { pushHistory: true, focusNode: true });
  });

  zoomOut.addEventListener("click", () => applyScale(scale / WORKFLOW_ZOOM_BUTTON_FACTOR));
  zoomReset.addEventListener("click", () => applyScale(1));
  zoomIn.addEventListener("click", () => applyScale(scale * WORKFLOW_ZOOM_BUTTON_FACTOR));
  zoomFit.addEventListener("click", () => {
    const style = window.getComputedStyle(viewport);
    const availableWidth = Math.max(
      1,
      viewport.clientWidth
        - (Number.parseFloat(style.paddingLeft) || 0)
        - (Number.parseFloat(style.paddingRight) || 0),
    );
    const availableHeight = Math.max(
      1,
      viewport.clientHeight
        - (Number.parseFloat(style.paddingTop) || 0)
        - (Number.parseFloat(style.paddingBottom) || 0),
    );
    applyScale(Math.min(1, availableWidth / layout.width, availableHeight / layout.height));
  });
  viewport.addEventListener(
    "wheel",
    (event) => {
      if (!workflowWheelOwnsZoom(event) || isNarrow()) return;
      event.preventDefault();
      applyScale(
        workflowZoomFromWheel(scale, event.deltaY),
        event.clientX,
        event.clientY,
      );
    },
    { passive: false },
  );

  let gestureScale = 1;
  viewport.addEventListener("gesturestart", (event) => {
    if (isNarrow()) return;
    gestureScale = scale;
    event.preventDefault();
  }, { passive: false });
  viewport.addEventListener("gesturechange", (event) => {
    if (isNarrow()) return;
    event.preventDefault();
    applyScale(gestureScale * event.scale, event.clientX, event.clientY);
  }, { passive: false });

  window.addEventListener("popstate", () => {
    const destination = new URL(window.location.href);
    const match = destination.pathname.match(/^\/sessions\/(\d+)\/workflow$/);
    if (!match) {
      window.location.reload();
      return;
    }
    const episode = payload.episodes.find(
      (item) => String(item.session_id) === match[1],
    );
    if (!episode) {
      window.location.reload();
      return;
    }
    selectEpisode(episode.episode_key, { focusNode: true, announce: true });
  });

  window.addEventListener("resize", () => {
    if (resizeFrame !== null) window.cancelAnimationFrame(resizeFrame);
    resizeFrame = window.requestAnimationFrame(() => {
      resizeFrame = null;
      try {
        renderLayout();
      } catch (_error) {
        failWorkflowMap(root, "맵을 다시 배치할 수 없습니다. 아래 텍스트 흐름을 이용하세요.");
      }
    });
  });

  try {
    const selectedOwner = (() => {
      const initial = buildWorkflowLayout(payload, orientation(), geometryFromCss(root));
      return initial.episodes.find(
        (episode) => episode.episode_key === selectedKey,
      )?.branchOwner;
    })();
    if (selectedOwner) expandedBranches.add(selectedOwner);
    root.classList.add("is-enhanced");
    renderLayout();
    root.setAttribute("aria-busy", "false");
    root.querySelector(".workflow-map-panel")?.setAttribute(
      "data-workflow-render-state",
      "ready",
    );
    renderMessage.textContent = "고정 배치가 준비되었습니다.";
    setControlsAvailable(controls, !isNarrow());
    updateScaleControls();
    showEpisodeTrace();
    window.history.replaceState(
      { ...window.history.state, workflowFocus: selectedKey },
      "",
    );
    if (restoration) {
      restoration.openDisclosureKeys.forEach((key) => {
        const disclosure = root.querySelector(
          `[data-workflow-disclosure-key="${CSS.escape(key)}"]`,
        );
        if (disclosure) disclosure.open = true;
      });
      if (restoration.focusKind === "relation") {
        inspectRelation(restoration.focusKey);
      }
      if (correctionFeedback) {
        correctionFeedback.textContent = WORKFLOW_RESULT_MESSAGES[restoration.resultCode];
        correctionFeedback.classList.add("success");
        correctionFeedback.hidden = false;
      }
      const restoreInteractionState = () => {
        window.requestAnimationFrame(() => {
          const focusTarget = restoration.focusKind === "relation"
            ? root.querySelector(
              `[data-workflow-relation-trace="${CSS.escape(restoration.focusKey)}"] [data-workflow-assertion-summary]`,
            ) || root.querySelector(
              `[data-workflow-relation-trace="${CSS.escape(restoration.focusKey)}"] h3`,
            )
            : root.querySelector(
              `[data-workflow-episode-trace="${CSS.escape(restoration.focusKey)}"] [data-workflow-assertion-summary]`,
            ) || root.querySelector(
              `[data-workflow-episode-position][data-episode-key="${CSS.escape(restoration.focusKey)}"] [data-workflow-episode]`,
            );
          focusTarget?.focus({ preventScroll: true });
          window.requestAnimationFrame(() => {
            viewport.scrollLeft = restoration.viewportScrollLeft;
            viewport.scrollTop = restoration.viewportScrollTop;
            if (traceScroll) traceScroll.scrollTop = restoration.traceScrollTop;
            window.scrollTo(restoration.outerScrollX, restoration.outerScrollY);
            root.dataset.workflowRestorationState = "complete";
          });
        });
      };
      if (document.readyState === "complete") {
        restoreInteractionState();
      } else {
        window.addEventListener("load", restoreInteractionState, { once: true });
      }
    }
  } catch (_error) {
    failWorkflowMap(root, "작업 흐름 맵을 렌더링할 수 없습니다. 아래 텍스트 흐름을 이용하세요.");
  }
}

if (typeof document !== "undefined") {
  const root = document.querySelector('[data-workflow-map][data-workflow-status="ready"]');
  if (root) setupWorkflowMap(root);
}
