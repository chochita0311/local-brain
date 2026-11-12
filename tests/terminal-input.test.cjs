'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {attachKoreanInput} = require('../src/localbrain/terminal/korean-input.cjs');

function fixture(ua = 'AppleWebKit/605.1.15') {
  const callbacks = new Map(), sent = [], children = [];
  const textarea = {value: ''};
  const preview = {style: {}, setAttribute() {}, classList: {toggle() {}}, remove() {}};
  const screen = {clientWidth: 300, clientHeight: 160, append: node => children.push(node)};
  const host = {
    ownerDocument: {defaultView: {navigator: {userAgent: ua}}, createElement: () => preview},
    addEventListener: (type, handler) => callbacks.set(type, handler),
    removeEventListener: type => callbacks.delete(type)
  };
  const terminal = {
    textarea, element: {querySelector: () => screen}, cols: 30, rows: 8,
    buffer: {active: {cursorX: 2, cursorY: 1}}, options: {fontSize: 13, fontFamily: 'test'},
    input: value => sent.push(value), onRender: () => ({dispose() {}})
  };
  const adapter = attachKoreanInput(terminal, host);
  function event(type, fields = {}) {
    const value = {target: textarea, ...fields, stopped: false,
      stopImmediatePropagation() { this.stopped = true; }};
    callbacks.get(type)?.(value);
    return value;
  }
  function input(inputType, data, value) {
    textarea.value = value;
    return event('input', {inputType, data});
  }
  const key = (key, keyCode, fields) => event('keydown', {key, keyCode, ...fields});
  return {terminal, adapter, sent, preview, callbacks, children, event, input, key};
}

test('WebKit resyllabification commits only the updated unsent range', () => {
  const f = fixture();
  f.input('insertText', 'ㄱ', 'already-sentㄱ');
  f.input('insertReplacementText', '가', 'already-sent가');
  f.input('insertReplacementText', '간', 'already-sent간');
  f.input('insertReplacementText', '가', 'already-sent가');
  f.input('insertText', '나', 'already-sent가나');
  assert.deepEqual(f.sent, ['가']);
  assert.equal(f.preview.textContent, '나');
  f.input('insertText', ' ', 'already-sent가나\u00a0');
  f.key(' ', 32);
  assert.deepEqual(f.sent, ['가', '나']);
  assert.equal(f.preview.textContent, '');
});

test('Enter flushes one final syllable before normal key processing', () => {
  const f = fixture();
  f.input('insertText', 'ㅎ', 'ㅎ');
  f.input('insertReplacementText', '하', '하');
  f.input('insertReplacementText', '한', '한');
  assert.deepEqual(f.sent, []);
  assert.equal(f.key('ㄴ', 229).stopped, true);
  assert.equal(f.key('Enter', 13).stopped, false);
  assert.deepEqual(f.sent, ['한']);
  f.event('focusout');
  assert.deepEqual(f.sent, ['한']);
});

test('native Backspace edits or deletes pending jamo without a shell DEL', () => {
  const f = fixture();
  f.input('insertText', '한', '한');
  assert.equal(f.key('Backspace', 8).stopped, true);
  f.input('insertReplacementText', '하', '하');
  f.input('insertReplacementText', 'ㅎ', 'ㅎ');
  f.input('deleteContentBackward', null, '');
  f.event('keyup', {keyCode: 8});
  assert.equal(f.key('Backspace', 8).stopped, false);
  f.key('Enter', 13);
  assert.deepEqual(f.sent, []);
});

test('deletion before keydown suppresses that key and releases the next Backspace', () => {
  const f = fixture();
  f.input('insertText', 'ㅎ', 'prefixㅎ');
  f.input('deleteContentBackward', null, 'prefix');
  assert.equal(f.key('Backspace', 8).stopped, true);
  f.event('keyup', {keyCode: 8});
  assert.equal(f.key('Backspace', 8).stopped, false);
  assert.deepEqual(f.sent, []);
});

