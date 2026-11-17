import {Terminal, FitAddon, Unicode11Addon, checkpointVersion, restoreCheckpoint, attachKoreanInput, DEFAULT_THEME, suppressColorReports} from './vendor/xterm/terminal.esm.js?v=9f95fc72cd8f';
import {terminalStatus, terminalIndicator, programTitle, workspaceGroups, latestTerminal, cleanShellExit, orderedTabs} from './terminal-state.js?v=e9569dec2fc8';

const page = document.querySelector('[data-terminal-page]');
const $ = name => page.querySelector('[data-terminal-' + name + ']');
const views = new Map();
const narrow = matchMedia('(max-width: 700px)');
const compact = matchMedia('(max-width: 1100px)');
let model = null;
let activeTab = null;
let focusedPane = null;
let requestNumber = 0;
let tabKey = '';
let managerKey = '';
let createTarget = null;
let working = false;
let feedbackSource = null;
let fontReady = false;
let activeWorkspace = null;
let railCollapsed = compact.matches;
let railKey = '';
let attentionGeneration = null;
let confirmedRead = 0;
const seenCompletions = new Map();
const workspaceTabs = new Map();
let renameEditor = null;
let dragState = null;
let suppressTabClickUntil = 0;
let pendingOrder = null;
let orderSaving = false;
let retiring = false;
const retiredAttempts = new Set();
const pendingCloses = new Map();
let workspaceEditor = null;
let workspaceSaving = false;
let folderTarget = null;
let workspaceMoveKey = '';
let backgroundInitialized = false;

