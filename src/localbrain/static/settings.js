(() => {
  const dialog = document.querySelector('#settings-dialog');
  if (!dialog) return;
  const $ = (selector, root = dialog) => root.querySelector(selector);
  const $$ = (selector, root = dialog) => [...root.querySelectorAll(selector)];
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!window.__TAURI__ || !link) return;
    const url = new URL(link.href, location.href);
    if (['http:', 'https:'].includes(url.protocol) && url.origin !== location.origin) {
      event.preventDefault(); window.__TAURI__.core.invoke('open_external', {url: url.href}).catch(error => message(String(error), true));
    }
  });
  let state, restoreFocus, selectedTab = 'general';
  let generalSaving = false, generalLoading = false, loadVersion = 0;
  let generalSave = Promise.resolve();
  let onboarding = document.body.dataset.onboarding === 'true', onboardingStep = 0, activeActions = 0;
  const onboardingSteps = ['welcome', 'sessions', 'context', 'search'];
  const generalForm = $('[data-general-form]');
  const syncForm = $('[data-sync-form]');
  const preferenceForms = [generalForm, syncForm];
  const sourceForm = $('[data-source-form]');
  const sourceRemovalDialog = document.querySelector('#source-remove-dialog');
  const contextForm = $('[data-context-form]');
  const contextRemovalDialog = document.querySelector('#context-remove-dialog');
  let contextSaving = false, pendingContextRemoval = null;
  let sourceSaving = false, sourceInitialValues;
  let picking = false;
  let pendingRemoval = null, removalNeedsReview = false;
  const message = (text, error = false) => {
    $('[data-settings-message]').textContent = text;
    $('[data-settings-message]').dataset.error = String(error);
    if (text && dialog.open) $('.settings-body').scrollTop = 0;
  };
  async function api(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '요청을 완료하지 못했습니다.');
    return data;
  }
  const post = (url, value, method = 'POST') => api(url, {method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(value)});
  const element = (tag, text, className) => {
    const node = document.createElement(tag); node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  function action(text, handler) {
    const button = element('button', text, 'secondary-button'); button.type = 'button';
    button.addEventListener('click', () => execute(handler, button)); return button;
  }
  async function execute(handler, button) {
    if (button) {button.disabled = true; button.setAttribute('aria-busy', 'true');}
    activeActions++; renderOnboardingControls();
    try { await handler(); } catch (error) { message(error.message, true); }
    finally {
      if (button) {button.disabled = false; button.removeAttribute('aria-busy');}
      activeActions--; renderOnboardingControls();
    }
  }
  async function pick(directory = true) {
    if (picking) return null;
    picking = true; renderOnboardingControls(); message('');
    try {
      if (window.__TAURI__) {
        // The dialog plugin attaches the chooser to this native window.
        return await window.__TAURI__.core.invoke('plugin:dialog|open', {
          options: {directory, multiple: false, title: directory ? '폴더 선택' : '파일 선택'},
        });
      }
      return (await post('/api/settings/choose-path', {directory})).path;
    } catch (error) {
      throw new Error(typeof error === 'string' ? error : error.message);
    } finally {picking = false; renderOnboardingControls();}
  }
  function editSource(value) {
    const form = sourceForm;
    form.reset();
    for (const key of ['source_id', 'provider_kind', 'display_label', 'agent_home', 'root']) form.elements[key].value = value[key] || '';
    const fields = form.elements, root = fields.root.value.trim().replace(/\/+$/, '');
    const suffix = fields.provider_kind.value === 'claude' ? '/projects' : '/sessions';
    // A conventional legacy root can supply its home without rewriting the registry.
    if (!fields.agent_home.value && root.endsWith(suffix)) fields.agent_home.value = root.slice(0, -suffix.length) || '/';
    if (root === defaultSourceRoot()) fields.root.value = '';
    sourceInitialValues = Object.fromEntries(['display_label', 'agent_home', 'root'].map(key => [key, fields[key].value]));
    form.elements.provider_kind.disabled = Boolean(value.source_id);
    $('[data-source-advanced]').open = Boolean(fields.root.value);
    form.hidden = false; message('');
    renderSourceControls(); updateSourcePaths();
    $('.settings-body').scrollTop = 0;
    form.elements.display_label.focus();
  }
  function renderSourceControls() {
    const editing = !sourceForm.hidden;
    const source = state?.session_sources?.sources.find(item => item.id === Number(sourceForm.elements.source_id.value));
    const title = editing ? (source ? '프로필 편집' : '프로필 추가') : '세션 소스';
    $('[data-source-heading]').textContent = title;
    $('[data-source-form-title]').textContent = title;
    $('[data-source-overview]').hidden = editing;
    $('[data-source-add]').hidden = editing;
    $('[data-source-submit]').textContent = source?.registered ? '저장' : source ? '다시 등록' : '추가';
    sourceForm.setAttribute('aria-busy', String(sourceSaving));
    $('fieldset', sourceForm).disabled = sourceSaving || picking;
    selects.filter(select => sourceForm.contains(select.root)).forEach(select => select.refresh());
    $$('[data-settings-tab]').forEach(button => {button.disabled = sourceSaving || contextSaving || picking;});
    for (const selector of ['[data-source-add]', '[data-source-cancel]', '[data-source-submit]']) {
      $(selector).disabled = activeActions > 0 || generalLoading || !state?.session_sources;
    }
    $$('[data-source-id], [data-source-remove], [data-profile-control]').forEach(button => {button.disabled = sourceSaving || generalLoading || button.dataset.profileDisabled === 'true';});
  }
  function showSourceOverview() {
    const key = sourceForm.elements.source_id.value;
    sourceForm.reset(); sourceForm.elements.provider_kind.disabled = false;
    sourceInitialValues = null;
    sourceForm.hidden = true; renderSourceControls();
    if (selectedTab === 'sessions' && dialog.open) {
      $('.settings-body').scrollTop = 0;
      const target = $$('[data-source-id]').find(button => button.dataset.sourceId === key) || $('[data-source-add]');
      if (!target.disabled) target.focus();
      else {const heading = $('[data-source-heading]'); heading.tabIndex = -1; heading.focus();}
    }
  }
  function defaultSourceRoot() {
    const fields = sourceForm.elements, home = fields.agent_home.value.trim();
    return home ? home.replace(/\/+$/, '') + (fields.provider_kind.value === 'claude' ? '/projects' : '/sessions') : '';
  }
  function sourceRoot() { return sourceForm.elements.root.value.trim() || defaultSourceRoot(); }
  function updateSourcePaths() {
    const fields = sourceForm.elements;
    fields.display_label.placeholder = fields.provider_kind.value === 'claude' ? 'Claude Code' : 'Codex';
    const home = fields.provider_kind.value === 'claude' ? '~/.claude' : '~/.codex';
    fields.agent_home.placeholder = home;
    const derived = defaultSourceRoot(), custom = Boolean(fields.root.value.trim());
    fields.root.placeholder = derived || home + (fields.provider_kind.value === 'claude' ? '/projects' : '/sessions');
    fields.agent_home.required = !custom;
    $('[data-source-home-required]').hidden = custom;
    $('#source-record-path').textContent = derived && !custom ? 'Session folder: ' + derived : '';
    $('#source-record-path').hidden = !derived || custom;
    $('[data-source-use-default]').hidden = !custom;
    const source = state?.session_sources?.sources.find(item => item.id === Number(fields.source_id.value));
    const root = sourceRoot().replace(/\/+$/, '');
    const unchanged = source && [source.root_path, source.display_path].some(path => path.replace(/\/+$/, '') === root);
    $('[data-reconnect-confirm]').hidden = !source || !root || unchanged;
    if ($('[data-reconnect-confirm]').hidden) fields.confirm_same_source.checked = false;
  }
  const selects = $$('[data-settings-select]').map(root => {
    const input = $('input', root), trigger = $('[role="combobox"]', root);
    const menu = $('[role="listbox"]', root), options = $$('[role="option"]', menu);
    let active = 0, typed = '', typedAt = 0;
    function close() {
      menu.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
      trigger.removeAttribute('aria-activedescendant');
      typed = '';
    }
    function refresh() {
      // Preserve stored zones or custom intervals until explicitly replaced.
      $('[data-select-value]', root).textContent = options.find(option => option.dataset.value === input.value)?.textContent || input.value + (root.dataset.selectSuffix || '');
      options.forEach(option => option.setAttribute('aria-selected', String(option.dataset.value === input.value)));
      trigger.disabled = input.disabled || Boolean(input.closest('fieldset')?.disabled);
    }
    function highlight(index) {
      active = Math.max(0, Math.min(options.length - 1, index));
      options.forEach((option, i) => option.toggleAttribute('data-active', i === active));
      trigger.setAttribute('aria-activedescendant', options[active].id);
    }
    function expand() {
      if (!menu.hidden || trigger.disabled) return;
      selects.forEach(select => select.close());
      menu.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      highlight(Math.max(0, options.findIndex(option => option.dataset.value === input.value)));
      // Scroll the settings pane only when needed; never flip the menu over its trigger.
      const body = $('.settings-body');
      const overflow = menu.getBoundingClientRect().bottom - body.getBoundingClientRect().bottom + parseFloat(getComputedStyle(body).paddingBottom);
      if (overflow > 0) body.scrollTop += overflow;
    }
    function choose(index = active) {
      const value = options[index].dataset.value, changed = input.value !== value;
      input.value = value;
      refresh(); close();
      if (changed) input.dispatchEvent(new Event('change', {bubbles: true}));
    }
    trigger.addEventListener('click', () => {
      trigger.focus();
      if (menu.hidden) expand(); else close();
    });
    menu.addEventListener('pointerdown', event => event.preventDefault());
    options.forEach((option, index) => {
      option.addEventListener('pointermove', () => highlight(index));
      option.addEventListener('click', () => {choose(index); trigger.focus();});
    });
    trigger.addEventListener('keydown', event => {
      const opened = !menu.hidden;
      if (event.key === 'Escape') {
        if (opened) {event.preventDefault(); event.stopPropagation(); close();}
        return;
      }
      if (event.key === 'Tab') {if (opened) choose(); return;}
      if (event.metaKey || event.ctrlKey) return;
      if (['Enter', ' ', 'ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
        event.preventDefault();
        if (opened && (event.key === 'Enter' || event.key === ' ' || (event.altKey && event.key === 'ArrowUp'))) {choose(); return;}
        expand();
        if (event.key === 'Home') highlight(0);
        else if (event.key === 'End') highlight(options.length - 1);
        else if (opened && event.key === 'ArrowDown' && !event.altKey) highlight(active + 1);
        else if (opened && event.key === 'ArrowUp') highlight(active - 1);
        return;
      }
      if (event.key.length === 1 && !event.altKey) {
        event.preventDefault();
        expand();
        const now = Date.now(), character = event.key.toLocaleLowerCase();
        typed = now - typedAt < 1000 ? typed + character : character;
        typedAt = now;
        const repeated = [...typed].every(value => value === character);
        const query = repeated ? character : typed;
        const indexes = options.map((_, index) => (active + 1 + index) % options.length);
        const match = indexes.find(index => options[index].textContent.toLocaleLowerCase().startsWith(query));
        if (match !== undefined) highlight(match);
      }
    });
    trigger.addEventListener('blur', () => {if (!menu.hidden) choose();});
    return {root, close, refresh, trigger};
  });
  document.addEventListener('pointerdown', event => {
    selects.forEach(select => {if (!select.root.contains(event.target)) select.close();});
  });
  dialog.addEventListener('close', () => selects.forEach(select => select.close()));
  function renderGeneral() {
    const preferences = state?.preferences;
    if (preferences && !generalSaving) {
      const saved = preferences.saved;
      for (const key of ['startup_screen', 'timezone']) generalForm.elements[key].value = saved[key];
      for (const kind of ['session', 'context']) {
        syncForm.elements[`${kind}_sync_choice`].value = saved[`${kind}_sync_enabled`] ? String(saved[`${kind}_sync_minutes`]) : 'off';
      }
    }
    preferenceForms.forEach(form => form.setAttribute('aria-busy', String(generalSaving || generalLoading)));
    const disabled = !preferences || generalSaving || generalLoading;
    selects.filter(select => preferenceForms.some(form => form.contains(select.root))).forEach(select => {
      select.close(); select.refresh();
      select.trigger.disabled = disabled || $('input', select.root).disabled;
    });
    renderOnboardingControls();
  }
  const orderPane = $('.settings-body'), orderAnimations = new WeakMap();
  let orderDrag = null;
  const orderRows = list => [...list.children].filter(row => row.dataset.orderId);
  const displayedOrder = list => orderRows(list).filter(row => row.dataset.orderEnabled === 'true').map(row => Number(row.dataset.orderId));
  function orderPositions() {
    return new Map($$('[data-order-id]').filter(row => row.getBoundingClientRect().width > 0)
      .map(row => [row.dataset.orderKind + ':' + row.dataset.orderId, row.getBoundingClientRect()]));
  }
  function animateOrderRows(before, skip = null) {
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches, style = getComputedStyle(dialog);
    $$('[data-order-id]').forEach(row => {
      const previous = before.get(row.dataset.orderKind + ':' + row.dataset.orderId);
      orderAnimations.get(row)?.cancel();
      const current = row.getBoundingClientRect();
      if (reduced || row === skip || !previous || !current.width || Math.abs(previous.top - current.top) < 1) return;
      const animation = row.animate([{transform: `translateY(${previous.top - current.top}px)`}, {transform: 'translateY(0)'}],
        {duration: parseFloat(style.getPropertyValue('--motion-standard-duration')), easing: style.getPropertyValue('--motion-ease').trim()});
      orderAnimations.set(row, animation);
      animation.finished.catch(() => {}); // A new position intentionally replaces a running transition.
    });
  }
  function showOrder(list, ids, skip = null) {
    const rows = orderRows(list), byId = new Map(rows.map(row => [Number(row.dataset.orderId), row]));
    if (ids.some(id => !byId.has(id)) || JSON.stringify(displayedOrder(list)) === JSON.stringify(ids)) return;
    const before = orderPositions(), movable = new Set(ids);
    let index = 0;
    // Retained/unconfigured rows keep their fixed slots outside the movable set.
    const next = rows.map(row => movable.has(Number(row.dataset.orderId)) ? byId.get(ids[index++]) : row);
    next.forEach((row, position) => {if (list.children[position] !== row) list.insertBefore(row, list.children[position] || null);});
    animateOrderRows(before, skip);
  }
  async function saveOrder(list, desired, source, options) {
    try {await options.save(desired, source.id);}
    finally {
      // On failed readback, the last confirmed order remains the presentation truth.
      if (list.isConnected) showOrder(list, options.ids());
    }
  }
  function finishOrderDrag(commit = false) {
    const drag = orderDrag;
    if (!drag) return;
    orderDrag = null;
    cancelAnimationFrame(drag.frame);
    if (orderPane.hasPointerCapture(drag.pointerId)) orderPane.releasePointerCapture(drag.pointerId);
    orderPane.classList.remove('is-sorting');
    drag.row.classList.remove('is-order-placeholder'); drag.ghost?.remove();
    const desired = displayedOrder(drag.list);
    if (commit && drag.started && JSON.stringify(desired) !== JSON.stringify(drag.original)) {
      execute(() => saveOrder(drag.list, desired, drag.source, drag.options));
    } else if (drag.started) {
      showOrder(drag.list, drag.original);
    }
    if (drag.grip.isConnected && !drag.grip.disabled) drag.grip.focus({preventScroll: true});
  }
  function moveOrderPreview() {
    const drag = orderDrag;
    if (!drag?.started) return;
    const pane = orderPane.getBoundingClientRect();
    const top = Math.max(pane.top, Math.min(drag.y - drag.offsetY, pane.bottom - drag.height));
    drag.ghost.style.top = top + 'px';
    if (drag.x < pane.left || drag.x > pane.right || drag.y < pane.top || drag.y > pane.bottom) return;
    const others = orderRows(drag.list).filter(row => row.dataset.orderEnabled === 'true' && row !== drag.row);
    const listTop = drag.list.getBoundingClientRect().top;
    // Layout offsets ignore running neighbor transforms, avoiding a moving hit target.
    const target = others.findIndex(row => drag.y < listTop + row.offsetTop + row.offsetHeight / 2);
    const desired = others.map(row => Number(row.dataset.orderId));
    desired.splice(target < 0 ? desired.length : target, 0, drag.source.id);
    showOrder(drag.list, desired, drag.row);
  }
  function scrollOrderPreview(time) {
    const drag = orderDrag;
    if (!drag?.started) return;
    const bounds = orderPane.getBoundingClientRect(), style = getComputedStyle(dialog);
    const edge = parseFloat(style.getPropertyValue('--control-min-height-touch'));
    const speed = parseFloat(style.getPropertyValue('--space-panel'));
    const elapsed = Math.min(32, time - (drag.lastFrame || time)); drag.lastFrame = time;
    if (drag.x >= bounds.left && drag.x <= bounds.right) {
      const direction = drag.y < bounds.top + edge ? -Math.min(1, (bounds.top + edge - drag.y) / edge)
        : drag.y > bounds.bottom - edge ? Math.min(1, (drag.y - bounds.bottom + edge) / edge) : 0;
      if (direction) {orderPane.scrollTop += direction * speed * elapsed / (1000 / 60); moveOrderPreview();}
    }
    drag.frame = requestAnimationFrame(scrollOrderPreview);
  }
  orderPane.addEventListener('pointermove', event => {
    const drag = orderDrag;
    if (!drag || event.pointerId !== drag.pointerId) return;
    drag.x = event.clientX; drag.y = event.clientY;
    if (!drag.started) {
      const threshold = parseFloat(getComputedStyle(dialog).getPropertyValue('--space-compact'));
      if (Math.hypot(drag.x - drag.startX, drag.y - drag.startY) < threshold) return;
      drag.started = true; closePalette();
      const bounds = drag.row.getBoundingClientRect();
      drag.height = bounds.height;
      drag.ghost = drag.row.cloneNode(true);
      drag.ghost.classList.add('settings-order-ghost'); drag.ghost.inert = true; drag.ghost.setAttribute('aria-hidden', 'true');
      [drag.ghost, ...drag.ghost.querySelectorAll('[id], [data-order-id]')].forEach(node => {node.removeAttribute('id'); delete node.dataset.orderId;});
      drag.ghost.querySelector('.settings-profile-palette')?.remove();
      Object.assign(drag.ghost.style, {left: bounds.left + 'px', width: bounds.width + 'px', height: bounds.height + 'px'});
      orderPane.append(drag.ghost); drag.row.classList.add('is-order-placeholder'); orderPane.classList.add('is-sorting');
      drag.frame = requestAnimationFrame(scrollOrderPreview);
    }
    event.preventDefault(); moveOrderPreview();
  });
  orderPane.addEventListener('pointerup', event => {
    if (orderDrag?.pointerId !== event.pointerId) return;
    const bounds = orderPane.getBoundingClientRect();
    finishOrderDrag(event.clientX >= bounds.left && event.clientX <= bounds.right && event.clientY >= bounds.top && event.clientY <= bounds.bottom);
  });
  orderPane.addEventListener('pointercancel', () => finishOrderDrag());
  orderPane.addEventListener('lostpointercapture', () => finishOrderDrag());
  document.addEventListener('keydown', event => {
    if (orderDrag && ['Escape', 'Tab'].includes(event.key)) {event.preventDefault(); event.stopPropagation(); finishOrderDrag();}
  }, true);
  window.addEventListener('blur', () => finishOrderDrag());
  window.addEventListener('resize', () => finishOrderDrag());
  function orderGrip(source, row, options) {
    const {kind, enabled = true, ids, busy} = options;
    row.dataset.orderId = source.id; row.dataset.orderKind = kind; row.dataset.orderEnabled = String(enabled);
    const grip = element('button', '⠿', 'settings-profile-grip'); grip.type = 'button';
    grip.dataset[kind + 'Grip'] = source.id; grip.dataset[kind + 'Control'] = '';
    grip.dataset.profileDisabled = String(!enabled); grip.disabled = !enabled;
    grip.setAttribute('aria-label', source.name + ' 순서 이동');
    grip.setAttribute('aria-describedby', kind + '-order-help');
    grip.title = '드래그 또는 ↑ ↓ 키로 순서 이동';
    grip.addEventListener('pointerdown', event => {
      if (event.button !== 0 || !event.isPrimary || !enabled || grip.disabled || busy() || generalLoading || orderDrag) return;
      event.preventDefault(); grip.focus({preventScroll: true});
      orderDrag = {source, row, grip, options, list: row.parentElement, original: ids(), pointerId: event.pointerId,
        startX: event.clientX, startY: event.clientY, x: event.clientX, y: event.clientY,
        offsetY: event.clientY - row.getBoundingClientRect().top, started: false};
      orderPane.setPointerCapture(event.pointerId);
    });
    grip.addEventListener('keydown', event => {
      if (!['ArrowUp', 'ArrowDown'].includes(event.key) || grip.disabled || busy() || generalLoading || orderDrag) return;
      event.preventDefault(); event.stopPropagation();
      const desired = ids(), from = desired.indexOf(source.id), to = from + (event.key === 'ArrowUp' ? -1 : 1);
      if (from < 0 || to < 0 || to >= desired.length) return;
      [desired[from], desired[to]] = [desired[to], desired[from]];
      const list = row.parentElement; showOrder(list, desired);
      execute(() => saveOrder(list, desired, source, options));
    });
    return grip;
  }
  function profileFocus(id, kind) {
    const attribute = kind.replace(/[A-Z]/g, letter => '-' + letter.toLowerCase());
    const node = $$('[data-profile-' + attribute + ']').find(item => item.dataset['profile' + kind[0].toUpperCase() + kind.slice(1)] === String(id));
    if (node && !node.disabled && dialog.open) node.focus();
  }
  async function changeProfile(change, id, focusKind) {
    if (sourceSaving || generalLoading) return;
    sourceSaving = true; renderSourceControls();
    const revision = state.session_sources.revision;
    let failure;
    try { await post('/api/settings/session-sources', {revision, ...change}); }
    catch (error) { failure = error; }
    try {
      await load();
      const actual = state.session_sources?.sources;
      const applied = actual && (change.action === 'color'
        ? actual.some(source => source.id === id && source.color === change.color)
        : JSON.stringify(actual.filter(source => source.configured).map(source => source.id)) === JSON.stringify(change.source_ids));
      if (!applied) throw failure || new Error('프로필 변경을 확인하지 못했습니다. 목록을 확인해 주세요.');
      $('[data-profile-status]').textContent = change.action === 'color' ? '프로필 색상을 변경했습니다.' : '프로필 순서를 변경했습니다.';
    } catch (error) { message(error.message, true); }
    finally { sourceSaving = false; renderSourceControls(); profileFocus(id, focusKind); }
  }
  let activePalette = null;
  function closePalette() {
    if (!activePalette) return;
    const {menu, trigger} = activePalette;
    activePalette = null;
    if (menu.matches(':popover-open')) menu.hidePopover();
    trigger.setAttribute('aria-expanded', 'false');
  }
  document.addEventListener('pointerdown', event => {
    if (activePalette && !activePalette.menu.contains(event.target) && !activePalette.trigger.contains(event.target)) closePalette();
  });
  document.addEventListener('focusin', event => {
    if (activePalette && !activePalette.menu.contains(event.target) && event.target !== activePalette.trigger) closePalette();
  });
  $('.settings-body').addEventListener('scroll', () => {
    if (activePalette && Math.abs(activePalette.trigger.getBoundingClientRect().bottom - activePalette.anchorBottom) > 1) closePalette();
  });
  window.addEventListener('resize', closePalette);
  function colorTag(inMenu = false) {
    const tag = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    tag.setAttribute('viewBox', '0 0 20 20'); tag.setAttribute('aria-hidden', 'true');
    // Both silhouettes span x=3..18, so their painted widths and edges match.
    const path = inMenu ? 'M18 5.5H7.5L3 10l4.5 4.5H18v-9ZM6.75 8.875a1.125 1.125 0 1 0 0 2.25 1.125 1.125 0 0 0 0-2.25Z'
      : 'M3 3h7.5L18 10.5 10.5 18 3 10.5V3Zm4 2.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z';
    tag.innerHTML = '<path fill-rule="evenodd" d="' + path + '"/>';
    return tag;
  }
  function profileControls(source, row) {
    const grip = orderGrip(source, row, {
      kind: 'profile', enabled: source.configured,
      ids: () => (state.session_sources?.sources || []).filter(item => item.configured).map(item => item.id),
      busy: () => sourceSaving || generalLoading,
      save: (ids, id) => changeProfile({action: 'reorder', source_ids: ids}, id, 'grip'),
    });
    const color = element('button', '', 'settings-profile-color'); color.type = 'button';
    color.append(colorTag());
    color.dataset.profileColor = source.color; color.dataset.profileColorTrigger = source.id;
    color.dataset.profileControl = ''; color.dataset.profileDisabled = String(!source.configured); color.disabled = !source.configured;
    color.setAttribute('aria-label', source.name + ' 색상 선택'); color.setAttribute('aria-expanded', 'false');
    color.title = '색상: ' + (state.session_sources.palette.find(choice => choice.value === source.color)?.label || source.color);
    const palette = element('div', '', 'settings-profile-palette'); palette.popover = 'auto'; palette.id = 'profile-palette-' + source.id;
    color.setAttribute('aria-controls', palette.id); color.setAttribute('aria-haspopup', 'menu');
    color.setAttribute('popovertarget', palette.id);
    palette.setAttribute('role', 'menu'); palette.setAttribute('aria-label', source.name + ' 색상');
    color.addEventListener('click', event => {
      event.preventDefault();
      const open = !palette.matches(':popover-open');
      closePalette();
      if (!open) return;
      selects.forEach(select => select.close());
      if (innerHeight - color.getBoundingClientRect().bottom < color.offsetHeight * 2) color.scrollIntoView({block: 'center', behavior: 'instant'});
      const bounds = color.getBoundingClientRect(), gap = parseFloat(getComputedStyle(dialog).getPropertyValue('--space-compact'));
      palette.style.left = bounds.left + 'px'; palette.style.top = (bounds.bottom + gap) + 'px';
      palette.style.maxHeight = Math.max(0, innerHeight - bounds.bottom - gap * 2) + 'px';
      palette.toggleAttribute('data-keyboard-focus', event.detail === 0);
      palette.showPopover();
      activePalette = {menu: palette, trigger: color, anchorBottom: bounds.bottom}; color.setAttribute('aria-expanded', 'true');
      $('[aria-checked="true"]', palette)?.focus({preventScroll: true});
    });
    palette.addEventListener('toggle', () => {
      if (!palette.matches(':popover-open') && activePalette?.menu === palette) closePalette();
    });
    palette.addEventListener('keydown', event => {
      if (event.key === 'Escape') {event.preventDefault(); event.stopPropagation(); closePalette(); color.focus();}
      if (event.key === 'Tab') {closePalette(); color.focus();}
      if (['ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) {
        // WebKit may retain pointer focus styling for this scripted focus move.
        palette.setAttribute('data-keyboard-focus', '');
        event.preventDefault(); const choices = $$('button', palette), index = choices.indexOf(document.activeElement);
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? choices.length - 1 : (index + choices.length + (event.key === 'ArrowDown' ? 1 : -1)) % choices.length;
        choices[next].focus();
      }
    });
    (state.session_sources.palette || []).forEach(choice => {
      const button = action('', () => {
        closePalette();
        return changeProfile({action: 'color', source_id: source.id, color: choice.value}, source.id, 'colorTrigger');
      });
      button.className = 'settings-profile-swatch'; button.dataset.profileColor = choice.value; button.dataset.profileControl = '';
      button.append(colorTag(true)); button.tabIndex = -1;
      button.setAttribute('aria-label', choice.label);
      button.setAttribute('role', 'menuitemradio'); button.setAttribute('aria-checked', String(source.color === choice.value)); palette.append(button);
    });
    return {grip, color, palette};
  }
  function render() {
    finishOrderDrag();
    const previousOrderPositions = orderPositions();
    closePalette();
    renderGeneral();
    if (state.session_sources) window.LocalBrainProfiles.apply(state.session_sources.sources);
    $('[data-source-list]').replaceChildren();
    (state.session_sources?.sources || []).forEach(source => {
      const row = element('article', '', 'settings-source-row');
      const identity = element('div', '', 'settings-source-identity');
      const name = element('div', '', 'settings-source-name');
      const provider = source.provider_kind === 'claude' ? 'Claude Code' : 'Codex';
      name.append(element('strong', source.name));
      if (source.name !== provider) name.append(element('small', provider));
      identity.append(name, element('p', source.display_path, 'settings-source-path'));
      if (!source.registered) identity.append(element('p', '등록 해제됨 · 기록 보관', 'settings-source-status'));
      else if (source.availability !== 'ready') {
        const statuses = {unavailable: '세션 폴더를 찾을 수 없습니다', config_missing: '프로필 설정을 확인해 주세요'};
        identity.append(element('p', statuses[source.availability] || '프로필 상태를 확인해 주세요', 'settings-source-status settings-source-warning'));
      }
      if (source.last_scan_error) identity.append(element('p', source.last_scan_error, 'settings-source-status settings-source-error'));
      const edit = action(source.registered ? '편집' : '다시 등록', () => editSource({source_id: source.id, provider_kind: source.provider_kind, display_label: source.name, agent_home: source.agent_home, root: source.root_path}));
      edit.classList.add('settings-source-row-action'); edit.dataset.sourceId = source.id;
      edit.setAttribute('aria-label', source.name + (source.registered ? ' 프로필 편집' : ' 프로필 다시 등록'));
      const actions = element('div', '', 'settings-source-row-actions'); actions.append(edit);
      if (source.registered) {
        const remove = action('등록 해제', () => requestSourceRemoval(source, remove));
        remove.classList.add('settings-source-row-action', 'settings-source-row-remove');
        remove.dataset.sourceRemove = source.id;
        remove.setAttribute('aria-label', source.name + ' 프로필 등록 해제'); actions.append(remove);
      }
      row.dataset.profileRow = source.id;
      const controls = profileControls(source, row);
      row.append(controls.grip, controls.color, identity, actions, controls.palette); $('[data-source-list]').append(row);
    });
    if (!state.session_sources?.sources.length) {
      const empty = element('div', '', 'settings-source-empty');
      empty.append(element('strong', '연결한 프로필이 없습니다'), element('p', 'Codex 또는 Claude Code 프로필을 추가하세요.'));
      $('[data-source-list]').append(empty);
    }
    $('[data-source-candidates]').replaceChildren();
    const candidates = state.candidates.filter(candidate => !(state.session_sources?.sources || []).some(source => source.provider_kind === candidate.provider_kind && source.root_path.replace(/\/+$/, '') === candidate.root.replace(/\/+$/, '')));
    $('[data-source-discovery]').hidden = candidates.length === 0;
    candidates.forEach(candidate => {
      const choice = action('', () => editSource(candidate)); choice.classList.add('settings-source-candidate');
      choice.append(element('strong', candidate.display_label), element('small', candidate.display_home));
      $('[data-source-candidates]').append(choice);
    });
    if (!sourceForm.hidden) updateSourcePaths();
    renderContexts();
    animateOrderRows(previousOrderPositions);
    renderModel(state.model);
    message(state.errors.concat(state.session_sources?.diagnostics.map(item => item.message) || []).join(' '), state.errors.length > 0);
  }
  function renderModel(model) {
    const names = {ready: '모델과 검색 준비 완료', 'index-failed': '모델 설치 완료 · 검색 인덱스 준비 실패. AI 검색 준비를 다시 시도해 주세요.', idle: '설치 전', downloading: '다운로드 중 · 네트워크 상태에 따라 몇 분 걸릴 수 있습니다', verifying: '다운로드한 파일 검증 중', installed: '모델 설치 완료', preparing: '모델 설치 완료 · 검색 준비 중', canceled: '중단됨 · 다운로드 재개 가능', failed: '설치 실패 · 연결과 저장공간을 확인한 후 재시도해 주세요'};
    $('[data-model-status]').textContent = model.runtime_missing.length ? '모델 실행 환경 없음 · local-models가 포함된 환경이 필요합니다.' : (model.installed && model.phase === 'idle' ? '모델 설치됨' : names[model.phase]);
    $('[data-model-action="install"]').disabled = model.running || model.runtime_missing.length > 0;
    $('[data-model-action="install"]').textContent = model.installed ? '다시 다운로드' : model.phase === 'canceled' || model.phase === 'failed' ? '다운로드 재개' : '모델 다운로드';
    $('[data-model-action="prepare"]').disabled = !model.installed || model.running || model.phase === 'preparing';
    $('[data-model-action="cancel"]').hidden = !(model.running && model.active_key === 'embedding') && model.phase !== 'preparing';
    for (const item of model.generation_models || []) {
      const missing = model.generation_runtime_missing || model.runtime_missing;
      const card = $(`[data-generation-model="${item.key}"]`);
      const phases = {downloading: '모델 다운로드 중', verifying: '공용 캐시 파일 검증 중', installed: '앱 연결 완료', canceled: '중단됨 · 다시 시도할 수 있습니다', failed: '설치 실패 · 연결과 저장공간을 확인한 후 재시도해 주세요'};
      card.querySelector('[data-generation-status]').textContent = missing.length ? '모델 실행 환경이 필요합니다.' : phases[item.phase] || (item.registered ? '앱에 연결됨 · 사용할 때 파일을 검증합니다' : item.cached ? '공용 캐시에서 발견됨 · 다운로드 없이 연결할 수 있습니다' : '설치 전');
      const install = card.querySelector('[data-generation-action="install"]');
      install.disabled = model.running || missing.length > 0;
      install.textContent = item.registered ? '설치 확인' : item.cached ? '공용 캐시 연결' : ['canceled', 'failed'].includes(item.phase) ? '다운로드 재개' : '모델 다운로드';
      card.querySelector('[data-generation-action="cancel"]').hidden = !item.running;
    }
  }
  async function load() {
    const version = ++loadVersion;
    generalLoading = true; renderGeneral();
    try {
      await generalSave;
      const next = await api('/api/settings');
      if (version !== loadVersion) return;
      state = next; generalLoading = false; render();
    } catch (error) {
      if (version === loadVersion) {
        generalLoading = false;
        if (state) state.preferences = null;
        renderGeneral();
      }
      throw error;
    }
  }
  function tab(name) {
    if (picking) return;
    finishOrderDrag();
    closePalette();
    const previous = selectedTab;
    selectedTab = name;
    if (!onboarding && previous === 'sessions') showSourceOverview();
    if (!onboarding && previous === 'context') showContextOverview(false);
    if (!onboarding && (previous !== name || ['sessions', 'context'].includes(name))) message('');
    selects.forEach(select => select.close());
    $$('[data-settings-panel]').forEach(panel => {panel.hidden = panel.dataset.settingsPanel !== name;});
    $$('[data-settings-tab]').forEach(button => {if (button.dataset.settingsTab === name) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');});
    $('.settings-body').scrollTop = 0;
    if (name === 'storage') execute(loadStorage);
    document.dispatchEvent(new CustomEvent('localbrain:settings-tab', {detail: name}));
  }
  function renderOnboardingControls() {
    renderSourceControls(); renderContextControls();
    dialog.classList.toggle('settings-dialog--onboarding', onboarding);
    $('[data-onboarding-progress]').hidden = !onboarding;
    $('[data-onboarding-footer]').hidden = !onboarding;
    $('.settings-nav').hidden = onboarding;
    $('#settings-title').textContent = onboarding ? 'LocalBrain 시작하기' : '설정';
    const close = $('[data-settings-close]');
    close.textContent = onboarding ? '나중에 설정' : '닫기';
    close.setAttribute('aria-label', onboarding ? '나중에 설정하고 시작' : '설정 닫기');
    close.disabled = contextSaving || picking || (onboarding && (activeActions > 0 || generalLoading));
    $('[data-onboarding-retry]').hidden = !onboarding || generalLoading || Boolean(state?.preferences);
    if (!onboarding) return;
    const busy = activeActions > 0 || generalLoading;
    const back = $('[data-onboarding-back]');
    back.disabled = busy || onboardingStep === 0;
    back.toggleAttribute('data-first-step', onboardingStep === 0);
    $('[data-onboarding-skip]').hidden = onboardingStep === 0;
    $('[data-onboarding-skip]').disabled = busy || !state?.preferences;
    const next = $('[data-onboarding-next]');
    next.disabled = busy || !state?.preferences;
    next.textContent = onboardingStep === onboardingSteps.length - 1 ? '시작하기' : '다음';
    $$('[data-onboarding-step]').forEach(item => {
      if (item.dataset.onboardingStep === onboardingSteps[onboardingStep]) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
    });
  }
  async function showOnboardingStep(animate = false) {
    const previous = $(`[data-settings-panel="${selectedTab}"]`);
    const previousIndex = onboardingSteps.indexOf(selectedTab);
    const previousScroll = $('.settings-body').scrollTop;
    tab(onboardingSteps[onboardingStep]);
    message(''); renderOnboardingControls();
    const incoming = $(`[data-settings-panel="${selectedTab}"]`);
    if (animate && previous !== incoming && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const style = getComputedStyle(dialog);
      const distance = parseFloat(style.getPropertyValue('--space-card'));
      const direction = onboardingStep > previousIndex ? 1 : -1;
      const timing = {duration: parseFloat(style.getPropertyValue('--motion-overlay-duration')), easing: style.getPropertyValue('--motion-ease').trim()};
      previous.hidden = false;
      previous.inert = true; incoming.inert = true;
      previous.setAttribute('aria-hidden', 'true');
      const outgoingMotion = previous.animate([{opacity: 1, transform: `translate(0, ${-previousScroll}px)`}, {opacity: 0, transform: `translate(${-direction * distance}px, ${-previousScroll}px)`}], timing);
      const incomingMotion = incoming.animate([{opacity: 0, transform: `translateX(${direction * distance}px)`}, {opacity: 1, transform: 'translateX(0)'}], timing);
      try { await Promise.all([outgoingMotion.finished, incomingMotion.finished]); }
      finally {
        previous.hidden = true; previous.inert = false; incoming.inert = false;
        previous.removeAttribute('aria-hidden');
      }
    }
    const title = $('h3', incoming);
    title.setAttribute('tabindex', '-1'); title.focus({preventScroll: true});
  }
  async function open(name = 'general') {
    if (picking) return;
    if (sourceRemovalDialog.open || contextRemovalDialog.open) return;
    if (onboarding && dialog.open) return;
    restoreFocus = document.activeElement;
    if (!dialog.open) dialog.showModal();
    if (onboarding) await showOnboardingStep(); else tab(name);
    message('설정을 불러오는 중…'); await execute(load);
  }
  $$('[data-settings-tab]').forEach(button => button.addEventListener('click', () => tab(button.dataset.settingsTab)));
  document.querySelectorAll('[data-settings-open]').forEach(button => button.addEventListener('click', () => open(button.dataset.settingsOpen || 'general')));
  $('[data-settings-close]').addEventListener('click', event => {
    if (onboarding) execute(finishOnboarding, event.currentTarget); else dialog.close();
  });
  dialog.addEventListener('cancel', event => {
    if (contextSaving || picking) {event.preventDefault(); return;}
    if (onboarding) {event.preventDefault(); if (!activeActions) execute(finishOnboarding);}
  });
  dialog.addEventListener('close', () => {finishOrderDrag(); closePalette(); sourceRemovalDialog.close(); contextRemovalDialog.close(); restoreFocus?.focus();});
  document.addEventListener('keydown', event => {if ((event.metaKey || event.ctrlKey) && event.key === ',') {event.preventDefault(); open();}});
  window.addEventListener('localbrain-settings', () => open());
  preferenceForms.forEach(form => form.addEventListener('submit', event => event.preventDefault()));
  function saveGeneral(changes, focus = document.activeElement) {
    if (!state?.preferences || generalSaving || generalLoading) return;
    if (Object.entries(changes).every(([key, value]) => state.preferences.saved[key] === value)) return;
    // A local write owns one revision; briefly lock choices instead of racing saves.
    generalSaving = true; renderGeneral(); message('');
    generalSave = (async () => {
      try {
        state.preferences = await post('/api/settings/preferences', {revision: state.preferences.revision, changes}, 'PATCH');
        window.dispatchEvent(new Event('localbrain-sync-requested'));
      } catch {
        try {
          state.preferences = (await api('/api/settings')).preferences;
          if (!state.preferences) throw new Error('Preferences unavailable');
          // A lost response can follow a successful write. Confirm against the file.
          const confirmed = Object.entries(changes).every(([key, value]) => state.preferences.saved[key] === value);
          if (!confirmed) message('설정을 저장하지 못했습니다. 현재 저장된 값으로 되돌렸습니다. 다시 선택해 주세요.', true);
        } catch {
          state.preferences = null;
          message('저장 상태를 확인하지 못했습니다. 설정을 닫았다가 다시 열어 주세요.', true);
        }
      } finally {
        generalSaving = false; renderGeneral();
        if (dialog.open && focus?.closest('[data-settings-panel]')?.dataset.settingsPanel === selectedTab && !generalLoading && document.activeElement === document.body) focus.focus();
      }
    })();
  }
  preferenceForms.forEach(form => form.addEventListener('change', event => {
    const input = event.target;
    const kind = input.dataset.syncKind;
    if (kind) {
      // Off preserves the interval; choosing minutes enables and updates it together.
      saveGeneral(input.value === 'off' ? {[`${kind}_sync_enabled`]: false} : {
        [`${kind}_sync_enabled`]: true, [`${kind}_sync_minutes`]: Number(input.value),
      });
    } else saveGeneral({[input.name]: input.value});
  }));
  $('[data-source-add]').addEventListener('click', () => editSource({provider_kind: 'codex'}));
  $('[data-source-cancel]').addEventListener('click', () => {showSourceOverview(); message('');});
  sourceForm.elements.provider_kind.addEventListener('change', updateSourcePaths);
  for (const key of ['agent_home', 'root']) sourceForm.elements[key].addEventListener('input', () => {sourceForm.elements.confirm_same_source.checked = false; updateSourcePaths();});
  $$('[data-pick]').forEach(button => button.addEventListener('click', event => execute(async () => {
    const path = await pick();
    if (path) {sourceForm.elements[button.dataset.pick].value = path; sourceForm.elements.confirm_same_source.checked = false; updateSourcePaths();}
  }, event.currentTarget)));
  $('[data-source-use-default]').addEventListener('click', () => {
    sourceForm.elements.root.value = ''; sourceForm.elements.confirm_same_source.checked = false;
    $('[data-source-advanced]').open = false; updateSourcePaths(); sourceForm.elements.agent_home.focus();
  });
  function hasPendingSource() {
    if (sourceForm.hidden) return false;
    const form = sourceForm.elements;
    const previous = state.session_sources?.sources.find(source => source.id === Number(form.source_id.value));
    if (!previous) return ['display_label', 'agent_home', 'root'].some(key => form[key].value.trim());
    return !previous.registered || ['display_label', 'agent_home', 'root'].some(key => form[key].value !== sourceInitialValues[key]) || form.confirm_same_source.checked;
  }
  async function saveSource() {
    if (!sourceForm.reportValidity()) return false;
    const data = Object.fromEntries(new FormData(sourceForm));
    data.provider_kind = sourceForm.elements.provider_kind.value;
    data.root = sourceRoot();
    data.confirm_same_source = sourceForm.elements.confirm_same_source.checked;
    data.action = data.confirm_same_source ? 'reconnect' : 'save'; data.revision = state.session_sources?.revision;
    if (!data.source_id) delete data.source_id;
    else data.source_id = Number(data.source_id);
    sourceSaving = true; renderSourceControls();
    try {
      await post('/api/settings/session-sources', data); await load(); showSourceOverview();
      message('프로필을 저장했습니다.'); return true;
    } finally {sourceSaving = false; renderSourceControls();}
  }
  sourceForm.addEventListener('submit', event => {event.preventDefault(); execute(saveSource, event.submitter);});
  function renderSourceRemoval() {
    sourceRemovalDialog.setAttribute('aria-busy', String(sourceSaving));
    $('[data-source-remove-cancel]', sourceRemovalDialog).disabled = sourceSaving;
    $('[data-source-remove-confirm]', sourceRemovalDialog).disabled = sourceSaving || removalNeedsReview;
  }
  function requestSourceRemoval(source, trigger) {
    if (pendingRemoval || sourceSaving || generalLoading || !source.registered) return;
    pendingRemoval = {id: source.id, revision: state.session_sources.revision, trigger};
    removalNeedsReview = false;
    $('[data-source-remove-name]', sourceRemovalDialog).textContent = source.name;
    $('[data-source-remove-error]', sourceRemovalDialog).hidden = true;
    renderSourceRemoval(); sourceRemovalDialog.showModal();
    dialog.inert = true;
    $('[data-source-remove-cancel]', sourceRemovalDialog).focus();
  }
  $('[data-source-remove-cancel]', sourceRemovalDialog).addEventListener('click', () => sourceRemovalDialog.close());
  sourceRemovalDialog.addEventListener('cancel', event => {
    event.preventDefault(); event.stopPropagation();
    if (!sourceSaving) sourceRemovalDialog.close();
  });
  sourceRemovalDialog.addEventListener('close', () => {
    dialog.inert = false;
    const previous = pendingRemoval; pendingRemoval = null;
    if (!previous || !dialog.open) return;
    const target = previous.trigger.isConnected ? previous.trigger
      : $$('[data-source-remove]').find(button => button.dataset.sourceRemove === String(previous.id))
        || $$('[data-source-id]').find(button => button.dataset.sourceId === String(previous.id)) || $('[data-source-add]');
    target.focus();
  });
  $('[data-source-remove-confirm]', sourceRemovalDialog).addEventListener('click', async () => {
    if (!pendingRemoval || sourceSaving || removalNeedsReview) return;
    const pending = pendingRemoval, errorMessage = $('[data-source-remove-error]', sourceRemovalDialog);
    sourceSaving = true; renderSourceControls(); renderSourceRemoval(); errorMessage.hidden = true;
    let removed = false;
    try {
      await post('/api/settings/session-sources', {revision: pending.revision, source_id: pending.id, action: 'remove'});
      await load(); removed = true;
    } catch (error) {
      try {
        // A lost response may follow a successful removal. Read the registry before retrying.
        await load();
        removed = state.session_sources?.sources.some(source => source.id === pending.id && !source.registered);
      } catch { /* Keep the confirmation open when persistence cannot be checked. */ }
      if (!removed) {
        removalNeedsReview = !state?.session_sources || state.session_sources.revision !== pending.revision;
        errorMessage.textContent = removalNeedsReview ? '목록이 변경되었습니다. 취소한 뒤 프로필을 다시 확인해 주세요.' : error.message;
        errorMessage.hidden = false;
      }
    } finally {sourceSaving = false; renderSourceControls(); renderSourceRemoval();}
    if (removed) {sourceRemovalDialog.close(); message('등록을 해제했습니다.');}
    else if (sourceRemovalDialog.open) $('[data-source-remove-' + (removalNeedsReview ? 'cancel' : 'confirm') + ']', sourceRemovalDialog).focus();
  });
  function renderContextControls() {
    const editing = !$('[data-context-editor]').hidden;
    $('[data-context-heading]').textContent = editing ? 'Local Context 추가' : 'Local Context';
    $('[data-context-overview]').hidden = editing;
    $('[data-context-add]').hidden = editing;
    const busy = contextSaving || generalLoading || picking;
    contextForm.setAttribute('aria-busy', String(contextSaving));
    $('fieldset', contextForm).disabled = busy;
    for (const selector of ['[data-context-add]', '[data-context-cancel]', '[data-context-submit]', '[data-notes-add]']) {
      $(selector).disabled = busy || !state;
    }
    $$('[data-context-control], [data-context-remove]').forEach(button => {button.disabled = busy;});
    $('[data-context-notes]').hidden = Boolean(state?.context_sources.some(source => source.source_type === 'apple_notes'));
    selects.filter(select => contextForm.contains(select.root)).forEach(select => select.refresh());
  }
  function showContextOverview(focus = true) {
    contextForm.reset();
    $('[data-context-editor]').hidden = true; renderContextControls();
    if (focus && dialog.open && selectedTab === 'context') $('[data-context-add]').focus();
  }
  function renderContexts() {
    const list = $('[data-context-list]'); list.replaceChildren();
    state.context_sources.forEach(source => {
      const row = element('article', '', 'settings-source-row settings-context-row'); row.dataset.contextRow = source.id;
      const identity = element('div', '', 'settings-source-identity');
      const name = element('div', '', 'settings-source-name'); name.append(element('strong', source.label));
      identity.append(name, element('p', source.display_path, 'settings-source-path'));
      const statuses = {pending: '가져오기 대기', scanning: '동기화 중', unreadable: '문서를 읽을 수 없습니다', missing: '경로를 찾을 수 없습니다', error: '문서를 가져오지 못했습니다'};
      const status = source.error || (!source.exists_now ? '경로를 찾을 수 없습니다' : statuses[source.status]);
      if (status) identity.append(element('p', status, 'settings-source-status' + (source.error || !source.exists_now || !source.readable || source.status === 'error' ? ' settings-source-error' : '')));
      const grip = orderGrip({id: source.id, name: source.label}, row, {
        kind: 'context', ids: () => state.context_sources.map(item => item.id),
        busy: () => contextSaving || generalLoading, save: changeContextOrder,
      });
      const remove = action('등록 해제', () => requestContextRemoval(source, remove));
      remove.classList.add('settings-source-row-action', 'settings-source-row-remove'); remove.dataset.contextRemove = source.id;
      remove.setAttribute('aria-label', source.label + ' 등록 해제');
      const actions = element('div', '', 'settings-source-row-actions'); actions.append(remove);
      row.append(grip, identity, actions); list.append(row);
    });
    if (!state.context_sources.length) {
      const empty = element('div', '', 'settings-source-empty');
      empty.append(element('strong', '연결한 문서가 없습니다'), element('p', '폴더, 파일 또는 Apple Notes를 추가하세요.')); list.append(empty);
    }
    renderContextControls();
  }
  async function changeContextOrder(ids, id) {
    if (contextSaving || generalLoading) return;
    const expected = state.context_sources.map(item => item.id);
    contextSaving = true; renderOnboardingControls();
    let failure;
    try {await post('/api/context-sources/order', {source_ids: ids, expected_source_ids: expected});}
    catch (error) {failure = error;}
    try {
      await load();
      if (JSON.stringify(state.context_sources.map(item => item.id)) !== JSON.stringify(ids)) throw failure || new Error('순서 변경을 확인하지 못했습니다.');
      $('[data-context-status]').textContent = 'Local Context 순서를 변경했습니다.';
    } catch (error) {message(error.message, true);}
    finally {
      contextSaving = false; renderOnboardingControls();
      $$('[data-context-grip]').find(button => button.dataset.contextGrip === String(id))?.focus();
    }
  }
  $('[data-context-add]').addEventListener('click', () => {
    $('[data-context-editor]').hidden = false; message(''); renderContextControls();
    $('.settings-body').scrollTop = 0; contextForm.elements.path.focus();
  });
  $('[data-context-cancel]').addEventListener('click', () => {showContextOverview(); message('');});
  $('[data-context-pick]').addEventListener('click', event => execute(async () => {const path = await pick(contextForm.elements.kind.value === 'roots'); if (path) contextForm.elements.path.value = path;}, event.currentTarget));
  async function saveContext() {
    if (!contextForm.reportValidity()) return false;
    if (contextSaving) return false;
    contextSaving = true; renderOnboardingControls(); message('문서를 가져오는 중…');
    try {
      const result = await post('/api/context-' + contextForm.elements.kind.value, {path: contextForm.elements.path.value});
      await load();
      if (result.report.failed) {
        message(onboarding ? '등록했지만 일부 문서를 읽지 못했습니다. 경로를 확인하거나 이 단계를 건너뛰어 주세요.' : '등록했지만 일부 문서를 읽지 못했습니다. Local Context에서 상태를 확인해 주세요.', true);
        return false;
      }
      showContextOverview(false); message('문서를 가져왔습니다.'); return true;
    } finally {contextSaving = false; renderOnboardingControls();}
  }
  contextForm.addEventListener('submit', event => {event.preventDefault(); execute(async () => {
    if (await saveContext()) {renderContextControls(); $('[data-context-add]').focus();}
  }, event.submitter);});
  $('[data-notes-add]').addEventListener('click', event => execute(async () => {
    if (contextSaving) return;
    contextSaving = true; renderOnboardingControls();
    try {
      const result = await post('/api/context-sources/apple-notes', {}); await load();
      showContextOverview(false);
      message(result.report.failed ? 'Apple Notes를 읽지 못했습니다. 접근 권한을 확인해 주세요.' : 'Apple Notes를 연결했습니다.', Boolean(result.report.failed));
    } finally {contextSaving = false; renderOnboardingControls();}
  }, event.currentTarget));
  function renderContextRemoval() {
    contextRemovalDialog.setAttribute('aria-busy', String(contextSaving));
    $('[data-context-remove-cancel]', contextRemovalDialog).disabled = contextSaving;
    $('[data-context-remove-confirm]', contextRemovalDialog).disabled = contextSaving;
  }
  function requestContextRemoval(source, trigger) {
    if (pendingContextRemoval || contextSaving || generalLoading) return;
    pendingContextRemoval = {id: source.id, trigger, inSettings: dialog.open};
    $('[data-context-remove-name]', contextRemovalDialog).textContent = source.label;
    $('[data-context-remove-error]', contextRemovalDialog).hidden = true;
    renderContextRemoval(); contextRemovalDialog.showModal(); dialog.inert = true;
    $('[data-context-remove-cancel]', contextRemovalDialog).focus();
  }
  window.addEventListener('localbrain:remove-context', event => requestContextRemoval(event.detail.source, event.detail.trigger));
  $('[data-context-remove-cancel]', contextRemovalDialog).addEventListener('click', () => contextRemovalDialog.close());
  contextRemovalDialog.addEventListener('cancel', event => {
    event.preventDefault(); event.stopPropagation(); if (!contextSaving) contextRemovalDialog.close();
  });
  contextRemovalDialog.addEventListener('close', () => {
    dialog.inert = false;
    const previous = pendingContextRemoval; pendingContextRemoval = null;
    if (!previous) return;
    const target = previous.trigger.isConnected ? previous.trigger : $$('[data-context-remove]').find(button => button.dataset.contextRemove === String(previous.id)) || $('[data-context-add]');
    target.focus();
  });
  $('[data-context-remove-confirm]', contextRemovalDialog).addEventListener('click', async () => {
    if (!pendingContextRemoval || contextSaving) return;
    const pending = pendingContextRemoval, errorMessage = $('[data-context-remove-error]', contextRemovalDialog);
    contextSaving = true; renderOnboardingControls(); renderContextRemoval(); errorMessage.hidden = true;
    let removed = false;
    try {
      await api('/api/context-sources/' + pending.id, {method: 'DELETE'});
      if (pending.inSettings) await load(); removed = true;
    } catch (error) {
      try {
        const current = await api('/api/settings');
        removed = !current.context_sources.some(source => source.id === pending.id);
        if (pending.inSettings) {state = current; render();}
      } catch { /* A failed confirmation stays open for an explicit retry. */ }
      if (!removed) {errorMessage.textContent = error.message; errorMessage.hidden = false;}
    } finally {contextSaving = false; renderOnboardingControls(); renderContextRemoval();}
    if (removed) {
      contextRemovalDialog.close();
      if (pending.inSettings) message('등록을 해제했습니다.'); else location.assign('/context');
    } else $('[data-context-remove-confirm]', contextRemovalDialog).focus();
  });
  $$('[data-model-action]').forEach(button => button.addEventListener('click', () => execute(async () => {renderModel(await post('/api/settings/model/' + button.dataset.modelAction, {})); message('요청을 적용했습니다. 진행 상태를 확인해 주세요.');}, button)));
  $$('[data-generation-action]').forEach(button => button.addEventListener('click', () => execute(async () => {
    const key = button.closest('[data-generation-model]').dataset.generationModel;
    renderModel(await post('/api/settings/model/' + key + '/' + button.dataset.generationAction, {}));
    document.dispatchEvent(new CustomEvent('localbrain:models-changed'));
    message('요청을 적용했습니다. 모델 진행 상태를 확인해 주세요.');
  }, button)));
  const bytes = value => `${(value / 1024 ** 3).toFixed(2)} GB`;
  async function loadStorage() {
    const data = await api('/api/settings/storage'); const root = $('[data-storage-summary]'); root.replaceChildren();
    const group = element('div', '', 'settings-group');
    for (const [name, key] of [['데이터·설정', 'data'], ['앱 캐시', 'cache'], ['공유 공개 모델 캐시', 'models']]) {
      const row = element('div', '', 'settings-group-row');
      const identity = element('div', '', 'settings-group-identity');
      identity.append(element('strong', name), element('p', data.display_paths[key], 'settings-location'));
      row.append(identity, element('span', bytes(data[key + '_bytes']), 'settings-size')); group.append(row);
    }
    root.append(group, element('p', '사용 가능한 공간 ' + bytes(data.free_bytes), 'settings-caption'));
    if (data.restore_pending) root.append(element('p', '복원 예약됨 · 앱과 웹 서버를 모두 종료한 후 다시 실행해 주세요.', 'settings-caption'));
  }
  $('[data-backup]').addEventListener('click', event => execute(async () => {
    if (window.__TAURI__) {
      const path = await window.__TAURI__.core.invoke('choose_backup_path');
      if (!path) return;
      message('백업을 만드는 중…'); await post('/api/settings/backup/export', {path}); message('백업 파일을 저장했습니다.'); return;
    }
    message('백업을 만드는 중…'); const response = await fetch('/api/settings/backup', {method: 'POST'});
    if (!response.ok) throw new Error((await response.json()).detail || '백업을 만들지 못했습니다.');
    const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'LocalBrain-backup.zip'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 60000); message('백업 파일을 저장했습니다.');
  }, event.currentTarget));
  $('[data-restore-form]').addEventListener('submit', event => {event.preventDefault(); const file = event.currentTarget.elements.archive.files[0]; execute(async () => {await api('/api/settings/restore', {method: 'POST', headers: {'Content-Type': 'application/zip', 'X-LocalBrain-Confirm': 'replace-after-restart'}, body: file}); await loadStorage(); message('복원을 예약했습니다. 앱과 웹 서버를 모두 종료한 후 다시 실행해 주세요.');}, event.submitter);});
  $('[data-cache-clear]').addEventListener('click', event => execute(async () => {const result = await post('/api/settings/cache/clear', {}); await loadStorage(); message(bytes(result.removed_bytes) + ' 캐시를 정리했습니다.');}, event.currentTarget));
  async function finishOnboarding() {
    const current = await api('/api/settings');
    if (!current.preferences) throw new Error(current.errors.join(' '));
    state = current;
    try {
      state.preferences = await post('/api/settings/preferences', {revision: current.preferences.revision, changes: {onboarding_completed: true}}, 'PATCH');
    } catch (error) {
      const confirmed = (await api('/api/settings')).preferences;
      if (!confirmed?.saved.onboarding_completed) throw error;
      state.preferences = confirmed;
    }
    onboarding = false;
    delete document.body.dataset.onboarding;
    document.querySelector('.app-shell').inert = false;
    document.querySelector('.skip-link').inert = false;
    dialog.close();
    location.replace('/' + state.preferences.effective.startup_screen);
  }
  $('[data-onboarding-back]').addEventListener('click', event => execute(async () => {onboardingStep--; await showOnboardingStep(true);}, event.currentTarget));
  $('[data-onboarding-retry]').addEventListener('click', event => execute(load, event.currentTarget));
  $('[data-onboarding-skip]').addEventListener('click', event => execute(async () => {
    if (onboardingStep === onboardingSteps.length - 1) await finishOnboarding();
    else {onboardingStep++; await showOnboardingStep(true);}
  }, event.currentTarget));
  $('[data-onboarding-next]').addEventListener('click', event => execute(async () => {
    if (selectedTab === 'sessions' && hasPendingSource() && !await saveSource()) return;
    if (selectedTab === 'context' && contextForm.elements.path.value.trim() && !await saveContext()) return;
    if (onboardingStep === onboardingSteps.length - 1) await finishOnboarding();
    else {onboardingStep++; await showOnboardingStep(true);}
  }, event.currentTarget));
  async function pollModel() {
    if (dialog.open && selectedTab === 'search') {
      try {
        const data = await api('/api/settings'); renderModel(data.model);
        const search = await api('/api/natural-search/status');
        $('[data-search-state]').textContent = search.state === 'disabled' ? '현재 꺼져 있습니다.' : `${search.title} · ${search.description}`;
        $('[data-model-action="disable"]').disabled = search.state === 'disabled';
      } catch (_) { /* explicit requests retain errors */ }
    }
    setTimeout(pollModel, 3000);
  }
  pollModel();
  if (onboarding) {
    const url = new URL(location.href); url.searchParams.delete('setup');
    history.replaceState(history.state, '', url);
    open();
  } else if (location.pathname === '/settings') open();
})();
