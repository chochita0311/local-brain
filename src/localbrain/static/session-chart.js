(() => {
  const root = document.querySelector('[data-session-chart]');
  if (!root) return;
  const fallback = root.querySelector('[data-chart-fallback]');
  const explorer = root.querySelector('[data-chart-explorer]');
  if (!explorer) { fallback.hidden = true; return; }

  try {
    const records = JSON.parse(root.querySelector('[data-chart-inventory]').textContent);
    const pinnedIds = new Set(JSON.parse(root.querySelector('[data-chart-pins]').textContent).filter(id => Number.isSafeInteger(id) && id > 0));
    const viewport = root.querySelector('[data-chart-viewport]');
    const nodes = root.querySelector('[data-chart-nodes]');
    const eventLayer = root.querySelector('[data-chart-events]');
    const axis = root.querySelector('[data-chart-axis]');
    const grid = root.querySelector('[data-chart-grid]');
    const projectAxis = root.querySelector('[data-chart-project-axis]');
    const guides = root.querySelector('[data-chart-guides]');
    const preview = root.querySelector('[data-chart-preview]');
    const hoverPreview = preview.cloneNode(true);
    hoverPreview.id = 'session-chart-hover-preview';
    hoverPreview.removeAttribute('data-chart-preview');
    hoverPreview.setAttribute('data-chart-hover-preview', '');
    hoverPreview.setAttribute('aria-label', '세션 미리보기');
    hoverPreview.tabIndex = 0;
    hoverPreview.classList.add('is-hover-preview');
    for (const selector of ['[data-chart-close]', '.session-chart-preview-actions', '[data-chart-activity-status]', '.session-chart-stack-selector select']) hoverPreview.querySelector(selector).remove();
    preview.parentElement.append(hoverPreview);
    const activityButton = root.querySelector('[data-chart-activity]');
    const activityStatus = root.querySelector('[data-chart-activity-status]');
    const status = root.querySelector('[data-chart-status]');
    const focusButton = root.querySelector('[data-chart-action="focus"]');
    const stackSelector = root.querySelector('[data-chart-stack-selector]');
    const stackSelect = root.querySelector('[data-chart-stack-select]');
    const projectFilter = root.querySelector('[data-chart-project-filter]');
    const projectOptions = root.querySelector('[data-chart-project-options]');
    const projectAll = root.querySelector('[data-chart-project-all]');
    const projectSearch = root.querySelector('[data-chart-project-search]');
    const preferenceError = root.querySelector('[data-chart-project-save-error]');
    const preferenceMessage = root.querySelector('[data-chart-project-save-message]');
    const preferenceRetry = root.querySelector('[data-chart-project-save-retry]');
    const style = getComputedStyle(root);
    const cssNumber = (name) => parseFloat(style.getPropertyValue(name));
    const hoverExitDelay = cssNumber('--motion-state-duration');
    const cardWidth = cssNumber('--workflow-node-width') - cssNumber('--space-40');
    const gap = cssNumber('--space-card');
    const pointSize = cssNumber('--space-section');
    const hitSize = cssNumber('--control-min-height-touch');
    const nodeInset = cssNumber('--space-compact') + cssNumber('--border-width-control');
    const anchor = hitSize / 2;
    const axisHeight = cssNumber('--space-40');
    const projectGap = cssNumber('--space-control-gap');
    const trackStep = hitSize + projectGap;
    const projectHeadingHeight = hitSize;
    const verticalStep = trackStep * 2;
    const DAY = 86400000;
    const BASE_SCALE = 160 / DAY;
    const MAX_SCALE = 0.01;
    const byId = new Map();
    const dated = [];
    const undated = [];
    const dateLabel = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' });
    const yearDate = new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    const fullDate = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
    const tickTime = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    for (const record of records) {
      if (!Number.isSafeInteger(record.id) || record.id <= 0 || byId.has(record.id)) continue;
      const item = { ...record, pinned: pinnedIds.has(record.id), time: record.observed_at ? Date.parse(record.observed_at) : NaN };
      const first = Date.parse(record.first_observed_at || record.started_at || '');
      item.first = Number.isFinite(first) ? Math.min(first, item.time) : item.time;
      byId.set(item.id, item);
      (Number.isFinite(item.time) ? dated : undated).push(item);
    }
    dated.sort((a, b) => a.time - b.time || a.id - b.id);
    const origin = dated.length ? dated.reduce((first, item) => Math.min(first, item.first), Infinity) : 0;
    const storageScope = `${root.dataset.source}:${root.dataset.workspace}`;
    const storageKey = `localbrain:session-chart:4:${storageScope}`;
    const projectStorageKey = `localbrain:session-chart-projects:1:${storageScope}`;
    const preferenceParams = new URLSearchParams({ source: root.dataset.source });
    if (root.dataset.workspace) preferenceParams.set('workspace', root.dataset.workspace);
    const preferenceUrl = `/sessions/chart/project-visibility?${preferenceParams}`;
    let scale = BASE_SCALE;
    let rowScale = 1;
    let cameraX = 0;
    let cameraY = 0;
    let selected = null;
    let hovered = null;
    let hoverBlocked = null;
    let lastPointer = null;
    let hoverDismissedAt = null;
    let hoverExitTimer = 0;
    let activity = null;
    let activityController = null;
    let activityState = 'idle';
    let width = 0;
    let labelWidth = 0;
    let height = 0;
    let worldHeight = 0;
    let frame = 0;
    let failed = false;
    const buttons = new Map();
    const projects = [];
    const hiddenProjects = new Set();
    let visibleDated = dated;
    let visibleUndated = undated;
    let stacks = new Map();
    let stackSignature = '';
    const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
    const offsets = new Map();
    let motionFrame = 0;
    let motionTime = 0;
    let panReturn = null;
    let drag = null;
    let suppressClick = false;
    let saved = null;
    let projectPreference = null;
    let preferencePending = null;
    let preferenceSaving = false;
    let preferenceSaveFailed = false;
    const serverPreference = JSON.parse(root.querySelector('[data-chart-project-preference]').textContent);
    const serverKeys = validProjectKeys(serverPreference.hidden_projects);
    let preferenceLoadFailed = !serverPreference.available || (serverPreference.hidden_projects !== null && serverKeys === null);
    const canMigratePreference = !preferenceLoadFailed && serverPreference.hidden_projects === null;
    try {
      saved = JSON.parse(sessionStorage.getItem(storageKey));
      if (!saved) {
        const previous = JSON.parse(sessionStorage.getItem(`localbrain:session-chart:3:${storageScope}`)) || JSON.parse(sessionStorage.getItem(`localbrain:session-chart:2:${storageScope}`)) || JSON.parse(sessionStorage.getItem(`localbrain:session-chart:1:${storageScope}`));
        // Earlier spacing used a different Y coordinate system.
        if (previous) saved = { centerTime: previous.centerTime, scale: previous.scale, selected: previous.selected };
      }
    } catch (_) { /* Private browsing may disable storage. */ }
    if (!preferenceLoadFailed && serverKeys !== null) {
      projectPreference = serverKeys;
      clearLegacyPreference();
    } else {
      try {
        const preference = JSON.parse(localStorage.getItem(projectStorageKey));
        projectPreference = preference ? validProjectKeys(preference.hiddenProjects) : null;
      } catch (_) { /* Legacy choices are optional migration input. */ }
    }
    if (saved && byId.has(saved.selected)) selected = byId.get(saved.selected);
    if (saved && Number.isFinite(saved.scale) && saved.scale > 0) scale = Math.min(saved.scale, MAX_SCALE);
    if (saved && Number.isFinite(saved.rowScale) && saved.rowScale > 0) rowScale = Math.min(1, saved.rowScale);

    function sessionUrl(item) {
      const params = new URLSearchParams({ display: 'chart' });
      if (root.dataset.source !== 'all') params.set('source', root.dataset.source);
      if (root.dataset.workspace) params.set('workspace', root.dataset.workspace);
      if (Number(root.dataset.listPage) > 1) params.set('page', root.dataset.listPage);
      return `/sessions/${item.id}?${params}`;
    }
    function save() {
      if (!width) return;
      try {
        sessionStorage.setItem(storageKey, JSON.stringify({
          centerTime: origin + (boundedCameraX(cameraX) + width / 2) / scale,
          scale, y: cameraY, rowScale, selected: selected ? selected.id : null,
          hiddenProjects: [...hiddenProjects],
          page: Number(root.dataset.listPage)
        }));
      } catch (_) { /* Navigation works without persistence. */ }
    }
    function validProjectKeys(value) {
      if (!Array.isArray(value) || value.length > 2000 || value.some(key => typeof key !== 'string' || key.length > 4096)) return null;
      const keys = [...new Set(value)];
      return new TextEncoder().encode(JSON.stringify(keys)).length <= 60000 ? keys : null;
    }
    function clearLegacyPreference() {
      try { localStorage.removeItem(projectStorageKey); } catch (_) { /* DB confirmation does not require browser storage. */ }
    }
    function showPreferenceError(kind) {
      preferenceError.hidden = !kind;
      preferenceMessage.textContent = kind === 'load' ? '프로젝트 설정을 불러오지 못했습니다.' : kind === 'save' ? '프로젝트 선택을 저장하지 못했습니다.' : '';
      preferenceRetry.textContent = kind === 'load' ? '다시 불러오기' : '다시 저장';
    }
    function saveProjectPreference(onlyIfMissing = false) {
      const knownKeys = new Set(projects.map(project => project.key));
      // Keep hidden folders that are temporarily absent from the scoped inventory.
      projectPreference = [...new Set([
        ...(projectPreference || []).filter(key => !knownKeys.has(key)),
        ...hiddenProjects
      ])];
      preferencePending = { hidden_projects: projectPreference.slice(), only_if_missing: onlyIfMissing };
      preferenceSaveFailed = false;
      flushProjectPreference();
    }
    async function flushProjectPreference() {
      if (preferenceSaving || preferenceSaveFailed || !preferencePending) return;
      preferenceSaving = true;
      while (preferencePending) {
        const writing = preferencePending;
        preferencePending = null;
        try {
          if (validProjectKeys(writing.hidden_projects) === null) throw new Error('Project preference exceeds the local limit');
          const response = await fetch(preferenceUrl, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(writing), keepalive: true
          });
          if (!response.ok) throw new Error('Project preference save failed');
          const confirmed = validProjectKeys((await response.json()).hidden_projects);
          if (confirmed === null) throw new Error('Invalid Project preference response');
          preferenceLoadFailed = false;
          clearLegacyPreference(); showPreferenceError(null);
          if (!preferencePending) {
            projectPreference = confirmed;
            if (writing.only_if_missing) {
              hiddenProjects.clear();
              const knownKeys = new Set(projects.map(project => project.key));
              for (const key of confirmed) if (knownKeys.has(key)) hiddenProjects.add(key);
              applyProjectFilter(false);
            }
          }
        } catch (_) {
          // Preserve the newest intent, including changes made during this request.
          if (!preferencePending) preferencePending = writing;
          preferenceSaveFailed = true;
          showPreferenceError('save');
          break;
        }
      }
      preferenceSaving = false;
    }
    function activityTimes() {
      if (!activity) return [];
      return activity.timestamps.length ? activity.timestamps : activity.metadata_times.map(item => item.at);
    }
    function bounds() {
      let first = visibleDated.length ? visibleDated.reduce((time, item) => Math.min(time, item.first), Infinity) : origin;
      let last = visibleDated.length ? visibleDated[visibleDated.length - 1].time : first;
      for (const value of activityTimes()) {
        const time = Date.parse(value);
        if (Number.isFinite(time)) { first = Math.min(first, time); last = Math.max(last, time); }
      }
      return { first, last };
    }
    function minScale() {
      const { first, last } = bounds();
      return Math.min(BASE_SCALE, Math.max(1e-12, (usablePlotWidth() - edgeInset() * 2 - hitSize * rowScale) / Math.max(DAY, last - first)));
    }
    function usablePlotWidth() {
      return !preview.hidden && getComputedStyle(preview).position === 'absolute' ? Math.max(hitSize, width - preview.offsetWidth - gap * 3) : width;
    }
    function minRowScale() {
      return Math.min(1, Math.max(1e-6, height / Math.max(1, worldHeight)));
    }
    function edgeInset() {
      const usable = usablePlotWidth();
      return Math.min(gap * 4, usable * 0.2, Math.max(0, (usable - hitSize * rowScale) / 2));
    }
    function panStretchLimit() {
      return Math.min(hitSize * 2, usablePlotWidth() / 2);
    }
    function cameraLimits() {
      const { first, last } = bounds();
      const inset = edgeInset();
      const min = (first - origin) * scale - anchor * rowScale - inset;
      return { min, max: Math.max(min, (last - origin) * scale + (hitSize - anchor) * rowScale - usablePlotWidth() + inset) };
    }
    function boundedCameraX(value) {
      const { min, max } = cameraLimits();
      return Math.max(min, Math.min(max, value));
    }
    function resistedCameraX(value) {
      const bounded = boundedCameraX(value);
      const delta = value - bounded;
      return bounded + delta / (1 + Math.abs(delta) / panStretchLimit());
    }
    function clampCamera() {
      const { min, max } = cameraLimits();
      const stretching = panReturn || (drag && !drag.item && drag.moved);
      const stretch = panStretchLimit();
      cameraX = stretching ? Math.max(min - stretch, Math.min(max + stretch, cameraX)) : boundedCameraX(cameraX);
      cameraY = Math.min(Math.max(0, worldHeight * rowScale - height), Math.max(0, cameraY));
    }
    function initializeHomes() {
      const groups = new Map();
      const compare = (a, b) => a.toLowerCase() < b.toLowerCase() ? -1 : a.toLowerCase() > b.toLowerCase() ? 1 : 0;
      // HEAD is a checkout reference; raw branch metadata stays available in preview.
      const chartBranch = item => item.git_branch === 'HEAD' ? null : item.git_branch || null;
      for (const item of byId.values()) {
        const key = item.project_key ?? item.cwd_raw ?? '';
        if (!groups.has(key)) groups.set(key, {
          key, name: item.project_name || key.split('/').filter(Boolean).pop() || '실행 폴더 없음',
          path: item.project_path || key, items: [], tracks: []
        });
        groups.get(key).items.push(item);
      }
      projects.push(...[...groups.values()].sort((a, b) => Number(!a.key) - Number(!b.key) || compare(a.name, b.name) || compare(a.key, b.key) || (a.key < b.key ? -1 : a.key > b.key ? 1 : 0)));
      for (const project of projects) {
        const branches = new Set(project.items.map(chartBranch));
        const hasBranches = [...branches].some(Boolean);
        const baseline = branches.has('master') ? 'master' : branches.has('main') ? 'main' : null;
        const rootTrack = { branch: baseline, name: baseline || (hasBranches ? '기준선' : ''), items: [], root: true };
        project.tracks.push(rootTrack);
        const byBranch = new Map();
        if (baseline || !hasBranches) byBranch.set(baseline, rootTrack);
        for (const branch of [...branches].filter(name => !byBranch.has(name)).sort((a, b) => Number(!a) - Number(!b) || compare(a || '', b || ''))) {
          const track = { branch, name: branch || '브랜치 없음', items: [], root: false };
          project.tracks.push(track); byBranch.set(branch, track);
        }
        for (const item of project.items) byBranch.get(chartBranch(item)).items.push(item);
        for (const track of project.tracks) {
          track.key = JSON.stringify([project.key, track.root, track.branch]);
          const times = track.items.filter(item => Number.isFinite(item.time));
          track.first = times.length ? times.reduce((first, item) => Math.min(first, item.first), Infinity) : NaN;
          for (const item of track.items) { item.track = track; item.project = project; }
        }
        const times = project.items.filter(item => Number.isFinite(item.time));
        project.first = times.length ? times.reduce((first, item) => Math.min(first, item.first), Infinity) : NaN;
      }
      if (projectPreference === null && saved) projectPreference = validProjectKeys(saved.hiddenProjects);
      const savedProjects = projectPreference || [];
      if (savedProjects.length) {
        const keys = new Set(projects.map(project => project.key));
        for (const key of savedProjects) if (typeof key === 'string' && keys.has(key)) hiddenProjects.add(key);
      }
      if (selected && hiddenProjects.has(selected.project.key)) selected = null;
      layoutProjects();
    }
    function layoutProjects() {
      let cursor = 0;
      for (const project of projects) {
        project.visible = !hiddenProjects.has(project.key);
        if (!project.visible) continue;
        project.top = cursor;
        for (const [index, track] of project.tracks.entries()) {
          track.y = cursor + projectHeadingHeight + index * trackStep;
          for (const item of track.items) item.y = track.y;
        }
        project.bottom = cursor + projectHeadingHeight + project.tracks.length * trackStep + projectGap;
        cursor = project.bottom;
      }
      worldHeight = cursor;
      visibleDated = dated.filter(item => item.project.visible);
      visibleUndated = undated.filter(item => item.project.visible);
    }
    function layout() {
      for (const item of dated) item.x = (item.time - origin) * scale;
    }
    function paintOffset(id) {
      const button = buttons.get(id);
      if (!button) return;
      const offset = offsets.get(id);
      const dx = offset ? offset.x : 0;
      const dy = offset ? offset.y : 0;
      button.style.transform = dx || dy ? `translate(${dx}px, ${dy}px) scale(${rowScale})` : '';
      button.style.setProperty('--chart-pull-x', `${dx / rowScale}px`);
      button.style.setProperty('--chart-pull-y', `${dy / rowScale}px`);
      button.classList.toggle('is-displaced', Math.abs(dx) + Math.abs(dy) > 1);
      button.classList.toggle('is-pulled', !!drag && drag.item?.id === id && drag.moved);
    }
    function clearMotion() {
      if (motionFrame) cancelAnimationFrame(motionFrame);
      motionFrame = 0; motionTime = 0;
      if (panReturn) { cameraX = panReturn.target; panReturn = null; scheduleRender(); }
      const ids = [...offsets.keys()];
      offsets.clear();
      for (const id of ids) paintOffset(id);
    }
    function animateReturn(time) {
      motionFrame = 0;
      const dt = Math.min(0.032, Math.max(0.001, motionTime ? (time - motionTime) / 1000 : 1 / 60));
      motionTime = time;
      if (panReturn) {
        panReturn.velocity += (-190 * (cameraX - panReturn.target) - 22 * panReturn.velocity) * dt;
        cameraX += panReturn.velocity * dt;
        if (Math.abs(cameraX - panReturn.target) < 0.1 && Math.abs(panReturn.velocity) < 0.5) {
          cameraX = panReturn.target; panReturn = null;
        }
        scheduleRender();
      }
      for (const [id, offset] of offsets) {
        // Damped spring to an immutable home; no graph edges or idle simulation.
        offset.vx += (-190 * offset.x - 22 * offset.vx) * dt;
        offset.vy += (-190 * offset.y - 22 * offset.vy) * dt;
        offset.x += offset.vx * dt; offset.y += offset.vy * dt;
        if (Math.abs(offset.x) + Math.abs(offset.y) < 0.1 && Math.abs(offset.vx) + Math.abs(offset.vy) < 0.5) offsets.delete(id);
        paintOffset(id);
      }
      if (offsets.size || panReturn) motionFrame = requestAnimationFrame(animateReturn);
      else motionTime = 0;
    }
    function sourceCue(item) {
      return item.source_kind === 'codex-company' ? 'CC' : item.source_kind === 'codex' ? 'CX' : item.provider_kind === 'claude' ? 'CL' : item.source_name.slice(0, 2).toUpperCase();
    }
    function pinIcon() {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      svg.classList.add('session-chart-pin-icon');
      for (const d of ['M8 3h8l-1 6 3 3v2H6v-2l3-3-1-6Z', 'M12 14v7']) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d); svg.append(path);
      }
      return svg;
    }
    function makeNode(item) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'session-chart-node';
      button.dataset.sessionId = item.id;
      button.setAttribute('aria-label', `${item.source_name} · ${item.title} · ${fullDate.format(item.time)}`);
      button.setAttribute('aria-controls', 'session-chart-preview');
      const cue = document.createElement('span');
      cue.className = 'session-chart-source';
      cue.dataset.kind = item.source_kind;
      cue.dataset.provider = item.provider_kind;
      cue.setAttribute('aria-hidden', 'true');
      cue.textContent = sourceCue(item);
      const copy = document.createElement('span');
      copy.className = 'session-chart-node-copy';
      const title = document.createElement('strong');
      title.textContent = item.title;
      copy.append(title);
      const badge = document.createElement('span');
      badge.className = 'session-chart-stack-count';
      badge.hidden = true;
      badge.setAttribute('aria-hidden', 'true');
      const pin = document.createElement('span');
      pin.className = 'session-chart-pin-marker';
      pin.hidden = true;
      pin.setAttribute('aria-hidden', 'true');
      pin.append(pinIcon());
      button.append(cue, copy, badge, pin);
      const showHover = (pointer = false) => {
        if (!drag && hoverBlocked !== item.id && (!pointer || !hoverDismissedAt)) setHovered(item.stack.includes(selected) ? selected : item);
      };
      const leaveHover = () => {
        if (item.stack.includes(hovered)) deferHoverExit();
        if (hoverBlocked === item.id) hoverBlocked = null;
      };
      button.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') showHover(true); });
      button.addEventListener('pointerleave', leaveHover);
      button.addEventListener('focus', () => { if (button.matches(':focus-visible')) showHover(); });
      button.addEventListener('blur', leaveHover);
      button.addEventListener('click', () => {
        const release = item.stack.includes(selected);
        hoverBlocked = release ? item.id : null;
        select(release ? null : item);
      });
      return button;
    }
    function drawProjects() {
      const focusedProject = document.activeElement.matches('.session-chart-project-heading') ? document.activeElement.dataset.projectKey : null;
      projectAxis.replaceChildren(); guides.replaceChildren();
      guides.setAttribute('viewBox', `0 0 ${width} ${height}`);
      const svg = (tag, attributes) => {
        const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
        for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
        return element;
      };
      const defs = svg('defs', {});
      const marker = svg('marker', { id: 'session-chart-arrow', viewBox: '0 0 8 8', refX: '7', refY: '4', markerWidth: String(6 * rowScale), markerHeight: String(6 * rowScale), orient: 'auto' });
      marker.append(svg('path', { d: 'M 0 1 L 7 4 L 0 7 Z', class: 'session-chart-guide-arrow' }));
      defs.append(marker); guides.append(defs);
      const guideEnd = Math.max(0, usablePlotWidth() - edgeInset());
      for (const project of projects) {
        if (!project.visible || project.bottom * rowScale < cameraY || project.top * rowScale > cameraY + height) continue;
        const heading = document.createElement('button');
        heading.type = 'button';
        heading.className = 'session-chart-project-heading';
        heading.dataset.projectKey = project.key;
        heading.title = project.path || project.name;
        heading.setAttribute('aria-label', `${project.name} 프로젝트 확대${project.path ? ' · ' + project.path : ''}`);
        heading.addEventListener('click', () => focusProject(project));
        const name = document.createElement('strong'); name.textContent = project.name;
        const path = document.createElement('small'); path.textContent = project.path;
        heading.append(name, path); projectAxis.append(heading);
        // Typography tokens may use rem; measure resolved pixels for projection.
        const headingHeight = rowScale < 1 ? Math.min(parseFloat(getComputedStyle(name).lineHeight), (project.bottom - project.top) * rowScale) : projectHeadingHeight;
        heading.style.height = `${headingHeight}px`;
        heading.style.top = `${Math.min(Math.max(0, project.top * rowScale - cameraY), project.bottom * rowScale - cameraY - headingHeight)}px`;
        if (focusedProject === project.key) heading.focus({ preventScroll: true });
        const rootY = (project.tracks[0].y + hitSize / 2) * rowScale - cameraY;
        for (const track of project.tracks) {
          const y = (track.y + hitSize / 2) * rowScale - cameraY;
          if (y < -hitSize || y > height + hitSize) continue;
          const label = document.createElement('span');
          label.className = 'session-chart-branch-label';
          label.classList.toggle('is-selected', selected?.track === track);
          label.style.top = `${track.y * rowScale - cameraY}px`;
          label.textContent = track.name; label.title = track.name;
          projectAxis.append(label);
          const first = track.root ? project.first : track.first;
          const x = Number.isFinite(first) ? (first - origin) * scale - cameraX : 0;
          if (x > guideEnd) continue;
          let d = `M ${Math.max(0, x)} ${y} H ${guideEnd}`;
          if (!track.root && track.branch && x > -gap * 2) {
            // The curve is a layout join, ending at first Session observation.
            d = `M ${x - gap * 2} ${rootY} C ${x - gap} ${rootY}, ${x - gap} ${y}, ${x} ${y} H ${guideEnd}`;
          }
          const classes = ['session-chart-guide'];
          if (track.root) classes.push('is-baseline');
          if (selected?.track === track) classes.push('is-selected');
          if (!Number.isFinite(first)) classes.push('is-undated');
          guides.append(svg('path', { d, class: classes.join(' '), 'marker-end': 'url(#session-chart-arrow)' }));
        }
        const bottom = (project.bottom - projectGap / 2) * rowScale - cameraY;
        if (bottom > 0 && bottom < height) guides.append(svg('line', { x1: '0', y1: bottom, x2: width, y2: bottom, class: 'session-chart-project-divider' }));
      }
    }
    function updateStackSelector() {
      const items = selected ? stacks.get(selected.id) || [] : [];
      stackSelector.hidden = items.length < 2;
      const signature = items.map(item => item.id).join(',');
      if (signature !== stackSignature) {
        stackSelect.replaceChildren();
        for (const item of items) {
          const option = document.createElement('option');
          option.value = item.id;
          option.textContent = `${item.pinned ? 'Pinned · ' : ''}${fullDate.format(item.time)} · ${item.source_name} · ${item.title}`;
          stackSelect.append(option);
        }
        stackSignature = signature;
      }
      if (selected) stackSelect.value = selected.id;
      root.querySelector('[data-chart-stack-label]').textContent = `이 위치의 세션 ${items.length}개`;
    }
    function drawAxis() {
      axis.replaceChildren();
      grid.replaceChildren();
      if (!visibleDated.length) return;
      const intervals = [1000, 10000, 60000, 300000, 900000, 3600000, 10800000, 21600000, DAY, DAY * 2, DAY * 7, DAY * 14, DAY * 30, DAY * 90, DAY * 365];
      const target = 120 / scale;
      const step = intervals.find(value => value >= target) || Math.ceil(target / (DAY * 365)) * DAY * 365;
      const start = origin + cameraX / scale;
      const end = start + width / scale;
      const boundsNow = bounds();
      for (let time = Math.ceil(start / step) * step; time <= end; time += step) {
        if (time < boundsNow.first - step || time > boundsNow.last + step) continue;
        const x = (time - origin) * scale - cameraX;
        const tick = document.createElement('span');
        tick.className = 'session-chart-tick';
        tick.style.left = `${x + nodeInset}px`;
        tick.textContent = step < DAY ? tickTime.format(time) : step >= DAY * 90 ? yearDate.format(time) : dateLabel.format(time);
        axis.append(tick);
        const line = document.createElement('span');
        line.className = 'session-chart-grid-line';
        line.style.left = `${x}px`;
        grid.append(line);
      }
    }
    function drawActivity() {
      eventLayer.replaceChildren();
      if (!selected || !Number.isFinite(selected.time) || !activity) return;
      // Collapse only overlapping screen pixels, preserving each bucket's exact observation count.
      const buckets = new Map();
      for (const value of activityTimes()) {
        const time = Date.parse(value);
        const x = (time - origin) * scale - cameraX;
        if (!Number.isFinite(x) || x < -hitSize || x > width + hitSize) continue;
        const key = Math.round(x / 6);
        const bucket = buckets.get(key);
        if (bucket) { bucket.count++; bucket.first = Math.min(bucket.first, time); bucket.last = Math.max(bucket.last, time); }
        else buckets.set(key, { x, first: time, last: time, count: 1 });
      }
      const y = (selected.y + hitSize / 2) * rowScale - cameraY;
      if (y < -hitSize || y > height) return;
      for (const bucket of buckets.values()) {
        const dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'session-chart-event';
        dot.style.left = `${bucket.x - hitSize * rowScale / 2}px`;
        dot.style.top = `${y}px`;
        const label = `${activity.timestamps.length ? '이벤트' : '메타데이터 시각'} ${bucket.count}개 · ${fullDate.format(bucket.first)}${bucket.last !== bucket.first ? ` — ${fullDate.format(bucket.last)}` : ''}`;
        dot.title = label;
        dot.setAttribute('aria-label', label);
        dot.addEventListener('click', () => { activityStatus.textContent = label; });
        eventLayer.append(dot);
      }
    }
    function render() {
      if (failed) return;
      try {
        frame = 0;
        updatePreview();
        clampCamera();
        root.classList.toggle('is-overview', rowScale < 1);
        root.style.setProperty('--session-chart-view-scale', rowScale);
        root.dataset.rowScale = rowScale;
        root.dataset.worldHeight = worldHeight;
        drawAxis();
        drawProjects();
        const targetSize = hitSize * rowScale;
        const candidates = visibleDated.filter(item => {
          const x = item.x - cameraX - anchor * rowScale;
          const y = item.y * rowScale - cameraY;
          return x + targetSize >= 0 && x <= width && y + targetSize >= 0 && y <= height;
        });
        const buckets = [];
        const currentTrackBucket = new Map();
        stacks = new Map();
        // Latest observed point anchors each bucket; adjacent targets stay apart.
        for (const item of [...candidates].reverse()) {
          let bucket = currentTrackBucket.get(item.track.key);
          if (!bucket || bucket.point.x - item.x >= targetSize) {
            bucket = { point: item, items: [] };
            currentTrackBucket.set(item.track.key, bucket); buckets.push(bucket);
          }
          bucket.items.unshift(item);
        }
        const displayed = buckets.map(({ point, items }) => {
          for (const item of items) stacks.set(item.id, items);
          point.stack = items;
          return point;
        });
        const captions = [];
        for (const item of [...displayed].sort((a, b) => Number(b.stack.includes(selected)) - Number(a.stack.includes(selected)) || a.id - b.id)) {
          const crowded = displayed.some(peer => peer !== item && Math.abs(peer.y - item.y) < hitSize && peer.x > item.x - hitSize && peer.x < item.x + cardWidth);
          const overlaps = captions.some(peer => Math.abs(peer.y - item.y) < hitSize && Math.abs(peer.x - item.x) < cardWidth);
          item.compact = rowScale < 1 || (!item.stack.includes(selected) && (crowded || overlaps || item.x - cameraX - anchor + cardWidth > width));
          if (!item.compact) captions.push(item);
        }
        const displayedIds = new Set();
        for (const item of displayed) {
          displayedIds.add(item.id);
          let button = buttons.get(item.id);
          if (!button) { button = makeNode(item); buttons.set(item.id, button); nodes.append(button); }
          button.style.left = `${item.x - cameraX - anchor * rowScale}px`;
          button.style.top = `${item.y * rowScale - cameraY}px`;
          button.tabIndex = rowScale < 1 ? -1 : 0;
          button.dataset.homeY = item.y;
          button.dataset.trackKey = item.track.key;
          button.dataset.sessionIds = item.stack.map(peer => peer.id).join(',');
          const badge = button.querySelector('.session-chart-stack-count');
          badge.hidden = item.stack.length < 2;
          badge.textContent = item.stack.length;
          const mixedSource = new Set(item.stack.map(peer => peer.source_kind)).size > 1;
          const cue = button.querySelector('.session-chart-source');
          cue.dataset.kind = mixedSource ? '' : item.source_kind;
          cue.dataset.provider = mixedSource ? '' : item.provider_kind;
          cue.textContent = mixedSource ? '+' : sourceCue(item);
          button.querySelector('.session-chart-node-copy strong').textContent = item.stack.length > 1 ? `세션 ${item.stack.length}개` : item.title;
          const pinnedCount = item.stack.filter(peer => peer.pinned).length;
          const pinLabel = pinnedCount ? item.stack.length > 1 ? `핀 고정된 세션 ${pinnedCount}개 포함 · ` : '핀 고정됨 · ' : '';
          button.classList.toggle('is-pinned', pinnedCount > 0);
          button.querySelector('.session-chart-pin-marker').hidden = !pinnedCount;
          button.setAttribute('aria-label', `${item.stack.includes(selected) ? '설명 해제' : '설명 고정'} · ${item.stack.length > 1 ? `${item.stack.length}개의 세션 · ` : ''}${pinLabel}${mixedSource ? '여러 소스' : item.source_name} · ${item.title} · ${fullDate.format(item.time)}`);
          button.classList.toggle('is-compact', item.compact);
          button.setAttribute('aria-pressed', String(item.stack.includes(selected)));
          paintOffset(item.id);
        }
        for (const [id, button] of buttons) {
          if (!displayedIds.has(id)) {
            if (button.classList.contains('is-hovered')) setHovered(null);
            if (hoverBlocked === id) hoverBlocked = null;
            if (document.activeElement === button) viewport.focus({ preventScroll: true });
            button.remove(); buttons.delete(id);
          }
        }
        drawActivity();
        updateStackSelector();
        updateHoverPreview();
        updateNodePreviewState();
        save();
      } catch (error) { fail(error); }
    }
    function fail(error) {
      failed = true;
      cancelDrag();
      if (activityController) activityController.abort();
      explorer.hidden = true; fallback.hidden = false;
      console.error('Session chart could not render', error);
    }
    function scheduleRender() { if (!failed && !frame) frame = requestAnimationFrame(render); }
    function updateNodePreviewState() {
      for (const [id, button] of buttons) {
        const items = byId.get(id).stack || [];
        button.classList.toggle('is-hovered', items.includes(hovered));
        if (!hoverPreview.hidden && items.includes(hovered)) button.setAttribute('aria-describedby', hoverPreview.id);
        else if (!preview.hidden && items.includes(selected)) button.setAttribute('aria-describedby', preview.id);
        else button.removeAttribute('aria-describedby');
      }
    }
    function setHovered(item) {
      if (item && (!item.project.visible || drag)) return;
      cancelHoverExit();
      if (hovered === item) return;
      hovered = item;
      hoverPreview.scrollTop = 0;
      updateHoverPreview(); updateNodePreviewState();
    }
    function hoverNode() {
      return hovered ? [...buttons.values()].find(node => byId.get(Number(node.dataset.sessionId)).stack.includes(hovered)) : null;
    }
    function cancelHoverExit() {
      clearTimeout(hoverExitTimer);
      hoverExitTimer = 0;
    }
    function hoverHasFocus() {
      const node = hoverNode();
      return (!hoverPreview.hidden && hoverPreview.matches(':focus-visible')) || node?.matches(':focus-visible');
    }
    function withinHoverRegion(point) {
      const node = hoverNode();
      if (!point || !node) return false;
      if (node.matches(':hover') || (!hoverPreview.hidden && hoverPreview.matches(':hover'))) return true;
      const a = node.getBoundingClientRect();
      const inside = rect => point.x >= rect.left && point.x <= rect.right && point.y >= rect.top && point.y <= rect.bottom;
      if (inside(a)) return true;
      if (hoverPreview.hidden) return false;
      const b = hoverPreview.getBoundingClientRect();
      if (inside(b)) return true;
      // Keep the facing-edge passage open without an invisible canvas hit target.
      let passage;
      if (b.left >= a.right) passage = [[a.right, a.top], [b.left, b.top], [b.left, b.bottom], [a.right, a.bottom]];
      else if (b.right <= a.left) passage = [[b.right, b.top], [a.left, a.top], [a.left, a.bottom], [b.right, b.bottom]];
      else if (b.top >= a.bottom) passage = [[a.left, a.bottom], [a.right, a.bottom], [b.right, b.top], [b.left, b.top]];
      else if (b.bottom <= a.top) passage = [[b.left, b.bottom], [b.right, b.bottom], [a.right, a.top], [a.left, a.top]];
      else return false;
      const sides = passage.map(([x, y], index) => {
        const next = passage[(index + 1) % passage.length];
        return (next[0] - x) * (point.y - y) - (next[1] - y) * (point.x - x);
      });
      return sides.every(side => side >= 0) || sides.every(side => side <= 0);
    }
    function deferHoverExit() {
      if (!hovered || hoverExitTimer) return;
      hoverExitTimer = setTimeout(() => {
        hoverExitTimer = 0;
        if (!hoverHasFocus() && !withinHoverRegion(lastPointer)) setHovered(null);
      }, hoverExitDelay);
    }
    function fillPreview(panel, item) {
      panel.querySelector('[data-chart-preview-source]').textContent = item.source_name;
      panel.querySelector('[data-chart-preview-pin]').hidden = !item.pinned;
      panel.querySelector('[data-chart-preview-title]').textContent = item.title;
      const time = panel.querySelector('[data-chart-preview-time]');
      time.textContent = Number.isFinite(item.time) ? fullDate.format(item.time) : '기록된 시각 없음';
      if (item.observed_at) time.dateTime = item.observed_at;
      else time.removeAttribute('datetime');
      panel.querySelector('[data-chart-preview-path]').textContent = item.cwd_raw || '기록 없음';
      panel.querySelector('[data-chart-preview-branch]').textContent = item.git_branch || '';
      panel.querySelector('[data-chart-preview-branch-row]').hidden = !item.git_branch;
    }
    function updateHoverPreview() {
      hoverPreview.hidden = !hovered || (hovered === selected && rowScale === 1);
      if (hoverPreview.hidden) return;
      fillPreview(hoverPreview, hovered);
      const items = stacks.get(hovered.id) || [];
      hoverPreview.querySelector('[data-chart-stack-selector]').hidden = items.length < 2;
      hoverPreview.querySelector('[data-chart-stack-label]').textContent = `이 위치의 세션 ${items.length}개`;
      const button = hoverNode();
      if (!button) { hoverPreview.hidden = true; return; }
      const target = button.getBoundingClientRect();
      const frame = viewport.getBoundingClientRect();
      hoverPreview.style.maxHeight = '';
      const panelWidth = hoverPreview.offsetWidth;
      let panelHeight = hoverPreview.offsetHeight;
      const minTop = axisHeight + gap;
      const maxRight = !preview.hidden && getComputedStyle(preview).position === 'absolute' ? preview.getBoundingClientRect().left - frame.left - gap : frame.width - gap;
      const right = target.right - frame.left + gap;
      const left = target.left - frame.left - panelWidth - gap;
      let x = right + panelWidth <= maxRight ? right : left;
      let y = target.top - frame.top + target.height / 2 - panelHeight / 2;
      if (x < gap) {
        x = Math.max(gap, Math.min(maxRight - panelWidth, target.left - frame.left));
        const below = target.bottom - frame.top + gap;
        const aboveSpace = Math.max(0, target.top - frame.top - gap - minTop);
        const belowSpace = Math.max(0, frame.height - gap - below);
        const placeBelow = belowSpace >= panelHeight || belowSpace >= aboveSpace;
        hoverPreview.style.maxHeight = `${Math.max(pointSize, placeBelow ? belowSpace : aboveSpace)}px`;
        panelHeight = hoverPreview.offsetHeight;
        y = placeBelow ? below : target.top - frame.top - panelHeight - gap;
      }
      hoverPreview.style.left = `${Math.max(gap, Math.min(maxRight - panelWidth, x))}px`;
      hoverPreview.style.top = `${Math.max(minTop, Math.min(frame.height - panelHeight - gap, y))}px`;
    }
    function updatePreview() {
      preview.hidden = !selected || rowScale < 1;
      focusButton.disabled = !selected || !Number.isFinite(selected.time);
      if (!selected) { stackSelector.hidden = true; updateNodePreviewState(); return; }
      fillPreview(preview, selected);
      root.querySelector('[data-chart-detail]').href = sessionUrl(selected);
      activityButton.disabled = activityState === 'loading';
      activityButton.textContent = activityState === 'error' ? '다시 불러오기' : activityState === 'loaded' ? '활동 시점 숨기기' : '활동 시점 보기';
      if (activityState === 'idle') activityStatus.textContent = '';
      updateNodePreviewState();
    }
    function select(item) {
      cancelDrag();
      if (item && !item.project.visible) return;
      const fromOverview = item && rowScale < 1;
      if (item && rowScale < 1) {
        rowScale = 1;
        cameraY = item.y - height / 2 + hitSize / 2;
      }
      if (selected !== item) {
        if (activityController) activityController.abort();
        activityController = null;
        activity = null;
        activityState = 'idle';
        activityStatus.textContent = '';
      }
      selected = item;
      updatePreview();
      if (item && !fromOverview && usablePlotWidth() < width) {
        const points = stacks.get(item.id) || [item];
        const point = points[points.length - 1];
        if (point.x - cameraX + anchor > usablePlotWidth() - gap) cameraX = point.x + anchor + gap - usablePlotWidth();
      }
      status.textContent = item ? `${item.title} 선택. 세션 상세에서 전체 대화를 볼 수 있습니다.` : '선택 해제';
      if (fromOverview) focusSelection();
      scheduleRender();
    }
    function focusSelection() {
      cancelDrag();
      if (!selected || !Number.isFinite(selected.time)) return;
      rowScale = 1;
      updatePreview();
      let first = selected.time;
      let last = selected.time;
      for (const value of activityTimes()) {
        const time = Date.parse(value);
        if (Number.isFinite(time)) { first = Math.min(first, time); last = Math.max(last, time); }
      }
      const usableWidth = usablePlotWidth();
      if (last > first) {
        scale = Math.min(MAX_SCALE, Math.max(minScale(), Math.max(pointSize, usableWidth - cardWidth - gap * 2) / (last - first)));
        layout();
        cameraX = (first - origin) * scale - gap - anchor;
      } else {
        const target = Math.max(anchor + gap, Math.min(usableWidth / 2, usableWidth - cardWidth + anchor - gap));
        cameraX = selected.x - target;
      }
      cameraY = selected.y - height / 2 + pointSize;
      scheduleRender();
    }
    function focusProject(project) {
      cancelDrag();
      if (selected && selected.project !== project) select(null);
      rowScale = 1;
      updatePreview();
      scale = Math.max(minScale(), scale); layout();
      cameraY = project.top - projectGap;
      scheduleRender();
    }
    function zoom(factor, at = width / 2, horizontalOnly = false) {
      cancelDrag();
      const time = origin + (cameraX + at) / scale;
      const rowCenter = (cameraY + height / 2) / rowScale;
      if (!horizontalOnly) {
        rowScale = Math.min(1, Math.max(minRowScale(), rowScale * factor));
        updatePreview();
      }
      scale = Math.min(MAX_SCALE, Math.max(minScale(), scale * factor));
      layout();
      cameraX = (time - origin) * scale - at;
      if (!horizontalOnly) {
        cameraY = rowCenter * rowScale - height / 2;
        if (rowScale === minRowScale() && rowScale < 1) viewport.scrollIntoView({ block: 'nearest' });
      }
      scheduleRender();
    }
    root.querySelectorAll('[data-chart-action]').forEach(button => button.addEventListener('click', () => {
      cancelDrag();
      const action = button.dataset.chartAction;
      if (action === 'zoom-out') zoom(0.5);
      if (action === 'zoom-in') zoom(2);
      if (action === 'fit') {
        rowScale = minRowScale(); updatePreview(); scale = minScale(); layout(); cameraY = 0;
        cameraX = cameraLimits().min;
        viewport.scrollIntoView({ block: 'nearest' });
      }
      if (action === 'focus') focusSelection();
      scheduleRender();
    }));
    root.querySelector('[data-chart-close]').addEventListener('click', () => { select(null); viewport.focus({ preventScroll: true }); });
    root.querySelector('[data-chart-detail]').addEventListener('click', save);
    stackSelect.addEventListener('change', () => {
      const item = byId.get(Number(stackSelect.value));
      if (item) select(item);
    });
    function updateProjectFilter() {
      const visibleCount = projects.length - hiddenProjects.size;
      projectAll.checked = visibleCount === projects.length;
      projectAll.indeterminate = visibleCount > 0 && visibleCount < projects.length;
      root.querySelector('[data-chart-project-filter-label]').textContent = visibleCount === projects.length ? '프로젝트' : `프로젝트 · ${visibleCount}/${projects.length}`;
      for (const checkbox of projectOptions.querySelectorAll('input')) checkbox.checked = !hiddenProjects.has(checkbox.dataset.projectKey);
    }
    function updateUndated() {
      const panel = root.querySelector('[data-chart-undated]');
      panel.hidden = !visibleUndated.length;
      root.querySelector('[data-chart-undated-summary]').textContent = `날짜를 확인할 수 없는 세션 ${visibleUndated.length}개`;
      const items = root.querySelector('[data-chart-undated-items]');
      items.replaceChildren();
      for (const item of visibleUndated) {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = sessionUrl(item); link.textContent = `${item.pinned ? 'Pinned · ' : ''}${item.source_name} · ${item.title}`;
        li.append(link); items.append(li);
      }
      const hasProjects = projects.some(project => project.visible);
      const empty = root.querySelector('[data-chart-undated-empty]');
      empty.hidden = !!visibleDated.length;
      empty.textContent = hasProjects ? '날짜를 확인할 수 있는 세션이 없습니다.' : '선택된 프로젝트 없음';
      root.querySelectorAll('[data-chart-action]').forEach(button => {
        const action = button.dataset.chartAction;
        if (action === 'focus') return;
        button.disabled = action === 'fit' ? !hasProjects : !visibleDated.length;
      });
    }
    function applyProjectFilter(persist = true) {
      cancelDrag();
      const previousLimits = cameraLimits();
      const atLeft = Math.abs(cameraX - previousLimits.min) < 0.5;
      const atRight = Math.abs(cameraX - previousLimits.max) < 0.5;
      const timeFitted = Math.abs(scale - minScale()) <= minScale() * 1e-6;
      const centerTime = origin + (cameraX + usablePlotWidth() / 2) / scale;
      const overview = rowScale < 1;
      if (selected && hiddenProjects.has(selected.project.key)) select(null);
      layoutProjects();
      rowScale = overview ? minRowScale() : 1;
      updatePreview();
      scale = timeFitted ? minScale() : Math.max(minScale(), scale);
      const nextLimits = cameraLimits();
      if (timeFitted || atLeft) cameraX = nextLimits.min;
      else if (atRight) cameraX = nextLimits.max;
      else cameraX = boundedCameraX((centerTime - origin) * scale - usablePlotWidth() / 2);
      layout(); updateProjectFilter(); updateUndated(); updatePreview();
      if (persist) saveProjectPreference();
      scheduleRender();
    }
    preferenceRetry.addEventListener('click', () => {
      if (!preferencePending && preferenceLoadFailed) { window.location.reload(); return; }
      preferenceSaveFailed = false;
      flushProjectPreference();
    });
    function buildProjectFilter() {
      for (const project of projects) {
        const label = document.createElement('label');
        label.className = 'session-chart-project-choice';
        label.dataset.search = `${project.name} ${project.path}`.toLowerCase();
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox'; checkbox.dataset.projectKey = project.key;
        const copy = document.createElement('span');
        const name = document.createElement('strong'); name.textContent = project.name;
        const path = document.createElement('small'); path.textContent = project.path;
        copy.append(name, path); label.append(checkbox, copy); projectOptions.append(label);
        checkbox.addEventListener('change', () => {
          if (checkbox.checked) hiddenProjects.delete(project.key);
          else hiddenProjects.add(project.key);
          applyProjectFilter();
        });
      }
      projectAll.addEventListener('change', () => {
        hiddenProjects.clear();
        if (!projectAll.checked) for (const project of projects) hiddenProjects.add(project.key);
        applyProjectFilter();
      });
      projectSearch.addEventListener('input', () => {
        const query = projectSearch.value.toLowerCase().trim();
        for (const label of projectOptions.children) label.hidden = !label.dataset.search.includes(query);
      });
      document.addEventListener('pointerdown', event => { if (projectFilter.open && !projectFilter.contains(event.target)) projectFilter.open = false; });
      projectFilter.addEventListener('keydown', event => {
        if (event.key === 'Escape') { projectFilter.open = false; projectFilter.querySelector('summary').focus(); event.stopPropagation(); }
      });
      updateProjectFilter();
    }
    activityButton.addEventListener('click', async () => {
      cancelDrag();
      if (!selected || activityState === 'loading') return;
      if (activityState === 'loaded') { activity = null; activityState = 'idle'; updatePreview(); scheduleRender(); return; }
      const item = selected;
      const controller = new AbortController();
      activityController = controller;
      activityState = 'loading';
      activityStatus.textContent = '활동 시점을 불러오는 중…';
      updatePreview();
      try {
        const response = await fetch(`/sessions/${item.id}/chart-activity`, { signal: controller.signal, cache: 'no-store' });
        if (!response.ok) throw new Error(String(response.status));
        const result = await response.json();
        if (selected !== item || controller.signal.aborted) return;
        if (result.session_id !== item.id || !Array.isArray(result.timestamps) || !Array.isArray(result.metadata_times)) throw new Error('Invalid activity');
        activity = result;
        activityState = 'loaded';
        const datedCount = result.timestamps.length;
        activityStatus.textContent = `이벤트 ${datedCount}개${result.undated_events ? ` · 시각 없음 ${result.undated_events}개` : ''}${!datedCount ? ' · 메타데이터 시각만 표시' : ''}`;
        updatePreview();
        focusSelection();
      } catch (error) {
        if (controller.signal.aborted || selected !== item) return;
        activity = null;
        activityState = 'error';
        activityStatus.textContent = '활동 시점을 불러오지 못했습니다. 다시 시도하거나 세션 상세를 여세요.';
        updatePreview();
      }
    });

    function cancelDrag() {
      hoverDismissedAt = lastPointer;
      setHovered(null);
      const current = drag;
      drag = null;
      viewport.classList.remove('is-dragging');
      if (current && viewport.hasPointerCapture(current.id)) viewport.releasePointerCapture(current.id);
      clearMotion();
      if (width) clampCamera();
    }
    root.addEventListener('pointermove', event => {
      if (event.pointerType === 'touch') return;
      lastPointer = { x: event.clientX, y: event.clientY };
      if (hoverDismissedAt && (lastPointer.x !== hoverDismissedAt.x || lastPointer.y !== hoverDismissedAt.y)) {
        // Reprojection can put another node under a stationary pointer after dismissal.
        hoverDismissedAt = null;
        const node = event.target.closest('.session-chart-node');
        const item = node ? byId.get(Number(node.dataset.sessionId)) : null;
        if (item && !drag && hoverBlocked !== item.id) setHovered(item.stack.includes(selected) ? selected : item);
      }
      if (hovered) {
        if (hoverHasFocus() || withinHoverRegion(lastPointer)) cancelHoverExit();
        else deferHoverExit();
      }
    });
    root.addEventListener('pointerleave', event => {
      if (event.pointerType === 'touch') return;
      lastPointer = { x: event.clientX, y: event.clientY };
      deferHoverExit();
    });
    hoverPreview.addEventListener('pointerenter', cancelHoverExit);
    hoverPreview.addEventListener('pointerleave', deferHoverExit);
    hoverPreview.addEventListener('focusin', cancelHoverExit);
    hoverPreview.addEventListener('focusout', deferHoverExit);
    hoverPreview.addEventListener('keydown', event => {
      if (event.key === 'Escape') { select(null); viewport.focus({ preventScroll: true }); }
    });
    viewport.addEventListener('pointerdown', event => {
      if (event.button !== 0 || !event.isPrimary || drag) return;
      const node = event.target.closest('.session-chart-node');
      if (!node && event.target.closest('button, a')) return;
      clearMotion(); suppressClick = false;
      const item = node ? byId.get(Number(node.dataset.sessionId)) : null;
      const radius = cardWidth * rowScale * 1.25;
      const neighbors = item && !motionPreference.matches ? [...buttons.keys()].map(id => byId.get(id))
        .filter(peer => peer !== item && peer.track === item.track)
        .map(peer => ({ item: peer, distance: Math.hypot(peer.x - item.x, peer.y - item.y) }))
        .filter(peer => peer.distance < radius).sort((a, b) => a.distance - b.distance).slice(0, 24)
        .map(peer => ({ item: peer.item, weight: (1 - peer.distance / radius) ** 2 * 0.18 })) : [];
      drag = { id: event.pointerId, item, neighbors, touch: event.pointerType === 'touch', x: event.clientX, y: event.clientY, cameraX, cameraY, moved: false };
      // Delay node capture until a real drag so an ordinary click keeps its target.
      if (!item) viewport.setPointerCapture(event.pointerId);
    });
    viewport.addEventListener('pointermove', event => {
      if (!drag || drag.id !== event.pointerId) return;
      const dx = event.clientX - drag.x;
      const dy = drag.touch && !drag.item ? 0 : event.clientY - drag.y;
      if (drag.touch && !drag.item && !drag.moved && Math.abs(dx) <= Math.abs(event.clientY - drag.y)) return;
      if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
      if (!drag.moved) return;
      setHovered(null);
      if (!viewport.hasPointerCapture(event.pointerId)) viewport.setPointerCapture(event.pointerId);
      viewport.classList.add('is-dragging');
      if (drag.item) {
        event.preventDefault();
        const x = dx / (1 + Math.abs(dx) / (hitSize * rowScale));
        const y = dy / (1 + Math.abs(dy) / (gap * rowScale / 2));
        offsets.set(drag.item.id, { x, y, vx: 0, vy: 0 });
        paintOffset(drag.item.id);
        for (const peer of drag.neighbors) {
          offsets.set(peer.item.id, { x: x * peer.weight, y: y * peer.weight, vx: 0, vy: 0 });
          paintOffset(peer.item.id);
        }
      } else {
        cameraX = resistedCameraX(drag.cameraX - dx); cameraY = drag.cameraY - dy;
        scheduleRender();
      }
    });
    function endDrag(event) {
      if (!drag || drag.id !== event.pointerId) return;
      suppressClick = drag.moved;
      const pulled = drag.item;
      drag = null;
      viewport.classList.remove('is-dragging');
      if (viewport.hasPointerCapture(event.pointerId)) viewport.releasePointerCapture(event.pointerId);
      if (pulled) {
        paintOffset(pulled.id);
        if (motionPreference.matches) clearMotion();
        else if (offsets.size) motionFrame = requestAnimationFrame(animateReturn);
      } else {
        const target = boundedCameraX(cameraX);
        if (motionPreference.matches) { cameraX = target; scheduleRender(); }
        else if (target !== cameraX) {
          panReturn = { target, velocity: 0 };
          motionFrame = requestAnimationFrame(animateReturn);
        }
      }
    }
    viewport.addEventListener('pointerup', endDrag);
    viewport.addEventListener('pointercancel', () => { cancelDrag(); suppressClick = false; });
    viewport.addEventListener('lostpointercapture', () => { if (drag) cancelDrag(); });
    viewport.addEventListener('click', event => {
      if (suppressClick && event.detail > 0) { suppressClick = false; event.preventDefault(); event.stopImmediatePropagation(); return; }
    }, true);
    viewport.addEventListener('click', event => {
      if (!event.target.closest('button, a') && (selected || hovered)) select(null);
    });
    viewport.addEventListener('wheel', event => {
      cancelDrag();
      // Shift-wheel can arrive on either axis; do not count a diagonal input twice.
      const horizontalDelta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
      if (event.ctrlKey || event.metaKey) {
        const delta = event.shiftKey ? horizontalDelta : event.deltaY;
        event.preventDefault();
        zoom(Math.exp(-Math.max(-100, Math.min(100, delta)) * 0.01), Math.max(0, Math.min(width, event.clientX - viewport.getBoundingClientRect().left - labelWidth)), event.shiftKey);
        return;
      }
      const beforeX = cameraX;
      const beforeY = cameraY;
      const deltaUnit = event.deltaMode === 1 ? gap : event.deltaMode === 2 ? height : 1;
      cameraX += (event.shiftKey ? horizontalDelta : event.deltaX) * deltaUnit;
      if (!event.shiftKey) cameraY += event.deltaY * deltaUnit;
      clampCamera();
      if (cameraX !== beforeX || cameraY !== beforeY) { event.preventDefault(); scheduleRender(); }
    }, { passive: false });
    viewport.addEventListener('keydown', event => {
      if (event.altKey || event.ctrlKey || event.metaKey || !visibleDated.length) return;
      if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
        event.preventDefault();
        let index = selected ? visibleDated.indexOf(selected) : -1;
        if (event.key === 'Home') index = 0;
        else if (event.key === 'End') index = visibleDated.length - 1;
        else index = index < 0 ? (event.key === 'ArrowRight' ? 0 : visibleDated.length - 1) : Math.min(visibleDated.length - 1, Math.max(0, index + (event.key === 'ArrowRight' ? 1 : -1)));
        select(visibleDated[index]); focusSelection();
      } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        event.preventDefault(); cancelDrag(); cameraY += verticalStep * (event.key === 'ArrowUp' ? -1 : 1); scheduleRender();
      } else if (event.key === '+' || event.key === '=') { event.preventDefault(); zoom(2); }
      else if (event.key === '-') { event.preventDefault(); zoom(0.5); }
      else if (event.key === 'Escape') { select(null); viewport.focus({ preventScroll: true }); }
    });
    explorer.hidden = false;
    fallback.hidden = true;
    function resize(initial = false) {
      if (failed) return;
      cancelDrag();
      const oldWidth = width;
      const wasFitted = oldWidth && rowScale < 1 && rowScale <= minRowScale() + 1e-6;
      const wasTimeFitted = oldWidth && Math.abs(scale - minScale()) <= minScale() * 1e-6;
      labelWidth = projectAxis.offsetWidth;
      width = viewport.clientWidth - labelWidth;
      height = viewport.clientHeight - axisHeight;
      if (!width || !height) return;
      const center = initial && saved && Number.isFinite(saved.centerTime) ? saved.centerTime : origin + (cameraX + oldWidth / 2) / scale;
      rowScale = wasFitted ? minRowScale() : Math.max(minRowScale(), rowScale);
      updatePreview();
      scale = (initial && !saved) || wasTimeFitted ? minScale() : Math.min(MAX_SCALE, Math.max(minScale(), scale));
      layout();
      if ((initial && !saved) || wasTimeFitted) {
        cameraX = cameraLimits().min;
        // Fitting time alone must not reset an independently scrolled Project axis.
        if (initial && !saved) cameraY = 0;
      } else {
        cameraX = (center - origin) * scale - width / 2;
        if (initial) cameraY = saved && Number.isFinite(saved.y) ? saved.y : selected ? selected.y * rowScale - height / 2 : 0;
      }
      scheduleRender();
    }
    initializeHomes(); buildProjectFilter(); updateUndated(); updatePreview(); resize(true);
    if (preferenceLoadFailed) showPreferenceError('load');
    if (canMigratePreference && projectPreference !== null) saveProjectPreference(true);
    new ResizeObserver(() => resize()).observe(viewport);
    motionPreference.addEventListener('change', cancelDrag);
    document.addEventListener('visibilitychange', () => { if (document.hidden) cancelDrag(); });
    window.addEventListener('pagehide', () => { cancelDrag(); save(); });
  } catch (error) {
    explorer.hidden = true;
    fallback.hidden = false;
    console.error('Session chart could not initialize', error);
  }
})();