function icon(name, className = '') {
  const namespace = 'http://www.w3.org/2000/svg';
  const node = document.createElementNS(namespace, 'svg');
  node.setAttribute('class', 'app-icon ' + className);
  node.setAttribute('viewBox', '0 0 960 960');
  node.setAttribute('aria-hidden', 'true');
  node.setAttribute('focusable', 'false');
  if (!name) return node;
  if (name === 'view_dot') {
    const dot = document.createElementNS(namespace, 'circle');
    dot.setAttribute('cx', '480'); dot.setAttribute('cy', '480'); dot.setAttribute('r', '160');
    dot.setAttribute('fill', 'currentColor'); node.append(dot);
    return node;
  }
  if (name === 'view_ring') {
    const ring = document.createElementNS(namespace, 'circle');
    ring.setAttribute('cx', '480'); ring.setAttribute('cy', '480'); ring.setAttribute('r', '128');
    ring.setAttribute('fill', 'none'); ring.setAttribute('stroke', 'currentColor');
    ring.setAttribute('stroke-width', '64'); node.append(ring);
    return node;
  }
  if (name === 'view_diamond') {
    const outline = document.createElementNS(namespace, 'polygon');
    outline.setAttribute('points', '480,160 800,480 480,800 160,480');
    outline.setAttribute('fill', 'none'); outline.setAttribute('stroke', 'currentColor');
    outline.setAttribute('stroke-width', '64'); node.append(outline);
    return node;
  }
  const use = document.createElementNS(namespace, 'use');
  const sprite = page.querySelector('[data-terminal-new] use').getAttribute('href').split('#')[0];
  use.setAttribute('href', sprite + '#' + name);
  node.append(use);
  return node;
}
function tabsInOrder() {
  return orderedTabs(model.tabs, pendingOrder?.generation === model.generation
    ? pendingOrder.order : model.presentation?.order || []);
}
function groups() { return workspaceGroups(model.workspaces, tabsInOrder()); }
function groupForTab(id) { return groups().find(group => group.tabs.some(tab => tab.id === id)); }
function currentWorkspace() { return groups().find(group => group.id === activeWorkspace); }
function visibleTabs() { return currentWorkspace()?.tabs.filter(tab => !tab.hidden) || []; }
function statusOf(term) { return terminalStatus(term, seenCompletions.get(term.id) || 0); }
function indicatorSymbol(terms, options) {
  const state = terminalIndicator(terms, options), node = icon(state.icon, 'terminal-view-symbol terminal-view-' + state.key);
  const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
  title.textContent = state.label; node.prepend(title);
  return node;
}
function commandBadge(term) {
  const state = statusOf(term), node = element('span', 'terminal-command-state terminal-state-' + state.key);
  node.hidden = !['error', 'failed', 'done', 'closing', 'exited'].includes(state.key);
  node.title = '셸 · ' + state.label;
  node.setAttribute('role', 'img'); node.setAttribute('aria-label', node.title);
  if (!node.hidden) node.append(icon(state.icon, 'terminal-state-symbol'));
  return node;
}
function programIndicator(terms) {
  const node = element('span', 'terminal-program-indicator');
  node.dataset.terminalProgram = JSON.stringify(terms.map(term => term.id));
  node.setAttribute('role', 'img'); node.setAttribute('aria-label', '프로그램 제목의 활동 표시');
  updateProgramIndicator(node);
  return node;
}
function updateProgramIndicator(node) {
  const ids = JSON.parse(node.dataset.terminalProgram);
  const terms = ids.map(id => model.terminals.find(term => term.id === id)).filter(Boolean);
  const reporting = terms.filter(term => programTitle(term.name).indicator);
  const term = reporting.find(term => term.id === focusedPane) || reporting[0];
  node.textContent = term ? programTitle(term.name).indicator : '';
  node.hidden = !term;
  node.title = term ? '프로그램 제목: ' + term.name : '';
}
function updateProgramIndicators(root) {
  for (const node of root.querySelectorAll('[data-terminal-program]')) updateProgramIndicator(node);
}
function applyRail() {
  page.classList.toggle('rail-collapsed', railCollapsed);
  $('rail').inert = railCollapsed;
  $('rail-toggle').setAttribute('aria-expanded', String(!railCollapsed));
  $('rail-toggle').hidden = !railCollapsed;
  $('rail-toggle').setAttribute('aria-label', '터미널 작업 탐색 펼치기');
}
function setBackgroundOpen(open) {
  $('hidden-list').hidden = !open;
  $('hidden-open').setAttribute('aria-expanded', String(open));
}
function revealBackground() {
  backgroundInitialized = true;
  setBackgroundOpen(true);
  railCollapsed = false; applyRail();
  $('hidden-open').focus({preventScroll: true});
}
function updateWindowFocus() {
  page.classList.toggle('window-inactive', document.hidden || !document.hasFocus());
}
function updateStatusbar() {
  if (!model) return;
  const view = views.get(focusedPane), term = view?.info || model.terminals.find(term => term.id === focusedPane);
  $('location').textContent = term?.cwd || currentWorkspace()?.cwd || '이 컴퓨터';
  $('location').title = term?.cwd || currentWorkspace()?.cwd || '이 컴퓨터';
  $('command').textContent = term ? '셸 · ' + statusOf(term).label : '';
  $('command').title = $('command').textContent;
  $('connection').textContent = view ? view.ws?.readyState === WebSocket.OPEN
    ? !view.painted ? '화면 복원 중' : view.writable && !view.info.inputError ? '입력 가능' : '읽기 전용'
    : '연결 중' : serviceState();
}
function markSeen(view) {
  const completion = view.renderedCompletion;
  if (!completion || !view.painted || document.hidden || !document.hasFocus()
    || focusedPane !== view.id || view.terminal.textarea !== document.activeElement) return;
  if (completion <= (seenCompletions.get(view.id) || 0)) return;
  seenCompletions.set(view.id, completion);
  renderTabs(); renderRail(); view.updateSymbol();
}
function selectGroup(id) {
  if (renameEditor) { saveTabName(false).then(saved => { if (saved) selectGroup(id); }); return; }
  if (activeTab) workspaceTabs.set(activeWorkspace, activeTab);
  activeWorkspace = id;
  const tabs = visibleTabs(), remembered = workspaceTabs.get(id);
  activeTab = tabs.find(tab => tab.id === remembered)?.id || tabs[0]?.id || null;
  focusedPane = null;
  reconcile();
  if (compact.matches) { railCollapsed = true; applyRail(); }
}
async function openExisting(tab, terminalId = null) {
  if (renameEditor && !(await saveTabName(false))) return;
  if (tab.hidden) {
    try { await api('/tabs/' + tab.id + '/show', {}); await refresh(); }
    catch (error) { feedback(error.message); return; }
  }
  $('manage-dialog').close();
  selectTab(tab.id, false);
  if (terminalId && currentTab()?.terminals.includes(terminalId)) { focusedPane = terminalId; reconcile(); }
  if (compact.matches && !railCollapsed) { railCollapsed = true; applyRail(); }
  requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
}
function renderRail() {
  updateProgramIndicators($('rail'));
  const folders = groups();
  const key = JSON.stringify([activeWorkspace, activeTab, focusedPane, folders, model.terminals.map(term =>
    [term.id, programTitle(term.name).title, term.state, term.error, term.closing, term.inputError, term.activity, seenCompletions.get(term.id)])]);
  $('hidden-count').textContent = String(model.tabs.filter(tab => tab.hidden).length);
  if (!backgroundInitialized) {
    setBackgroundOpen(model.tabs.some(tab => tab.hidden)); backgroundInitialized = true;
  }
  const hiddenIds = new Set(model.tabs.filter(tab => tab.hidden).flatMap(tab => tab.terminals));
  const hiddenStates = model.terminals.filter(term => hiddenIds.has(term.id)).map(statusOf);
  const errors = hiddenStates.filter(state => state.priority === 0).length;
  const completions = hiddenStates.filter(state => state.key === 'done').length;
  $('hidden-open').classList.toggle('has-error', errors > 0);
  $('hidden-open').classList.toggle('has-completion', !errors && completions > 0);
  $('hidden-open').setAttribute('aria-label', '백그라운드 탭 ' + model.tabs.filter(tab => tab.hidden).length + '개'
    + (errors ? ' · 오류 ' + errors + '개' : '') + (completions ? ' · 새 완료 ' + completions + '개' : ''));
  $('rail-service').textContent = serviceState();
  if (key === railKey) return;
  railKey = key;
  const folderNodes = folders.map(group => {
    const node = button('', () => selectGroup(group.id), 'terminal-group' + (group.id === activeWorkspace ? ' selected' : ''));
    node.title = group.name + (group.cwd ? ' · 기본 폴더 ' + group.cwd : '');
    node.setAttribute('aria-label', group.name + ' 작업공간');
    node.dataset.terminalFocus = 'workspace:' + group.id;
    node.setAttribute('aria-pressed', String(group.id === activeWorkspace));
    const visibleCount = group.tabs.filter(tab => !tab.hidden).length;
    node.title += ' · 열린 탭 ' + visibleCount + '개 · 백그라운드 ' + (group.tabs.length - visibleCount) + '개';
    node.append(icon('space_dashboard'), element('span', 'terminal-group-name', group.name), element('small', '', String(visibleCount)));
    const row = element('div', 'terminal-group-row');
    const edit = button('⋯', () => editWorkspace(group), 'shell-icon-button terminal-group-edit');
    edit.setAttribute('aria-label', group.name + ' 작업공간 설정');
    edit.dataset.terminalFocus = 'workspace-edit:' + group.id;
    row.append(node, edit);
    return row;
  });
  if (!folderNodes.length) folderNodes.push(element('p', 'terminal-rail-empty', '작업공간을 추가하세요.'));
  replaceRows($('groups'), folderNodes);
  const openMenus = new Set([...$('tasks').querySelectorAll('details[open]')].map(node => node.dataset.terminalTaskMenu));
  const foreground = new Set(model.tabs.filter(tab => !tab.hidden).flatMap(tab => tab.terminals));
  const tasks = model.terminals.filter(term => foreground.has(term.id)).sort((a, b) => statusOf(a).priority - statusOf(b).priority);
  $('task-count').textContent = String(tasks.length);
  const taskNodes = tasks.map(term => {
    const tab = model.tabs.find(tab => tab.terminals.includes(term.id)), group = groupForTab(tab?.id);
    const state = statusOf(term);
    const displayName = tab?.terminals.length === 1 ? tab.name : programTitle(term.name).title;
    const node = button('', () => openExisting(tab, term.id), 'terminal-task' + (term.id === focusedPane ? ' selected' : ''));
    node.title = displayName + ' · ' + terminalIndicator([term], {current: term.id === focusedPane}).label + ' · 셸 · ' + state.label + ' · ' + term.cwd;
    node.setAttribute('aria-label', node.title);
    node.dataset.terminalFocus = 'task:' + term.id;
    const copy = element('span', 'terminal-task-copy');
    const context = [...new Set([tab?.terminals.length > 1 ? tab.name : '', group?.name || '작업 공간'])]
      .filter(name => name && name !== displayName).join(' · ');
    copy.append(element('span', 'terminal-task-name', displayName));
    if (context && context !== displayName) copy.append(element('small', '', context));
    node.append(indicatorSymbol([term], {current: term.id === focusedPane}), programIndicator([term]), copy, commandBadge(term));
    const row = element('div', 'terminal-task-row');
    const menu = element('details', 'terminal-menu terminal-task-menu');
    menu.dataset.terminalTaskMenu = term.id;
    menu.open = openMenus.has(term.id);
    const summary = element('summary');
    summary.setAttribute('aria-label', displayName + ' 작업 메뉴');
    summary.dataset.terminalFocus = 'task-menu:' + term.id;
    summary.append(icon('more_horiz'));
    const items = element('div', 'terminal-menu-items');
    const action = (name, key, callback) => {
      const item = button(name, () => { setMenuOpen(menu, false); callback(); });
      item.dataset.terminalFocus = 'task-action:' + key + ':' + term.id;
      items.append(item);
    };
    action('터미널로 이동', 'open', () => openExisting(tab, term.id));
    action(tab.terminals.length > 1 ? '탭 전체를 백그라운드로 · ' + tab.terminals.length + '개' : '백그라운드로 보내기', 'background', () => backgroundTab(tab));
    action('탭 이름 변경', 'rename', async () => {
      if (renameEditor && !(await saveTabName(false))) return;
      selectTab(tab.id, false);
      if (compact.matches) { railCollapsed = true; applyRail(); }
      startTabRename(tab.id);
    });
    action('이 터미널 종료', 'stop', () => closePane(term));
    menu.append(summary, items);
    row.append(node, menu);
    return row;
  });
  if (!taskNodes.length) taskNodes.push(element('p', 'terminal-rail-empty', '열린 터미널 없음'));
  replaceRows($('tasks'), taskNodes);
  for (const menu of $('tasks').querySelectorAll('details[open]')) positionMenu(menu);
  const hidden = model.tabs.filter(tab => tab.hidden).map(tab => {
    const row = element('div', 'terminal-task-row terminal-background-row');
    row.dataset.terminalHiddenTab = tab.id;
    const terms = model.terminals.filter(term => tab.terminals.includes(term.id));
    const lead = [...terms].sort((a, b) => statusOf(a).priority - statusOf(b).priority)[0];
    const copy = element('span', 'terminal-task-copy');
    copy.append(element('span', 'terminal-task-name', tab.name));
    const group = groupForTab(tab.id)?.name;
    const open = button('', () => openExisting(tab), 'terminal-task');
    open.dataset.terminalFocus = 'hidden:' + tab.id;
    open.title = tab.name + ' 백그라운드 탭 다시 열기 · 터미널 ' + terms.length + '개'
      + (group ? ' · 작업공간 ' + group : '')
      + (lead ? ' · 셸 · ' + statusOf(lead).label : '');
    open.setAttribute('aria-label', open.title);
    open.append(indicatorSymbol(terms, {hidden: true}), programIndicator(terms), copy);
    if (lead) {
      open.append(commandBadge(lead));
    }
    if (terms.length > 1) open.append(element('small', 'terminal-tab-count', String(terms.length)));
    const end = button('×', () => closeTab(tab), 'shell-icon-button');
    end.dataset.terminalFocus = 'hidden-stop:' + tab.id;
    end.title = tab.name + ' 백그라운드 탭 종료 · 터미널 ' + terms.length + '개';
    end.setAttribute('aria-label', end.title);
    row.append(open, end);
    return row;
  });
  const hiddenHadFocus = $('hidden-list').contains(document.activeElement);
  replaceRows($('hidden-list'), hidden.length ? hidden : [element('p', 'terminal-rail-empty', '백그라운드 터미널 없음')]);
  if (hiddenHadFocus && !$('hidden-list').contains(document.activeElement)) $('hidden-open').focus({preventScroll: true});
  queueMicrotask(retireCleanExits);
}

