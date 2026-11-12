'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {EventEmitter} = require('node:events');
const {PtyInput, LIMIT} = require('../src/localbrain/terminal/pty-input.cjs');

function fixture() {
  const calls = [], output = [], errors = [];
  const pty = Object.assign(new EventEmitter(), {fd: 42});
  const input = new PtyInput(pty, () => errors.push('failed'),
    (fd, buffer, offset, length, position, done) => calls.push({buffer, offset, length, done}));
  function complete(count, error) {
    const call = calls.shift();
    assert.ok(call, 'expected an in-flight OS write');
    if (!error) output.push(Buffer.from(call.buffer.subarray(call.offset, call.offset + count)));
    call.done(error, count);
    return call;
  }
  return {pty, input, calls, output, errors, complete};
}

async function drain(f, size = 16384) {
  for (let turns = 0; f.input.bytes && turns < 10000; turns++) {
    if (f.calls.length) f.complete(Math.min(size, f.calls[0].length));
    await new Promise(resolve => setImmediate(resolve));
  }
  assert.equal(f.input.bytes, 0, 'accepted input must eventually drain');
}

test('partial OS writes preserve byte ordering across Korean, binary and later events', async () => {
  const f = fixture();
  const first = '한글'.repeat(4000), second = Buffer.from([0, 255, 13]), third = 'NEXT';
  assert.equal(f.input.enqueue(first), true);
  assert.equal(f.input.enqueue(second), true);
  assert.equal(f.input.enqueue(third), true);
  await drain(f, 257);
  assert.deepEqual(Buffer.concat(f.output), Buffer.concat([Buffer.from(first), second, Buffer.from(third)]));
  assert.equal(f.input.bytes, 0);
  assert.deepEqual(f.errors, []);
  f.input.dispose();
});

test('a full input budget rejects the whole next event and drains without omissions', async () => {
  const f = fixture();
  const accepted = Buffer.alloc(LIMIT, 65);
  assert.equal(f.input.enqueue(accepted), true);
  assert.equal(f.input.enqueue('한'), false);
  assert.equal(f.input.bytes, LIMIT);
  await drain(f);
  assert.deepEqual(Buffer.concat(f.output), accepted);
  assert.equal(f.input.enqueue('다음'), true);
  await drain(f);
  assert.equal(Buffer.concat(f.output).subarray(LIMIT).toString(), '다음');
  f.input.dispose();
});

test('EAGAIN retains bytes, delays retry, and accepts later input without reordering', async () => {
  const f = fixture();
  f.input.enqueue('FIRST');
  f.complete(0, Object.assign(new Error('blocked'), {code: 'EAGAIN'}));
  f.input.enqueue('SECOND');
  assert.equal(f.calls.length, 0, 'enqueue must not spin while waiting to retry');
  await new Promise(resolve => setTimeout(resolve, 25));
  await drain(f);
  assert.equal(Buffer.concat(f.output).toString(), 'FIRSTSECOND');
  f.input.dispose();
});

test('disposal invalidates in-flight callbacks and cancels a scheduled retry', async () => {
  const f = fixture();
  f.input.enqueue('PENDING');
  f.input.dispose();
  f.complete(1);
  assert.equal(f.calls.length, 0);
  assert.equal(f.input.enqueue('LATE'), false);
  const retry = fixture();
  retry.input.enqueue('PENDING');
  retry.complete(0, Object.assign(new Error('blocked'), {code: 'EAGAIN'}));
  retry.input.dispose();
  await new Promise(resolve => setTimeout(resolve, 25));
  assert.equal(retry.calls.length, 0);
  assert.equal(retry.input.bytes, 0);
});

test('an OS write failure reports once and rejects further input', () => {
  const f = fixture();
  f.input.enqueue('PENDING');
  f.complete(0, Object.assign(new Error('closed'), {code: 'EIO'}));
  assert.deepEqual(f.errors, ['failed']);
  assert.equal(f.input.enqueue('LATE'), false);
  assert.equal(f.input.bytes, 0);
});

test('PTY close retires retries before process exit or descriptor reuse', async () => {
  const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'lb-pty-close-'));
  let fd, replacement;
  try {
    fd = fs.openSync(path.join(folder, 'original'), 'w');
    const pty = Object.assign(new EventEmitter(), {fd});
    let first = true;
    const input = new PtyInput(pty, () => assert.fail('closed writer must not issue a syscall'),
      (number, buffer, offset, length, position, done) => {
        if (first) { first = false; done(Object.assign(new Error('blocked'), {code: 'EAGAIN'}), 0); }
        else done(null, fs.writeSync(number, buffer, offset, length));
      });
    assert.equal(input.enqueue('OLD_TERMINAL_INPUT'), true);
    pty.emit('close'); // the process has not emitted exit
    fs.closeSync(fd); fd = undefined;
    replacement = fs.openSync(path.join(folder, 'replacement'), 'w');
    assert.equal(replacement, pty.fd, 'exercise actual reuse of the numeric descriptor');
    assert.equal(input.enqueue('LATE_OLD_INPUT'), false);
    await new Promise(resolve => setTimeout(resolve, 25));
    assert.equal(input.bytes, 0);
    assert.equal(fs.statSync(path.join(folder, 'replacement')).size, 0);
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
    if (replacement !== undefined) fs.closeSync(replacement);
    fs.rmSync(folder, {recursive: true, force: true});
  }
});
