(() => {
  const root = document.querySelector("[data-learning-draft]");
  if (!root || !root.dataset.learningDraft) return;
  const key = "localbrain:learning-draft:v1:" + root.dataset.learningDraft;
  const form = root.querySelector(".learning-answer-form");
  const notice = document.getElementById("learning-draft-notice");
  const show = text => { if (notice) notice.textContent = text; };
  const scene = root.querySelector(".learning-scene");
  // Only a reference that actually fits below the shared header can stay sticky.
  const fitScene = () => {
    if (!scene) return;
    const header = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--shell-header-height")) || 0;
    const gap = parseFloat(getComputedStyle(scene).paddingTop) || 0;
    scene.classList.toggle("learning-scene-sticky", scene.offsetHeight + header + gap * 2 < innerHeight);
  };
  if (scene) {
    new ResizeObserver(fitScene).observe(scene);
    window.addEventListener("resize", fitScene, { passive: true });
    fitScene();
  }
  if (root.dataset.learningSaved === "1") {
    try { sessionStorage.removeItem(key); } catch (_) { /* The saved server record already exists. */ }
    return;
  }
  if (!form) return;
  const answer = form.elements.answer;
  const hint = form.querySelector("[data-learning-help-choice]");
  let helpUsed = hint.checked;
  let storageAvailable = true;
  const lockHint = () => {
    if (!helpUsed) return;
    hint.checked = true;
    hint.disabled = true;
    let value = form.querySelector("[data-learning-hint-value]");
    if (!value) {
      value = document.createElement("input");
      value.type = "hidden";
      value.name = "hint_used";
      value.dataset.learningHintValue = "1";
      form.append(value);
    }
    value.value = "1";
  };
  try {
    const saved = JSON.parse(sessionStorage.getItem(key) || "null");
    if (root.dataset.learningError !== "1" && saved && typeof saved.answer === "string" && saved.answer.length <= 8000) {
      answer.value = saved.answer;
      for (const choice of form.querySelectorAll('[name="confidence"]')) choice.checked = choice.value === saved.confidence;
      helpUsed = helpUsed || saved.hint_used === true;
      show("이 탭에서 작성하던 초안을 복원했습니다. 답변 저장 전입니다.");
    }
  } catch (_) {
    storageAvailable = false;
    show("이 탭의 초안 복원을 사용할 수 없습니다. 작성 후 답변 저장을 눌러 주세요.");
  }
  lockHint();
  const save = () => {
    if (!storageAvailable) return;
    const selected = form.querySelector('[name="confidence"]:checked');
    try {
      sessionStorage.setItem(key, JSON.stringify({
        answer: answer.value, confidence: selected ? selected.value : "", hint_used: helpUsed
      }));
      show("작성 중인 내용은 이 탭에 임시 보관됩니다. 학습 기록은 답변 저장 후 남습니다.");
    } catch (_) {
      storageAvailable = false;
      show("초안을 임시 보관하지 못했습니다. 입력은 남아 있으니 답변 저장을 눌러 주세요.");
    }
  };
  root.querySelectorAll("[data-learning-help]").forEach(details => {
    details.addEventListener("toggle", () => {
      if (!details.open) return;
      helpUsed = true;
      lockHint();
      save();
    });
  });
  hint.addEventListener("change", () => { helpUsed = helpUsed || hint.checked; lockHint(); save(); });
  form.addEventListener("input", save);
  form.addEventListener("change", save);
  form.addEventListener("submit", save);
})();

