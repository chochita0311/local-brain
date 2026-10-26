(() => {
  const region = document.querySelector("[data-natural-search-status]");
  if (!region) return;
  let timer;
  let controller;
  let stopped = false;
  let sawPreparation = ["preparing", "partial"].includes(region.dataset.state);

  async function refresh() {
    if (stopped || document.hidden) return;
    controller = new AbortController();
    try {
      const response = await fetch("/api/natural-search/status", {cache: "no-store", signal: controller.signal});
      if (!response.ok) throw new Error("status-unavailable");
      const status = await response.json();
      region.dataset.state = status.state;
      if (["preparing", "partial"].includes(status.state)) sawPreparation = true;
      for (const [selector, value] of [["[data-search-status-title]", status.title], ["[data-search-status-copy]", status.description]]) {
        const element = region.querySelector(selector);
        if (element.textContent !== value) element.textContent = value;
      }
      const count = status.eligible_parents
        ? `원문 ${status.parents} / ${status.eligible_parents}개 준비${status.state === "preparing" ? ` · 본문 구간 ${status.fragments || 0}개 처리` : ""}` : "";
      const counter = region.querySelector("[data-search-status-count]");
      if (counter.textContent !== count) counter.textContent = count;
      region.querySelector("[data-search-coverage]").hidden = ["disabled", "model-missing"].includes(status.state);
      const coverage = `검색 허용 범위 밖 세션 ${status.excluded_sessions || 0}개 · 본문 없는 원문 ${(status.empty_sessions || 0) + (status.empty_documents || 0)}개 · 앱 저장 영역의 문서 ${status.excluded_runtime_documents || 0}개 제외. 읽을 수 없는 Local Context 등록 경로 ${status.unreadable_context_roots || 0}개.`;
      const coverageCopy = region.querySelector("[data-search-coverage-copy]");
      if (coverageCopy.textContent !== coverage) coverageCopy.textContent = coverage;
      region.querySelector("[data-search-install]").hidden = !["disabled", "model-missing"].includes(status.state);
      region.querySelector("[data-search-prepare]").hidden = !["disabled", "failed", "partial", "model-missing"].includes(status.state);
      region.querySelector("[data-search-cancel]").hidden = !status.can_cancel;
      if (status.state === "ready" && sawPreparation) region.querySelector("[data-search-repeat]").hidden = false;
    } catch (error) {
      if (error.name !== "AbortError") {
        region.querySelector("[data-search-status-copy]").textContent = "진행 상태를 확인하지 못했습니다. 입력한 검색어는 유지됩니다. 연결을 확인하거나 페이지를 새로고침해 주세요.";
      }
    } finally {
      controller = null;
      if (!stopped && !document.hidden) timer = window.setTimeout(refresh, 3000);
    }
  }
  function pause() { window.clearTimeout(timer); controller?.abort(); }
  window.addEventListener("pagehide", () => { stopped = true; pause(); });
  window.addEventListener("pageshow", () => { if (stopped) { stopped = false; refresh(); } });
  document.addEventListener("visibilitychange", () => { pause(); if (!document.hidden) refresh(); });
  timer = window.setTimeout(refresh, 3000);
})();