function positionMenu(menu) {
  const items = menu.querySelector('.terminal-menu-items'), trigger = menu.querySelector('summary').getBoundingClientRect();
  items.setAttribute('role', 'menu');
  const summary = menu.querySelector('summary');
  summary.setAttribute('aria-haspopup', 'menu'); summary.setAttribute('aria-expanded', 'true');
  for (const item of items.querySelectorAll('button')) {
    if (!item.hasAttribute('role')) item.setAttribute('role', 'menuitem');
    item.tabIndex = -1;
  }
  const gap = parseFloat(getComputedStyle(items).getPropertyValue('--space-compact'));
  items.style.maxHeight = '';
  const below = innerHeight - trigger.bottom - gap * 2, above = trigger.top - gap * 2;
  const down = items.getBoundingClientRect().height <= below || below >= above;
  items.style.maxHeight = Math.max(0, down ? below : above) + 'px';
  const box = items.getBoundingClientRect();
  items.style.left = Math.max(gap, Math.min(trigger.right - box.width, innerWidth - box.width - gap)) + 'px';
  items.style.top = (down ? trigger.bottom + gap : Math.max(gap, trigger.top - gap - box.height)) + 'px';
}

function setMenuOpen(menu, open) {
  if (open) {
    for (const peer of page.querySelectorAll('.terminal-menu[open]')) if (peer !== menu) setMenuOpen(peer, false);
    if (menu === $('tab-menu')) menu.dataset.tabId = currentTab()?.id || '';
  }
  menu.open = open;
  menu.querySelector('summary').setAttribute('aria-expanded', String(open));
  if (menu === $('tab-menu')) showWorkspaceChoices(false);
  if (open) positionMenu(menu);
}

function showWorkspaceChoices(show, focus = false) {
  $('tab-actions').hidden = show;
  $('workspace-choices').hidden = !show;
  $('workspace-move').setAttribute('aria-expanded', String(show));
  $('tab-menu').querySelector('.terminal-menu-items').setAttribute('aria-label', show ? '탭을 옮길 작업공간' : '탭 동작');
  if ($('tab-menu').open) positionMenu($('tab-menu'));
  if (focus) (show ? $('workspace-destinations').querySelector('[aria-checked="true"]') : $('workspace-move'))?.focus({preventScroll: true});
}

function renderWorkspaceDestinations() {
  const folders = groups();
  const key = JSON.stringify([folders.map(group => [group.id, group.name]), activeWorkspace, working]);
  if (key === workspaceMoveKey) return;
  workspaceMoveKey = key;
  const focused = document.activeElement.dataset.terminalWorkspaceDestination;
  const rows = folders.map(group => {
    const row = button('', () => moveTabToWorkspace(group.id), '');
    row.dataset.terminalWorkspaceDestination = group.id;
    row.setAttribute('role', 'menuitemradio');
    row.setAttribute('aria-checked', String(group.id === activeWorkspace));
    row.disabled = working;
    row.title = group.name;
    row.append(element('span', '', group.name));
    if (group.id === activeWorkspace) row.append(icon('check'));
    return row;
  });
  $('workspace-destinations').replaceChildren(...rows);
  if (focused && $('tab-menu').open) rows.find(row => row.dataset.terminalWorkspaceDestination === focused)?.focus({preventScroll: true});
  if ($('tab-menu').open) positionMenu($('tab-menu'));
}

async function backgroundTab(tab) {
  if (renameEditor && !(await saveTabName(false))) return;
  if (await mutate('/tabs/' + tab.id + '/hide')) revealBackground();
}

async function retireCleanExits() {
  if (retiring || !model?.generation || model.service.stopping || !['running', 'incompatible'].includes(model.service.state)) return;
  const generation = model.generation;
  const targets = model.terminals.filter(term => cleanShellExit(term) && !retiredAttempts.has(generation + ':' + term.id));
  if (!targets.length) return;
  retiring = true;
  let retryLater = false;
  try {
    for (const term of targets) {
      if (model.generation !== generation) break;
      retiredAttempts.add(generation + ':' + term.id);
      views.get(term.id)?.disconnect();
      try { await api('/terminals/' + term.id + '/stop', {generation}); }
      catch (error) {
        if (['busy', 'stopping'].includes(error.code)) { retiredAttempts.delete(generation + ':' + term.id); retryLater = true; }
        else if (!['not_found', 'conflict'].includes(error.code) && error.status !== 404) feedback('종료된 터미널을 정리하지 못했습니다. ×로 다시 닫아 주세요.');
      }
    }
    await refresh();
  } finally {
    retiring = false;
    if (retryLater) setTimeout(retireCleanExits, 750);
    else queueMicrotask(retireCleanExits);
  }
}

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
function replaceRows(container, nodes) {
  const focused = container.contains(document.activeElement) ? document.activeElement.dataset.terminalFocus : null;
  container.replaceChildren(...nodes);
  if (focused) [...container.querySelectorAll('[data-terminal-focus]')].find(node => node.dataset.terminalFocus === focused)?.focus({preventScroll: true});
}
function feedback(message = '', source = 'action') {
  feedbackSource = message ? source : null;
  for (const name of ['error', 'manage-error']) {
    $(name).textContent = message;
    $(name).hidden = !message;
  }
}
function serviceFeedback() {
  if (model?.service.state === 'incompatible') {
    feedback(model.terminals.length
      ? '이전 버전의 터미널 서비스입니다. 기존 작업을 마친 뒤 서비스를 업데이트하면 새 터미널을 열 수 있습니다.'
      : '이전 버전의 빈 터미널 서비스가 남아 있습니다. 서비스를 업데이트하면 새 터미널을 열 수 있습니다.', 'compatibility');
  } else if (feedbackSource === 'compatibility') feedback();
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
    if (!Array.isArray(data.workspaces?.items)) {
      throw new Error('작업공간을 불러올 수 없습니다. LocalBrain을 다시 실행해 주세요.');
    }
    if (data.workspaces?.needsSave) {
      try { data.workspaces = await api('/workspaces/reconcile', {generation: data.generation}); }
      catch (error) { data.workspaces.error = error.message; }
    }
    if (number !== requestNumber) return;
    if (model?.generation === data.generation) {
      const latest = new Map(model.terminals.map(term => [term.id, term]));
      for (const view of views.values()) latest.set(view.id, latestTerminal(latest.get(view.id), view.info));
      data.terminals = data.terminals.map(term => latestTerminal(latest.get(term.id), term));
    }
    if (data.generation !== attentionGeneration) {
      endTabDrag(false);
      seenCompletions.clear(); workspaceTabs.clear(); attentionGeneration = data.generation;
      retiredAttempts.clear(); pendingOrder = null;
    }
    model = data;
    confirmedRead++;
    const ids = new Set(model.terminals.map(term => term.id));
    for (const id of seenCompletions.keys()) if (!ids.has(id)) seenCompletions.delete(id);
    for (const key of retiredAttempts) if (!ids.has(key.slice(33))) retiredAttempts.delete(key);
    const folders = new Set(groups().map(group => group.id));
    for (const cwd of workspaceTabs.keys()) if (!folders.has(cwd)) workspaceTabs.delete(cwd);
    if (feedbackSource === 'connection') feedback();
    if (data.service.unclean) feedback('관리 서비스가 예기치 않게 종료되었습니다. 이전 작업이 남아 있을 수 있습니다.', 'recovery');
    else if (feedbackSource === 'recovery') feedback();
    reconcile();
    if (model.presentation?.error && (!feedbackSource || feedbackSource === 'order-read')) feedback(model.presentation.error, 'order-read');
    else if (!model.presentation?.error && feedbackSource === 'order-read') feedback();
    if (data.workspaces?.error && (!feedbackSource || feedbackSource === 'workspace')) feedback(data.workspaces.error, 'workspace');
    else if (!data.workspaces?.error && feedbackSource === 'workspace') feedback();
  } catch (error) {
    if (number !== requestNumber) return;
    feedback(error.message, 'connection');
    if (model) {
      model.service = {...model.service, state: 'unknown', running: null};
      renderManagement(); updateStatusbar();
      $('rail-service').textContent = serviceState();
    }
    $('new').disabled = $('empty-action').disabled = true;
    $('count').textContent = '—';
    $('create-retry').disabled = $('folder-submit').disabled = true;
    $('folder-open').disabled = true;
    page.querySelectorAll('[data-terminal-split]').forEach(node => { node.disabled = true; });
  }
  finally { page.setAttribute('aria-busy', 'false'); }
}
async function mutate(url, body = {}) {
  try {
    feedback();
    await api(url, body);
    await refresh();
    return true;
  } catch (error) { feedback(error.message); return false; }
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
  if (renameEditor) { saveTabName(false).then(saved => { if (saved) selectTab(id, focusTerminal); }); return; }
  if (activeTab) workspaceTabs.set(activeWorkspace, activeTab);
  activeWorkspace = groupForTab(id)?.id ?? activeWorkspace;
  activeTab = id;
  workspaceTabs.set(activeWorkspace, id);
  focusedPane = model.tabs.find(tab => tab.id === id)?.terminals[0] || null;
  reconcile();
  if (focusTerminal) requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
}
async function closeTab(tab) {
  const fromBackground = tab.hidden && $('hidden-list').contains(document.activeElement);
  if (renameEditor?.id === tab.id) cancelTabRename(false);
  if (await endTerminals(tab.terminals, '/tabs/' + tab.id + '/stop', {expected: expectedScope(tab.terminals)})) {
    if (fromBackground && !page.querySelector('dialog[open]')) {
      ($('hidden-list').querySelector('button') || $('hidden-open')).focus({preventScroll: true});
    }
  }
}

