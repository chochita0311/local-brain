'use strict';

const fs = require('node:fs');
const LIMIT = 256 * 1024;
const PAGE = 16 * 1024;

function writeNonblocking(fd, buffer, offset, length, position, done) {
  let count;
  try { count = fs.writeSync(fd, buffer, offset, length); }
  catch (error) { done(error, 0); return; }
  done(null, count);
}

// node-pty1.1's Unix write queue has no bound/drain API. Its pinned Unix fd
// getter lets this owner retain the same nonblocking writes with an explicit
// byte budget, without changing or patching the installed dependency.
class PtyInput {
  constructor(pty, onError, write = writeNonblocking) {
    this.fd = pty.fd; this.onError = onError;
    this.write = write; this.queue = []; this.bytes = 0;
    this.writing = false; this.closed = false;
    pty.on('close', () => this.dispose());
  }
  enqueue(data) {
    const size = Buffer.isBuffer(data) ? data.length : Buffer.byteLength(data);
    if (this.closed || size + this.bytes > LIMIT) return false;
    if (!size) return true;
    const input = Buffer.isBuffer(data) ? data : Buffer.from(data);
    for (let offset = 0; offset < input.length;) {
      let tail = this.queue.at(-1);
      if (!tail || tail.used === PAGE || this.writing && tail === this.queue[0]) {
        tail = {buffer: Buffer.allocUnsafe(PAGE), used: 0, offset: 0};
        this.queue.push(tail);
      }
      const count = Math.min(PAGE - tail.used, input.length - offset);
      input.copy(tail.buffer, tail.used, offset, offset + count);
      tail.used += count; offset += count;
    }
    this.bytes += size; this.pump();
    return true;
  }
  pump() {
    if (this.closed || this.writing || this.timer || this.immediate || !this.queue.length) return;
    this.writing = true;
    const head = this.queue[0];
    this.write(this.fd, head.buffer, head.offset, head.used - head.offset, null, (error, written) => {
      this.writing = false;
      if (this.closed) return;
      if (error?.code === 'EAGAIN' || !error && written === 0) {
        this.timer = setTimeout(() => { this.timer = null; this.pump(); }, 10);
        return;
      }
      if (error) { this.dispose(); this.onError(); return; }
      head.offset += written; this.bytes -= written;
      if (head.offset === head.used) this.queue.shift();
      // The pinned Unix fd is nonblocking. Keep its syscall in this turn so
      // exit/close cannot race an off-thread write into a reused descriptor.
      // Yield between pages; a full pipe retries later without a busy loop.
      if (this.queue.length) this.immediate = setImmediate(() => { this.immediate = null; this.pump(); });
    });
  }
  dispose() {
    this.closed = true; clearTimeout(this.timer); this.timer = null;
    clearImmediate(this.immediate); this.immediate = null;
    this.queue.length = 0; this.bytes = 0;
  }
}

module.exports = {PtyInput, LIMIT};
