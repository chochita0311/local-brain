(() => {
  'use strict';
  const root = document.querySelector('[data-context-chat]');
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  const question = $('[data-chat-question]'), model = $('[data-chat-model]');
  const transcript = $('[data-chat-transcript]'), status = $('[data-chat-status]');
  let messages = [], controller = null, version = 0, busy = false, ready = false, state = null;

  function notice(text, error = false) { status.textContent = text; status.toggleAttribute('data-error', error); }
  function controls() {
    question.disabled = !ready || busy;
    $('[data-chat-send]').disabled = !ready || busy || !question.value.trim();
    $('[data-chat-send]').hidden = busy;
    $('[data-chat-stop]').hidden = !busy;
    model.disabled = busy;
    $('[data-chat-clear]').disabled = !transcript.childElementCount && !question.value;
    $('[data-chat-form]').setAttribute('aria-busy', String(busy));
    root.querySelectorAll('[data-chat-example]').forEach(button => { button.disabled = busy; });
  }
  function unload() { fetch('/api/context-search/unload', {method: 'POST', keepalive: true}).catch(() => {}); }
  function reset() {
    version++; controller?.abort(); controller = null; messages = []; busy = false;
    question.value = ''; transcript.replaceChildren(); $('[data-chat-intro]').hidden = false;
    notice(ready ? '자료에서 찾은 근거와 함께 답변합니다.' : '모델과 자료 연결을 확인해 주세요.');
    controls(); unload();
  }
  async function load() {
    try {
      const response = await fetch('/api/context-search/status', {cache: 'no-store'});
      const next = await response.json();
      if (!response.ok) throw new Error(next.detail || '자료 목록을 확인하지 못했습니다.');
      state = next;
      for (const item of state.models) {
        const option = model.querySelector(`option[value="${item.key}"]`);
        option.disabled = !item.available || state.runtime_missing.length > 0;
        option.textContent = item.name + (item.available ? '' : ' · 설치 필요');
      }
      if (model.selectedOptions[0]?.disabled) {
        const available = state.models.find(item => item.available);
        if (available) model.value = available.key;
      }
      const own = state.sources.filter(item => item.kind === 'local').length;
      const received = state.sources.length - own;
      $('[data-chat-sources]').textContent = `Local Context ${own}개 · 받은 폴더 ${received}개`;
      const list = $('[data-chat-source-list]'); list.replaceChildren();
      for (const source of state.sources) {
        const li = document.createElement('li');
        li.textContent = source.name + (source.kind === 'received' ? ' · 받은 사본' + (source.syncing ? ' · 동기화 사용' : ' · 동기화 중단') + (source.observed_at ? ' · 마지막 수신 ' + source.observed_at : '') : ' · 내 Local Context');
        list.append(li);
      }
      const hasModel = state.models.some(item => item.available) && !state.runtime_missing.length;
      ready = hasModel && state.sources.length > 0;
      $('[data-chat-setup]').hidden = hasModel;
      $('[data-chat-context-setup]').hidden = state.sources.length > 0;
      if (!busy) notice(!hasModel ? '설정에서 답변 모델을 설치하거나 공용 캐시에 있는 모델을 연결해 주세요.' : !state.sources.length ? 'Local Context를 연결하거나 Google Drive 폴더를 먼저 받아 주세요.' : '자료에서 찾은 근거와 함께 답변합니다.');
    } catch (error) { ready = false; notice(error.message, true); }
    controls();
  }
  function addMessage(role, text, label) {
    const article = document.createElement('article'); article.className = 'context-chat-message'; article.dataset.role = role;
    const heading = document.createElement('h2'); heading.textContent = label;
    const body = document.createElement('div'); body.className = 'context-chat-message-body'; body.textContent = text;
    article.append(heading, body); transcript.append(article); return article;
  }
  function evidence(article, items, limited) {
    if (limited) {
      const note = document.createElement('p'); note.className = 'context-chat-caption';
      note.textContent = '모델이 확인한 자료 범위에 한계가 있습니다. 폴더·파일·키워드를 구체화해 주세요.'; article.append(note);
    }
    if (!items.length) return;
    const details = document.createElement('details'); details.className = 'context-chat-evidence';
    const summary = document.createElement('summary'); summary.textContent = `확인한 근거 ${items.length}개`;
    const list = document.createElement('ul');
    for (const item of items) {
      const li = document.createElement('li'), title = document.createElement('strong'), quote = document.createElement('pre');
      title.textContent = `[${item.ref}] ${item.source} / ${item.path}:${item.line}`; quote.textContent = item.text;
      li.append(title, quote); list.append(li);
    }
    details.append(summary, list); article.append(details);
  }
  async function submit(event) {
    event.preventDefault();
    const text = question.value.trim(); if (!text || !ready || busy) return;
    const turn = ++version, selected = model.value, label = model.selectedOptions[0].textContent;
    controller = new AbortController(); const signal = controller.signal;
    busy = true; question.value = ''; $('[data-chat-intro]').hidden = true;
    addMessage('user', text, '나'); controls(); notice('로컬 모델을 준비하고 있습니다.');
    let finished = false;
    const history = [...messages.slice(-6), {role: 'user', content: text}];
    try {
      const response = await fetch('/api/context-search/answer', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({model: selected, messages: history}), signal});
      if (!response.ok) { const value = await response.json(); throw new Error(value.detail || '질문을 처리하지 못했습니다.'); }
      const reader = response.body.getReader(), decoder = new TextDecoder(); let pending = '';
      const phases = {loading: '모델 파일을 검증하고 메모리에 올리고 있습니다. 첫 질문은 더 걸릴 수 있습니다.', generating: '자료를 살펴보고 답변을 준비하고 있습니다.', searching: '폴더와 문서에서 필요한 내용을 찾고 있습니다.', reading: '찾은 파일의 내용을 읽고 있습니다.'};
      while (true) {
        const {value, done} = await reader.read();
        if (turn !== version) { await reader.cancel(); return; }
        pending += decoder.decode(value || new Uint8Array(), {stream: !done});
        let end;
        while ((end = pending.indexOf('\n')) >= 0) {
          const item = JSON.parse(pending.slice(0, end)); pending = pending.slice(end + 1);
          if (item.type === 'status') notice(phases[item.phase] || '답변을 준비하고 있습니다.');
          else if (item.type === 'error') throw new Error(item.message);
          else if (item.type === 'answer') {
            const article = addMessage('assistant', item.text, label); evidence(article, item.evidence || [], item.limited);
            if (typeof item.html === 'string') {
              const body = article.querySelector('.context-chat-message-body');
              body.classList.add('markdown-body'); body.innerHTML = item.html;
            }
            messages = [...history, {role: 'assistant', content: item.text}];
            finished = true; notice('답변 완료 · 근거를 열어 원문 내용을 확인할 수 있습니다.');
          }
        }
        if (done) break;
      }
      if (!finished) throw new Error('응답 연결이 끊겼습니다. 다시 시도해 주세요.');
    } catch (error) {
      if (turn !== version) return;
      notice(error.name === 'AbortError' ? '생성을 중단했습니다. 질문을 수정하거나 다시 보낼 수 있습니다.' : error.message, error.name !== 'AbortError');
      question.value = text;
    } finally {
      if (turn === version) { controller = null; busy = false; controls(); question.focus(); }
    }
  }
  $('[data-chat-form]').addEventListener('submit', submit);
  question.addEventListener('input', controls);
  question.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); if (!busy) $('[data-chat-form]').requestSubmit(); } });
  $('[data-chat-stop]').addEventListener('click', () => controller?.abort());
  $('[data-chat-clear]').addEventListener('click', () => { reset(); question.focus(); });
  root.querySelectorAll('[data-chat-example]').forEach(button => button.addEventListener('click', () => { question.value = button.textContent; controls(); question.focus(); }));
  model.addEventListener('change', () => { unload(); notice('다음 답변부터 선택한 모델을 사용합니다.'); });
  document.addEventListener('localbrain:settings-tab', reset);
  document.addEventListener('localbrain:models-changed', load);
  document.addEventListener('visibilitychange', () => { if (document.hidden) reset(); else load(); });
  window.addEventListener('pagehide', reset);
  window.addEventListener('pageshow', () => { reset(); load(); });
  document.addEventListener('click', event => { const link = event.target.closest('a[href]'); if (link && !link.hash && !event.ctrlKey && !event.metaKey) reset(); }, {capture: true});
  document.querySelector('#settings-dialog')?.addEventListener('close', load);
  load();
})();
