(() => {
  'use strict';
  const panel = document.querySelector('[data-settings-panel="google-drive"]');
  if (!panel) return;
  const $ = selector => panel.querySelector(selector);
  let state, connectionId, timer, checking = false, loading = Promise.resolve(), saving = Promise.resolve();
  const labels = new Map([[15, '15분'], [30, '30분'], [60, '1시간'], [180, '3시간'], [360, '6시간'], [720, '12시간'], [1440, '24시간']]);
  const node = (tag, text, className) => {
    const value = document.createElement(tag);
    if (text !== undefined) value.textContent = text;
    if (className) value.className = className;
    return value;
  };
  const current = () => state?.connections.find(item => item.id === connectionId);
  const path = suffix => '/' + encodeURIComponent(connectionId) + suffix;
  function message(text, error = false) {
    $('[data-drive-message]').textContent = text;
    $('[data-drive-message]').setAttribute('role', error ? 'alert' : 'status');
  }
  async function api(suffix = '', method = 'GET', body) {
    const response = await fetch('/api/settings/google-drive' + suffix, {method,
      headers: body === undefined ? {} : {'Content-Type': 'application/json'},
      ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    const value = await response.json();
    if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : '요청을 완료하지 못했습니다.');
    return value;
  }
  async function perform(operation, button) {
    if (button) button.disabled = true;
    try { await operation(); } catch (error) { message(error.message, true); }
    finally { if (button) button.disabled = false; if (state) observations(); }
  }
  function save(key, changes) {
    const id = connectionId;
    saving = saving.catch(() => {}).then(async () => {
      await api('/' + encodeURIComponent(id) + '/jobs/' + encodeURIComponent(key), 'PATCH', changes);
      message('설정을 저장했습니다.'); await load(false);
    });
    saving.catch(error => message(error.message, true));
    return saving;
  }
  function date(value) {
    return value ? new Intl.DateTimeFormat('ko', {timeZone: state.timezone, dateStyle: 'short', timeStyle: 'short'}).format(new Date(value)) : '없음';
  }
  function report(root, job, progress) {
    const revision = JSON.stringify([job || {}, progress]);
    if (root.dataset.revision === revision) return;
    const expanded = root.querySelector('details')?.open;
    root.dataset.revision = revision;
    root.replaceChildren();
    if (job?.message) root.append(node('p', job.message));
    const times = [];
    if (job?.observed_at && job.status !== 'running') times.push(`최근 결과: ${date(job.observed_at)}`);
    if (job?.last_success) times.push(`마지막 성공: ${date(job.last_success)}`);
    if (job?.next_slot) times.push(`다음 정시: ${date(job.next_slot)}`);
    if (times.length) root.append(node('p', times.join(' · ')));
    if (job?.status === 'running') {
      if (progress) {
        const stages = {preparing: '업로드 준비 중', scanning: '로컬 파일 목록 확인 중', remote: '원격 상태 묶음 확인 중', syncing: '파일 확인·전송 중',
          checking: '원본 변경·삭제 확인 중', cleanup: '삭제 반영 중', finishing: '결과 정리 중'};
        root.append(node('p', stages[progress.stage] || '동기화 중입니다.'));
        if (progress.stage === 'remote') {
          root.append(node('p', `원격 응답 확인 ${progress.remote_checked}/${progress.remote_total} 항목`));
        } else if (progress.total !== null && progress.total !== undefined) {
          root.append(node('p', `확인한 항목 ${progress.processed}/${progress.total} · 파일 전송 ${progress.transferred} · 미갱신 ${progress.excluded}`));
        }
        if (progress.active_items > 1) root.append(node('p', `동시 처리 ${progress.active_items}항목`));
        if (progress.current) root.append(node('p', `최근 처리 항목: ${progress.current}`, 'drive-path'));
        if (progress.uploading && progress.file_bytes > 0) {
          root.append(node('p', `최근 파일 수신 확인 ${progress.current_bytes.toLocaleString()} / ${progress.file_bytes.toLocaleString()} bytes`));
        }
        if (progress.last_activity_at) {
          const time = new Intl.DateTimeFormat('ko', {timeZone: state.timezone, timeStyle: 'medium'}).format(new Date(progress.last_activity_at));
          root.append(node('p', `최근 진행: ${time}`));
        }
      }
      return; // Prior run totals must not appear as the current run's progress.
    }
    if (!job?.report || !Object.keys(job.report).length) return;
    const value = job.report;
    root.append(node('p', `파일 전송 ${value.transferred || 0} · 구조·삭제 반영 ${value.changed || 0} · 미갱신 ${value.excluded || 0}`));
    if (value.destination) root.append(node('p', value.destination, 'drive-path'));
    if (value.errors?.length) {
      const details = node('details'), list = node('ul');
      details.open = Boolean(expanded);
      details.append(node('summary', '항목별 결과'));
      value.errors.forEach(error => list.append(node('li', `${error.path || '폴더'}: ${error.message}`)));
      details.append(list); root.append(details);
    }
  }
  function schedule(key, job, title = '내 업로드') {
    const group = node('div', undefined, 'drive-schedule'), label = node('label', undefined, 'drive-option');
    const checkbox = node('input'); checkbox.type = 'checkbox'; checkbox.checked = Boolean(job?.auto);
    checkbox.setAttribute('aria-label', title + ' 자동 실행');
    checkbox.addEventListener('change', () => save(key, {auto: checkbox.checked}));
    label.append(checkbox, node('span', '자동 실행')); group.append(label);
    const intervalLabel = node('label', undefined, 'drive-interval'), select = node('select');
    intervalLabel.append(node('span', '실행 주기'));
    select.setAttribute('aria-label', title + ' 실행 주기');
    labels.forEach((text, value) => { const option = node('option', text); option.value = value; select.append(option); });
    select.value = job?.interval || (key === 'upload' ? 360 : 1440);
    select.addEventListener('change', () => save(key, {interval: Number(select.value)}));
    intervalLabel.append(select); group.append(intervalLabel); return group;
  }
  function observations() {
    const connection = current(); if (!connection) return;
    const account = connection.account;
    const rootVerified = Boolean(connection.health.root?.last_success);
    $('[data-drive-account]').textContent = checking ? 'Google 계정과 공유 폴더를 확인하고 있습니다.' :
      connection.auth_pending ? '브라우저에서 Google 로그인을 마친 뒤 연결 확인을 눌러 주세요.' :
      account ? `연결 계정: ${account.emailAddress || account.displayName} · ${connection.health.auth?.status === 'error' ? '연결 확인 실패' : connection.health.root?.status === 'ok' ? '공유 폴더 확인 완료' : '공유 폴더 확인 필요'}` :
      connection.health.auth?.status === 'error' ? '계정 확인이 완료되지 않았습니다. 연결 진단에서 원인을 확인할 수 있습니다.' :
      '터미널에서 로그인했다면 연결 확인을 눌러 주세요. 다시 로그인할 필요는 없습니다.';
    $('[data-drive-provider]').textContent = state.gcloud_message || '';
    const authBusy = checking || !state.gcloud_ready || connection.auth_pending || Boolean(state.active);
    $('[data-drive-connect]').disabled = authBusy;
    $('[data-drive-connect]').textContent = checking ? '연결 확인 중…' : '연결 확인';
    $('[data-drive-login]').disabled = authBusy;
    $('[data-drive-account-input]').disabled = checking || connection.auth_pending || Boolean(state.active);
    const picker = $('[data-drive-connections] select');
    if (picker) picker.disabled = checking;
    $('[data-drive-add] button').disabled = checking;
    const options = $('[data-drive-auth-options]'), reason = connection.health.auth?.code || '';
    if (options.dataset.reason !== reason) {
      if (['unauthenticated', 'reauth', 'scope'].includes(reason)) options.open = true;
      options.dataset.reason = reason;
    }
    // Setup is progressive, but a later access error must not hide saved controls.
    $('[data-drive-sync-settings]').hidden = !(rootVerified || connection.publishers.length || Object.values(connection.jobs).some(job => job.selected));
    $('[data-drive-upload-options]').hidden = !connection.jobs.upload.selected;
    $('[data-drive-health]').replaceChildren();
    Object.entries({auth: '인증', api: 'API 통신', root: '루트 접근'}).forEach(([area, title]) => {
      const value = connection.health[area];
      $('[data-drive-health]').append(node('p', value ? `${title}: ${value.message} · 확인 ${date(value.observed_at)}` : `${title}: 아직 확인하지 않았습니다.`));
    });
    const uploadProgress = state.active?.connection_id === connection.id && state.active.job === 'upload' ? state.active.progress : null;
    report($('[data-drive-upload-status]'), connection.jobs.upload, uploadProgress);
    $('[data-drive-upload-run]').disabled = checking || connection.auth_pending || Boolean(state.active) || !connection.jobs.upload.selected;
    $('[data-drive-browse]').disabled = checking || connection.auth_pending || Boolean(state.active);
    panel.querySelectorAll('[data-drive-job-status]').forEach(root => report(root, connection.jobs[root.dataset.driveJobStatus]));
    panel.querySelectorAll('[data-drive-receive-options]').forEach(root => {root.hidden = !connection.jobs[root.dataset.driveReceiveOptions]?.selected;});
    panel.querySelectorAll('[data-drive-receive-run]').forEach(button => {
      button.hidden = !connection.jobs[button.dataset.driveReceiveRun]?.selected;
      button.disabled = checking || connection.auth_pending || Boolean(state.active) || !connection.jobs[button.dataset.driveReceiveRun]?.selected;
    });
  }
  function render() {
    if (!state.connections.some(item => item.id === connectionId)) connectionId = state.connections[0]?.id;
    const picker = $('[data-drive-connections]'); picker.replaceChildren();
    if (state.connections.length > 1) {
      const label = node('label', undefined, 'settings-field'), select = node('select'); label.append(node('span', '저장소'));
      state.connections.forEach(item => {const option = node('option', item.target); option.value = item.id; select.append(option);});
      select.value = connectionId; select.addEventListener('change', () => {connectionId = select.value; render();});
      label.append(select); picker.append(label);
    }
    $('[data-drive-add-details]').open = !state.connections.length;
    const connection = current(); $('[data-drive-content]').hidden = !connection;
    if (!connection) return;
    $('[data-drive-account-input]').value = connection.gcloud_account || connection.account?.emailAddress || '';
    $('[data-drive-target]').textContent = `대상: ${connection.target} · 루트: ${connection.url}`;
    const sources = $('[data-drive-sources]'); sources.replaceChildren();
    if (!state.sources.length) sources.append(node('p', '먼저 Local Context에서 파일·폴더를 등록해 주세요.'));
    state.sources.forEach(source => {
      const label = node('label', undefined, 'drive-option'), checkbox = node('input');
      checkbox.type = 'checkbox'; checkbox.value = source.id; checkbox.dataset.driveSource = '';
      checkbox.checked = connection.jobs.upload.sources.includes(source.id);
      checkbox.addEventListener('change', () => save('upload', {sources: Array.from(sources.querySelectorAll('input:checked'), input => Number(input.value))}));
      const text = node('span', source.label || source.path.split('/').pop());
      text.append(node('small', source.path, 'drive-path')); label.append(checkbox, text); sources.append(label);
    });
    $('[data-drive-upload-schedule]').replaceChildren(schedule('upload', connection.jobs.upload));
    const publishers = $('[data-drive-publishers]'); publishers.replaceChildren();
    const cached = new Map(connection.publishers.map(item => [item.id, item]));
    Object.keys(connection.jobs).filter(key => key.startsWith('receive:')).forEach(key => {
      const id = key.slice(8); if (!cached.has(id)) cached.set(id, {id, name: '이전에 선택한 폴더 · 목록에서 확인 필요'});
    });
    if (!cached.size) publishers.append(node('p', connection.health.root?.status === 'ok' ? '이 공유 폴더에는 받을 다른 폴더가 없습니다.' : '루트 폴더를 조회하면 받을 수 있는 폴더가 표시됩니다.'));
    cached.forEach(publisher => {
      const key = 'receive:' + publisher.id, job = connection.jobs[key], section = node('div', undefined, 'drive-publisher');
      section.setAttribute('role', 'group'); section.setAttribute('aria-label', publisher.name);
      const heading = node('div', undefined, 'settings-source-heading'), label = node('label', undefined, 'drive-option'), checkbox = node('input');
      checkbox.type = 'checkbox'; checkbox.checked = Boolean(job?.selected);
      checkbox.addEventListener('change', () => save(key, {selected: checkbox.checked}));
      label.append(checkbox, node('span', publisher.name)); heading.append(label);
      const run = node('button', '지금 받기', 'secondary-button'); run.type = 'button'; run.dataset.driveReceiveRun = key;
      run.setAttribute('aria-label', publisher.name + ' 지금 받기');
      run.addEventListener('click', () => perform(async () => {await saving; await api(path('/jobs/' + encodeURIComponent(key) + '/run'), 'POST'); await load(false);}, run));
      heading.append(run); section.append(heading);
      const options = node('div'); options.dataset.driveReceiveOptions = key;
      const status = node('div'); status.dataset.driveJobStatus = key;
      options.append(schedule(key, job, publisher.name), status); section.append(options); publishers.append(section);
    });
    observations();
  }
  function load(full = true) {
    // An action's refresh must follow an in-flight poll rather than be dropped.
    loading = loading.catch(() => {}).then(async () => {
      state = await api(); if (full) render(); else observations();
      clearTimeout(timer);
      // Poll local cached state only; this endpoint never makes a Google call.
      if (!panel.hidden && panel.closest('dialog')?.open) {
        timer = setTimeout(() => perform(() => load(false)), state.active || state.connections.some(c => c.auth_pending) ? 1500 : 5000);
      }
    });
    return loading;
  }
  $('[data-drive-add]').addEventListener('submit', event => {
    event.preventDefault(); const form = event.currentTarget;
    perform(async () => {
      const connection = await api('/connections', 'POST', {url: form.elements.root_url.value, target: form.elements.target.value});
      connectionId = connection.id; await load(); form.reset();
      message('저장소를 저장했습니다. 기존 로그인과 공유 폴더를 확인합니다.');
      await verifyConnection();
    }, event.submitter);
  });
  async function verifyConnection() {
    await saving;
    const id = '/' + encodeURIComponent(connectionId);
    const account = $('[data-drive-account-input]').value.trim();
    checking = true; observations();
    try {
      await api(id + '/connect', 'POST', {account, login: false});
      await api(id + '/browse', 'POST');
      await load();
      message('연결을 확인했습니다. 올리거나 받을 자료를 선택해 주세요.');
    } finally {
      checking = false;
      await load(false);
    }
  }
  function loginGoogle(button) {
    perform(async () => {
      await saving;
      await api(path('/connect'), 'POST', {account: $('[data-drive-account-input]').value.trim(), login: true});
      message('브라우저에서 Google 로그인을 마친 뒤 연결 확인을 눌러 주세요.');
      await load(false);
    }, button);
  }
  $('[data-drive-connect]').addEventListener('click', event => perform(verifyConnection, event.currentTarget));
  $('[data-drive-login]').addEventListener('click', event => loginGoogle(event.currentTarget));
  $('[data-drive-browse]').addEventListener('click', event => perform(async () => {await saving; await api(path('/browse'), 'POST'); await load(); message('루트 폴더를 조회했습니다.');}, event.currentTarget));
  $('[data-drive-upload-run]').addEventListener('click', event => perform(async () => {await saving; await api(path('/jobs/upload/run'), 'POST'); await load(false);}, event.currentTarget));
  document.addEventListener('localbrain:settings-tab', event => {clearTimeout(timer); if (event.detail === 'google-drive') perform(() => load());});
  panel.closest('dialog')?.addEventListener('close', () => clearTimeout(timer));
})();
