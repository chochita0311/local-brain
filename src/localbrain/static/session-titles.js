/* Inline titles remain independent of card navigation and source synchronization. */
(() => {
  const editorFor = (node) => node?.closest?.("[data-session-title-editor]");
  const field = (editor) => editor.querySelector(".session-title-input");
  const clickedCaret = (summary, event) => {
    if (event.detail === 0) return null; // Keyboard activation has no text point.
    const label = summary.querySelector("[data-session-title-label]");
    const position = document.caretPositionFromPoint?.(event.clientX, event.clientY);
    const range = position ? null : document.caretRangeFromPoint?.(event.clientX, event.clientY);
    const node = position?.offsetNode ?? range?.startContainer;
    const offset = position?.offset ?? range?.startOffset;
    if (!node || !label.contains(node)) {
      return event.clientX <= label.getBoundingClientRect().left ? 0 : label.textContent.length;
    }
    const before = document.createRange();
    before.selectNodeContents(label);
    before.setEnd(node, offset);
    return before.toString().length;
  };
  const close = (editor) => {
    editor.open = false;
    editor.style.removeProperty("width");
    editor.classList.remove("has-error");
    editor.querySelector(".session-title-feedback").hidden = true;
    field(editor).removeAttribute("aria-invalid");
  };
  const present = (saved) => {
    document.querySelectorAll(`[data-session-title-label="${saved.id}"]`).forEach((label) => {
      label.textContent = saved.effective_title;
      label.title = saved.effective_title;
    });
    document.querySelectorAll(`[data-session-title-link="${saved.id}"]`).forEach((link) => {
      link.setAttribute("aria-label", `세션 열기: ${saved.effective_title}`);
    });
    document.querySelectorAll(`[data-session-title-editor="${saved.id}"]`).forEach((editor) => {
      const input = field(editor);
      input.value = input.dataset.savedTitle = saved.effective_title;
      input.placeholder = saved.title;
      editor.querySelector("summary").setAttribute("aria-label", `제목 편집: ${saved.effective_title}`);
      if (editor.closest(".session-heading")) document.title = `${saved.effective_title} · LocalBrain`;
    });
  };
  const save = (editor) => {
    if (editor.titleSave) return editor.titleSave;
    const input = field(editor);
    if (input.value === input.dataset.savedTitle) {
      close(editor);
      return Promise.resolve(true);
    }
    const form = editor.querySelector("form");
    const body = new URLSearchParams(new FormData(form));
    const feedback = editor.querySelector(".session-title-feedback");
    feedback.hidden = true;
    editor.classList.remove("has-error");
    input.disabled = true;
    editor.setAttribute("aria-busy", "true");
    editor.titleSave = (async () => {
      let failureMessage = "제목을 저장하지 못했습니다. 다시 저장해 주세요.";
      try {
        const response = await fetch(form.action, {
          method: "POST", body, headers: {Accept: "application/json"}, keepalive: true,
        });
        if (!response.ok) {
          if (response.status === 400) failureMessage = "한 줄로 500자 이내의 제목을 입력한 뒤 다시 저장해 주세요.";
          throw new Error("title-save-failed");
        }
        const saved = await response.json();
        if (String(saved.id) !== editor.dataset.sessionTitleEditor || typeof saved.effective_title !== "string") {
          throw new Error("invalid-title-response");
        }
        present(saved);
        close(editor);
        return true;
      } catch (_error) {
        // Keep the draft and expose retry; an unconfirmed write is never shown as saved.
        editor.classList.add("has-error");
        feedback.textContent = failureMessage;
        feedback.hidden = false;
        input.setAttribute("aria-invalid", "true");
        return false;
      } finally {
        input.disabled = false;
        editor.removeAttribute("aria-busy");
        editor.titleSave = null;
      }
    })();
    return editor.titleSave;
  };
  document.querySelectorAll("[data-session-title-editor]").forEach((editor) => editor.classList.add("is-enhanced"));
  document.addEventListener("click", (event) => {
    const editor = editorFor(event.target);
    if (editor && event.target.closest("summary")) {
      event.preventDefault();
      if (editor.titleSave) return;
      // Measure before hiding the label; both offsets use UTF-16 text positions.
      const caret = clickedCaret(editor.querySelector("summary"), event);
      editor.classList.add("is-enhanced");
      editor.style.width = "100%";
      editor.open = true;
      const input = field(editor);
      input.focus({preventScroll: true});
      const offset = caret ?? input.value.length;
      input.setSelectionRange(offset, offset);
    }
    const link = event.target.closest("[data-session-title-link]");
    const pending = link?.closest(".session-row")?.querySelector("[data-session-title-editor]")?.titleSave;
    if (pending && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) {
      event.preventDefault();
      pending.then((saved) => { if (saved) window.location.assign(link.href); });
    }
  });
  document.addEventListener("submit", (event) => {
    const editor = editorFor(event.target);
    if (!editor) return;
    event.preventDefault();
    save(editor);
  });
  document.addEventListener("compositionstart", (event) => {
    if (event.target.matches(".session-title-input")) event.target.dataset.composing = "true";
  });
  document.addEventListener("compositionend", (event) => {
    if (event.target.matches(".session-title-input")) delete event.target.dataset.composing;
  });
  document.addEventListener("keydown", (event) => {
    if (!event.target.matches(".session-title-input")) return;
    if (event.isComposing || event.keyCode === 229 || event.target.dataset.composing) return;
    const editor = editorFor(event.target);
    if (event.key === "Enter") {
      event.preventDefault();
      event.stopPropagation();
      save(editor).then((saved) => { if (saved && editor.isConnected) editor.querySelector("summary").focus({preventScroll: true}); });
    } else if (event.key === "Escape" && !editor.titleSave) {
      event.preventDefault();
      event.stopPropagation();
      close(editor);
      field(editor).value = field(editor).dataset.savedTitle;
      editor.querySelector("summary").focus({preventScroll: true});
    }
  });
  document.addEventListener("focusout", (event) => {
    if (!event.target.matches(".session-title-input")) return;
    const editor = editorFor(event.target);
    if (editor.open && !editor.contains(event.relatedTarget) && !event.target.dataset.composing) save(editor);
  });
})();
