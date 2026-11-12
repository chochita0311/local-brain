'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {Terminal: Browser} = require('@xterm/xterm');
const {Unicode11Addon} = require('@xterm/addon-unicode11');
const Headless = process.env.LOCALBRAIN_TERMINAL_TEST_ENGINE
  ? require(path.join(process.env.LOCALBRAIN_TERMINAL_TEST_ENGINE, 'node_modules/@xterm/headless')).Terminal : Browser;
const checkpoint = require('../src/localbrain/terminal/checkpoint.cjs');
const E = '\x1b';
const make = Type => {
  const t = new Type({cols: 30, rows: 8, scrollback: 1000, allowProposedApi: true});
  t.loadAddon(new Unicode11Addon()); t.unicode.activeVersion = '11'; checkpoint.install(t);
  return t;
};
const write = (t, s) => new Promise(resolve => t.write(s, resolve));
const transfer = (a, b, history = 1000) => checkpoint.restore(b, JSON.parse(JSON.stringify(checkpoint.capture(a, history))));
// Observe the result through cells/modes and future writes, independently of the
// checkpoint's transport representation. Link IDs themselves are receiver-local.
function observe(t) {
  const buffers = ['normal', 'alternate'].map(name => {
    const b = t.buffer[name];
    return {cursor: [b.cursorX, b.cursorY, b.baseY], lines: Array.from({length: b.length}, (_, y) => {
      const line = b.getLine(y);
      return [line.isWrapped, Array.from({length: line.length}, (_, x) => {
        const cell = line.getCell(x);
        const link = t._core._oscLinkService.getLinkData(cell.extended.urlId);
        return [cell.getChars(), cell.getWidth(), cell.fg, cell.bg, cell.extended._ext, cell.getUnderlineStyle(),
          link ? {id: link.id ?? null, uri: link.uri} : null];
      })];
    })};
  });
  return {buffers, active: t.buffer.active.type, modes: t.modes,
    convertEol: t.options.convertEol, cursorBlink: t.options.cursorBlink,
    hidden: t._core.coreService.isCursorHidden, dec: {...t._core.coreService.decPrivateModes},
    title: t._core._inputHandler._windowTitle};
}
const cases = [
  ['CSI', E + '[31', 'mRED'],
  ['OSC', E + ']0;STA', 'TUS\x07VISIBLE'],
  ['OSC terminator', E + ']0;STA' + E, '\\VISIBLE'],
  ['large OSC identifier', E + ']' + '9'.repeat(400), ';ignored\x07VISIBLE'],
  ['DCS', E + 'P$q', 'm' + E + '\\VISIBLE'],
  ['APC discard', 'A' + E + '_arbitrary', 'payload' + E + '\\B'],
  ['charset ESC', 'A' + E + '(', '0q'],
  ['region', 'ONE\r\nTWO\r\nTHREE' + E + '[2;5r' + E + '[5;1H', '\r\nNEXT'],
  ['saved cursor', 'AAA' + E + '7' + E + '[5;5H', E + '8X'],
  ['tab stops', E + '[3g' + E + '[1;5H' + E + 'H\r', '\tX'],
  ['G1', E + ')0\x0eq', 'q\x0fTEXT'],
  ['protected cell', E + '[1"qA', E + '[?2J'],
  ['underline', E + '[4:3;58:2::255:0:0mA', 'B'],
  ['signed attributes', E + '[9mA', 'B'],
  ['closed link', E + ']8;id=sample;https://example.test/\x07A' + E + ']8;;\x07', 'B'],
  ['open link', E + ']8;id=sample;https://example.test/\x07A', 'B'],
  ['cursor hidden', E + '[?25lA', 'B'],
  ['cursor style', E + '[6 qA', 'B'],
  ['cursor blink', E + '[?12hA', 'B'],
  ['mouse', E + '[?1000h' + E + '[?1006hA', 'B'],
  ['newline', E + '[20hAB', '\nX'],
  ['wrap', '123456789012345678901234567890', 'X'],
  ['Unicode', 'A🧠한글', '\u0301B'],
  ['join after control', 'A' + E + '[m', '\u0301B'],
  ['split surrogate', 'A\ud83e', '\udde0B'],
  ['split UTF8', new Uint8Array([65, 0xf0, 0x9f]), new Uint8Array([0xa7, 0xa0, 66])],
  ['alternate saved cursors', E + '[3;4H' + E + '7' + E + '[?1049hALT' + E + '[2;3H' + E + '7' + E + '[H', E + '8X' + E + '[?1049l' + E + '8Y'],
  ['origin', E + '[2;5r' + E + '[?6h' + E + '[2;3HA', 'B'],
  ['REP', 'A', E + '[3b'],
];
for (const [name, prefix, suffix] of cases) test('checkpoint continuation: ' + name, async () => {
  const a = make(Headless), b = make(Browser);
  try {
    await write(a, prefix);
    // A reused renderer must discard its own partial control and old screen.
    await write(b, 'STALE' + E + ']0;unfinished');
    transfer(a, b);
    assert.deepEqual(observe(b), observe(a));
    await write(a, suffix); await write(b, suffix);
    assert.deepEqual(observe(b), observe(a));
  } finally {a.dispose(); b.dispose();}
});
test('all fragment positions and subsequent resize/reflow preserve future cells', async () => {
  const sequence = '한글A' + E + '[38:2::4:5:6m' + E + ')0\x0eq' + E + '[3g' + E + '[4G' + E + 'H\r\tTEXT';
  for (let split = 0; split <= sequence.length; split++) {
    const a = make(Headless), b = make(Browser);
    try {
      await write(a, sequence.slice(0, split)); transfer(a, b);
      await write(a, sequence.slice(split)); await write(b, sequence.slice(split));
      a.resize(17, 6); b.resize(17, 6);
      await write(a, '\r\nAFTER'); await write(b, '\r\nAFTER');
      assert.deepEqual(observe(b), observe(a), 'split ' + split);
    } finally {a.dispose(); b.dispose();}
  }
});
test('history dropping retains screen, scroll region and saved cursor behavior', async () => {
  const a = make(Headless), b = make(Browser);
  try {
    await write(a, E + '7' + 'history\r\n'.repeat(1200) + E + '[2;6r' + E + '[6;1H');
    transfer(a, b, 0);
    await write(a, '\r\nNEXT' + E + '8X'); await write(b, '\r\nNEXT' + E + '8X');
    const screen = t => Array.from({length: t.rows}, (_, y) => t.buffer.active.getLine(t.buffer.active.baseY + y).translateToString());
    assert.deepEqual(screen(b), screen(a));
    assert.deepEqual([b.buffer.active.cursorX, b.buffer.active.cursorY], [a.buffer.active.cursorX, a.buffer.active.cursorY]);
  } finally {a.dispose(); b.dispose();}
});
test('restored query handler remains receiver-owned and suppresses duplicate replies', async () => {
  const a = make(Headless), b = make(Browser), replies = [];
  b.parser.registerDcsHandler({intermediates: '$', final: 'q'}, () => true);
  b.onData(value => replies.push(value));
  try {
    await write(a, E + 'P$q'); transfer(a, b);
    await write(b, 'm' + E + '\\');
    assert.deepEqual(replies, []);
  } finally {a.dispose(); b.dispose();}
});
test('incompatible or oversized checkpoint cannot be silently imported', () => {
  const a = make(Headless), b = make(Browser);
  try {
    const state = JSON.parse(JSON.stringify(checkpoint.capture(a)));
    assert.throws(() => checkpoint.restore(b, {...state, version: 'future'}));
    assert.throws(() => checkpoint.restore(b, {...state, cols: 999}));
    assert.throws(() => checkpoint.restore(b, {...state, title: ['x'.repeat(checkpoint.LIMIT), '', [], []]}));
  } finally {a.dispose(); b.dispose();}
});
test('ANSI palette reset preserves separately changed foreground/background/cursor', async () => {
  const a = make(Headless), b = make(Browser);
  try {
    await write(a, E + ']11;rgb:11/22/33\x07' + E + ']4;1;rgb:ff/00/00\x07' + E + ']104\x07');
    const state = checkpoint.capture(a);
    assert.deepEqual(state.palette, [[257, [17, 34, 51]]]);
    transfer(a, b);
    assert.deepEqual(checkpoint.capture(b).palette, state.palette);
  } finally {a.dispose(); b.dispose();}
});
test('pending-wrap tab at the maximum column does not prevent reconnection', async () => {
  const a = make(Headless), b = make(Browser);
  try {
    a.resize(240, 8);
    await write(a, 'X'.repeat(240) + E + 'H');
    transfer(a, b);
    await write(a, '\r\tY'); await write(b, '\r\tY');
    assert.deepEqual(observe(b), observe(a));
  } finally {a.dispose(); b.dispose();}
});
test('long-lived link ID allocation is not restricted to a packed uint32 cell', async () => {
  const a = make(Headless), b = make(Browser);
  try {
    a._core._oscLinkService._nextId = 2 ** 32 + 1;
    await write(a, E + ']8;;https://example.test/\x07A');
    transfer(a, b); await write(a, 'B'); await write(b, 'B');
    assert.deepEqual(observe(b), observe(a));
  } finally {a.dispose(); b.dispose();}
});
test('alternate-screen shrink/checkpoint/grow retains the hidden right-hand cells', async () => {
  const a = make(Headless), b = make(Browser);
  try {
    await write(a, E + '[?1049h' + 'A'.repeat(15) + E + '[31m' + 'RIGHT_EDGE');
    a.resize(17, 8);
    await write(b, 'STALE' + E + '[31');
    transfer(a, b);
    assert.deepEqual(observe(b), observe(a));
    a.resize(30, 8); b.resize(30, 8);
    await write(a, E + '[2;1HNEXT'); await write(b, E + '[2;1HNEXT');
    assert.deepEqual(observe(b), observe(a));
    assert.match(b.buffer.alternate.getLine(0).translateToString(true), /RIGHT_EDGE/);
  } finally {a.dispose(); b.dispose();}
});
for (const [name, prefix, suffix, history] of [
  ['unprinted open link', E + ']8;;https://example.test/\x07' + E + '[2;1H', E + '[H' + E + '[JX', 1000],
  ['closed unprinted link reused later', E + ']8;id=sample;https://example.test/\x07' + E + ']8;;\x07' + E + '[2;1H', E + ']8;id=sample;https://example.test/\x07' + E + '[H' + E + '[JX', 1000],
  ['omitted history link marker', E + ']8;id=sample;https://example.test/\x07' + E + ']8;;\x07' + '\r\n'.repeat(500), E + ']8;id=sample;https://example.test/\x07' + E + '[H' + E + '[JX', 0],
  ['link surviving native reset', E + ']8;id=sample;https://example.test/\x07' + E + ']8;;\x07' + E + 'c' + E + '[2;1H', E + ']8;id=sample;https://example.test/\x07' + E + '[H' + E + '[JX', 1000],
  ['protected link after marker removal', E + ']8;;https://example.test/\x07' + E + '[1"qA' + E + '[2;1H' + E + '[?2J', E + '[H' + E + '[0"qB', 1000],
]) test('link lifetime: ' + name, async () => {
  const a = make(Headless), b = make(Browser);
  try {
    await write(a, prefix);
    await write(b, 'STALE' + E + '[31');
    transfer(a, b, history);
    await write(a, suffix); await write(b, suffix);
    assert.deepEqual(observe(b), observe(a));
  } finally {a.dispose(); b.dispose();}
});
test('height shrink retains a native link marker beyond the remaining lines', async () => {
  const a = make(Headless), b = make(Browser);
  try {
    await write(a, E + '[8;1H' + E + ']8;id=sample;https://example.test/\x07X' + E + ']8;;\x07' + E + '[H');
    a.resize(30, 4); transfer(a, b);
    await write(a, E + ']8;id=sample;https://example.test/\x07Y');
    await write(b, E + ']8;id=sample;https://example.test/\x07Y');
    a.resize(30, 8); b.resize(30, 8);
    assert.deepEqual(observe(b), observe(a));
  } finally {a.dispose(); b.dispose();}
});
test('repeated resets coalesce equivalent permanent link anchors', async () => {
  const a = make(Headless), b = make(Browser);
  const open = E + ']8;id=sample;https://example.test/\x07', close = E + ']8;;\x07';
  try {
    await write(a, open + close + E + 'c' + (E + '[2;1H' + open + close + E + '[H' + E + '[M' + E + 'c').repeat(2160));
    const entry = [...a._core._oscLinkService._dataByLinkId.values()][0];
    assert.ok(entry.lines.length > 2160);
    const state = checkpoint.capture(a);
    assert.deepEqual(state.links[0][2], [[-1, 0]]);
    transfer(a, b);
    await write(a, open + E + '[H' + E + '[JX'); await write(b, open + E + '[H' + E + '[JX');
    assert.deepEqual(observe(b), observe(a));
  } finally {a.dispose(); b.dispose();}
});
test('resize replaces truncated history with the manager checkpoint before later output', async () => {
  const a = make(Headless), b = make(Browser);
  try {
    await write(a, 'A'.repeat(360) + '\r\n'); transfer(a, b, 0);
    // The managed view requests resize; it never reflows omitted text itself.
    a.resize(60, 8); transfer(a, b, 0);
    await write(a, 'Z'); await write(b, 'Z');
    assert.deepEqual(observe(b), observe(a));
  } finally {a.dispose(); b.dispose();}
});
