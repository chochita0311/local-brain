'use strict';

// This process, not FastAPI or a browser, owns every PTY and logical VT screen.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const net = require('node:net');
const crypto = require('node:crypto');
const {execFile} = require('node:child_process');
const {sameProcess, ownedProcesses, signalTargets} = require('./ownership.cjs');
const checkpoint = require('./checkpoint.cjs');
const {PtyInput} = require('./pty-input.cjs');
const {installColorReports} = require('./colors.cjs');
const root = process.argv[2];
const python = process.argv[3];
const engine = path.join(root, 'engine', 'node_modules');
const pty = require(path.join(engine, 'node-pty'));
const {Terminal} = require(path.join(engine, '@xterm/headless'));
const {SerializeAddon} = require(path.join(engine, '@xterm/addon-serialize'));
const {Unicode11Addon} = require(path.join(engine, '@xterm/addon-unicode11'));
const VERSION = 1;
const buildHash = crypto.createHash('sha256');
for (const name of ['manager.cjs', 'ownership.cjs', 'checkpoint.cjs', 'pty-input.cjs', 'colors.cjs', 'processes.py', 'runtime/package-lock.json']) {
  buildHash.update(name + '\0').update(fs.readFileSync(path.join(__dirname, name)));
}
const build = buildHash.digest('hex');
const MAX_TERMINALS = 32;
const TAIL_BYTES = 128 * 1024;
const MAX_FRAME = 2 * 1024 * 1024;
const generation = crypto.randomBytes(16).toString('hex');
const socketPath = path.join(root, 'control.sock');
const identityPath = path.join(root, 'identity.json');
const terminals = new Map();
const tabs = new Map();
const creations = new Map();
const connections = new Set();
let stopOperations = 0;
let shuttingDown = false;
const isStopping = () => shuttingDown || stopOperations > 0;
let revision = 0;
let lastActivity = Date.now();

