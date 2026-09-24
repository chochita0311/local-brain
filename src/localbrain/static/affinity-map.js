/* Passive SVG enhancement. Native SSR navigation remains the complete fallback. */
(() => {
  'use strict';
  if (window.__localbrainAffinity) return;
  window.__localbrainAffinity = true;
  const NS = 'http://www.w3.org/2000/svg';
  let graph = null, controller = null, generation = 0, nativeOnly = false;
  const root = () => document.querySelector('[data-affinity-root]');
  const el = (tag, attrs = {}, text = null) => {
    const item = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) item.setAttribute(key, String(value));
    if (text !== null) item.textContent = text;
    return item;
  };
  const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));

  function neighborhoodOrder(nodes, edges) {
    // Selection never participates in ordering. Greedy adjacency uses only
    // measured affinity; a disconnected strand starts the next neighborhood.
    const rank = (a, b) => b.occurrences - a.occurrences || a.id.localeCompare(b.id);
    const seeds = [...nodes].sort(rank), remaining = new Map(seeds.map(n => [n.id, n])), result = [];
    const neighbors = new Map(nodes.map(n => [n.id, []]));
    for (const e of edges) {
      if (!remaining.has(e.left) || !remaining.has(e.right)) continue;
      neighbors.get(e.left).push({node: remaining.get(e.right), weight: e.similarity});
      neighbors.get(e.right).push({node: remaining.get(e.left), weight: e.similarity});
    }
    for (const list of neighbors.values()) list.sort((a, b) => b.weight - a.weight || rank(a.node, b.node));
    let seed = 0;
    while (remaining.size) {
      const last = result.at(-1);
      while (!remaining.has(seeds[seed].id)) seed++;
      const next = (last && neighbors.get(last.id).find(e => e.weight > 0 && remaining.has(e.node.id))?.node) || seeds[seed];
      remaining.delete(next.id); result.push({...next});
    }
    return result;
  }

  const curve = (a, b) => {
    const bend = (b.x - a.x) * 0.45 || 18;
    return `M${a.x},${a.y} C${a.x + bend},${a.y} ${b.x - bend},${b.y} ${b.x},${b.y}`;
  };
  const dateLabel = value => new Date(value).toISOString().slice(0, 10).replaceAll('-', '.');

  function save() {
    if (!root()) return;
    history.replaceState({...history.state, affinity: {scope: graph?.scope,
      transform: graph ? {...graph.transform} : null, allEdges: graph?.allEdges === true,
      viewport: graph?.viewport,
      listOpen: root().querySelector('[data-affinity-list]')?.open,
      traceY: root().querySelector('.affinity-inspector')?.scrollTop || 0, scrollY: window.scrollY}}, '', location.href);
  }

  function render(saved = null) {
    graph?.destroy(); graph = null;
    const panel = root(), data = panel?.querySelector('[data-affinity-graph]');
    if (!data) return;
    const canvas = panel.querySelector('[data-affinity-canvas]');
    const visual = panel.querySelector('[data-affinity-visual]');
    const fallback = panel.querySelector('[data-affinity-list]');
    const abort = new AbortController();
    let observer, animation = 0;
    try {
      const payload = JSON.parse(data.textContent), scope = JSON.stringify(payload.scope);
      if (!Array.isArray(payload.nodes) || !payload.nodes.length || !payload.timeline) throw new Error('Invalid map');
      visual.hidden = false;
      const W = canvas.clientWidth, H = canvas.clientHeight, left = Math.min(182, W * 0.34), right = W - 24, top = 48;
      const timeline = payload.timeline, start = Date.parse(timeline.start), end = Date.parse(timeline.end);
      const dated = Number.isFinite(start) && Number.isFinite(end) && end > start;
      const span = dated ? end - start : 1, periodMs = timeline.period_days * 86400000;
      const xAt = at => left + (at - start) / span * (right - left);
      const points = neighborhoodOrder(payload.nodes, payload.edges), byId = new Map(points.map(n => [n.id, n]));
      const gap = clamp((H - top - 30) / points.length, 32, 90);
      points.forEach((n, i) => {n.y = top + gap * (i + 0.5);});
      const placedEdges = payload.edges.filter(e => e.left_at && e.right_at && byId.has(e.left) && byId.has(e.right));
      const incident = new Map(points.map(n => [n.id, []]));
      for (const e of placedEdges) {incident.get(e.left).push(e); incident.get(e.right).push(e);}
      const yAt = (n, at) => {
        let pull = 0, mass = 1;
        for (const e of incident.get(n.id)) {
          const isLeft = e.left === n.id;
          const other = byId.get(isLeft ? e.right : e.left);
          const witness = Date.parse(isLeft ? e.left_at : e.right_at);
          const weight = e.similarity * Math.exp(-(((at - witness) / Math.max(periodMs * 2, span / 14)) ** 2));
          pull += Math.sign(other.y - n.y) * weight; mass += weight;
        }
        return n.y + gap * 0.38 * pull / mass;
      };
      const svg = el('svg', {viewBox: `0 0 ${W} ${H}`, role: 'group', 'aria-label': '좌에서 우로 시간이 흐르는 유사도 지도. 업무 인과관계가 아닙니다.'});
      // The native scroll extent owns input; the sticky SVG projects that
      // viewport with fixed readable row labels and calendar ticks.
      svg.style.width = `${W}px`; svg.style.height = `${H}px`;
      const extent = document.createElement('div'); extent.className = 'affinity-extent'; extent.append(svg);
      const defs = el('defs'), clip = el('clipPath', {id: 'affinity-time-clip'});
      clip.append(el('rect', {x: left - 8, y: top - 8, width: W - left + 8, height: H - top + 8})); defs.append(clip);
      const clipped = el('g', {'clip-path': 'url(#affinity-time-clip)'}), layer = el('g', {class: 'affinity-world'});
      const grid = el('g', {'aria-hidden': 'true'}), lines = el('g', {'aria-hidden': 'true'}), dots = el('g');
      const labels = el('g', {class: 'affinity-strand-labels'}), axis = el('g', {'aria-hidden': 'true', class: 'affinity-time-axis'});
      svg.append(defs, grid, clipped, labels, axis); clipped.append(layer); layer.append(lines, dots);
      const selected = points.find(n => n.selected)?.id;
      const ranked = [...placedEdges].sort((a, b) => b.similarity - a.similarity || a.left.localeCompare(b.left) || a.right.localeCompare(b.right));
      const selectedEdges = ranked.filter(e => e.left === selected || e.right === selected);
      const compact = [...new Set([...selectedEdges, ...ranked.slice(0, 18)])];
      function drawEdges(all) {
        lines.replaceChildren();
        const shown = all ? ranked : compact;
        for (const e of shown) {
          const a = byId.get(e.left), b = byId.get(e.right);
          const ta = Date.parse(e.left_at), tb = Date.parse(e.right_at);
          lines.append(el('path', {d: curve({x: xAt(ta), y: yAt(a, ta)}, {x: xAt(tb), y: yAt(b, tb)}),
            'data-left': e.left, 'data-right': e.right,
            class: `affinity-edge${e.left === selected || e.right === selected ? ' is-related' : ''}`}));
        }
        panel.querySelector('[data-map-edge-count]').textContent = `유사 연결 ${shown.length} / ${payload.edges.length}개 · ${timeline.period_days}일 단위 관찰${payload.edges.length > ranked.length ? ' · 시간 미확인 연결 제외' : ''}`;
      }
      const allEdges = saved?.scope === scope && saved.allEdges === true;
      panel.querySelector('[data-map-all-edges]').checked = allEdges;
      drawEdges(allEdges);
      for (const n of points) {
        const a = el('a', {href: n.href + '#affinity-inspector', tabindex: '0', 'data-affinity-link': '',
          'data-affinity-map-node': n.id, class: `affinity-node${n.selected ? ' is-selected' : ''}`,
          'aria-label': `${n.title}, 세션 ${n.sessions}개, 근거 ${n.occurrences}개${n.selected ? ', 선택됨' : ''}`});
        if (n.selected) a.setAttribute('aria-current', 'true');
        a.append(el('title', {}, `${n.title}\n세션 ${n.sessions}개 · 근거 ${n.occurrences}개`));
        const budget = Math.max(4, Math.floor((left - 28) / 12)), title = Array.from(n.title);
        a.append(el('rect', {x: 4, y: -gap / 2 + 1, width: left - 16, height: Math.max(16, gap - 2), class: 'affinity-label-target'}));
        a.append(el('text', {x: 12, y: 4}, title.slice(0, budget).join('') + (title.length > budget ? '…' : '')));
        a.append(el('text', {x: 12, y: 23, class: 'affinity-node-count'}, n.selected ? '선택됨' : `${n.sessions}개 세션 · ${n.occurrences}개 근거`));
        labels.append(a); n.label = a;
        const strand = el('g', {class: `affinity-strand${n.selected ? ' is-selected' : ''}`, 'data-strand': n.id});
        const link = el('a', {href: n.href + '#affinity-inspector', 'data-affinity-link': '', tabindex: '-1', 'aria-hidden': 'true'});
        strand.append(link); dots.append(strand); n.strand = strand;
        n.knots = n.activity.filter(p => p.at !== null).map(p => ({...p, x: xAt(p.at), y: yAt(n, p.at)}));
        for (let i = 1; i < n.knots.length; i++) {
          const prev = n.knots[i - 1], next = n.knots[i];
          const d = curve(prev, next), empty = Number(next.period) - Number(prev.period) > 1;
          link.append(el('path', {d, class: 'affinity-strand-hit'}));
          link.append(el('path', {d, class: `affinity-strand-path${empty ? ' is-gap' : ''}`}));
        }
        for (const p of n.knots) {
          const knot = el('a', {href: p.href + '#affinity-inspector', tabindex: '0', 'data-affinity-link': '',
            'data-affinity-period': p.period, 'data-strand': n.id, 'data-at': p.at,
            class: `affinity-knot${n.selected && payload.period === p.period ? ' is-selected' : ''}`,
            transform: `translate(${p.x} ${p.y})`, 'aria-label': `${n.title}, ${dateLabel(p.first)}, 세션 ${p.sessions}개, 근거 ${p.occurrences}개`});
          if (n.selected && payload.period === p.period) knot.setAttribute('aria-current', 'true');
          knot.append(el('title', {}, `${dateLabel(p.first)} — ${dateLabel(p.last)}\n세션 ${p.sessions}개 · 근거 ${p.occurrences}개`));
          const shape = el('g', {class: 'affinity-knot-shape'});
          shape.append(el('circle', {r: 10, class: 'affinity-knot-target'}));
          shape.append(el('circle', {r: 3 + Math.min(4, Math.log2(1 + p.occurrences)), class: 'affinity-knot-mark'}));
          shape.append(el('text', {x: 0, y: -14, class: 'affinity-knot-detail'}, `${dateLabel(p.first).slice(5)} · ${p.occurrences}`));
          knot.append(shape); strand.append(knot); p.shape = shape;
        }
        const unknown = n.activity.find(p => p.period === 'unknown');
        if (unknown) {
          const u = el('a', {href: unknown.href + '#affinity-inspector', 'data-affinity-link': '', class: 'affinity-unknown', tabindex: '0'});
          u.setAttribute('aria-label', `${n.title}, 시간 미확인 근거 ${unknown.occurrences}개`);
          u.append(el('title', {}, `시간 미확인 ${unknown.occurrences}개`), el('text', {x: left - 20, y: 4}, '?'));
          labels.append(u); n.unknown = u;
        }
      }
      const fitted = () => ({k: 1, x: 0, y: 0});
      const initial = () => ({k: dated ? 2 : 1, x: dated ? -left : 0, y: dated ? -top : 0});
      const transform = saved?.scope === scope && saved.transform ? {...saved.transform}
        : initial();
      const old = saved?.scope === scope ? saved.viewport : null;
      if (old && (old.width !== W || old.height !== H)) {
        const timeFraction = (((old.left + old.right) / 2 - transform.x) / transform.k - old.left) / (old.right - old.left);
        const row = ((old.height / 2 - transform.y) / transform.k - top) / old.gap;
        transform.x = (left + right) / 2 - (left + timeFraction * (right - left)) * transform.k;
        transform.y = H / 2 - (top + row * gap) * transform.k;
      }
      const axisDate = value => dateLabel(value).slice(span / transform.k > 370 * 86400000 ? 0 : 5);
      const bounds = () => {
        const maxX = left * (1 - transform.k), maxY = top * (1 - transform.k);
        return {maxX, minX: right * (1 - transform.k), maxY,
          minY: maxY - Math.max(0, points.length * gap * transform.k - (H - top - 16))};
      };
      const apply = () => {
        transform.k = clamp(Number(transform.k) || 1, 1, 8);
        const limit = bounds();
        transform.x = clamp(Number(transform.x) || 0, limit.minX, limit.maxX);
        transform.y = clamp(Number(transform.y) || 0, limit.minY, limit.maxY);
        extent.style.width = `${W + limit.maxX - limit.minX}px`;
        extent.style.height = `${H + limit.maxY - limit.minY}px`;
        canvas.scrollLeft = limit.maxX - transform.x; canvas.scrollTop = limit.maxY - transform.y;
        layer.setAttribute('transform', `translate(${transform.x} ${transform.y}) scale(${transform.k})`);
        for (const n of points) {
          const y = n.y * transform.k + transform.y;
          n.label.setAttribute('transform', `translate(0 ${y.toFixed(3)})`);
          n.label.style.display = y < top || y > H - 8 ? 'none' : '';
          n.label.querySelector('.affinity-node-count').style.display = gap * transform.k < 42 ? 'none' : '';
          n.unknown?.setAttribute('transform', `translate(0 ${y.toFixed(3)})`);
          if (n.unknown) n.unknown.style.display = n.label.style.display;
          n.knots.forEach((p, i) => {
            p.shape.setAttribute('transform', `scale(${1 / transform.k})`);
            const space = Math.min(i ? p.x - n.knots[i - 1].x : Infinity, i + 1 < n.knots.length ? n.knots[i + 1].x - p.x : Infinity) * transform.k;
            p.shape.querySelector('text').style.display = transform.k >= 1.6 && space > 76 ? '' : 'none';
          });
        }
        axis.replaceChildren(el('text', {x: 12, y: 24}, dated ? `${new Date(start).getUTCFullYear()} · UTC →` : '시간 미확인'));
        grid.replaceChildren();
        if (dated) {
          const target = span / transform.k / Math.max(1, Math.floor((right - left) / 80));
          const steps = [1/24, 1/4, 1/2, 1, 2, 7, 14].map(d => d * 86400000);
          const step = steps.find(s => s >= target) || target;
          const visibleStart = start + ((left - transform.x) / transform.k - left) / (right - left) * span;
          const ticks = [];
          if (target >= 21 * 86400000) {
            const monthStep = [1,2,3,6,12,24,120].find(m => m * 40 * 86400000 >= target) || 120;
            const date = new Date(visibleStart), firstMonth = date.getUTCFullYear() * 12 + date.getUTCMonth();
            for (let m = Math.floor(firstMonth / monthStep) * monthStep, i = 0; i < 30; m += monthStep, i++) {
              const t = Date.UTC(Math.floor(m / 12), m % 12, 1); if (t > end) break; ticks.push(t);
            }
          } else for (let t = Math.ceil(visibleStart / step) * step, i = 0; i < 30 && t <= end; t += step, i++) ticks.push(t);
          for (const t of ticks) {
            const x = xAt(t) * transform.k + transform.x;
            if (x > right + 1) break;
            if (t < start || x < left) continue;
            axis.append(el('text', {x, y: 24, 'text-anchor': 'middle', 'data-time-tick': t}, step < 86400000 ? new Date(t).toISOString().slice(5,16).replace('T',' ') : axisDate(t)));
            grid.append(el('line', {x1: x, x2: x, y1: top - 12, y2: H, class: 'affinity-time-grid'}));
          }
        }
        panel.querySelector('[data-map-zoom]').textContent = `${Math.round(transform.k * 100)}%`;
        panel.querySelector('[data-map-action="in"]').disabled = transform.k >= 8;
        panel.querySelector('[data-map-action="out"]').disabled = transform.k <= 1;
        panel.querySelector('[data-map-action="earlier"]').disabled = !dated || transform.x >= limit.maxX - 1;
        panel.querySelector('[data-map-action="later"]').disabled = !dated || transform.x <= limit.minX + 1;
        const from = start + ((left - transform.x) / transform.k - left) / (right - left) * span;
        const until = start + ((right - transform.x) / transform.k - left) / (right - left) * span;
        panel.querySelector('[data-map-window]').textContent = dated ? `${dateLabel(from)} — ${dateLabel(until)} · 좌우로 탐색` : '시간 미확인 · 위아래로 탐색';
      };
      const at = event => {
        const p = svg.createSVGPoint(); p.x = event.clientX; p.y = event.clientY;
        return p.matrixTransform(svg.getScreenCTM().inverse());
      };
      const move = (next, smooth = true) => {
        cancelAnimationFrame(animation);
        const duration = smooth && !matchMedia('(prefers-reduced-motion: reduce)').matches
          ? parseFloat(getComputedStyle(canvas).getPropertyValue('--motion-state-duration')) || 120 : 0;
        const from = {...transform}, began = performance.now();
        const frame = time => {
          const p = duration ? clamp((time - began) / duration, 0, 1) : 1, eased = 1 - (1 - p) ** 3;
          for (const key of ['x','y','k']) transform[key] = from[key] + (next[key] - from[key]) * eased;
          apply(); if (p < 1) animation = requestAnimationFrame(frame); else save();
        };
        frame(began);
      };
      const zoom = (factor, point = {x: (left + right) / 2, y: H / 2}, smooth = true) => {
        const scale = clamp(transform.k * factor, 1, 8) / transform.k;
        move({x: point.x - (point.x - transform.x) * scale, y: point.y - (point.y - transform.y) * scale, k: transform.k * scale}, smooth);
      };
      panel.querySelector('[data-map-all-edges]').addEventListener('change', e => {
        graph.allEdges = e.target.checked; drawEdges(graph.allEdges); save();
      }, {signal: abort.signal});
      panel.querySelector('[data-map-action="in"]').addEventListener('click', () => zoom(1.25), {signal: abort.signal});
      panel.querySelector('[data-map-action="out"]').addEventListener('click', () => zoom(0.8), {signal: abort.signal});
      const reset = () => move(initial());
      panel.querySelector('[data-map-action="reset"]').addEventListener('click', reset, {signal: abort.signal});
      panel.querySelector('[data-map-action="fit"]').addEventListener('click', () => {
        move({...fitted(), y: top + (transform.y - top) / transform.k});
      }, {signal: abort.signal});
      for (const [action, direction] of [['earlier', 1], ['later', -1]]) {
        panel.querySelector(`[data-map-action="${action}"]`).addEventListener('click', () => {
          move({...transform, x: transform.x + direction * (right - left) * 0.7});
        }, {signal: abort.signal});
      }
      const lens = panel.querySelector('[data-map-action="lens"]'); lens.disabled = !selected;
      lens.addEventListener('click', () => {
        const ids = new Set([selected, ...selectedEdges.flatMap(e => [e.left, e.right])]);
        const nearby = points.filter(n => ids.has(n.id)), anchor = byId.get(selected);
        const knots = nearby.flatMap(n => n.knots), xs = knots.map(p => p.x);
        const minX = xs.length ? Math.min(...xs) : left, maxX = xs.length ? Math.max(...xs) : right;
        const moment = anchor.knots.find(p => p.period === payload.period);
        const k = moment ? 3 : clamp((right - left) / Math.max(80, maxX - minX + 30), 1.6, 4);
        move({k, x: (left + right) / 2 - (moment ? moment.x : (minX + maxX) / 2) * k, y: H / 2 - anchor.y * k});
      }, {signal: abort.signal});
      const highlight = id => {
        const related = new Set([id, ...payload.edges.filter(e => e.left === id || e.right === id).flatMap(e => [e.left,e.right])]);
        for (const n of points) {
          n.strand.classList.toggle('is-muted', Boolean(id) && !related.has(n.id));
          n.strand.classList.toggle('is-hovered', n.id === id); n.label.classList.toggle('is-hovered', n.id === id);
        }
        for (const p of lines.children) p.classList.toggle('is-hovered', Boolean(id) && [p.dataset.left,p.dataset.right].includes(id));
      };
      const inspectHover = e => {
        const target = e.target.closest('[data-strand], [data-affinity-map-node]');
        highlight(target?.dataset.strand || target?.dataset.affinityMapNode);
      };
      canvas.addEventListener('pointerover', inspectHover, {signal: abort.signal});
      canvas.addEventListener('focusin', e => {
        inspectHover(e);
        const target = e.target.closest('[data-affinity-period]');
        if (!target) return;
        const knot = byId.get(target.dataset.strand)?.knots.find(p => p.period === target.dataset.affinityPeriod);
        if (!knot) return;
        const x = knot.x * transform.k + transform.x, y = knot.y * transform.k + transform.y;
        if (x < left + 12 || x > right - 12 || y < top + 12 || y > H - 16)
          move({...transform, x: transform.x + clamp(x, left + 12, right - 12) - x,
            y: transform.y + clamp(y, top + 12, H - 16) - y}, false);
      }, {signal: abort.signal});
      canvas.addEventListener('pointerleave', () => highlight(null), {signal: abort.signal});
      canvas.addEventListener('focusout', () => highlight(null), {signal: abort.signal});
      canvas.addEventListener('wheel', e => {if (e.ctrlKey || e.metaKey) {e.preventDefault(); zoom(e.deltaY > 0 ? 0.9 : 1.1, at(e), false);}}, {passive: false, signal: abort.signal});
      canvas.addEventListener('scroll', () => {
        const limit = bounds(), x = limit.maxX - canvas.scrollLeft, y = limit.maxY - canvas.scrollTop;
        // Ignore scroll notifications caused by projecting our own camera.
        if (Math.abs(transform.x - x) < 1 && Math.abs(transform.y - y) < 1) return;
        cancelAnimationFrame(animation); transform.x = x; transform.y = y; apply(); save();
      }, {passive: true, signal: abort.signal});
      canvas.addEventListener('keydown', e => {
        if (e.target !== canvas || e.altKey || e.ctrlKey || e.metaKey) return;
        if (e.key === '+' || e.key === '=') zoom(1.25, undefined, false);
        else if (e.key === '-') zoom(0.8, undefined, false);
        else if (e.key === '0') reset();
        else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
          transform.x += e.key === 'ArrowLeft' ? 45 : e.key === 'ArrowRight' ? -45 : 0;
          transform.y += e.key === 'ArrowUp' ? 45 : e.key === 'ArrowDown' ? -45 : 0;
          apply(); save();
        } else return;
        e.preventDefault();
      }, {signal: abort.signal});
      let drag = null;
      canvas.addEventListener('pointerdown', e => {
        if (e.button !== 0 || e.pointerType === 'touch' || e.target.closest('a')) return;
        const rect = canvas.getBoundingClientRect();
        if (e.clientX - rect.left >= canvas.clientWidth || e.clientY - rect.top >= canvas.clientHeight) return;
        cancelAnimationFrame(animation);
        drag = {point: at(e), x: transform.x, y: transform.y};
        canvas.setPointerCapture(e.pointerId); canvas.classList.add('is-dragging'); canvas.focus({preventScroll: true});
      }, {signal: abort.signal});
      canvas.addEventListener('pointermove', e => {
        if (!drag) return;
        const p = at(e); transform.x = drag.x + p.x - drag.point.x; transform.y = drag.y + p.y - drag.point.y; apply();
      }, {signal: abort.signal});
      for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(type, () => {
        if (drag) save(); drag = null; canvas.classList.remove('is-dragging');
      }, {signal: abort.signal});
      canvas.replaceChildren(extent); visual.hidden = false;
      const narrow = matchMedia('(max-width: 700px)');
      fallback.open = old?.narrow === false && narrow.matches ? true
        : saved?.scope === scope && typeof saved.listOpen === 'boolean' ? saved.listOpen : narrow.matches;
      narrow.addEventListener('change', e => {if (e.matches) fallback.open = true;}, {signal: abort.signal});
      const viewport = {width: W, height: H, left, right, gap, narrow: narrow.matches};
      graph = {scope, transform, viewport, allEdges, destroy: () => {abort.abort(); observer?.disconnect(); cancelAnimationFrame(animation);}, apply}; apply();
      observer = new ResizeObserver(() => {
        if (Math.abs(canvas.clientWidth - W) < 1 && Math.abs(canvas.clientHeight - H) < 1) return;
        const state = {scope, transform: {...transform}, viewport, allEdges: graph.allEdges, listOpen: fallback.open};
        render(state); save();
      }); observer.observe(canvas);
      if (saved?.scope === scope && saved.traceY) panel.querySelector('.affinity-inspector').scrollTop = saved.traceY;
      fallback.addEventListener('toggle', save, {signal: abort.signal});
      panel.dataset.enhanced = 'true';
    } catch (_) {
      abort.abort(); visual.hidden = true; fallback.open = true;
      panel.querySelector('[data-affinity-render-status]').hidden = false;
      panel.dataset.enhanced = 'failed';
    }
  }

  async function navigate(target, {pop = false, saved = null, search = false, listPage = false} = {}) {
    const ticket = ++generation, prior = graph ? {scope: graph.scope, transform: {...graph.transform}, viewport: graph.viewport, allEdges: graph.allEdges,
      listOpen: root().querySelector('[data-affinity-list]')?.open} : null;
    const oldScroll = scrollY;
    const footerTop = listPage ? root().querySelector('[data-affinity-pagination]')?.getBoundingClientRect().top : null;
    controller?.abort(); controller = new AbortController();
    if (!pop) save();
    root().setAttribute('aria-busy', 'true');
    root().querySelector('[data-affinity-navigation-status]').textContent = '지도를 불러오고 있습니다.';
    try {
      const response = await fetch(target.href, {signal: controller.signal, headers: {Accept: 'text/html'}, cache: 'no-store'});
      if (!response.ok) throw new Error('Unavailable');
      const documentCopy = new DOMParser().parseFromString(await response.text(), 'text/html');
      const next = documentCopy.querySelector('[data-affinity-root]');
      if (!next) throw new Error('Invalid view');
      if (ticket !== generation) return;
      root().replaceWith(next);
      if (!pop) history.pushState({}, '', target.href);
      render(saved || prior);
      if (pop) scrollTo({top: saved?.scrollY || 0, behavior: 'instant'});
      else if (listPage) {
        const footer = next.querySelector('[data-affinity-pagination]');
        footer?.focus({preventScroll: true});
        if (footer && footerTop !== null) scrollTo({top: scrollY + footer.getBoundingClientRect().top - footerTop, behavior: 'instant'});
      }
      else if (target.hash === '#affinity-inspector') {
        const inspector = document.getElementById('affinity-inspector');
        inspector?.focus({preventScroll: true});
        if (innerWidth <= 920) inspector?.scrollIntoView({block: 'start', behavior: 'instant'});
        else scrollTo({top: oldScroll, behavior: 'instant'});
      } else if (search) next.querySelector('[name="q"]')?.focus({preventScroll: true});
      else {next.querySelector('.affinity-toolbar h2')?.setAttribute('tabindex', '-1'); next.querySelector('.affinity-toolbar h2')?.focus({preventScroll: true});}
      next.querySelector('[data-affinity-navigation-status]').textContent = '선택한 범위를 표시했습니다.';
      save();
    } catch (error) {
      if (error.name === 'AbortError' || ticket !== generation) return;
      // An unsuccessful enhancement must not strand a valid native route.
      if (pop) {location.reload(); return;}
      nativeOnly = true;
      const status = root().querySelector('[data-affinity-navigation-status]');
      status.classList.remove('sr-only'); status.classList.add('affinity-render-status');
      status.textContent = '화면을 불러오지 못했습니다. 링크를 다시 누르면 기본 페이지로 엽니다.';
    } finally {if (ticket === generation) root()?.removeAttribute('aria-busy');}
  }

  document.addEventListener('click', e => {
    const link = e.target.closest('[data-affinity-link]');
    if (nativeOnly || !link || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const target = new URL(link.getAttribute('href'), location.href);
    if (target.origin !== location.origin || target.pathname !== '/auto-work') return;
    e.preventDefault(); navigate(target, {listPage: link.hasAttribute('data-affinity-page')});
  });
  document.addEventListener('submit', e => {
    if (nativeOnly || !e.target.matches('[data-affinity-search]')) return;
    e.preventDefault(); const target = new URL('/auto-work', location.origin);
    target.search = new URLSearchParams(new FormData(e.target)); navigate(target, {search: true});
  });
  window.addEventListener('popstate', e => {if (root()) navigate(new URL(location.href), {pop: true, saved: e.state?.affinity});});
  window.addEventListener('pagehide', save);
  window.addEventListener('pageshow', e => {if (e.persisted && graph) graph.apply();});
  render(history.state?.affinity); save();
})();