async function endTerminals(ids, url, body) {
  if (ids.some(id => pendingCloses.has(id))) return false;
  const origin = document.activeElement;
  for (const id of ids) { pendingCloses.set(id, null); views.get(id)?.prepareClose(); }
  try {
    const ended = await mutate(url, body);
    if (ended) restoreCloseFocus(origin);
    else {
      for (const id of ids) {
        pendingCloses.set(id, confirmedRead);
        const view = views.get(id); if (view) view.closeFailedAt = confirmedRead;
      }
      await refresh();
      if (ids.some(id => views.has(id) && !views.get(id).closeRequested)) restoreCloseFocus(origin);
    }
    return ended;
  } finally { for (const id of ids) pendingCloses.delete(id); }
}

function restoreCloseFocus(origin) {
  if (renameEditor || page.querySelector('dialog[open]')) return;
  requestAnimationFrame(() => {
    const active = document.activeElement;
    const sameAction = origin?.dataset.terminalFocus
      && active.dataset.terminalFocus === origin.dataset.terminalFocus;
    if (active !== origin && active !== document.body && !sameAction) return;
    const view = views.get(focusedPane);
    if (view) view.terminal.focus();
    else $('new').focus({preventScroll: true});
  });
}
function renderTabs() {
  updateProgramIndicators($('tabs'));
  for (const holder of $('tabs').children) {
    const tab = model.tabs.find(tab => tab.id === holder.dataset.terminalTab);
    if (!tab) continue;
    const terms = model.terminals.filter(term => tab.terminals.includes(term.id));
    const lead = [...terms].sort((a, b) => statusOf(a).priority - statusOf(b).priority)[0];
    const marker = indicatorSymbol(terms, {current: tab.id === activeTab});
    marker.dataset.terminalTabIndicator = '';
    holder.querySelector('[data-terminal-tab-indicator]').replaceWith(marker);
    const badge = holder.querySelector('[data-terminal-tab-command]');
    if (lead && badge && badge.title !== '셸 · ' + statusOf(lead).label) {
      const next = commandBadge(lead); next.dataset.terminalTabCommand = '';
      badge.replaceWith(next);
    }
    const select = holder.querySelector('[role="tab"]');
    select.title = tab.name + ' · ' + terminalIndicator(terms, {current: tab.id === activeTab}).label + (lead ? ' · 셸 · ' + statusOf(lead).label : '');
    select.setAttribute('aria-label', select.title);
  }
  const tabs = visibleTabs();
  if (dragState) return;
  if (renameEditor && tabs.some(tab => tab.id === renameEditor.id)) return;
  if (renameEditor) cancelTabRename(false);
  const key = JSON.stringify([activeTab, tabs.map(tab => [tab.id, tab.name, tab.terminals])]);
  if (key === tabKey) return;
  tabKey = key;
  const fragment = document.createDocumentFragment();
  for (const tab of tabs) {
    const holder = element('div', 'terminal-tab' + (tab.id === activeTab ? ' selected' : ''));
    holder.dataset.terminalTab = tab.id;
    const select = button('', event => {
      if (performance.now() < suppressTabClickUntil) return;
      if (tab.id === activeTab && event.target.closest('.terminal-tab-name')) startTabRename(tab.id, event);
      else selectTab(tab.id);
    }, '');
    select.addEventListener('pointerdown', event => beginTabDrag(event, tab.id, holder));
    const terms = model.terminals.filter(term => tab.terminals.includes(term.id));
    const lead = [...terms].sort((a, b) => statusOf(a).priority - statusOf(b).priority)[0];
    const marker = indicatorSymbol(terms, {current: tab.id === activeTab});
    marker.dataset.terminalTabIndicator = '';
    select.append(marker, programIndicator(terms));
    select.append(element('span', 'terminal-tab-name', tab.name));
    if (lead) {
      const badge = commandBadge(lead); badge.dataset.terminalTabCommand = '';
      select.append(badge);
    }
    if (terms.length > 1) select.append(element('small', 'terminal-tab-count', String(terms.length)));
    select.setAttribute('role', 'tab');
    select.dataset.terminalFocus = 'tab:' + tab.id;
    select.setAttribute('aria-selected', String(tab.id === activeTab));
    select.tabIndex = tab.id === activeTab ? 0 : -1;
    select.title = tab.name + ' · ' + terminalIndicator(terms, {current: tab.id === activeTab}).label + (lead ? ' · 셸 · ' + statusOf(lead).label : '');
    select.setAttribute('aria-label', select.title);
    select.setAttribute('aria-keyshortcuts', 'F2 Alt+Shift+ArrowLeft Alt+Shift+ArrowRight');
    select.addEventListener('keydown', event => {
      if (event.key === 'F2') { event.preventDefault(); startTabRename(tab.id); return; }
      if (event.altKey && event.shiftKey && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
        event.preventDefault(); moveTabBy(tab.id, event.key === 'ArrowLeft' ? -1 : 1); return;
      }
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const tabs = visibleTabs();
      const index = tabs.findIndex(item => item.id === tab.id);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1
        : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      selectTab(tabs[next].id, false);
      $('tabs').querySelector('[aria-selected="true"]')?.focus();
    });
    const close = button('×', () => closeTab(tab), 'terminal-close');
    close.setAttribute('aria-label', tab.name + ' 탭 닫기 및 종료');
    close.dataset.terminalFocus = 'close:' + tab.id;
    holder.append(select, close);
    fragment.append(holder);
  }
  replaceRows($('tabs'), [fragment]);
}

function startTabRename(id, event = null) {
  if (working || orderSaving || dragState || performance.now() < suppressTabClickUntil || renameEditor) return;
  const tab = model.tabs.find(tab => tab.id === id);
  const holder = [...$('tabs').children].find(node => node.dataset.terminalTab === id);
  if (!tab || !holder) return;
  const select = holder.querySelector('[role="tab"]'), label = select.querySelector('.terminal-tab-name');
  let caret = tab.name.length;
  if (event?.detail) {
    const position = document.caretPositionFromPoint?.(event.clientX, event.clientY);
    const range = position ? null : document.caretRangeFromPoint?.(event.clientX, event.clientY);
    const node = position?.offsetNode ?? range?.startContainer;
    if (node && label.contains(node)) {
      const before = document.createRange(); before.selectNodeContents(label);
      before.setEnd(node, position?.offset ?? range.startOffset); caret = before.toString().length;
    }
  }
  const input = element('input', 'terminal-tab-input');
  input.value = tab.name; input.maxLength = 120;
  input.setAttribute('aria-label', '탭 이름');
  input.dataset.terminalFocus = 'rename:' + id;
  select.hidden = true; holder.insertBefore(input, holder.querySelector('.terminal-close'));
  renameEditor = {id, input, select, original: tab.name, pending: null};
  input.addEventListener('keydown', event => {
    if (event.isComposing || event.keyCode === 229) return;
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); cancelTabRename(true); }
    else if (event.key === 'Enter') { event.preventDefault(); saveTabName(true); }
  });
  input.addEventListener('blur', () => { if (renameEditor?.input === input) saveTabName(false); });
  input.focus({preventScroll: true}); input.setSelectionRange(caret, caret);
}

