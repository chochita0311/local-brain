import {Terminal, FitAddon, Unicode11Addon, checkpointVersion, restoreCheckpoint, attachKoreanInput, DEFAULT_THEME, suppressColorReports} from './vendor/xterm/terminal.esm.js?v=9f95fc72cd8f';

const page = document.querySelector('[data-terminal-page]');
const $ = name => page.querySelector('[data-terminal-' + name + ']');
const views = new Map();
const narrow = matchMedia('(max-width: 700px)');
let model = null;
let activeTab = null;
let focusedPane = null;
let requestNumber = 0;
let tabKey = '';
let managerKey = '';
let createTarget = null;
let createFingerprint = null;
let working = false;
let feedbackSource = null;
let fontReady = false;

async function loadFonts() {
  $('font-retry').hidden = true;
  feedback('터미널 글꼴 불러오는 중…', 'font');
  try {
    // A distinct URL-only family avoids silently substituting an installed font.
    const faces = await Promise.all([400, 700].map(weight =>
      document.fonts.load(weight + ' 13px "LocalBrain Terminal"', 'Aa한글\ue0b0')));
    if (faces.some(loaded => !loaded.length || loaded.some(face => face.status !== 'loaded'))) throw new Error();
    fontReady = true;
    if (feedbackSource === 'font') feedback();
  } catch (_) {
    feedback('터미널 글꼴을 불러오지 못했습니다.', 'font');
    $('font-retry').hidden = false;
  }
  reconcile();
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function button(text, action, className = 'secondary-button') {
  const node = element('button', className, text);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}
function feedback(message = '', source = 'action') {
  feedbackSource = message ? source : null;
  for (const name of ['error', 'manage-error']) {
    $(name).textContent = message;
    $(name).hidden = !message;
  }
}
async function api(url, body) {
  let response, data;
  try {
    response = await fetch('/api/terminal' + url, body === undefined ? {} : {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
  } catch (_) { throw new Error('웹 서버에 연결할 수 없습니다.'); }
  try { data = await response.json(); }
  catch (_) { throw new Error('서버 응답을 확인할 수 없습니다.'); }
  if (!response.ok) {
    const error = new Error(data.error?.message || data.detail || '요청을 완료하지 못했습니다.');
    error.status = response.status; error.code = data.error?.code;
    throw error;
  }
  return data;
}
async function refresh() {
  const number = ++requestNumber;
  try {
    const data = await api('');
    if (number !== requestNumber) return;
    model = data;
    if (feedbackSource === 'connection') feedback();
    if (data.service.unclean) feedback('관리 서비스가 예기치 않게 종료되었습니다. 이전 작업이 남아 있을 수 있습니다.', 'recovery');
    else if (feedbackSource === 'recovery') feedback();
    reconcile();
  } catch (error) {
    if (number !== requestNumber) return;
    feedback(error.message, 'connection');
    if (model) {
      model.service = {...model.service, state: 'unknown', running: null};
      renderManagement();
    }
    $('new').disabled = $('empty-action').disabled = true;
  }
  finally { page.setAttribute('aria-busy', 'false'); }
}
async function mutate(url, body = {}) {
  try {
    feedback();
    await api(url, body);
    await refresh();
  } catch (error) { feedback(error.message); }
}
function currentTab() { return model?.tabs.find(tab => tab.id === activeTab && !tab.hidden); }
function liveCount(ids) {
  return model.terminals.filter(term => term.state === 'running' && (!ids || ids.includes(term.id))).length;
}
function expectedScope(ids = model.terminals.map(term => term.id)) {
  return {generation: model.generation, terminals: [...ids]};
}
function confirmStop(ids, service = null) {
  const count = liveCount(ids);
  return !count || confirm('터미널 ' + count + '개를 종료'
    + (service === 'restart' ? '하고 서비스를 재시작' : service ? '하고 서비스를 중지' : '') + '할까요?');
}
function selectTab(id, focusTerminal = true) {
  activeTab = id;
  focusedPane = model.tabs.find(tab => tab.id === id)?.terminals[0] || null;
  reconcile();
  if (focusTerminal) requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
}
async function closeTab(tab) {
  if (confirmStop(tab.terminals)) await mutate('/tabs/' + tab.id + '/stop', {expected: expectedScope(tab.terminals)});
}
function renderTabs() {
  const key = JSON.stringify([activeTab, model.tabs.map(tab => [tab.id, tab.name, tab.hidden, tab.terminals])]);
  if (key === tabKey) return;
  tabKey = key;
  const fragment = document.createDocumentFragment();
  for (const tab of model.tabs.filter(item => !item.hidden)) {
    const holder = element('div', 'terminal-tab' + (tab.id === activeTab ? ' selected' : ''));
    const select = button(tab.name, () => selectTab(tab.id), '');
    select.setAttribute('role', 'tab');
    select.setAttribute('aria-selected', String(tab.id === activeTab));
    select.tabIndex = tab.id === activeTab ? 0 : -1;
    select.title = tab.name;
    select.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const tabs = model.tabs.filter(item => !item.hidden);
      const index = tabs.findIndex(item => item.id === tab.id);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1
        : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      selectTab(tabs[next].id, false);
      $('tabs').querySelector('[aria-selected="true"]')?.focus();
    });
    const close = button('×', () => closeTab(tab), 'terminal-close');
    close.setAttribute('aria-label', tab.name + ' 탭 닫기 및 종료');
    holder.append(select, close);
    fragment.append(holder);
  }
  $('tabs').replaceChildren(fragment);
}
function serviceState() {
  if (model.service.unclean) return '이전 작업 확인 필요';
  return {running: '실행 중', stopped: '중지됨', unknown: '연결 실패',
    incompatible: '버전 확인 필요', unsupported: 'macOS 웹 전용'}[model.service.state] || '상태 미확인';
}
function renderManagement() {
  $('service-state').textContent = serviceState();
  const running = ['running', 'incompatible'].includes(model.service.state);
  page.querySelector('[data-terminal-service="start"]').disabled = running || !model.dependencies.installed;
  page.querySelector('[data-terminal-service="stop"]').disabled = !running;
  page.querySelector('[data-terminal-service="restart"]').disabled = !running;
  $('stop-all').disabled = !model.terminals.length;
  const key = JSON.stringify([model.tabs, model.terminals.map(t => [t.id, t.name, t.cwd, t.state, t.closing, t.error, t.inputError])]);
  if (key === managerKey) return;
  managerKey = key;
  const fragment = document.createDocumentFragment();
  if (!model.tabs.length) fragment.append(element('span', '', '터미널 없음'));
  for (const tab of model.tabs) {
    const row = element('div', 'terminal-managed-row');
    const copy = element('div', 'terminal-managed-copy');
    const title = element('strong', '', tab.name);
    const terms = model.terminals.filter(item => tab.terminals.includes(item.id));
    copy.append(title, element('small', '', (tab.hidden ? '백그라운드 · ' : '표시 중 · ') + terms.length + '개'));
    const actions = element('div', 'terminal-actions');
    const open = button(tab.hidden ? '열기' : '보기', async () => {
      if (tab.hidden) await mutate('/tabs/' + tab.id + '/show');
      $('manage-dialog').close();
      selectTab(tab.id);
    });
    open.setAttribute('aria-label', tab.name + ' 탭 열기');
    actions.append(open);
    if (!tab.hidden) {
      const background = button('백그라운드', () => mutate('/tabs/' + tab.id + '/hide'));
      background.setAttribute('aria-label', tab.name + ' 탭 백그라운드로 보내기');
      actions.append(background);
    }
    const end = button('터미널 종료', () => closeTab(tab));
    end.setAttribute('aria-label', tab.name + ' 탭의 터미널 종료');
    actions.append(end);
    row.append(copy, actions);
    fragment.append(row);
    for (const term of terms) {
      const detail = element('details');
      const state = term.error ? ' · 종료 확인 필요' : term.closing ? ' · 종료 중'
        : term.state === 'exited' ? ' · 종료됨' : term.inputError ? ' · 입력 오류' : '';
      detail.append(element('summary', '', term.name + state));
      const path = element('p', '', term.cwd);
      const identity = element('code', '', term.id);
      detail.append(path, identity, button('종료', () => closePane(term)));
      if (term.error || term.inputError) detail.append(element('p', 'terminal-feedback', term.error || term.inputError));
      fragment.append(detail);
    }
  }
  $('managed-list').replaceChildren(fragment);
}
async function closePane(term) {
  if (confirmStop([term.id])) await mutate('/terminals/' + term.id + '/stop');
}
async function createTerminal(source = null, direction = null) {
  if (!fontReady || !model?.dependencies.installed || working || !['running', 'stopped'].includes(model.service.state)) return;
  const body = source ? {tabId: source.tabId, direction, cwd: source.cwd, shell: source.shell} : {};
  const fingerprint = JSON.stringify(source ? {id: source.id, direction} : {});
  working = true; feedback(); reconcile();
  try {
    if (!createTarget || createFingerprint !== fingerprint) {
      const paths = source ? body : await api('/settings?launch=true');
      createTarget = {...paths, key: crypto.randomUUID()}; createFingerprint = fingerprint;
    }
    const result = await api('/terminals', createTarget);
    activeTab = result.tabId; focusedPane = result.terminal.id;
    createTarget = null; createFingerprint = null;
    await refresh();
    requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
  } catch (error) {
    if (error.status && error.status < 500 && !['disconnected', 'unavailable', 'runtime_error'].includes(error.code)) createTarget = null;
    feedback(error.message);
  } finally {working = false; await refresh();}
}
async function install() {
  if (working) return;
  working = true;
  $('empty-action').disabled = true;
  $('empty-text').textContent = '구성요소 설치 중…';
  try { await api('/install', {}); }
  catch (error) { feedback(error.message); }
  finally { working = false; await refresh(); }
}
function reconcile() {
  if (!model) return;
  const visible = model.tabs.filter(tab => !tab.hidden);
  if (!visible.some(tab => tab.id === activeTab)) activeTab = visible[0]?.id || null;
  const tab = currentTab();
  if (!tab?.terminals.includes(focusedPane)) focusedPane = tab?.terminals[0] || null;
  $('count').textContent = model.service.running === null ? '—' : String(liveCount());
  $('new').disabled = !fontReady || !model.dependencies.installed || working || model.service.state === 'incompatible';
  $('tab-menu').hidden = !tab;
  renderTabs();
  renderManagement();
  $('empty').hidden = Boolean(tab);
  $('empty-action').disabled = !fontReady || working || !model.dependencies.node || !model.dependencies.npm
    || !['running', 'stopped'].includes(model.service.state);
  if (!model.dependencies.node || !model.dependencies.npm) {
    $('empty-text').textContent = 'Node.js 20 이상이 필요합니다.';
    $('empty-action').hidden = true;
  } else {
    $('empty-action').hidden = false;
    $('empty-action').textContent = model.dependencies.installed
      ? model.tabs.length ? '실행 중 보기' : '새 터미널' : '구성요소 설치';
    $('empty-text').textContent = working ? '구성요소 설치 중…' : model.tabs.length ? '백그라운드에서 실행 중' : '터미널 없음';
  }
  const allTerms = tab ? tab.terminals.map(id => model.terminals.find(term => term.id === id)).filter(Boolean) : [];
  $('pane-select').hidden = !narrow.matches || allTerms.length < 2;
  const options = allTerms.map(term => {
    const option = element('option', '', term.name); option.value = term.id; return option;
  });
  $('pane-select').replaceChildren(...options);
  $('pane-select').value = focusedPane || '';
  const shown = !fontReady ? [] : narrow.matches ? allTerms.filter(term => term.id === focusedPane) : allTerms;
  const ids = new Set(shown.map(term => term.id));
  for (const [id, view] of views) if (!ids.has(id)) { view.dispose(); views.delete(id); }
  $('workspace').className = 'terminal-workspace' + (shown.length === 1 ? ' single' : '')
    + (tab?.direction === 'down' ? ' down' : '') + (shown.length > 2 ? ' multi' : '');
  for (const term of shown) {
    if (!views.has(term.id)) {
      const view = new Pane(term);
      views.set(term.id, view);
      $('workspace').append(view.node);
      view.open();
    }
    views.get(term.id).update(term, tab);
  }
}
class Pane {
  constructor(term) {
    this.id = term.id;
    this.info = term;
    this.alive = true;
    this.writable = false;
    this.outbox = [];
    this.outboxBytes = 0;
    this.painted = false;
    this.historyTruncated = false;
    this.node = element('section', 'terminal-pane');
    this.node.setAttribute('aria-label', term.name);
    const header = element('header', 'terminal-pane-header');
    this.name = element('span', 'terminal-pane-name', term.name);
    this.status = element('span', 'terminal-pane-status', '연결 중');
    this.take = button('제어권 가져오기', () => this.send({type: 'claim'}), 'terminal-takeover');
    this.take.hidden = true;
    const menu = element('details', 'terminal-menu');
    const summary = element('summary', '', '⋯'); summary.setAttribute('aria-label', '터미널 메뉴');
    const actions = element('div', 'terminal-menu-items');
    this.right = button('오른쪽 분할', () => { menu.open = false; createTerminal(this.info, 'right'); }, '');
    this.down = button('아래쪽 분할', () => { menu.open = false; createTerminal(this.info, 'down'); }, '');
    actions.append(this.right, this.down);
    menu.append(summary, actions);
    const close = button('×', () => closePane(this.info), 'shell-icon-button');
    close.setAttribute('aria-label', '이 터미널 닫기 및 종료');
    header.append(this.name, this.status, this.take, menu, close);
    this.body = element('div', 'terminal-pane-body');
    this.body.dataset.terminalInput = '';
    this.host = element('div', 'terminal-emulator');
    this.body.append(this.host);
    this.node.append(header, this.body);
    this.node.addEventListener('focusin', () => {
      focusedPane = this.id;
      for (const [id, view] of views) view.node.classList.toggle('focused', id === this.id);
    });
    const styles = getComputedStyle(document.documentElement);
    this.terminal = new Terminal({
      cols: term.cols, rows: term.rows, scrollback: 1000, convertEol: false,
      fontFamily: styles.getPropertyValue('--terminal-font-family').trim(),
      allowProposedApi: true,
      screenReaderMode: true, disableStdin: true,
      theme: {...DEFAULT_THEME}
    });
    this.terminal.loadAddon(new Unicode11Addon());
    // Old running managers retain their original width rules until explicitly updated.
    this.terminal.unicode.activeVersion = term.unicodeVersion === '11' ? '11' : '6';
    this.fitAddon = new FitAddon();
    this.terminal.loadAddon(this.fitAddon);
    this.terminal.attachCustomKeyEventHandler(event => {
      if (event.isComposing || event.keyCode === 229) return true;
      if (event.type === 'keydown' && event.key === 'Escape' && event.shiftKey) {
        event.preventDefault();
        summary.focus();
        return false;
      }
      return true;
    });
    this.body.title = 'Shift+Esc: 터미널 메뉴로 이동';
    this.terminal.parser.registerOscHandler(52, () => true);
    suppressColorReports(this.terminal);
    this.terminal.parser.registerDcsHandler({intermediates: '$', final: 'q'}, () => true);
    for (const final of ['n', 'c']) for (const prefix of ['', '?', '>', '=']) {
      this.terminal.parser.registerCsiHandler({prefix, final}, () => true);
    }
    this.terminal.parser.registerCsiHandler({final: 't'}, params => [14, 16, 18, 20, 21].includes(params[0]));
    this.painting = Promise.resolve();
    for (const prefix of ['', '?']) {
      this.terminal.parser.registerCsiHandler({prefix, intermediates: '$', final: 'p'}, () => true);
    }
    this.terminal.onData(data => { if (this.writable) this.send({type: 'input', data}); });
    this.terminal.onBinary(data => { if (this.writable) this.send({type: 'binary', data: btoa(data)}); });
    this.body.addEventListener('paste', event => {
      const data = event.clipboardData?.getData('text/plain') || '';
      if (new TextEncoder().encode(data).length > 64000) {
        event.preventDefault(); event.stopImmediatePropagation(); feedback('붙여넣을 내용이 너무 큽니다.');
      } else if (/[\r\n]/.test(data) && !this.terminal.modes.bracketedPasteMode && !confirm('여러 줄을 붙여넣을까요?')) {
        event.preventDefault(); event.stopImmediatePropagation();
      }
    }, true);
    this.resizeObserver = new ResizeObserver(() => this.fit());
  }
  async open() {
    await document.fonts.ready;
    if (!this.alive) return;
    this.terminal.options.fontSize = parseFloat(getComputedStyle(this.body).fontSize);
    this.terminal.open(this.host);
    this.koreanInput = attachKoreanInput(this.terminal, this.host);
    this.resizeObserver.observe(this.body);
    this.connect();
  }
  update(info, tab) {
    this.info = info;
    if (info.error) this.showStatus('종료 확인 필요');
    this.name.textContent = info.name;
    this.name.title = info.cwd;
    this.right.textContent = tab?.terminals.length > 1 ? '분할 추가' : '오른쪽 분할';
    this.down.hidden = tab?.terminals.length > 1;
    this.right.disabled = this.down.disabled = !tab || tab.terminals.length >= 4 || working
      || !['running', 'stopped'].includes(model.service.state);
    this.node.classList.toggle('focused', focusedPane === this.id);
  }
  showStatus(text) {
    this.status.textContent = text + (this.historyTruncated ? ' · 이력 생략' : '');
    this.status.title = this.historyTruncated ? '화면 복원에서 이전 출력 일부를 생략했습니다.' : '';
  }
  control(writable) {
    this.writable = writable;
    this.terminal.options.disableStdin = !writable || !this.painted || Boolean(this.info.inputError);
    if (!writable || this.info.inputError) { this.koreanInput?.cancel(); this.discardInput(); }
    this.take.hidden = writable || this.info.state !== 'running' || this.ws?.readyState !== WebSocket.OPEN;
    this.showStatus(this.info.error ? '종료 확인 필요' : this.info.state === 'exited' ? '종료됨'
      : this.info.inputError ? '입력 오류' : this.info.closing ? '종료 중' : writable ? '실행 중' : '읽기 전용');
    if (writable) this.fit();
  }
  send(value) {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      if (['input', 'binary'].includes(value.type)) feedback('연결이 끊겨 입력을 보내지 못했습니다.');
      return false;
    }
    const values = [];
    if (value.type === 'input') {
      // Bound both UTF-8 payloads and JSON escaping without splitting a surrogate pair.
      for (let start = 0; start < value.data.length;) {
        let end = Math.min(start + 8192, value.data.length);
        if (end < value.data.length && /[\uD800-\uDBFF]/.test(value.data[end - 1])) end--;
        values.push({...value, data: value.data.slice(start, end)}); start = end;
      }
    } else values.push(value);
    const packets = values.map(item => {
      const data = JSON.stringify(item);
      return {data, bytes: new TextEncoder().encode(data).length, input: ['input', 'binary'].includes(item.type),
        paste: value.type === 'input' && value.data.startsWith('\x1b[200~')};
    });
    const bytes = packets.reduce((sum, item) => sum + item.bytes, 0);
    if (this.outboxBytes + bytes > 512 * 1024) {
      feedback('연결이 밀려 입력을 보내지 못했습니다. 연결을 확인한 뒤 다시 입력해 주세요.');
      return false;
    }
    this.outbox.push(...packets); this.outboxBytes += bytes;
    this.flush();
    return true;
  }
  flush() {
    clearTimeout(this.sendTimer);
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    while (this.outbox.length && this.ws.bufferedAmount <= 65536) {
      const packet = this.outbox.shift(); this.outboxBytes -= packet.bytes;
      try { this.ws.send(packet.data); }
      catch (_) { feedback('연결이 끊겨 입력을 보내지 못했습니다.'); this.ws.close(); return; }
    }
    if (this.outbox.length) this.sendTimer = setTimeout(() => this.flush(), 16);
  }
  discardInput() {
    if (this.outbox.some(item => item.input)) {
      feedback(this.outbox.some(item => item.paste)
        ? '붙여넣기가 일부만 전송됐을 수 있습니다. 연결 후 Ctrl+C로 현재 입력을 취소하고 다시 확인해 주세요.'
        : '미전송 입력을 취소했습니다. 일부 입력은 전송됐을 수 있으니 현재 입력줄을 확인해 주세요.');
      this.outbox = this.outbox.filter(item => !item.input);
      this.outboxBytes = this.outbox.reduce((sum, item) => sum + item.bytes, 0);
    }
  }
  clearOutbox() {
    clearTimeout(this.sendTimer);
    this.discardInput();
    this.outbox = []; this.outboxBytes = 0;
  }
  connect() {
    if (!this.alive || document.hidden || this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) return;
    this.koreanInput?.cancel();
    this.clearOutbox();
    this.painted = false;
    this.terminal.options.disableStdin = true;
    const url = new URL('/api/terminal/terminals/' + this.id + '/stream', location.href);
    url.searchParams.set('unicode', this.terminal.unicode.activeVersion);
    url.searchParams.set('checkpoint', checkpointVersion);
    url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(url);
    this.ws = ws;
    this.showStatus('연결 중');
    ws.onmessage = event => {
      if (!this.alive || this.ws !== ws) return;
      const frame = JSON.parse(event.data);
      if (frame.type === 'control') this.control(frame.writable);
      if (frame.type === 'error') {
        const interrupted = ['input_busy', 'input_failed'].includes(frame.code);
        if (interrupted) this.clearOutbox();
        feedback(this.info.checkpointVersion && this.info.checkpointVersion !== checkpointVersion
          ? '터미널 서비스의 버전이 다릅니다. 작업을 마친 뒤 관리에서 서비스를 재시작해 주세요.'
          : interrupted ? frame.message + ' 입력이 일부만 전달됐을 수 있습니다. 연결 후 Ctrl+C로 확인해 주세요.' : frame.message,
        interrupted ? 'input:' + this.id : 'stream:' + this.id);
      }
      if (frame.type !== 'output') return;
      if (frame.snapshot) this.historyTruncated = Boolean(frame.truncated);
      this.info = {...this.info, ...frame.terminal};
      if (typeof frame.writable === 'boolean') this.control(frame.writable);
      this.painting = this.painting.then(async () => {
        if (this.ws !== ws || !this.alive) return;
        if (frame.checkpoint) restoreCheckpoint(this.terminal, frame.checkpoint);
        else {
          if (frame.snapshot) {
            if (frame.terminal.checkpointVersion === checkpointVersion) throw new Error('화면 복원 데이터를 확인할 수 없습니다.');
            this.terminal._core._inputHandler._parser.reset();
            this.terminal.reset();
            this.terminal.resize(frame.terminal.cols, frame.terminal.rows);
          }
          await new Promise(resolve => this.terminal.write(frame.data, resolve));
        }
        if (this.ws !== ws || !this.alive) return;
        this.painted = true;
        if (this.info.inputError) feedback(this.info.inputError, 'stream:' + this.id);
        else if (feedbackSource === 'stream:' + this.id) feedback();
        this.control(this.writable);
        this.send({type: 'ack', seq: frame.seq});
        this.fit();
      }).catch(() => {
        if (this.ws !== ws || !this.alive) return;
        feedback('터미널 화면을 복원하지 못했습니다. 다시 연결합니다.', 'stream:' + this.id);
        ws.close();
      });
    };
    ws.onclose = () => {
      if (!this.alive || this.ws !== ws) return;
      this.koreanInput?.cancel();
      this.clearOutbox();
      this.writable = false;
      this.terminal.options.disableStdin = true;
      this.take.hidden = true;
      this.showStatus(this.info.error ? '종료 확인 필요' : this.info.state === 'exited' ? '종료됨' : '연결 끊김');
      if (!document.hidden && this.info.state === 'running') this.retry = setTimeout(() => this.connect(), 2000);
    };
    ws.onerror = () => ws.close();
  }
  fit() {
    cancelAnimationFrame(this.fitFrame);
    this.fitFrame = requestAnimationFrame(() => {
      if (!this.alive || !this.painted || !this.writable || document.hidden || !this.body.clientWidth) return;
      const dimensions = this.fitAddon.proposeDimensions();
      if (!dimensions) return;
      const cols = Math.max(10, Math.min(240, dimensions.cols));
      const rows = Math.max(4, Math.min(80, dimensions.rows));
      if (this.terminal.cols !== cols || this.terminal.rows !== rows) {
        this.send({type: 'resize', cols, rows});
      }
    });
  }
  disconnect() {
    this.koreanInput?.cancel();
    this.clearOutbox();
    clearTimeout(this.retry);
    this.ws?.close();
  }
  dispose() {
    this.koreanInput?.dispose();
    this.clearOutbox();
    this.alive = false;
    clearTimeout(this.retry);
    cancelAnimationFrame(this.fitFrame);
    this.resizeObserver.disconnect();
    this.ws?.close();
    this.terminal.dispose();
    this.node.remove();
  }
}
$('new').addEventListener('click', () => createTerminal());
page.addEventListener('click', event => {
  for (const menu of page.querySelectorAll('.terminal-menu[open]')) {
    if (!menu.contains(event.target)) menu.open = false;
  }
});
page.addEventListener('focusin', event => {
  for (const menu of page.querySelectorAll('.terminal-menu[open]')) {
    if (!menu.contains(event.target)) menu.open = false;
  }
});
page.addEventListener('keydown', event => {
  if (event.key !== 'Escape' || event.shiftKey) return;
  const menu = event.target.closest('.terminal-menu[open]');
  if (!menu) return;
  menu.open = false;
  menu.querySelector('summary').focus();
  event.preventDefault(); event.stopPropagation();
}, true);
$('empty-action').addEventListener('click', () => {
  if (!model.dependencies.installed) return install();
  if (model.tabs.length) $('manage-dialog').showModal();
  else createTerminal();
});
$('manage').addEventListener('click', () => $('manage-dialog').showModal());
page.querySelectorAll('[data-terminal-dialog-close]').forEach(node => node.addEventListener('click', () => node.closest('dialog').close()));
$('pane-select').addEventListener('change', event => {
  focusedPane = event.target.value; reconcile();
  requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
});
$('background').addEventListener('click', async () => {
  const tab = currentTab();
  $('tab-menu').open = false;
  if (tab) await mutate('/tabs/' + tab.id + '/hide');
});
$('rename').addEventListener('click', async () => {
  const tab = currentTab(); if (!tab) return;
  $('tab-menu').open = false;
  const name = prompt('탭 이름', tab.name);
  if (name?.trim()) await mutate('/tabs/' + tab.id + '/rename', {name: name.trim()});
});
$('stop-all').addEventListener('click', () => {
  if (confirmStop()) mutate('/stop', {expected: expectedScope()});
});
page.querySelectorAll('[data-terminal-service]').forEach(node => node.addEventListener('click', async () => {
  const action = node.dataset.terminalService;
  if (action !== 'start' && !confirmStop(null, action)) return;
  node.disabled = true;
  await mutate('/service/' + action, action === 'start' ? {} : {expected: expectedScope()});
}));
narrow.addEventListener('change', reconcile);
document.addEventListener('visibilitychange', () => {
  for (const view of views.values()) document.hidden ? view.disconnect() : view.connect();
  if (!document.hidden) refresh();
});
window.addEventListener('pagehide', () => { for (const view of views.values()) view.dispose(); views.clear(); });
window.addEventListener('pageshow', event => { if (event.persisted) refresh(); });
setInterval(() => { if (!document.hidden && !working) refresh(); }, 3000);
$('font-retry').addEventListener('click', () => location.reload());
loadFonts();
refresh();
