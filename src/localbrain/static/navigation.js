// One owner for app-wide native history; feature views keep their own renderers.
(() => {
  const button = document.querySelector('[data-app-back]');
  if (!button) return;
  const forwardButton = document.querySelector('[data-app-forward]');
  const key = 'localbrain:navigation:1';
  const markerKey = 'localbrainNavigation';
  const limit = 50;
  const nativePush = history.pushState.bind(history);
  const nativeReplace = history.replaceState.bind(history);
  const record = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const fresh = () => ({session: crypto.randomUUID(), entries: [], cursor: -1});
  const marker = () => record(history.state)[markerKey];
  const url = value => new URL(value, location.href);
  const withoutHash = value => {const result = url(value); result.hash = ''; return result.href;};

  function read() {
    try {
      const saved = JSON.parse(sessionStorage.getItem(key));
      if (!saved || typeof saved.session !== 'string' || !Array.isArray(saved.entries)
          || !saved.entries.length || saved.entries.length > limit
          || !Number.isInteger(saved.cursor) || saved.cursor < 0 || saved.cursor >= saved.entries.length
          || saved.entries.some(entry => typeof entry.id !== 'string' || typeof entry.href !== 'string'
            || entry.href.length > 16384 || url(entry.href).origin !== location.origin)) return null;
      return saved;
    } catch (_) { return null; }
  }

  let registry = read() || fresh();
  let current = null;
  let restoring = false;
  let pending = false;
  let traversal = null;
  let scrollTimer;
  let settleVersion = 0;
  const documentReady = document.readyState === 'complete' ? Promise.resolve()
    : new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve, {once: true}));

  function persist() {
    try { sessionStorage.setItem(key, JSON.stringify(registry)); }
    catch (_) { /* Existing links and partial views also work without storage. */ }
  }

  function refresh() {
    const update = (control, disabled, label) => {
      if (!control) return;
      control.disabled = disabled;
      control.dataset.shellTooltip = label;
    };
    update(button, !!traversal || registry.cursor <= 0 || history.length <= 1,
      '뒤로');
    update(forwardButton, !!traversal || registry.cursor >= registry.entries.length - 1 || history.length <= 1,
      '앞으로');
  }

  function save(leaving = false) {
    if (!current || restoring || (!leaving && marker()?.id !== current.id)) return;
    const panes = {};
    document.querySelectorAll('[data-navigation-scroll]').forEach(pane => {
      panes[pane.dataset.navigationScroll] = [pane.scrollLeft, pane.scrollTop];
    });
    current.scroll = {window: [scrollX, scrollY], panes};
    persist();
  }

  function restore(saved) {
    const position = value => Array.isArray(value) && value.length === 2 && value.every(Number.isFinite);
    if (saved) {
      document.querySelectorAll('[data-navigation-scroll]').forEach(pane => {
        const point = saved.panes?.[pane.dataset.navigationScroll];
        if (position(point)) {pane.scrollLeft = point[0]; pane.scrollTop = point[1];}
      });
      if (position(saved.window)) window.scrollTo(saved.window[0], saved.window[1]);
    }
    restoring = false;
    save();
  }

  function schedule() {
    const version = ++settleVersion;
    const id = current?.id;
    const saved = current?.scroll;
    const apply = () => {
      if (version !== settleVersion || id !== current?.id || pending) return;
      restore(saved);
    };
    documentReady.then(() => document.fonts?.ready).then(() => {
      // WKWebView suspends animation frames while the app window is hidden.
      if (document.hidden) apply();
      // Reapply the same snapshot after queued feature scrolls resume.
      requestAnimationFrame(() => requestAnimationFrame(apply));
    });
  }

  function add(state, destination, push) {
    const entry = {id: crypto.randomUUID(), href: destination.href, scroll: null, views: {}};
    const value = {...record(state), [markerKey]: {session: registry.session, id: entry.id}};
    // Do not mutate bookkeeping until the native operation has succeeded.
    (push ? nativePush : nativeReplace)(value, '', destination.href);
    registry.entries = registry.entries.slice(0, registry.cursor + 1).concat(entry).slice(-limit);
    registry.cursor = registry.entries.length - 1;
    registry.pending = null;
    current = entry;
    restoring = false;
    persist(); refresh();
  }

  function activate(initial = false) {
    const previousId = current?.id;
    registry = read() || registry;
    const value = marker();
    const found = value?.session === registry.session
      ? registry.entries.findIndex(entry => entry.id === value.id && entry.href === location.href) : -1;
    if (found >= 0) {
      registry.cursor = found;
      current = registry.entries[found];
      restoring = !!current.scroll;
      registry.pending = null;
    } else {
      const previous = registry.entries[registry.cursor];
      let referrerMatches = false;
      try {referrerMatches = !!document.referrer && withoutHash(document.referrer) === withoutHash(previous?.href);} catch (_) {}
      const intended = registry.pending?.from === previous?.id && registry.pending?.to === location.href;
      const fragment = !initial && current && withoutHash(current.href) === withoutHash(location.href);
      const knownMarker = value?.session === registry.session && registry.entries.some(entry => entry.id === value.id);
      if (intended && registry.pending.replace) {
        // Completing setup replaces the current native entry, including at root.
        nativeReplace({...record(history.state), [markerKey]: {session: registry.session, id: previous.id}}, '', location.href);
        current = previous;
        current.href = location.href;
        current.scroll = null;
        current.views = {};
        restoring = false;
        registry.pending = null;
      } else {
        // A native traversal can reach an evicted entry; it is a new safe root.
        if ((value && !knownMarker) || (!fragment && !(history.length > 1 && (referrerMatches || intended)))) registry = fresh();
        add(history.state, url(location.href), false);
      }
    }
    if (current?.id !== previousId) pending = false;
    if (initial || traversal?.target === current?.id) traversal = null;
    persist(); refresh(); schedule();
  }

  // The handshake never renders this script, so it cannot become a predecessor.
  activate(true);
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

  window.LocalBrainNavigation = {
    save,
    pushState(state, _unused, destination = location.href) {
      const next = url(destination);
      if (next.href === location.href) {this.replaceState(state, '', next); return;}
      add(state, next, true);
    },
    replaceState(state, _unused, destination = location.href) {
      const next = url(destination);
      nativeReplace({...record(state), [markerKey]: {session: registry.session, id: current.id}}, '', next.href);
      current.href = next.href;
      persist(); refresh();
    },
    replaceLocation(destination) {
      const next = url(destination);
      save();
      registry.pending = {from: current.id, to: next.href, replace: true};
      persist();
      location.replace(next.href);
    },
    pending() {pending = true;},
    settled() {pending = false; schedule();},
    getView(name) {return current?.views?.[name] || null;},
    setView(name, value) {
      if (!current || restoring) return;
      current.views = {...current.views, [name]: value};
      persist();
    },
  };

  const traverse = (direction, control) => {
    if (!control || control.disabled) return;
    const target = registry.entries[registry.cursor + (direction === 'back' ? -1 : 1)];
    if (!target) {refresh(); return;}
    save();
    traversal = {target: target.id}; refresh();
    try { history[direction](); }
    catch (error) { traversal = null; refresh(); throw error; }
  };
  window.navigation?.addEventListener('navigate', event => {
    const request = traversal;
    if (!request) return;
    if (event.navigationType !== 'traverse') {
      if (event.destination.sameDocument) request.sameDocumentChange = true;
      return;
    }
    event.signal?.addEventListener('abort', () => {
      // A same-document update can abort this signal while the traversal loads.
      queueMicrotask(() => {
        if (traversal !== request || request.sameDocumentChange) return;
        traversal = null; refresh();
      });
    }, {once: true});
  });
  button.addEventListener('click', () => traverse('back', button));
  forwardButton?.addEventListener('click', () => traverse('forward', forwardButton));
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
        || event.shiftKey || event.altKey || (link.target && link.target !== '_self') || link.hasAttribute('download')) return;
    const destination = url(link.href);
    if (destination.origin !== location.origin) return;
    save();
    registry.pending = {from: current.id, to: destination.href};
    persist();
  }, true);
  document.addEventListener('submit', event => {
    if (!(event.target instanceof HTMLFormElement) || (event.target.target && event.target.target !== '_self')) return;
    save();
  }, true);
  document.addEventListener('scroll', () => {
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => save(), 120);
  }, true);
  window.addEventListener('pagehide', () => {clearTimeout(scrollTimer); save(true);});
  // Initial deferred scripts have already activated; keep their render wait.
  window.addEventListener('pageshow', event => {if (event.persisted) activate(true);});
  window.addEventListener('popstate', () => activate());
  window.addEventListener('hashchange', () => {
    if (current?.href !== location.href) activate();
  });
})();
