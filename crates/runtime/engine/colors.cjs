'use strict';

// Shared by headless reports and browser rendering; matches the design's code
// surface/white foreground. Palette values are the pinned xterm6 defaults.
const DEFAULT_THEME = Object.freeze({background: '#191919', foreground: '#ffffff', cursor: '#ffffff'});
const ANSI = [0x2e3436, 0xcc0000, 0x4e9a06, 0xc4a000, 0x3465a4, 0x75507b, 0x06989a, 0xd3d7cf,
  0x555753, 0xef2929, 0x8ae234, 0xfce94f, 0x729fcf, 0xad7fa8, 0x34e2e2, 0xeeeeec];
const rgb = value => [value >>> 16 & 255, value >>> 8 & 255, value & 255];
function defaultColor(index) {
  if (index < 16) return rgb(ANSI[index]);
  if (index < 232) {
    const n = index - 16, ramp = [0, 95, 135, 175, 215, 255];
    return [ramp[Math.floor(n / 36)], ramp[Math.floor(n / 6) % 6], ramp[n % 6]];
  }
  if (index < 256) return Array(3).fill(8 + (index - 232) * 10);
  return rgb(parseInt(DEFAULT_THEME[index === 257 ? 'background' : index === 258 ? 'cursor' : 'foreground'].slice(1), 16));
}
function reportColor(index, color) {
  const ident = index < 256 ? '4;' + index : String(index - 246);
  return '\x1b]' + ident + ';rgb:' + color.map(n => n.toString(16).padStart(2, '0').repeat(2)).join('/') + '\x1b\\';
}
function installColorReports(terminal, send) {
  const palette = new Map();
  return terminal._core._inputHandler.onColor(events => {
    for (const event of events) {
      if (event.type === 0) send(reportColor(event.index, palette.get(event.index) || defaultColor(event.index)));
      else if (event.type === 1) palette.set(event.index, [...event.color]);
      else if (event.index === undefined) {
        for (const index of palette.keys()) if (index < 256) palette.delete(index);
      } else palette.delete(event.index);
    }
  });
}
function suppressColorReports(terminal) {
  const handler = terminal._core._inputHandler;
  terminal.parser.registerOscHandler(4, data => {
    const slots = data.split(';'), kept = [];
    let query = false;
    for (let i = 0; i + 1 < slots.length; i += 2) {
      if (slots[i + 1] === '?') query = true;
      else kept.push(slots[i], slots[i + 1]);
    }
    if (!query) return false;
    if (kept.length) handler.setOrReportIndexedColor(kept.join(';'));
    return true;
  });
  for (let code = 10; code <= 12; code++) terminal.parser.registerOscHandler(code, data => {
    const slots = data.split(';');
    if (!slots.includes('?')) return false;
    handler._setOrReportSpecialColor(slots.map(value => value === '?' ? '' : value).join(';'), code - 10);
    return true;
  });
}
module.exports = {DEFAULT_THEME, defaultColor, reportColor, installColorReports, suppressColorReports};