test('menu paste flushes pending Korean before the clipboard handler sends text', () => {
  const f = fixture();
  f.input('insertText', '한', '한');
  assert.equal(f.event('paste').stopped, false);
  f.terminal.input('pasted');
  f.key('Enter', 13);
  assert.deepEqual(f.sent, ['한', 'pasted']);
});

test('ordinary keyCode 229 fallback is available again after Korean commits', () => {
  const f = fixture();
  f.input('insertText', 'ㅎ', 'ㅎ');
  assert.equal(f.key('ㅎ', 229).stopped, true);
  f.input('insertReplacementText', '한', '한');
  assert.equal(f.key('ㄴ', 229).stopped, true);
  f.key('Enter', 13);
  assert.equal(f.key('.', 229).stopped, false);
  assert.deepEqual(f.sent, ['한']);
});

test('Cmd+V leaves pending Korean for paste confirmation; Ctrl+V commits for literal-next', () => {
  const f = fixture();
  f.input('insertText', '한', '한');
  f.key('v', 86, {metaKey: true, code: 'KeyV'});
  assert.deepEqual(f.sent, []);
  assert.equal(f.preview.textContent, '한');
  // A rejected paste is stopped by the host guard before reaching this adapter.
  f.key('v', 86, {ctrlKey: true, code: 'KeyV'});
  assert.deepEqual(f.sent, ['한']);
});

test('cancellation releases a native composition path before a new WebKit syllable', () => {
  const f = fixture();
  f.event('compositionstart');
  f.adapter.cancel();
  f.input('insertText', '새', '새');
  f.key('Enter', 13);
  assert.deepEqual(f.sent, ['새']);
});

test('Shift keeps a compound pending and a control chord commits once', () => {
  const f = fixture();
  f.input('insertText', 'ㅎ', 'ㅎ');
  f.input('insertReplacementText', '해', '해');
  f.key('Shift', 16, {shiftKey: true});
  assert.deepEqual(f.sent, []);
  f.input('insertReplacementText', '했', '했');
  assert.equal(f.key('c', 67, {ctrlKey: true}).stopped, false);
  assert.deepEqual(f.sent, ['했']);
  assert.equal(f.preview.style.fontSize, '13px');
});

test('native composition handover and its final input stay on xterm path', async () => {
  const f = fixture();
  f.input('insertText', '한', '한');
  f.event('compositionstart');
  assert.deepEqual(f.sent, ['한']);
  assert.equal(f.input('insertText', 'あ', '한あ').stopped, false);
  assert.equal(f.key('Process', 229).stopped, false);
  f.event('compositionend');
  assert.equal(f.input('insertText', '한', '한あ한').stopped, false);
  await new Promise(resolve => setTimeout(resolve, 5));
  assert.deepEqual(f.sent, ['한']);
});

test('lost ownership cancels pending input and later blur cannot replay it', () => {
  const f = fixture();
  f.input('insertText', '한', '한');
  f.terminal.options.disableStdin = true;
  f.adapter.cancel();
  f.event('focusout');
  f.terminal.options.disableStdin = false;
  f.key('Enter', 13);
  assert.deepEqual(f.sent, []);
  assert.equal(f.terminal.textarea.value, '');
});

test('an invalidated textarea prefix never replays prior contents', () => {
  const f = fixture();
  f.input('insertText', 'ㅎ', 'prior-commandㅎ');
  f.input('insertReplacementText', '한', 'unexpected-prior-command한');
  f.key('Enter', 13);
  assert.deepEqual(f.sent, []);
});

test('Chromium has no adapter listeners or preview', () => {
  const f = fixture('AppleWebKit/537.36 Chrome/130.0');
  assert.equal(f.callbacks.size, 0);
  assert.equal(f.children.length, 0);
  f.adapter.dispose();
});

test('disposal removes listeners and discards an uncommitted syllable', () => {
  const f = fixture();
  f.input('insertText', '한', '한');
  f.adapter.dispose();
  f.event('focusout');
  assert.equal(f.callbacks.size, 0);
  assert.deepEqual(f.sent, []);
});
