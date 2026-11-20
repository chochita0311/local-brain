document.getElementById('retry').addEventListener('click', async () => {
  document.getElementById('retry').hidden = true;
  document.getElementById('status').textContent = '로컬 자료를 준비하고 있습니다.';
  try { await window.__TAURI__.core.invoke('retry_backend'); }
  catch { document.getElementById('status').textContent = '시작하지 못했습니다. 앱을 종료한 뒤 다시 열어 주세요.'; document.getElementById('retry').hidden = false; }
});