function cancelTabRename(returnFocus) {
  const editor = renameEditor;
  if (!editor) return;
  renameEditor = null;
  editor.input.remove(); editor.select.hidden = false;
  if (feedbackSource === 'rename') feedback();
  tabKey = ''; renderTabs();
  if (returnFocus) $('tabs').querySelector('[aria-selected="true"]')?.focus({preventScroll: true});
}

async function saveTabName(returnFocus) {
  const editor = renameEditor;
  if (!editor) return true;
  if (editor.pending) return editor.pending;
  const name = editor.input.value.trim();
  if (!name) { editor.input.setAttribute('aria-invalid', 'true'); feedback('탭 이름을 1~120자로 입력해 주세요.', 'rename'); return false; }
  if (name === editor.original) { cancelTabRename(returnFocus); return true; }
  editor.pending = Promise.resolve().then(async () => {
    editor.input.disabled = true;
    try {
      await api('/tabs/' + editor.id + '/rename', {name});
      const tab = model.tabs.find(tab => tab.id === editor.id);
      if (tab) tab.name = name;
      if (renameEditor === editor) cancelTabRename(returnFocus);
      await refresh();
      return true;
    } catch (error) {
      if (renameEditor === editor) { editor.input.setAttribute('aria-invalid', 'true'); feedback(error.message, 'rename'); }
      return false;
    } finally { editor.input.disabled = false; editor.pending = null; }
  });
  return editor.pending;
}

async function reorderTab(sourceId, targetId, before) {
  if (working || orderSaving || sourceId === targetId) return;
  const visible = visibleTabs(), source = visible.find(tab => tab.id === sourceId);
  if (!source || !visible.some(tab => tab.id === targetId)) return;
  const ids = visible.map(tab => tab.id).filter(id => id !== sourceId);
  ids.splice(ids.indexOf(targetId) + (before ? 0 : 1), 0, sourceId);
  const slots = new Set(visible.map(tab => tab.id)); let index = 0;
  const order = tabsInOrder().map(tab => slots.has(tab.id) ? ids[index++] : tab.id);
  if (order.every((id, i) => id === tabsInOrder()[i].id)) return;
  const generation = model.generation;
  pendingOrder = {generation, order}; orderSaving = true; renderTabs();
  try {
    const saved = await api('/view-order', {generation, order});
    if (model.generation === generation) model.presentation = {order: saved.order};
  } catch (error) { feedback(error.message, 'order'); }
  finally { pendingOrder = null; orderSaving = false; tabKey = ''; reconcile(); await refresh(); }
}

function moveTabBy(id, delta) {
  const tabs = visibleTabs(), index = tabs.findIndex(tab => tab.id === id), target = tabs[index + delta];
  if (target) reorderTab(id, target.id, delta < 0);
}

function beginTabDrag(event, id, holder) {
  if (event.button !== 0 || event.pointerType !== 'mouse' || !event.isPrimary || renameEditor || orderSaving || visibleTabs().length < 2) return;
  dragState = {id, holder, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY,
    x: event.clientX, y: event.clientY, moving: false, frame: 0, target: null, before: true};
}

function paintTabDrag() {
  const drag = dragState;
  if (!drag?.moving) return;
  const strip = $('tabs'), bounds = strip.getBoundingClientRect();
  strip.scrollLeft += drag.x < bounds.left + 24 ? -12 : drag.x > bounds.right - 24 ? 12 : 0;
  drag.target = null;
  for (const node of strip.children) {
    node.classList.remove('drop-before', 'drop-after');
    const rect = node.getBoundingClientRect();
    if (node.dataset.terminalTab !== drag.id && drag.x >= rect.left && drag.x <= rect.right
      && drag.y >= bounds.top - 12 && drag.y <= bounds.bottom + 12) {
      drag.target = node.dataset.terminalTab; drag.before = drag.x < rect.left + rect.width / 2;
      node.classList.add(drag.before ? 'drop-before' : 'drop-after');
    }
  }
  drag.frame = requestAnimationFrame(paintTabDrag);
}

