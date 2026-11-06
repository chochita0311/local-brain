// Injected by the macOS host on every navigation, before the page can paint.
(() => {
  window.__LOCALBRAIN_NATIVE_TITLEBAR__ = true;
  const apply = () => {
    if (!document.documentElement) return false;
    document.documentElement.classList.add('native-window-toolbar');
    return true;
  };
  if (apply()) return;
  const observer = new MutationObserver(() => {if (apply()) observer.disconnect();});
  observer.observe(document, {childList: true});
})();
