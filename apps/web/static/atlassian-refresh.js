(() => {
  const page = document.querySelector("[data-atlassian-refresh]");
  if (!page) return;

  const controls = [...page.querySelectorAll("[data-refresh-item]")];
  const callOutput = page.querySelector("[data-selected-calls]");
  const countOutput = page.querySelector("[data-selected-count]");
  const submit = page.querySelector("[data-refresh-submit]");
  const message = page.querySelector("[data-refresh-budget-message]");
  const budget = Number(page.dataset.callBudget || 20);
  const executorReady = page.dataset.executorReady === "true";

  const refreshSelection = () => {
    const selected = controls.filter((control) => control.checked && !control.disabled);
    const calls = selected.reduce(
      (total, control) => total + Number(control.dataset.requestCount || 0),
      0,
    );
    if (callOutput) callOutput.textContent = String(calls);
    if (countOutput) countOutput.textContent = String(selected.length);
    const invalid = calls === 0 || calls > budget;
    if (submit) submit.disabled = !executorReady || invalid;
    if (message) {
      message.textContent =
        calls > budget
          ? `${budget} reads를 넘었습니다. 일부 대상을 제외하세요.`
          : calls === 0
            ? "최소 한 대상을 선택하세요."
            : `${selected.length}개 선택 · ${calls} remote reads`;
    }
  };
  controls.forEach((control) => control.addEventListener("change", refreshSelection));
  refreshSelection();

  const runPanel = page.querySelector("[data-refresh-run]");
  if (!runPanel) return;
  if (!["queued", "running", "cancelling"].includes(runPanel.dataset.refreshStatus)) {
    return;
  }
  const runId = runPanel.dataset.refreshRun;
  const poll = window.setInterval(async () => {
    try {
      const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;
      const payload = await response.json();
      if (!["queued", "running", "cancelling"].includes(payload.run.status)) {
        window.clearInterval(poll);
        window.location.reload();
      }
    } catch (_error) {
      window.clearInterval(poll);
    }
  }, 2000);
})();
