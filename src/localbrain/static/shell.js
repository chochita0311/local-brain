// Shared toolbar presentation. Native window chrome and web pages use one DOM.
(() => {
  const root = document.documentElement;
  const storageKey = 'localbrain:sidebar:1';
  if (window.__LOCALBRAIN_NATIVE_TITLEBAR__ === true) root.classList.add('native-window-toolbar');
  const restoreSidebar = () => {
    try {root.classList.toggle('sidebar-collapsed', sessionStorage.getItem(storageKey) === 'collapsed');}
    catch (_) { /* Sidebar controls remain usable without browser storage. */ }
  };
  restoreSidebar();

  function bind() {
    const sidebar = document.getElementById('app-sidebar');
    const toggle = document.querySelector('[data-sidebar-toggle]');
    if (!sidebar || !toggle) return;
    const mac = /Mac|iPhone|iPad/.test(navigator.platform);
    const searchHint = mac ? '⌘K' : 'Ctrl+K';
    const shortcut = (control, keys, accessible) => {
      if (!control) return;
      control.setAttribute('aria-keyshortcuts', accessible);
      control.dataset.shortcutKeys = JSON.stringify(keys);
    };
    shortcut(document.querySelector('[data-app-back]'), mac ? ['⌘', '['] : ['Alt', '←'], mac ? 'Meta+[' : 'Alt+ArrowLeft');
    shortcut(document.querySelector('[data-app-forward]'), mac ? ['⌘', ']'] : ['Alt', '→'], mac ? 'Meta+]' : 'Alt+ArrowRight');
    toggle.setAttribute('aria-keyshortcuts', mac ? 'Meta+Shift+S' : 'Control+Shift+S');
    const input = document.getElementById('global-query');
    const search = document.querySelector('.search-link');
    const badge = document.querySelector('[data-search-shortcut]');
    if (badge) {badge.textContent = searchHint; badge.hidden = false;}
    if (input) {
      input.setAttribute('aria-keyshortcuts', mac ? 'Meta+K' : 'Control+K');
    }
    const settings = document.querySelector('.settings-gear');
    if (settings) settings.dataset.shortcutKeys = JSON.stringify(mac ? ['⌘', ','] : ['Ctrl', ',']);
    if (search) {
      if (!input) search.setAttribute('aria-keyshortcuts', mac ? 'Meta+K' : 'Control+K');
    }

    const updateSidebar = () => {
      const expanded = !root.classList.contains('sidebar-collapsed');
      toggle.setAttribute('aria-expanded', String(expanded));
      toggle.setAttribute('aria-label', expanded ? '사이드바 접기' : '사이드바 펼치기');
      toggle.dataset.shellTooltip = toggle.getAttribute('aria-label');
      toggle.dataset.shortcutKeys = JSON.stringify(mac ? ['⌘', '⇧', 'S'] : ['Ctrl', 'Shift', 'S']);
    };
    const blocked = () => document.querySelector('.workspace-header')?.closest('[inert]')
      || document.querySelector('dialog[open], [aria-modal="true"]') !== null;
    toggle.disabled = false;
    updateSidebar();
    window.addEventListener('pageshow', event => {
      if (!event.persisted) return;
      restoreSidebar();
      updateSidebar();
      window.dispatchEvent(new Event('resize'));
    });
    toggle.addEventListener('click', () => {
      if (blocked()) return;
      const collapsed = root.classList.toggle('sidebar-collapsed');
      try {sessionStorage.setItem(storageKey, collapsed ? 'collapsed' : 'expanded');} catch (_) {}
      updateSidebar();
      window.dispatchEvent(new Event('resize'));
    });

    document.addEventListener('keydown', event => {
      if (event.defaultPrevented || event.isComposing || event.keyCode === 229) return;
      const key = event.key.toLowerCase();
      const modifier = mac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey;
      let command;
      if (modifier && !event.altKey) {
        if (!event.shiftKey && key === 'k') command = 'search';
        if (event.shiftKey && key === 's') command = 'sidebar';
        if (mac && !event.shiftKey && key === '[') command = 'back';
        if (mac && !event.shiftKey && key === ']') command = 'forward';
      }
      if (!mac && event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
        if (key === 'arrowleft') command = 'back';
        if (key === 'arrowright') command = 'forward';
      }
      if (!command) return;
      event.preventDefault();
      if (blocked()) return;
      // Window commands take precedence over a focused view's plain arrow keys.
      event.stopPropagation();
      if (command === 'sidebar') toggle.click();
      else if (command === 'search') {
        if (input) {input.focus(); input.select();}
        else search?.click();
      } else document.querySelector(command === 'back' ? '[data-app-back]' : '[data-app-forward]')?.click();
    }, true);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind, {once: true});
  else bind();
})();
