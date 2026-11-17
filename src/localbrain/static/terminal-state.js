// Display only explicit runtime/shell metadata. Visibility and input ownership are separate axes.
export function latestTerminal(current, incoming) {
  return current?.id === incoming.id && current.seq > incoming.seq ? current : incoming;
}

// Program activity is title presentation, independent of shell command state.
export function programTitle(name) {
  const prefix = /^([\u2801-\u28ff])\s+/u.exec(name);
  return prefix ? {indicator: prefix[1], title: name.slice(prefix[0].length)} : {indicator: '', title: name};
}

export function terminalIndicator(terms, {current = false, hidden = false} = {}) {
  if (hidden) return {key: 'hidden', icon: 'view_diamond', label: '백그라운드'};
  if (current) return {key: 'current', icon: 'check', label: '현재 선택'};
  if (terms.some(term => term.state === 'running' && term.activity?.state === 'running')) {
    return {key: 'running', icon: 'view_dot', label: '명령·프로그램 실행 중'};
  }
  if (terms.length && terms.every(term => term.state === 'running' && term.activity?.state === 'prompt')) {
    return {key: 'idle', icon: 'view_ring', label: '프롬프트 대기'};
  }
  return {key: 'neutral', icon: null, label: '열린 터미널'};
}

export function terminalStatus(term, seen = 0) {
  const status = (key, icon, label, priority) => ({key, icon, label, priority});
  if (term.error) return status('error', 'error', '종료 확인 필요', 0);
  if (term.closing) return status('closing', 'progress_activity', '종료 중', 1);
  if (term.inputError) return status('error', 'error', '입력 연결 오류', 0);
  if (term.state === 'exited') return Number.isInteger(term.exitCode) && term.exitCode !== 0
    ? status('failed', 'error', '셸 오류 종료 · ' + term.exitCode, 0)
    : status('exited', 'stop_circle', '셸 종료' + (!Number.isInteger(term.exitCode) ? ' · 종료 코드 미확인' : ' · ' + term.exitCode), 6);
  const activity = term.activity;
  if (activity?.state === 'running') return status('working', 'progress_activity', '명령 실행 중', 3);
  if (activity?.completion > seen) {
    if (activity.exitCode === null) return status('done', 'circle', '새 명령 종료 · 결과 미확인', 2);
    return activity.exitCode === 0 ? status('done', 'check_circle', '새 명령 완료', 2)
      : status('failed', 'error', '새 명령 실패 · ' + activity.exitCode, 0);
  }
  if (activity?.state === 'prompt') return status('idle', 'circle', '프롬프트 대기', 5);
  if (activity?.state === 'finished') {
    return activity.exitCode === null ? status('unknown', 'circle', '명령 종료 · 결과 미확인', 5)
      : activity.exitCode === 0 ? status('finished', 'check', '명령 완료', 5)
        : status('failed', 'error', '명령 실패 · ' + activity.exitCode, 4);
  }
  return status('unknown', 'circle', '셸 실행 중 · 명령 상태 미확인', 5);
}

export function cleanShellExit(term) {
  // Clean refers to confirmed process cleanup, independently of a program's exit code.
  return term.state === 'exited' && !term.closing && !term.error && !term.inputError;
}

export function orderedTabs(tabs, order = []) {
  const rank = new Map(order.map((id, index) => [id, index]));
  return [...tabs].sort((a, b) => (rank.get(a.id) ?? order.length) - (rank.get(b.id) ?? order.length));
}

export function workspaceGroups(workspaces, tabs) {
  return workspaces.items.map(item => ({...item, tabs: tabs.filter(tab => item.tabs.includes(tab.id))}));
}
