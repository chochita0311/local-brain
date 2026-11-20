'use strict';

// Version-pinned xterm6 adapter. SerializeAddon deliberately omits parser state,
// several modes and cell attributes. Transfer data, never parser handlers/code.
// Call only after the preceding Terminal.write callback has completed.
const VERSION = 'xterm6-v3';
const LIMIT = 1900 * 1024;
const palettes = new WeakMap();
function requireValue(ok) { if (!ok) throw new Error('Invalid terminal checkpoint'); }
function number(n, low = 0, high = 0xffffffff) {
  requireValue(Number.isInteger(n) && n >= low && n <= high); return n;
}
function text(s) { requireValue(typeof s === 'string'); return s; }
function flag(b) { requireValue(typeof b === 'boolean'); return b; }
function list(a, max) { requireValue(Array.isArray(a) && a.length <= max); return a; }
function charset(value) {
  if (value === null || value === undefined) return undefined;
  requireValue(value && typeof value === 'object' && !Array.isArray(value));
  const copy = Object.create(null);
  requireValue(Object.keys(value).length <= 128);
  for (const [key, val] of Object.entries(value)) {
    requireValue(key.length === 1 && typeof val === 'string' && val.length <= 4);
    copy[key] = val;
  }
  return copy;
}
function params(p) {
  return {values: Array.from(p.params), length: p.length, sub: Array.from(p._subParams),
    subLength: p._subParamsLength, indices: Array.from(p._subParamsIdx),
    reject: p._rejectDigits, rejectSub: p._rejectSubDigits, digitSub: p._digitIsSub};
}
function applyParams(target, value) {
  for (const [key, array, max] of [['values', target.params, 0x7fffffff],
    ['sub', target._subParams, 0x7fffffff], ['indices', target._subParamsIdx, 0xffff]]) {
    requireValue(list(value[key], 32).length === array.length);
    array.set(value[key].map(n => number(n, -1, max)));
  }
  target.length = number(value.length, 0, 32);
  target._subParamsLength = number(value.subLength, 0, 32);
  target._rejectDigits = flag(value.reject);
  target._rejectSubDigits = flag(value.rejectSub);
  target._digitIsSub = flag(value.digitSub);
  return target;
}
function attr(a) { return [a.fg, a.bg, a.extended._ext, a.extended.urlId]; }
function applyAttr(target, value, links) {
  requireValue(list(value, 4).length === 4);
  target.fg = number(value[0], -0x80000000); target.bg = number(value[1], -0x80000000);
  target.extended = target.extended.clone();
  target.extended._ext = number(value[2], -0x80000000);
  target.extended.urlId = links.get(number(value[3], 0, Number.MAX_SAFE_INTEGER)) || 0;
}
function install(terminal) {
  if (palettes.has(terminal)) return;
  const palette = new Map();
  palettes.set(terminal, palette);
  terminal._core._inputHandler.onColor(events => {
    for (const event of events) {
      if (event.type === 1) palette.set(event.index, [...event.color]);
      else if (event.type === 2) {
        // OSC104 without an index resets ANSI slots, not foreground/background/cursor.
        if (event.index === undefined) {
          for (const index of palette.keys()) if (index < 256) palette.delete(index);
        } else palette.delete(event.index);
      }
    }
  });
}
function capture(terminal, history = 1000) {
  install(terminal);
  const c = terminal._core, h = c._inputHandler, p = h._parser, bs = c._bufferService;
  requireValue(!h._parseStack.paused && !p._oscParser._stack.paused && !p._dcsParser._stack.paused);
  const markerBuffers = new Map();
  [bs.buffers.normal, bs.buffers.alt].forEach((buffer, index) => {
    for (const marker of buffer.markers) markerBuffers.set(marker, index);
  });
  const linkIds = new Set();
  const remember = a => { const value = attr(a); if (value[3]) linkIds.add(value[3]); return value; };
  const buffers = ['normal', 'alt'].map(name => {
    const b = bs.buffers[name], start = Math.max(0, b.ybase - history);
    const lines = [];
    for (let row = start; row < b.lines.length; row++) {
      const line = b.lines.get(row), runs = [], combined = [], extended = [];
      for (let col = 0; col < line.length; col++) {
        const i = col * 3, data = line._data;
        if (runs.length && data[i] === runs.at(-3) && data[i + 1] === runs.at(-2) && data[i + 2] === runs.at(-1)) runs[runs.length - 4]++;
        else runs.push(1, data[i], data[i + 1], data[i + 2]);
        if (line.isCombined(col)) combined.push([col, line._combined[col]]);
        if (line._extendedAttrs[col] && (data[i + 2] & 0x10000000)) {
          const a = line._extendedAttrs[col];
          extended.push([col, a._ext, a.urlId]); if (a.urlId) linkIds.add(a.urlId);
        }
      }
      lines.push({width: line.length, wrapped: line.isWrapped, runs, combined, extended});
    }
    return {x: b.x, y: b.y, ybase: b.ybase, omitted: start,
      savedX: b.savedX, savedY: b.savedY, savedAttr: remember(b.savedCurAttrData),
      savedCharset: b.savedCharset || null, top: b.scrollTop, bottom: b.scrollBottom,
      tabs: Object.keys(b.tabs).filter(k => b.tabs[k]).map(Number), lines};
  });
  const currentAttr = remember(h._curAttrData), eraseAttr = remember(h._eraseAttrDataInternal);
  // Named links can be reused without any currently printed/current reference.
  // Unreferenced anonymous entries have no VT operation that can select them.
  for (const [id, entry] of c._oscLinkService._dataByLinkId) {
    if (entry.data.id !== undefined) linkIds.add(id);
  }
  const payload = active => ({data: active[0]?._data || '', limited: Boolean(active[0]?._hitLimit)});
  const osc = p._oscParser, dcs = p._dcsParser;
  const result = {version: VERSION, cols: terminal.cols, rows: terminal.rows,
    active: bs.buffer === bs.buffers.alt ? 1 : 0, buffers, currentAttr, eraseAttr,
    modes: {...c.coreService.modes}, dec: {...c.coreService.decPrivateModes},
    cursorHidden: c.coreService.isCursorHidden, cursorInitialized: c.coreService.isCursorInitialized,
    mouse: [c.coreMouseService.activeProtocol, c.coreMouseService.activeEncoding],
    convertEol: terminal.options.convertEol,
    cursorBlink: terminal.options.cursorBlink,
    charset: {level: c._charsetService.glevel, current: c._charsetService.charset || null,
      sets: Array.from(c._charsetService._charsets, value => value || null)},
    parser: {state: p.currentState, collect: p._collect, join: p.precedingJoinState, params: params(p._params),
      osc: {state: osc._state, id: Number.isFinite(osc._id) ? osc._id : null, ...payload(osc._active)},
      dcs: {ident: dcs._ident, ...payload(dcs._active), params: params(dcs._active[0]?._params || p._params)}},
    decoder: {string: h._stringDecoder._interim, utf8: Array.from(h._utf8Decoder.interim)},
    title: [h._windowTitle, h._iconName, [...h._windowTitleStack], [...h._iconNameStack]],
    palette: [...palettes.get(terminal)],
    links: [...linkIds].map(id => {
      const entry = c._oscLinkService._dataByLinkId.get(id);
      let anchors = (entry?.lines || []).map(marker => [markerBuffers.get(marker) ?? -1, marker.line]);
      // A retired-buffer marker never receives further trim/erase events. One
      // such anchor already makes the entry permanent; copying duplicate
      // retired markers would amplify the engine's reset bookkeeping leak.
      if (anchors.some(([buffer]) => buffer < 0)) anchors = [[-1, 0]];
      else anchors = [...new Map(anchors.map(anchor => [anchor.join(':'), anchor])).values()];
      return [id, entry?.data || null, anchors];
    })};
  return result;
}
function restore(terminal, state) {
  requireValue(state?.version === VERSION && JSON.stringify(state).length <= LIMIT);
  const cols = number(state.cols, 10, 240), rows = number(state.rows, 4, 80);
  requireValue(list(state.buffers, 2).length === 2);
  install(terminal);
  const c = terminal._core, h = c._inputHandler, p = h._parser, bs = c._bufferService;
  const cursorInitialized = c.coreService.isCursorInitialized;
  // Public reset intentionally preserves parser/decoder state in xterm6.
  p.reset(); h._stringDecoder.clear(); h._utf8Decoder.clear();
  for (const b of [bs.buffers.normal, bs.buffers.alt]) b.clearAllMarkers();
  terminal.reset(); terminal.resize(cols, rows);
  c._oscLinkService._dataByLinkId.clear(); c._oscLinkService._entriesWithId.clear();
  const linkData = new Map(list(state.links, 100000).map(([id, data, anchors]) => {
    number(id, 0, Number.MAX_SAFE_INTEGER);
    requireValue(data === null || (typeof data.uri === 'string' && (data.id === undefined || typeof data.id === 'string')));
    for (const [buffer, row] of list(anchors, LIMIT)) { number(buffer, -1, 1); number(row, 0, Number.MAX_SAFE_INTEGER); }
    requireValue(data === null || anchors.length > 0);
    return [id, {data, anchors}];
  }));
  const links = new Map();
  for (let index = 0; index < 2; index++) {
    const b = index ? bs.buffers.alt : bs.buffers.normal, v = state.buffers[index];
    const lines = list(v.lines, rows + (index ? 0 : 1000));
    requireValue(lines.length === 0 && index === 1 || lines.length >= rows);
    const omitted = number(v.omitted, 0, index ? 0 : 1000);
    requireValue(omitted + lines.length <= rows + (index ? 0 : 1000));
    b.lines.length = 0;
    // Preserve logical row positions/marker expiry even when old text is omitted.
    // These blank placeholders contain no omitted output and stay within scrollback.
    for (let i = 0; i < omitted; i++) b.lines.push(b.getBlankLine());
    for (const vline of lines) {
      // xterm retains an alternate line's right-hand cells when columns shrink.
      // They become visible again after growth; width is independent of viewport.
      const width = number(vline.width, cols, 240);
      const line = b.getBlankLine(undefined, flag(vline.wrapped));
      if (width !== cols) line.resize(width, b.getNullCell());
      const runs = list(vline.runs, width * 4); requireValue(runs.length % 4 === 0);
      let col = 0;
      for (let r = 0; r < runs.length; r += 4) {
        const count = number(runs[r], 1, width), content = number(runs[r + 1]), fg = number(runs[r + 2]), bg = number(runs[r + 3]);
        requireValue(col + count <= width);
        for (let end = col + count; col < end; col++) line._data.set([content, fg, bg], col * 3);
      }
      requireValue(col === width);
      for (const [col, value] of list(vline.combined, width)) line._combined[number(col, 0, width - 1)] = text(value);
      for (const [col, ext, id] of list(vline.extended, width)) {
        const a = h._curAttrData.extended.clone(); a._ext = number(ext, -0x80000000);
        a.urlId = number(id, 0, Number.MAX_SAFE_INTEGER); line._extendedAttrs[number(col, 0, width - 1)] = a;
      }
      b.lines.push(line);
    }
    b.x = number(v.x, 0, cols); b.y = number(v.y, 0, rows - 1);
    b.ybase = number(v.ybase, 0, Math.max(0, omitted + lines.length - rows)); b.ydisp = b.ybase;
    b.savedX = number(v.savedX, 0, 240); b.savedY = number(v.savedY, 0, 1080);
    b.scrollTop = number(v.top, 0, rows - 1); b.scrollBottom = number(v.bottom, b.scrollTop, rows - 1);
    b.savedCharset = charset(v.savedCharset);
    b.tabs = Object.create(null);
    for (const col of list(v.tabs, 241)) b.tabs[number(col, 0, 240)] = true;
  }
  const serviceLinks = c._oscLinkService;
  for (const [id, {data, anchors}] of linkData) {
    if (data === null) {
      // A native cell can retain a dangling URL ID after selective erase. Keep
      // its derived underline without inventing a resolvable URI or marker.
      links.set(id, serviceLinks._nextId++);
      continue;
    }
    for (let i = 0; i < anchors.length; i++) {
      const [index, row] = anchors[i], b = index === 1 ? bs.buffers.alt : bs.buffers.normal;
      const previous = bs.buffers._activeBuffer, y = b.y;
      bs.buffers._activeBuffer = b; b.y = (index < 0 ? 0 : row) - b.ybase;
      if (i === 0) links.set(id, serviceLinks.registerLink(data));
      else if (index >= 0) {
        // Rebuild marker state, not insertion-time de-duplication. Shrink/pop can
        // leave an otherwise live marker beyond the current line count.
        const entry = serviceLinks._dataByLinkId.get(links.get(id)), marker = b.addMarker(row);
        entry.lines.push(marker);
        marker.onDispose(() => serviceLinks._removeMarkerFromLink(entry, marker));
      }
      if (index < 0) {
        // Native RIS may leave link markers attached to a retired buffer. Such
        // a marker does not receive active-buffer trim/erase events. Recreate a
        // receiver-native detached marker, never a source callback/object graph.
        const entry = serviceLinks._dataByLinkId.get(links.get(id));
        const original = entry.lines[0];
        const marker = new original.constructor(row);
        if (i === 0) entry.lines[0] = marker; else entry.lines.push(marker);
        marker.onDispose(() => serviceLinks._removeMarkerFromLink(entry, marker));
        if (i === 0) original.dispose();
      }
      bs.buffers._activeBuffer = previous; b.y = y;
    }
  }
  for (let index = 0; index < 2; index++) {
    const b = index ? bs.buffers.alt : bs.buffers.normal;
    for (let row = 0; row < b.lines.length; row++) {
      const line = b.lines.get(row);
      for (const a of Object.values(line._extendedAttrs)) a.urlId = links.get(a.urlId) || 0;
    }
  }
  const active = number(state.active, 0, 1) ? bs.buffers.alt : bs.buffers.normal;
  bs.buffers._activeBuffer = active;
  bs.buffers._onBufferActivate.fire({activeBuffer: active, inactiveBuffer: active === bs.buffers.alt ? bs.buffers.normal : bs.buffers.alt});
  applyAttr(h._curAttrData, state.currentAttr, links); applyAttr(h._eraseAttrDataInternal, state.eraseAttr, links);
  state.buffers.forEach((value, i) => applyAttr((i ? bs.buffers.alt : bs.buffers.normal).savedCurAttrData, value.savedAttr, links));
  const service = c.coreService;
  for (const key of Object.keys(service.modes)) service.modes[key] = flag(state.modes[key]);
  for (const key of Object.keys(service.decPrivateModes)) {
    const value = state.dec[key];
    if (key === 'cursorStyle') { requireValue(value === undefined || ['block', 'underline', 'bar'].includes(value)); service.decPrivateModes[key] = value; }
    else if (key === 'cursorBlink' && value === undefined) service.decPrivateModes[key] = undefined;
    else service.decPrivateModes[key] = flag(value);
  }
  service.isCursorHidden = flag(state.cursorHidden);
  service.isCursorInitialized = terminal.element ? cursorInitialized : flag(state.cursorInitialized);
  requireValue(list(state.mouse, 2).length === 2
    && ['NONE', 'X10', 'VT200', 'DRAG', 'ANY'].includes(state.mouse[0])
    && ['DEFAULT', 'SGR', 'SGR_PIXELS'].includes(state.mouse[1]));
  c.coreMouseService.activeProtocol = state.mouse[0]; c.coreMouseService.activeEncoding = state.mouse[1];
  terminal.options.convertEol = flag(state.convertEol);
  terminal.options.cursorBlink = flag(state.cursorBlink);
  c._charsetService._charsets = list(state.charset.sets, 4).map(charset);
  c._charsetService.glevel = number(state.charset.level, 0, 3);
  c._charsetService.charset = charset(state.charset.current);
  requireValue(list(state.title, 4).length === 4);
  h._windowTitle = text(state.title[0]); h._iconName = text(state.title[1]);
  h._windowTitleStack = list(state.title[2], 10).map(text); h._iconNameStack = list(state.title[3], 10).map(text);
  h._onColor.fire([{type: 2}, ...[256, 257, 258].map(index => ({type: 2, index})), ...list(state.palette, 259).map(([index, color]) => {
    number(index, 0, 258); requireValue(list(color, 3).length === 3);
    return {type: 1, index, color: color.map(n => number(n, 0, 65535))};
  })]);
  const saved = state.parser;
  applyParams(p._params, saved.params);
  p.currentState = number(saved.state, 0, 13); p._collect = number(saved.collect, -0x80000000);
  p.precedingJoinState = number(saved.join);
  const osc = p._oscParser, dcs = p._dcsParser;
  osc._state = number(saved.osc.state, 0, 3);
  // A long unknown numeric OSC identifier can overflow the engine's Number.
  osc._id = saved.osc.id === null ? Infinity : number(saved.osc.id, -1, Number.MAX_VALUE);
  osc._active = osc._state === 2 ? osc._handlers[osc._id] || [] : [];
  for (const handler of osc._active) {
    handler.start(); handler._data = text(saved.osc.data); handler._hitLimit = flag(saved.osc.limited);
  }
  dcs.hook(number(saved.dcs.ident), applyParams(p._params.clone(), saved.dcs.params));
  for (const handler of dcs._active) {
    handler._data = text(saved.dcs.data); handler._hitLimit = flag(saved.dcs.limited);
  }
  h._stringDecoder._interim = number(state.decoder.string, 0, 65535);
  requireValue(list(state.decoder.utf8, 3).length === 3);
  h._utf8Decoder.interim.set(state.decoder.utf8.map(n => number(n, 0, 255)));
  bs.isUserScrolling = false;
  bs._cachedBlankLine = undefined;
  bs._onScroll.fire(active.ydisp);
  h._dirtyRowTracker.markAllDirty();
  h._onCursorMove.fire();
  if (terminal.element) terminal.refresh(0, rows - 1);
}

exports.VERSION = VERSION;
exports.LIMIT = LIMIT;
exports.install = install;
exports.capture = capture;
exports.restore = restore;
