'use strict';

function cancelComposition(terminal, pending = false) {
  const core = terminal._core, helper = core?._compositionHelper;
  if (helper) {
    const composing = pending || helper.isComposing || helper._isSendingComposition || terminal.textarea.value;
    // Old deferred callbacks retain their helper. Retire it with composition
    // sends disabled, rather than letting a late callback use regained authority.
    helper._isComposing = true; helper._isSendingComposition = false;
    if (composing) terminal.blur();
    helper._isComposing = true; helper._isSendingComposition = false;
    helper._compositionView.classList.remove('active');
    core._compositionHelper = core._instantiationService.createInstance(
      helper.constructor, terminal.textarea, helper._compositionView);
  }
  if (terminal.textarea) terminal.textarea.value = '';
}

// WebKit's macOS Korean IME edits a syllable in place without composition
// events. Keep that unsent range until a boundary; xterm owns every other input
// path, including browsers/IMEs which provide real composition events.
function attachKoreanInput(terminal, host) {
  const view = host.ownerDocument.defaultView;
  const ua = view.navigator.userAgent;
  if (!/AppleWebKit/.test(ua) || /Chrome|Chromium|Edg|OPR/.test(ua)) {
    return {cancel() { cancelComposition(terminal); }, dispose() { cancelComposition(terminal); }};
  }
  const textarea = terminal.textarea;
  const screen = terminal.element.querySelector('.xterm-screen');
  const preview = host.ownerDocument.createElement('span');
  preview.className = 'composition-view';
  preview.setAttribute('aria-hidden', 'true');
  screen.append(preview);
  let held = null;
  let prefix = '';
  let replacementInput = false;
  let nativeComposition = false;
  let pendingBackspace = false;
  let skipBackspace = false;
  let endingTimer;
  const listeners = [];
  const on = (type, listener) => {
    host.addEventListener(type, listener, true);
    listeners.push(() => host.removeEventListener(type, listener, true));
  };
  function paint() {
    preview.textContent = held || '';
    preview.classList.toggle('active', Boolean(held));
    const cellWidth = screen.clientWidth / terminal.cols;
    const cellHeight = screen.clientHeight / terminal.rows;
    Object.assign(preview.style, {
      left: Math.min(terminal.buffer.active.cursorX, terminal.cols - 1) * cellWidth + 'px',
      top: terminal.buffer.active.cursorY * cellHeight + 'px',
      height: cellHeight + 'px', lineHeight: cellHeight + 'px',
      fontFamily: terminal.options.fontFamily, fontSize: terminal.options.fontSize + 'px',
      background: terminal.options.theme?.background || '',
      color: terminal.options.theme?.foreground || ''
    });
  }
  function finish() {
    const text = held;
    held = null;
    prefix = '';
    pendingBackspace = skipBackspace = false;
    replacementInput = false;
    paint();
    if (text && !terminal.options.disableStdin) terminal.input(text, true);
  }
  function cancel() {
    const pending = held !== null;
    clearTimeout(endingTimer);
    nativeComposition = false;
    held = null;
    prefix = '';
    pendingBackspace = skipBackspace = false;
    replacementInput = false;
    cancelComposition(terminal, pending);
    paint();
  }
  on('input', event => {
    if (event.target !== textarea || nativeComposition || event.isComposing) return;
    if (terminal.options.disableStdin) { cancel(); return; }
    const startsHangul = event.inputType === 'insertText'
      && /^[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\ud7b0-\ud7ff]$/.test(event.data || '');
    if (startsHangul) {
      event.stopImmediatePropagation();
      finish();
      replacementInput = true;
      held = event.data;
      prefix = textarea.value.slice(0, -held.length);
      paint();
    } else if (held !== null && ['insertReplacementText', 'deleteContentBackward'].includes(event.inputType)) {
      event.stopImmediatePropagation();
      replacementInput = true;
      // A changed prefix is outside the unsent range. Never replay old textarea
      // contents or manufacture shell edits from an ambiguous native mutation.
      if (!textarea.value.startsWith(prefix)) { cancel(); return; }
      held = textarea.value.slice(prefix.length);
      if (!held) {
        held = null;
        prefix = '';
        // Some native edits precede their keydown. Suppress that same key,
        // while letting the next physical Backspace reach committed shell text.
        skipBackspace = !pendingBackspace;
        pendingBackspace = false;
      }
      paint();
    } else if (held !== null && event.inputType === 'insertText') {
      finish();
      // Ordinary ASCII stays on xterm's keydown/keypress path. In particular,
      // WebKit's textarea NBSP is not a shell space and must not be forwarded.
      event.stopImmediatePropagation();
    }
  });
  on('keydown', event => {
    if (event.target !== textarea || nativeComposition) return;
    if (event.keyCode === 229 && replacementInput && !event.ctrlKey && !event.metaKey && !event.altKey) {
      replacementInput = false;
      event.stopImmediatePropagation();
      return;
    }
    if (['Shift', 'Control', 'Alt', 'Meta', 'CapsLock'].includes(event.key)) return;
    // The later paste event owns confirmation and commit, including rejection.
    // Ctrl+V remains the shell's literal-next-character chord on macOS.
    if (event.metaKey && !event.ctrlKey && !event.altKey
      && (event.code === 'KeyV' || event.key.toLowerCase() === 'v')) return;
    if (event.key === 'Backspace' && skipBackspace) {
      skipBackspace = false;
      event.stopImmediatePropagation();
      return;
    }
    if (held !== null && event.key === 'Backspace') {
      // Let the input method/browser edit the held range. It may remove only
      // one jamo; sending DEL now would erase already committed shell input.
      pendingBackspace = true;
      event.stopImmediatePropagation();
      return;
    }
    finish();
  });
  on('keyup', event => {
    if (event.target === textarea && [8, 229].includes(event.keyCode)) {
      pendingBackspace = skipBackspace = false;
      replacementInput = false;
    }
  });
  on('paste', event => { if (event.target === textarea) finish(); });
  on('compositionstart', event => {
    if (event.target !== textarea) return;
    clearTimeout(endingTimer);
    finish();
    nativeComposition = true;
  });
  on('compositionend', event => {
    if (event.target !== textarea) return;
    // The native ending chain can include a final input before xterm's
    // asynchronous composition send; it still belongs to that native path.
    endingTimer = setTimeout(() => { nativeComposition = false; }, 0);
  });
  on('focusout', event => { if (event.target === textarea) finish(); });
  const render = terminal.onRender(paint);
  return {cancel, dispose() {
    cancel();
    clearTimeout(endingTimer);
    for (const remove of listeners) remove();
    render.dispose();
    preview.remove();
  }};
}

module.exports = {attachKoreanInput};