class Failure extends Error {
  constructor(code, message) { super(message); this.code = code; }
}
function check(condition, code, message) {
  if (!condition) throw new Failure(code, message);
}
function integer(value, low, high, name) {
  check(Number.isInteger(value) && value >= low && value <= high, 'invalid', name + ' 범위가 올바르지 않습니다.');
  return value;
}
function getTerminal(id) {
  const term = terminals.get(id);
  check(term, 'not_found', '터미널을 찾을 수 없습니다.');
  return term;
}
function publicTerminal(term) {
  return {id: term.id, tabId: term.tabId, name: term.name, cwd: term.cwd,
    shell: term.shell, pid: term.pty.pid, state: term.state, exitCode: term.exitCode,
    cols: term.cols, rows: term.rows, seq: term.seq, unicodeVersion: '11', checkpointVersion: checkpoint.VERSION,
    closing: Boolean(term.ending || (term.shellExited && term.state !== 'exited')), error: term.stopError || null,
    inputError: term.inputError || null,
    controlled: Boolean(term.lease && term.lease.expires > Date.now())};
}
function listing() {
  return {running: true, generation, revision,
    tabs: [...tabs.values()].map(tab => ({...tab, terminals: [...tab.terminals]})),
    terminals: [...terminals.values()].map(publicTerminal)};
}
function pruneCreationHistory() {
  for (const [key, entry] of creations) {
    if (creations.size <= 256) break;
    // Keep every pending/live request; terminal count bounds those entries.
    if (!entry.pending && !terminals.has(entry.terminalId)) creations.delete(key);
  }
}
function changed(term) {
  revision++;
  if (term) {
    term.seq++;
    for (const done of [...term.waiters]) done();
  }
}
function own(term, token) {
  check(term.lease && term.lease.token === token && term.lease.expires > Date.now(),
    'not_owner', '다른 화면에서 제어 중입니다.');
  term.lease.expires = Date.now() + 20000;
}
function confirmedScope(expected, ids = [...terminals.keys()]) {
  check(expected && expected.generation === generation && Array.isArray(expected.terminals)
    && expected.terminals.length === ids.length && new Set(expected.terminals).size === ids.length
    && ids.every(id => expected.terminals.includes(id)), 'conflict',
    '실행 목록이 변경되었습니다. 범위를 다시 확인해 주세요.');
}
let inspection = null;
async function processTable(fresh = false) {
  // Concurrent cleanup shares one short-lived reader. Creation must not use an
  // inventory begun before its PTY was spawned.
  if (fresh && inspection) await inspection.catch(() => {});
  if (!inspection) {
    inspection = new Promise((resolve, reject) => {
      execFile(python, ['-S', path.join(__dirname, 'processes.py')],
        {encoding: 'utf8', timeout: 3000, maxBuffer: 8 * 1024 * 1024,
          env: {...process.env, LC_ALL: 'C', TZ: 'UTC'}}, (error, output) => {
          if (error) { reject(error); return; }
          try { resolve(JSON.parse(output)); } catch (invalid) { reject(invalid); }
        });
    }).finally(() => { inspection = null; });
  }
  return inspection;
}
async function descendants(term) {
  const table = await processTable();
  // forkpty creates a session whose ID is the PTY child's PID. Session membership
  // survives a normal shell exit/reparenting; an explicit setsid is outside it.
  const records = ownedProcesses(term.owner, term.members, term.ownershipLost, table);
  check(records, 'identity', '원래 터미널의 소유권을 확인할 수 없습니다. 다른 작업은 종료하지 않았습니다.');
  term.members = records;
  return records;
}
async function signalOwned(records, signal) {
  const targets = signalTargets(records, await processTable());
  for (const item of targets.reverse()) {
    try { process.kill(item.pid, signal); }
    catch (error) { if (error.code !== 'ESRCH') throw error; }
  }
}
async function waitGone(records, timeout) {
  const until = Date.now() + timeout;
  do {
    const current = new Map((await processTable()).map(item => [item.pid, item]));
    if (records.every(item => !sameProcess(current.get(item.pid), item))) return true;
    await new Promise(resolve => setTimeout(resolve, 50));
  } while (Date.now() < until);
  return false;
}
async function terminate(term, force = false) {
  if (term.ending) return term.ending;
  term.ending = (async () => {
    await term.ready;
    if (term.state === 'running') {
      const records = await descendants(term);
      await signalOwned(records, force ? 'SIGKILL' : 'SIGTERM');
      if (!force) await signalOwned(records, 'SIGHUP');
      if (!(await waitGone(records, force ? 100 : 3000))) {
        await signalOwned(records, 'SIGKILL');
        check(await waitGone(records, 2000), 'stop_failed', '종료를 확인하지 못했습니다.');
      }
      // A child can fork between the first inventory and its signal. Once the
      // shell exits, its remaining POSIX session still belongs to this PTY.
      const deadline = Date.now() + 2000;
      let remaining = await descendants(term);
      while (remaining.length && Date.now() < deadline) {
        await signalOwned(remaining, 'SIGKILL');
        await waitGone(remaining, 100);
        remaining = await descendants(term);
      }
      check(!remaining.length, 'stop_failed', '남은 자식 프로세스의 종료를 확인하지 못했습니다.');
      // The native exit event drains the PTY. Do not leave an unbounded read wait.
      await Promise.race([term.exited, new Promise(resolve => setTimeout(resolve, 500))]);
      term.state = 'exited';
      term.stopError = null;
      changed(term);
    }
  })();
  changed(term);
  try { await term.ending; }
  catch (error) {
    term.ownershipLost = true;
    term.stopError = error instanceof Failure ? error.message : '프로세스 종료를 확인하지 못했습니다.';
    changed(term);
    throw error;
  }
  finally { term.ending = null; }
}
function removeTerminal(term) {
  if (!terminals.has(term.id)) return;
  const tab = tabs.get(term.tabId);
  if (tab) {
    tab.terminals = tab.terminals.filter(id => id !== term.id);
    if (!tab.terminals.length) tabs.delete(tab.id);
  }
  terminals.delete(term.id);
  term.parsed.then(() => term.screen.dispose());
  changed(term);
}
async function stopAll(force) {
  stopOperations++;
  try {
    const targets = [...terminals.values()];
    const results = await Promise.allSettled(targets.map(term => terminate(term, force)));
    check(results.every(item => item.status === 'fulfilled'), 'stop_failed', '일부 터미널의 종료를 확인하지 못했습니다.');
    for (const term of targets) removeTerminal(term);
  } finally { stopOperations--; }
}
async function create(params) {
  check(!isStopping(), 'stopping', '서비스를 중지하고 있습니다.');
  check(terminals.size < MAX_TERMINALS, 'limit', '터미널 한도에 도달했습니다. 사용하지 않는 터미널을 닫아 주세요.');
  const tab = params.tabId ? tabs.get(params.tabId) : null;
  check(!params.tabId || tab, 'not_found', '탭을 찾을 수 없습니다.');
  check(!tab || !tab.closing, 'stopping', '탭을 종료하고 있습니다.');
  check(!tab || tab.terminals.length < 4, 'limit', '탭은 최대 4개로 분할할 수 있습니다.');
  const inherited = tab && terminals.get(tab.terminals[0]);
  const cwdInput = params.cwd === undefined || params.cwd === ''
    ? (inherited && inherited.cwd) || os.homedir() : params.cwd;
  check(typeof cwdInput === 'string' && cwdInput.length <= 4096, 'invalid', '작업 폴더를 확인해 주세요.');
  const cwd = path.resolve(cwdInput.replace(/^~(?=\/|$)/, os.homedir()));
  try {
    check(fs.statSync(cwd).isDirectory(), 'invalid', '작업 폴더를 찾을 수 없습니다.');
    fs.accessSync(cwd, fs.constants.X_OK);
  } catch (_) { throw new Failure('invalid', '작업 폴더에 접근할 수 없습니다.'); }
  const shell = params.shell === undefined || params.shell === ''
    ? process.env.SHELL || '/bin/zsh' : params.shell;
  check(typeof shell === 'string' && path.isAbsolute(shell) && shell.length <= 4096,
    'invalid', '셸 실행 파일의 절대 경로를 입력해 주세요.');
  try { fs.accessSync(shell, fs.constants.X_OK); }
  catch (_) { throw new Failure('invalid', '셸 실행 파일을 찾을 수 없습니다.'); }
  const cols = integer(params.cols ?? 80, 10, 240, '열');
  const rows = integer(params.rows ?? 24, 4, 80, '행');
  const id = 't-' + crypto.randomBytes(6).toString('hex');
  const tabId = tab ? tab.id : 'tab-' + crypto.randomBytes(6).toString('hex');
  const name = path.basename(cwd) || path.basename(shell);
  const screen = new Terminal({cols, rows, scrollback: 1000, allowProposedApi: true});
  screen.loadAddon(new Unicode11Addon());
  screen.unicode.activeVersion = '11';
  const serializer = new SerializeAddon();
  screen.loadAddon(serializer);
  checkpoint.install(screen);
  // No output-triggered clipboard operations; no image or URL addons are installed.
  screen.parser.registerOscHandler(52, () => true);
  const env = {...process.env, TERM: 'xterm-256color', COLORTERM: 'truecolor', TERM_PROGRAM: 'LocalBrain'};
  delete env.LOCALBRAIN_DESKTOP_TOKEN;
  let child;
  try { child = pty.spawn(shell, ['-l'], {name: 'xterm-256color', cols, rows, cwd, env}); }
  catch (_) { screen.dispose(); throw new Failure('spawn_failed', '셸을 시작하지 못했습니다.'); }
  let exited;
  const term = {id, tabId, name, cwd, shell, cols, rows, screen, serializer, pty: child,
    state: 'running', exitCode: null, seq: 0, snapshotSeq: 0, tail: [], tailBytes: 0,
    tailFloor: 0, pendingBytes: 0, parsed: Promise.resolve(), waiters: new Set(),
    lease: null, ending: null, owner: {pid: child.pid, born: null}, members: [], ownershipLost: false,
    exited: new Promise(resolve => { exited = resolve; })};
  terminals.set(id, term);
  if (tab) {
    tab.terminals.push(id);
    tab.direction = params.direction === 'down' ? 'down' : 'right';
  } else tabs.set(tabId, {id: tabId, name, hidden: false, direction: 'right', terminals: [id]});
  screen.onTitleChange(title => {
    if (title) { term.name = title.replace(/[\x00-\x1f\x7f]/g, '').slice(0, 120); revision++; }
  });
  screen.parser.registerOscHandler(7, data => {
    try {
      const url = new URL(data);
      if (url.protocol === 'file:' && ['', 'localhost', os.hostname()].includes(url.hostname)) {
        const reported = decodeURIComponent(url.pathname);
        if (path.isAbsolute(reported) && reported.length <= 4096) term.cwd = reported;
      }
    } catch (_) { /* Unrecognized OSC metadata does not change the start folder. */ }
    return true;
  });
  function inputFailed(message) {
    if (term.inputError || term.shellExited || term.ending) return;
    term.inputError = message;
    child.pause(); changed(term);
  }
  term.input = new PtyInput(child,
    () => inputFailed('터미널 입력 연결을 확인할 수 없습니다. 관리에서 이 터미널을 종료해 주세요.'));
  function reply(data) {
    if (term.state !== 'running' || term.shellExited || term.ending || term.inputError) return;
    if (!term.input.enqueue(data)) inputFailed('터미널 응답이 입력 한도를 초과해 출력을 중지했습니다. 관리에서 이 터미널을 종료해 주세요.');
  }
  screen.onData(reply);
  installColorReports(screen, reply);
  child.onData(data => {
    term.pendingBytes += Buffer.byteLength(data);
    if (term.pendingBytes > 1024 * 1024) child.pause();
    term.parsed = term.parsed.then(() => new Promise(resolve => {
      screen.write(data, () => {
        term.pendingBytes -= Buffer.byteLength(data);
        if (term.pendingBytes < 64 * 1024 && term.state === 'running'
          && !term.inputError && !term.shellExited && !term.ending) child.resume();
        term.seq++;
        const bytes = Buffer.byteLength(data);
        term.tail.push({seq: term.seq, data, bytes});
        term.tailBytes += bytes;
        while (term.tailBytes > TAIL_BYTES && term.tail.length) {
          const first = term.tail.shift();
          term.tailBytes -= first.bytes;
          term.tailFloor = first.seq;
        }
        for (const done of [...term.waiters]) done();
        resolve();
      });
    }));
  });
  child.onExit(({exitCode, signal}) => {
    term.shellExited = true;
    term.input.dispose();
    term.lease = null;
    term.parsed.then(() => {
      term.exitCode = signal ? null : exitCode;
      exited();
      terminate(term).catch(() => { term.stopError = '자식 프로세스 종료를 확인하지 못했습니다.'; changed(term); });
    });
  });
  term.ready = processTable(true).then(table => {
    const owner = table.find(item => item.pid === child.pid && item.parent === process.pid && item.session === child.pid);
    if (owner) { term.owner = owner; term.members = ownedProcesses(owner, [], false, table); }
  }).catch(() => { term.ownershipLost = true; });
  changed(term);
  await term.ready;
  return {terminal: publicTerminal(term), tabId, ...listing()};
}
async function read(term, params, socket) {
  await term.ready;
  const after = Number.isInteger(params.after) ? params.after : -1;
  if (params.lease && term.lease && term.lease.token === params.lease && term.lease.expires > Date.now()) {
    term.lease.expires = Date.now() + 20000;
  }
  if (after === term.seq && term.state === 'running') {
    await new Promise(resolve => {
      const done = () => { clearTimeout(timer); term.waiters.delete(done); socket.off('close', done); resolve(); };
      const timer = setTimeout(done, 10000);
      term.waiters.add(done);
      socket.once('close', done);
    });
  }
  await term.parsed;
  check(terminals.has(term.id), 'not_found', '터미널이 종료되었습니다.');
  const snapshot = after < 0 || after < term.snapshotSeq || after < term.tailFloor;
  if (snapshot && params.checkpointVersion === checkpoint.VERSION) {
    // Drop only history when the frame is large. Never truncate semantic state
    // or replay a suffix on a renderer with an incomplete checkpoint.
    for (const history of [1000, 200, 0]) {
      const state = checkpoint.capture(term.screen, history);
      if (Buffer.byteLength(JSON.stringify(state)) <= checkpoint.LIMIT) {
        return {terminal: publicTerminal(term), seq: term.seq, data: '', checkpoint: state,
          snapshot: true, truncated: state.buffers[0].omitted > 0,
          writable: Boolean(term.lease && term.lease.token === params.lease && term.lease.expires > Date.now())};
      }
    }
    throw new Failure('checkpoint_limit', '현재 화면 상태가 복원 한도를 초과했습니다. 출력이 정리된 뒤 다시 연결해 주세요.');
  }
  let data = snapshot ? term.serializer.serialize({scrollback: 1000})
    : term.tail.filter(part => part.seq > after).map(part => part.data).join('');
  let truncated = false;
  if (Buffer.byteLength(JSON.stringify(data)) > MAX_FRAME / 2) {
    data = term.serializer.serialize({scrollback: 0});
    truncated = true;
  }
  return {terminal: publicTerminal(term), seq: term.seq, data, snapshot: snapshot || truncated, truncated,
    writable: Boolean(term.lease && term.lease.token === params.lease && term.lease.expires > Date.now())};
}
async function handle(method, params, socket) {
  lastActivity = Date.now();
  for (const flag of ['force', 'all', 'takeover']) {
    check(params[flag] === undefined || typeof params[flag] === 'boolean', 'invalid', '옵션 형식을 확인해 주세요.');
  }
  switch (method) {
    case 'status':
      return {running: true, pid: process.pid, generation, version: VERSION, build, stopping: isStopping(),
        terminals: terminals.size, rss: process.memoryUsage().rss, uptime: process.uptime()};
    case 'list': return listing();
    case 'create': {
      check(typeof params.key === 'string' && /^[a-zA-Z0-9-]{16,128}$/.test(params.key),
        'invalid', '생성 요청 식별자가 필요합니다.');
      const fingerprint = JSON.stringify({...params, key: undefined});
      const previous = creations.get(params.key);
      if (previous) {
        check(previous.fingerprint === fingerprint, 'conflict', '다른 생성 요청에 같은 식별자를 사용할 수 없습니다.');
        return previous.promise;
      }
      const promise = create(params);
      const entry = {fingerprint, promise, pending: true, terminalId: null};
      creations.set(params.key, entry);
      // Only a successful creation consumes the key. A corrected environment can retry.
      promise.then(result => {
        entry.pending = false;
        entry.terminalId = result.terminal.id;
        pruneCreationHistory();
      }, () => { if (creations.get(params.key)?.promise === promise) creations.delete(params.key); });
      return promise;
    }
    case 'tab': {
      const tab = tabs.get(params.id);
      check(tab, 'not_found', '탭을 찾을 수 없습니다.');
      if (params.action === 'stop') {
        confirmedScope(params.expected, tab.terminals);
        tab.closing = true;
        try {
          await Promise.all(tab.terminals.map(id => terminate(getTerminal(id), params.force)));
          for (const id of [...tab.terminals]) removeTerminal(getTerminal(id));
        } finally { tab.closing = false; }
      } else if (params.action === 'hide' || params.action === 'show') {
        tab.hidden = params.action === 'hide';
        revision++;
      } else if (params.action === 'rename') {
        check(typeof params.name === 'string' && params.name.trim() && params.name.length <= 120,
          'invalid', '이름은 1~120자로 입력해 주세요.');
        tab.name = params.name.trim(); revision++;
      } else throw new Failure('invalid', '알 수 없는 탭 동작입니다.');
      return listing();
    }
    case 'stop': {
      if (params.all) { confirmedScope(params.expected); await stopAll(params.force); }
      else { const term = getTerminal(params.id); await terminate(term, params.force); removeTerminal(term); }
      return listing();
    }
    case 'claim': {
      const term = getTerminal(params.id);
      check(params.unicodeVersion === '11' && params.checkpointVersion === checkpoint.VERSION,
        'client_update_required', '터미널 화면을 새로고침한 뒤 다시 연결해 주세요.');
      await term.ready;
      check(terminals.has(term.id), 'not_found', '터미널이 종료되었습니다.');
      check(term.state === 'running' && !term.shellExited && !isStopping() && !term.ending, 'exited', '종료된 터미널입니다.');
      const busy = term.lease && term.lease.expires > Date.now();
      if (busy && !params.takeover) return {writable: false, lease: null};
      term.lease = {token: crypto.randomBytes(16).toString('hex'), expires: Date.now() + 20000};
      changed(term);
      return {writable: true, lease: term.lease.token};
    }
    case 'release': {
      const term = getTerminal(params.id);
      if (term.lease && term.lease.token === params.lease) { term.lease = null; changed(term); }
      return {released: true};
    }
    case 'binary':
    case 'input': {
      const term = getTerminal(params.id);
      await term.ready;
      own(term, params.lease);
      check(!isStopping() && !term.shellExited && !term.ending && term.state === 'running', 'exited', '종료된 터미널입니다.');
      check(typeof params.data === 'string' && Buffer.byteLength(params.data) <= 65536,
        'invalid', '입력이 너무 큽니다.');
      let data = params.data;
      if (method === 'binary') {
        check(/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(data),
          'invalid', '바이너리 입력 형식을 확인해 주세요.');
        data = Buffer.from(data, 'base64');
      }
      check(!term.inputError, 'input_failed', term.inputError);
      check(!term.input.closed, 'input_failed', '터미널 입력 연결이 종료되었습니다. 관리에서 이 터미널을 확인해 주세요.');
      check(term.input.enqueue(data), 'input_busy', '프로그램의 입력 처리가 밀려 전송하지 못했습니다. 현재 입력줄을 확인한 뒤 다시 시도해 주세요.');
      return {written: true};
    }
    case 'resize': {
      const term = getTerminal(params.id);
      await term.ready;
      own(term, params.lease);
      const cols = integer(params.cols, 10, 240, '열');
      const rows = integer(params.rows, 4, 80, '행');
      await term.parsed;
      own(term, params.lease);
      check(terminals.has(term.id) && !term.ending && !isStopping(), 'exited', '종료 중인 터미널입니다.');
      term.screen.resize(cols, rows);
      if (term.state === 'running') term.pty.resize(cols, rows);
      term.cols = cols; term.rows = rows; changed(term); term.snapshotSeq = term.seq;
      return {resized: true};
    }
    case 'read': return read(getTerminal(params.id), params, socket);
    case 'shutdown':
      confirmedScope(params.expected);
      shuttingDown = true;
      try { await stopAll(params.force); }
      catch (error) { shuttingDown = false; throw error; }
      setTimeout(() => exitCleanly(), 30);
      return {stopped: true};
    default: throw new Failure('invalid', '알 수 없는 명령입니다.');
  }
}
const server = net.createServer(socket => {
  connections.add(socket);
  socket.setEncoding('utf8');
  let buffer = '';
  let busy = false;
  socket.on('data', chunk => {
    buffer += chunk;
    if (Buffer.byteLength(buffer) > 256 * 1024) { socket.destroy(); return; }
    const end = buffer.indexOf('\n');
    if (end < 0) return;
    if (busy || buffer.indexOf('\n', end + 1) >= 0) { socket.destroy(); return; }
    const line = buffer.slice(0, end); buffer = buffer.slice(end + 1); busy = true;
    Promise.resolve().then(() => {
      const request = JSON.parse(line);
      check(request && typeof request.method === 'string' && request.params &&
        typeof request.params === 'object' && !Array.isArray(request.params),
        'invalid', '요청 형식이 올바르지 않습니다.');
      check(!request.generation || request.generation === generation,
        'conflict', '서비스가 변경되었습니다. 다시 연결해 주세요.');
      return handle(request.method, request.params, socket);
    }).then(result => {
      const reply = JSON.stringify({ok: true, result}) + '\n';
      check(Buffer.byteLength(reply) <= MAX_FRAME, 'limit', '화면 출력 한도를 초과했습니다.');
      if (!socket.destroyed) socket.write(reply);
    }).catch(error => {
      if (!socket.destroyed) socket.write(JSON.stringify({ok: false, error: {
        code: error instanceof Failure ? error.code : 'runtime_error',
        message: error instanceof Failure ? error.message : '터미널 요청을 처리하지 못했습니다.'
      }}) + '\n');
    }).finally(() => { busy = false; });
  });
  socket.on('error', () => {});
  socket.on('close', () => connections.delete(socket));
});
function exitCleanly() {
  server.close();
  for (const socket of connections) socket.destroy();
  try {
    const identity = JSON.parse(fs.readFileSync(identityPath, 'utf8'));
    if (identity.generation === generation) fs.unlinkSync(identityPath);
  } catch (_) { /* A newer owner must never be removed. */ }
  try { fs.unlinkSync(socketPath); } catch (_) {}
  process.exit(0);
}
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, async () => {
  if (shuttingDown) return;
  shuttingDown = true;
  try { await stopAll(true); exitCleanly(); }
  catch (_) { shuttingDown = false; }
});
server.on('error', () => process.exit(1));
processTable(true).then(table => {
  const ownProcess = table.find(item => item.pid === process.pid && !item.dead);
  check(ownProcess?.born, 'identity', '서비스 시작 식별 정보를 확인할 수 없습니다.');
  server.listen(socketPath, () => {
    fs.chmodSync(socketPath, 0o600);
    fs.writeFileSync(identityPath, JSON.stringify({pid: process.pid, born: ownProcess.born, birthFormat: 'utc-lstart-v1', generation, version: VERSION, build}),
      {mode: 0o600, flag: 'wx'});
  });
}).catch(() => process.exit(1));
setInterval(() => {
  if (!terminals.size && !connections.size && Date.now() - lastActivity > 60000) exitCleanly();
}, 5000).unref();
