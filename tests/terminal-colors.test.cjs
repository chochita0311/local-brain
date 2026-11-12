'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {Terminal: Browser} = require('@xterm/xterm');
const Headless = process.env.LOCALBRAIN_TERMINAL_TEST_ENGINE
  ? require(path.join(process.env.LOCALBRAIN_TERMINAL_TEST_ENGINE, 'node_modules/@xterm/headless')).Terminal : Browser;
const checkpoint = require('../src/localbrain/terminal/checkpoint.cjs');
const {installColorReports, suppressColorReports} = require('../src/localbrain/terminal/colors.cjs');
const write = (t, text) => new Promise(resolve => t.write(text, resolve));
const osc = data => '\x1b]' + data + '\x1b\\';

test('headless answers default, changed, restored and ordered mixed OSC colors', async () => {
  const terminal = new Headless({allowProposedApi: true}), replies = [];
  checkpoint.install(terminal); // checkpoint recording must not change query ordering
  installColorReports(terminal, text => replies.push(text));
  try {
    await write(terminal, osc('11;?') + osc('4;1;?;1;#123456;1;?') + osc('10;#abcdef;?'));
    assert.deepEqual(replies, [osc('11;rgb:1919/1919/1919'), osc('4;1;rgb:cccc/0000/0000'),
      osc('4;1;rgb:1212/3434/5656'), osc('11;rgb:1919/1919/1919')]);
    replies.length = 0;
    await write(terminal, osc('104') + osc('4;1;?') + osc('10;?') + osc('110') + osc('10;?'));
    assert.deepEqual(replies, [osc('4;1;rgb:cccc/0000/0000'), osc('10;rgb:abab/cdcd/efef'),
      osc('10;rgb:ffff/ffff/ffff')]);
  } finally { terminal.dispose(); }
});

test('browser suppresses OSC reports while retaining color mutations in mixed commands', async () => {
  const terminal = new Browser({allowProposedApi: true}), reports = [], colors = [];
  terminal._core._inputHandler.onColor(events => colors.push(...events));
  terminal.onData(text => reports.push(text));
  suppressColorReports(terminal);
  try {
    await write(terminal, osc('4;1;?;2;#123456;3;?') + osc('10;?;#abcdef;?') + osc('12;#112233'));
    assert.deepEqual(reports, []);
    assert.deepEqual(colors.filter(event => event.type === 0), []);
    assert.deepEqual(colors.filter(event => event.type === 1).map(event => [event.index, event.color]),
      [[2, [18, 52, 86]], [257, [171, 205, 239]], [258, [17, 34, 51]]]);
  } finally { terminal.dispose(); }
});