function endTabDrag(commit = false) {
  const drag = dragState;
  if (!drag) return;
  dragState = null; cancelAnimationFrame(drag.frame);
  if (!drag.moving) return;
  if (drag.holder.hasPointerCapture(drag.pointerId)) drag.holder.releasePointerCapture(drag.pointerId);
  drag.holder.classList.remove('dragging');
  for (const node of $('tabs').children) node.classList.remove('drop-before', 'drop-after');
  if (drag.moving) suppressTabClickUntil = performance.now() + 300;
  if (commit && drag.target) reorderTab(drag.id, drag.target, drag.before);
  else { tabKey = ''; renderTabs(); }
}
function serviceState() {
  if (model.service.unclean) return '이전 작업 확인 필요';
  return {running: '실행 중', stopped: '중지됨', unknown: '연결 실패',
    incompatible: '버전 확인 필요', unsupported: '지원하지 않는 환경'}[model.service.state] || '상태 미확인';
}
function renderManagement() {
  $('service-state').textContent = serviceState();
  const running = ['running', 'incompatible'].includes(model.service.state);
  page.querySelector('[data-terminal-service="start"]').disabled = model.service.state !== 'stopped' || !(model.dependencies.installed || model.dependencies.bundleReady);
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
    const open = button(tab.hidden ? '열기' : '보기', () => openExisting(tab));
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
  await endTerminals([term.id], '/terminals/' + term.id + '/stop', {generation: model.generation});
}
async function createTerminal(source = null, direction = null, folder = null, retry = false) {
  if (renameEditor && !(await saveTabName(false))) return false;
  if (!fontReady || !(model?.dependencies.installed || model?.dependencies.bundleReady) || working || !['running', 'stopped'].includes(model.service.state)) return false;
  // Resolve an uncertain request before starting another, even if refresh discovered its new group.
  if (createTarget && !retry) return false;
  const body = source ? {tabId: source.tabId, direction, cwd: folder || source.cwd, shell: source.shell} : {};
  working = true; feedback(); reconcile();
  try {
    if (!createTarget) {
      const cwd = folder || currentWorkspace()?.cwd;
      const paths = source ? body : await api('/settings?launch=true' + (cwd ? '&cwd=' + encodeURIComponent(cwd) : ''));
      const workspaceId = source ? groupForTab(source.tabId)?.id : activeWorkspace;
      createTarget = {...paths, ...(workspaceId ? {workspaceId} : {}), key: crypto.randomUUID()};
    }
    const result = await api('/terminals', createTarget);
    if (activeTab) workspaceTabs.set(activeWorkspace, activeTab);
    activeWorkspace = result.workspaces?.items.find(item => item.tabs.includes(result.tabId))?.id || createTarget.workspaceId || null;
    activeTab = result.tabId; focusedPane = result.terminal.id;
    workspaceTabs.set(activeWorkspace, activeTab);
    createTarget = null;
    await refresh();
    if (activeTab !== result.tabId) selectTab(result.tabId, false);
    if (result.workspaceError) feedback(result.workspaceError, 'workspace-save');
    requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
    return true;
  } catch (error) {
    if (error.status && error.status < 500 && !['disconnected', 'unavailable', 'runtime_error'].includes(error.code)) createTarget = null;
    feedback(error.message);
    if ($('folder-dialog').open) { $('folder-error').textContent = error.message; $('folder-error').hidden = false; }
    return false;
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
  if (!feedbackSource || feedbackSource === 'compatibility') serviceFeedback();
  const folders = groups();
  if (!folders.some(group => group.id === activeWorkspace)) activeWorkspace = folders[0]?.id ?? null;
  const visible = visibleTabs();
  if (!visible.some(tab => tab.id === activeTab)) activeTab = visible[0]?.id || null;
  const tab = currentTab();
  if (!tab?.terminals.includes(focusedPane)) focusedPane = tab?.terminals[0] || null;
  $('count').textContent = model.service.running === null ? '—' : String(liveCount());
  const canCreate = fontReady && (model.dependencies.installed || model.dependencies.bundleReady) && !working && ['running', 'stopped'].includes(model.service.state);
  $('new').disabled = !canCreate || Boolean(createTarget);
  $('folder-open').disabled = working || workspaceSaving || Boolean(createTarget);
  $('create-retry').hidden = !createTarget;
  $('create-retry').disabled = !canCreate;
  $('folder-submit').disabled = !canCreate;
  $('folder-path').disabled = $('folder-pick').disabled = working || Boolean(createTarget);
  $('update-service').hidden = model.service.state !== 'incompatible';
  $('update-service').disabled = working;
  $('tab-menu').hidden = false;
  $('tab-menu').querySelector('summary').setAttribute('aria-label', tab ? '현재 탭 메뉴' : '터미널 메뉴');
  $('background').hidden = $('rename').hidden = !tab;
  page.querySelectorAll('[data-terminal-move]').forEach(node => { node.hidden = !tab; });
  if ($('tab-menu').open && $('tab-menu').dataset.tabId !== (tab?.id || '')) setMenuOpen($('tab-menu'), false);
  $('workspace-move').hidden = !tab;
  const tabIndex = visible.findIndex(item => item.id === activeTab);
  page.querySelector('[data-terminal-move="left"]').disabled = orderSaving || tabIndex <= 0;
  page.querySelector('[data-terminal-move="right"]').disabled = orderSaving || tabIndex < 0 || tabIndex >= visible.length - 1;
  $('folder-tab').disabled = $('new').disabled;
  if (workspaceEditor && $('workspace-dialog').open && !workspaceSaving) {
    $('workspace-remove').disabled = Boolean(groups().find(group => group.id === workspaceEditor.id)?.tabs.length);
  }
  $('workspace-move').disabled = !tab || working;
  renderWorkspaceDestinations();
  renderTabs();
  renderManagement();
  renderRail();
  $('empty').hidden = Boolean(tab);
  $('empty-action').disabled = !fontReady || working || !model.dependencies.node || !model.dependencies.npm
    || !['running', 'stopped'].includes(model.service.state);
  if (!model.dependencies.node || !model.dependencies.npm) {
    $('empty-text').textContent = '터미널 실행 구성요소를 찾지 못했습니다. 앱이나 설치 구성을 확인해 주세요.';
    $('empty-action').hidden = true;
  } else {
    $('empty-action').hidden = false;
    $('empty-action').textContent = (model.dependencies.installed || model.dependencies.bundleReady)
      ? visible.length ? '새 터미널' : currentWorkspace()?.tabs.length ? '백그라운드 보기' : '새 터미널' : '구성요소 설치';
    $('empty-text').textContent = working ? '준비 중…' : currentWorkspace()?.tabs.length
      ? '이 작업공간의 터미널이 백그라운드에서 실행 중입니다.' : '새 터미널을 열어 시작하세요.';
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
  let removedFocus = null;
  for (const [id, view] of views) if (!ids.has(id)) {
    if (view.node.contains(document.activeElement) && !model.terminals.some(term => term.id === id)) removedFocus = document.activeElement;
    view.dispose(); views.delete(id);
  }
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
  updateStatusbar();
  // A newer poll may apply removal after the initiating stop's refresh was superseded.
  if (removedFocus) restoreCloseFocus(removedFocus);
}
class Pane {
  constructor(term) {
    this.id = term.id;
    this.info = term;
    this.alive = true;
    this.writable = false;
    this.reportedWritable = false;
    this.closeRequested = pendingCloses.has(term.id);
    this.closeFailedAt = pendingCloses.get(term.id) ?? null;
    this.outbox = [];
    this.outboxBytes = 0;
    this.painted = false;
    this.historyTruncated = false;
    this.node = element('section', 'terminal-pane');
    this.node.dataset.terminalPane = term.id;
    this.node.setAttribute('aria-label', term.name);
    const header = element('header', 'terminal-pane-header');
    this.name = element('span', 'terminal-pane-name', programTitle(term.name).title);
    this.symbol = indicatorSymbol([term], {current: term.id === focusedPane});
    this.program = programIndicator([term]);
    this.command = commandBadge(term);
    this.status = element('span', 'terminal-pane-status', '연결 중');
    this.take = button('제어권 가져오기', () => this.send({type: 'claim'}), 'terminal-takeover');
    this.take.hidden = true;
    const menu = element('details', 'terminal-menu');
    const summary = element('summary'); summary.setAttribute('aria-label', '터미널 메뉴'); summary.title = '터미널 메뉴';
    summary.append(icon('more_horiz'));
    const actions = element('div', 'terminal-menu-items');
    this.right = button('', () => createTerminal(this.info, 'right'), 'shell-icon-button');
    this.right.dataset.terminalSplit = 'right';
    this.right.append(icon('vertical_split'));
    this.down = button('', () => createTerminal(this.info, 'down'), 'shell-icon-button');
    this.down.dataset.terminalSplit = 'down';
    this.down.append(icon('horizontal_split'));
    this.down.setAttribute('aria-label', '아래쪽 분할'); this.down.title = '아래쪽 분할';
    this.otherFolder = button('다른 폴더에서 분할…', () => { setMenuOpen(menu, false); openFolderDialog(this.info, 'right'); }, '');
    this.otherFolder.dataset.terminalSplitFolder = '';
    actions.append(this.otherFolder);
    menu.append(summary, actions);
    const close = button('×', () => closePane(this.info), 'shell-icon-button');
    close.setAttribute('aria-label', '이 터미널 닫기 및 종료');
    const controls = element('div', 'terminal-pane-actions');
    controls.append(this.right, this.down, menu, close);
    header.append(this.symbol, this.program, this.name, this.command, this.status, this.take, controls);
    this.body = element('div', 'terminal-pane-body');
    this.body.dataset.terminalInput = '';
    this.host = element('div', 'terminal-emulator');
    this.body.append(this.host);
    this.node.append(header, this.body);
    this.node.addEventListener('focusin', () => {
      focusedPane = this.id;
      for (const [id, view] of views) { view.node.classList.toggle('focused', id === this.id); view.updateSymbol(); }
      renderTabs(); renderRail(); updateStatusbar(); markSeen(this);
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
    this.pendingCompletion = 0;
    this.renderedCompletion = 0;
    this.renderListener = this.terminal.onRender(({start, end}) => {
      if (start !== 0 || end < this.terminal.rows - 1) return;
      const completion = this.pendingCompletion, connection = this.ws;
      cancelAnimationFrame(this.renderFrame);
      this.renderFrame = requestAnimationFrame(() => {
        if (!this.alive || this.ws !== connection || !this.painted) return;
        this.renderedCompletion = Math.max(this.renderedCompletion, completion);
        markSeen(this);
      });
    });
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
    if (info.seq >= this.info.seq) this.info = info;
    info = this.info;
    if (this.closeFailedAt !== null && confirmedRead > this.closeFailedAt
        && ['running', 'incompatible'].includes(model.service.state)
        && info.state === 'running' && !info.error && !info.inputError && !info.closing) {
      this.closeRequested = false; this.closeFailedAt = null;
      this.control(this.reportedWritable); this.connect();
    }
    if (info.error) this.showStatus('종료 확인 필요');
    const splitLabel = tab?.terminals.length > 1 ? '분할 추가' : '오른쪽 분할';
    this.right.setAttribute('aria-label', splitLabel); this.right.title = splitLabel;
    this.down.hidden = tab?.terminals.length > 1;
    this.right.disabled = this.down.disabled = this.otherFolder.disabled = !tab || tab.terminals.length >= 4 || working || Boolean(createTarget) || !fontReady
      || !['running', 'stopped'].includes(model.service.state);
    this.node.classList.toggle('focused', focusedPane === this.id);
    this.updateSymbol();
  }
  updateSymbol() {
    const symbol = indicatorSymbol([this.info], {current: this.id === focusedPane});
    this.symbol.replaceWith(symbol); this.symbol = symbol;
    const command = commandBadge(this.info);
    this.command.replaceWith(command); this.command = command;
    this.name.textContent = programTitle(this.info.name).title;
    this.name.title = this.info.name + ' · ' + this.info.cwd;
    updateProgramIndicator(this.program);
    this.node.setAttribute('aria-label', programTitle(this.info.name).title + ' · ' + terminalIndicator([this.info], {current: this.id === focusedPane}).label + ' · 셸 · ' + statusOf(this.info).label);
  }
  showStatus(text) {
    this.status.textContent = text + (this.historyTruncated ? ' · 이력 생략' : '');
    this.status.title = this.historyTruncated ? '화면 복원에서 이전 출력 일부를 생략했습니다.' : '';
  }
  control(writable) {
    this.reportedWritable = writable;
    writable = writable && !this.closeRequested;
    this.writable = writable;
    this.terminal.options.disableStdin = !writable || !this.painted || Boolean(this.info.inputError);
    if (!writable || this.info.inputError) { this.koreanInput?.cancel(); this.discardInput(); }
    this.take.hidden = this.closeRequested || writable || this.info.state !== 'running' || this.ws?.readyState !== WebSocket.OPEN;
    this.showStatus(this.info.error ? '종료 확인 필요' : this.info.state === 'exited' ? '종료됨'
      : this.info.inputError ? '입력 오류' : this.closeRequested || this.info.closing ? '종료 중' : writable ? this.painted ? '' : '화면 복원 중' : '읽기 전용');
    this.updateSymbol(); updateStatusbar();
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
    this.pendingCompletion = this.renderedCompletion = 0;
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
        if (this.closeRequested && !interrupted) return;
        if (interrupted) this.clearOutbox();
        feedback(this.info.checkpointVersion && this.info.checkpointVersion !== checkpointVersion
          ? '터미널 서비스의 버전이 다릅니다. 작업을 마친 뒤 관리에서 서비스를 재시작해 주세요.'
          : interrupted ? frame.message + ' 입력이 일부만 전달됐을 수 있습니다. 연결 후 Ctrl+C로 확인해 주세요.' : frame.message,
        interrupted ? 'input:' + this.id : 'stream:' + this.id);
      }
      if (frame.type !== 'output') return;
      if (frame.snapshot) this.historyTruncated = Boolean(frame.truncated);
      this.info = latestTerminal(this.info, frame.terminal);
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
        const completion = frame.terminal.activity?.completion || 0;
        if (completion > this.renderedCompletion) {
          this.pendingCompletion = Math.max(this.pendingCompletion, completion);
          // onRender is withheld during DEC synchronized output; parsing alone cannot mark seen.
          this.terminal.refresh(0, this.terminal.rows - 1);
        }
        const current = model.terminals.findIndex(term => term.id === this.id);
        if (current >= 0 && frame.terminal.seq >= model.terminals[current].seq) model.terminals[current] = {...frame.terminal};
        if (this.info.inputError) feedback(this.info.inputError, 'stream:' + this.id);
        else if (feedbackSource === 'stream:' + this.id) feedback();
        this.control(this.reportedWritable);
        this.send({type: 'ack', seq: frame.seq});
        this.fit();
        markSeen(this); renderTabs(); renderRail();
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
      this.reportedWritable = false;
      this.terminal.options.disableStdin = true;
      this.take.hidden = true;
      this.showStatus(this.info.error ? '종료 확인 필요' : this.info.state === 'exited' ? '종료됨' : '연결 끊김');
      if (!document.hidden && !this.closeRequested && this.info.state === 'running') this.retry = setTimeout(() => this.connect(), 2000);
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
  prepareClose() {
    this.closeRequested = true; this.closeFailedAt = null;
    this.control(this.reportedWritable);
  }
  disconnect() {
    this.koreanInput?.cancel();
    this.clearOutbox();
    clearTimeout(this.retry);
    const ws = this.ws; this.ws = null;
    this.control(false); this.showStatus('연결 끊김');
    ws?.close();
  }
  dispose() {
    this.koreanInput?.dispose();
    this.clearOutbox();
    this.alive = false;
    clearTimeout(this.retry);
    cancelAnimationFrame(this.fitFrame);
    cancelAnimationFrame(this.renderFrame);
    this.renderListener.dispose();
    this.resizeObserver.disconnect();
    this.ws?.close();
    this.terminal.dispose();
    this.node.remove();
  }
}
$('new').addEventListener('click', () => createTerminal());
$('create-retry').addEventListener('click', () => createTerminal(null, null, null, true));
$('update-service').addEventListener('click', async () => {
  if (working || model?.service.state !== 'incompatible' || !confirmStop(null, 'restart')) return;
  const expected = expectedScope();
  working = true; reconcile();
  try { await api('/service/restart', {expected}); createTarget = null; }
  catch (error) { feedback(error.message); }
  finally { working = false; await refresh(); }
});
$('rail-toggle').addEventListener('click', () => { railCollapsed = !railCollapsed; applyRail(); });
$('rail-close').addEventListener('click', () => { railCollapsed = true; applyRail(); $('rail-toggle').focus(); });
async function editWorkspace(group = null) {
  if (workspaceSaving) return;
  if (renameEditor && !(await saveTabName(false))) return;
  workspaceEditor = group;
  $('workspace-title').textContent = group ? '작업공간 설정' : '작업공간 추가';
  $('workspace-name').value = group?.name || '';
  $('workspace-cwd').value = group?.cwd || '';
  $('workspace-error').hidden = true;
  $('workspace-submit').textContent = group ? '저장' : '추가';
  $('workspace-remove').hidden = !group;
  $('workspace-remove').disabled = Boolean(group?.tabs.length);
  $('workspace-remove').title = group?.tabs.length ? '터미널을 모두 종료하면 목록에서 제거할 수 있습니다.' : '';
  $('workspace-dialog').showModal();
  $('workspace-name').focus(); $('workspace-name').select();
}
$('folder-open').addEventListener('click', () => editWorkspace());
$('workspace-close').addEventListener('click', () => $('workspace-dialog').close());
$('workspace-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (workspaceSaving) return;
  workspaceSaving = true;
  $('workspace-submit').disabled = true;
  $('workspace-remove').disabled = true;
  $('workspace-error').hidden = true;
  const body = {name: $('workspace-name').value, cwd: $('workspace-cwd').value};
  if (workspaceEditor) body.id = workspaceEditor.id;
  try {
    const saved = await api('/workspaces/' + (workspaceEditor ? 'update' : 'create'), body);
    const stillOpen = $('workspace-dialog').open;
    if (stillOpen && !workspaceEditor) activeWorkspace = saved.id;
    await refresh();
    if (stillOpen && $('workspace-dialog').open) {
      $('workspace-dialog').close();
      if (workspaceEditor) page.querySelector('[data-terminal-focus="workspace-edit:' + workspaceEditor.id + '"]')?.focus();
      else $('new').focus();
    }
  } catch (error) {
    if ($('workspace-dialog').open) { $('workspace-error').textContent = error.message; $('workspace-error').hidden = false; }
    else feedback(error.message, 'workspace-save');
  } finally { workspaceSaving = false; $('workspace-submit').disabled = false; reconcile(); }
});
$('workspace-remove').addEventListener('click', async () => {
  if (!workspaceEditor || workspaceSaving) return;
  workspaceSaving = true;
  $('workspace-submit').disabled = true;
  $('workspace-remove').disabled = true;
  try {
    await api('/workspaces/remove', {id: workspaceEditor.id});
    await refresh();
    if ($('workspace-dialog').open) {
      $('workspace-dialog').close();
      requestAnimationFrame(() => { if (document.activeElement === document.body) $('folder-open').focus(); });
    }
  } catch (error) {
    if ($('workspace-dialog').open) { $('workspace-error').textContent = error.message; $('workspace-error').hidden = false; }
    else feedback(error.message, 'workspace-save');
  } finally { workspaceSaving = false; $('workspace-submit').disabled = false; reconcile(); }
});
async function openFolderDialog(source = null, direction = null) {
  if (renameEditor && !(await saveTabName(false))) return;
  if (working || createTarget || $('new').disabled || (source && currentTab()?.terminals.length >= 4)) return;
  folderTarget = {source, direction};
  $('folder-error').hidden = true;
  $('folder-title').textContent = source ? '다른 폴더에서 분할' : '다른 폴더에서 새 탭';
  $('folder-hint').textContent = source ? '현재 탭에 분할 터미널을 추가합니다.' : '현재 작업공간에 새 탭을 추가합니다.';
  $('folder-path').value = source?.cwd || currentWorkspace()?.cwd || model?.defaultCwd || '';
  $('folder-dialog').showModal();
  $('folder-path').focus(); $('folder-path').select();
}
$('folder-tab').addEventListener('click', () => { setMenuOpen($('tab-menu'), false); openFolderDialog(); });
$('folder-close').addEventListener('click', () => $('folder-dialog').close());
async function pickDirectory(trigger, input, errorNode) {
  trigger.disabled = true;
  try {
    let path;
    if (window.__TAURI__) path = await window.__TAURI__.core.invoke('plugin:dialog|open', {
      options: {directory: true, multiple: false, title: '작업 폴더 선택'}
    });
    else {
      const response = await fetch('/api/settings/choose-path', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({directory: true})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || '폴더를 선택하지 못했습니다. 경로를 직접 입력해 주세요.');
      path = result.path;
    }
    if (path) input.value = path;
  } catch (error) {
    errorNode.textContent = typeof error === 'string' ? error : error.message;
    errorNode.hidden = false;
  } finally { trigger.disabled = false; input.focus(); }
}
$('folder-pick').addEventListener('click', () => pickDirectory($('folder-pick'), $('folder-path'), $('folder-error')));
$('workspace-pick').addEventListener('click', () => pickDirectory($('workspace-pick'), $('workspace-cwd'), $('workspace-error')));
$('folder-form').addEventListener('submit', async event => {
  event.preventDefault();
  const path = $('folder-path').value;
  if (!path || working) return;
  $('folder-error').hidden = true;
  $('folder-submit').disabled = true;
  $('folder-path').disabled = $('folder-pick').disabled = true;
  try {
    if (await createTerminal(folderTarget?.source || null, folderTarget?.direction || null, path, Boolean(createTarget))) {
      $('folder-dialog').close();
      if (compact.matches) { railCollapsed = true; applyRail(); }
      requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
    }
  } finally {
    $('folder-submit').disabled = false;
    $('folder-path').disabled = $('folder-pick').disabled = Boolean(createTarget);
  }
});
$('hidden-open').addEventListener('click', () => {
  backgroundInitialized = true;
  setBackgroundOpen($('hidden-list').hidden);
});
document.addEventListener('click', event => {
  const summary = event.target.closest('.terminal-menu > summary');
  if (summary && page.contains(summary)) {
    event.preventDefault();
    setMenuOpen(summary.parentElement, !summary.parentElement.open);
    return;
  }
  for (const menu of page.querySelectorAll('.terminal-menu[open]')) {
    if (!menu.contains(event.target)) setMenuOpen(menu, false);
  }
});
document.addEventListener('focusin', event => {
  for (const menu of page.querySelectorAll('.terminal-menu[open]')) {
    if (!menu.contains(event.target)) setMenuOpen(menu, false);
  }
});
page.addEventListener('keydown', event => {
  const menu = event.target.closest('.terminal-menu');
  if (menu?.open && event.key === 'Tab') {
    setMenuOpen(menu, false); menu.querySelector('summary').focus(); return;
  }
  if (event.isComposing || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return;
  if (!menu || !['Escape', 'ArrowLeft', 'ArrowRight', 'ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
  const choosingWorkspace = menu === $('tab-menu') && !$('workspace-choices').hidden;
  if ((event.key === 'Escape' || event.key === 'ArrowLeft') && menu.open) {
    if (choosingWorkspace) showWorkspaceChoices(false, true);
    else { setMenuOpen(menu, false); menu.querySelector('summary').focus(); }
  } else if (event.key === 'ArrowRight' && event.target === $('workspace-move')) showWorkspaceChoices(true, true);
  else if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
    if (!menu.open) setMenuOpen(menu, true);
    const buttons = [...menu.querySelectorAll('.terminal-menu-items button:not(:disabled)')].filter(item => item.getClientRects().length);
    const index = buttons.indexOf(document.activeElement);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1
      : index < 0 ? event.key === 'ArrowDown' ? 0 : buttons.length - 1
      : (index + (event.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
    buttons[next]?.focus();
  } else return;
  event.preventDefault(); event.stopPropagation();
}, true);
$('empty-action').addEventListener('click', () => {
  if (!model.dependencies.installed && !model.dependencies.bundleReady) return install();
  if (currentWorkspace()?.tabs.some(tab => tab.hidden)) revealBackground();
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
  setMenuOpen($('tab-menu'), false);
  if (tab) await backgroundTab(tab);
});
$('rename').addEventListener('click', async () => {
  const tab = currentTab(); if (!tab) return;
  setMenuOpen($('tab-menu'), false);
  startTabRename(tab.id);
});
$('workspace-move').addEventListener('click', () => showWorkspaceChoices(true, true));
$('workspace-back').addEventListener('click', () => showWorkspaceChoices(false, true));
async function moveTabToWorkspace(destination) {
  const tab = currentTab();
  if (!tab || working || tab.id !== $('tab-menu').dataset.tabId) return;
  setMenuOpen($('tab-menu'), false);
  if (destination === activeWorkspace) { views.get(focusedPane)?.terminal.focus(); return; }
  working = true; feedback(); reconcile();
  let moved = false;
  try {
    await api('/workspaces/move', {id: destination, tabId: tab.id, generation: model.generation});
    activeWorkspace = destination;
    workspaceTabs.set(destination, tab.id);
    moved = true;
  } catch (error) { feedback(error.message); }
  finally { working = false; await refresh(); }
  if (moved) requestAnimationFrame(() => views.get(focusedPane)?.terminal.focus());
  else $('tab-menu').querySelector('summary').focus();
}
page.querySelectorAll('[data-terminal-move]').forEach(node => node.addEventListener('click', () => {
  setMenuOpen($('tab-menu'), false);
  if (activeTab) moveTabBy(activeTab, node.dataset.terminalMove === 'left' ? -1 : 1);
}));
window.addEventListener('pointermove', event => {
  const drag = dragState;
  if (!drag || event.pointerId !== drag.pointerId) return;
  drag.x = event.clientX; drag.y = event.clientY;
  if (!drag.moving && Math.hypot(drag.x - drag.startX, drag.y - drag.startY) > 6) {
    drag.moving = true; drag.holder.setPointerCapture(event.pointerId);
    drag.holder.classList.add('dragging'); paintTabDrag();
  }
  if (drag.moving) event.preventDefault();
});
window.addEventListener('pointerup', event => { if (event.pointerId === dragState?.pointerId) endTabDrag(true); });
window.addEventListener('pointercancel', () => endTabDrag(false));
window.addEventListener('blur', () => { endTabDrag(false); updateWindowFocus(); });
page.addEventListener('keydown', event => {
  if (event.key === 'Escape' && dragState) { endTabDrag(false); event.preventDefault(); }
});
const dismissMenus = () => page.querySelectorAll('.terminal-menu[open]').forEach(menu => setMenuOpen(menu, false));
page.addEventListener('scroll', event => {
  if (!event.target.closest?.('.terminal-menu-items')) dismissMenus();
}, true);
window.addEventListener('resize', dismissMenus);
$('stop-all').addEventListener('click', () => {
  if (confirmStop()) mutate('/stop', {expected: expectedScope()});
});
page.querySelectorAll('[data-terminal-service]').forEach(node => node.addEventListener('click', async () => {
  const action = node.dataset.terminalService;
  if (action !== 'start' && !confirmStop(null, action)) return;
  node.disabled = true;
  await mutate('/service/' + action, action === 'start' ? {} : {expected: expectedScope()});
}));
narrow.addEventListener('change', () => {
  if (narrow.matches) { railCollapsed = true; applyRail(); }
  reconcile();
});
compact.addEventListener('change', () => {
  if (compact.matches) { railCollapsed = true; applyRail(); }
});
window.addEventListener('focus', () => { updateWindowFocus(); for (const view of views.values()) markSeen(view); });
document.addEventListener('visibilitychange', () => {
  updateWindowFocus();
  if (document.hidden) endTabDrag(false);
  for (const view of views.values()) document.hidden ? view.disconnect() : view.connect();
  if (!document.hidden) refresh();
});
window.addEventListener('pagehide', () => { for (const view of views.values()) view.dispose(); views.clear(); });
window.addEventListener('pageshow', event => { if (event.persisted) refresh(); });
setInterval(() => { if (!document.hidden && !working) refresh(); }, 3000);
$('font-retry').addEventListener('click', () => location.reload());
applyRail();
updateWindowFocus();
loadFonts();
refresh();
