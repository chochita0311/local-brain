(() => {
  const form = document.querySelector('[data-auto-work-refresh]');
  if (!form) return;
  const button = form.querySelector('[data-auto-work-refresh-button]');
  const progress = form.querySelector('[data-auto-work-progress]');
  const revealNavigation = () => {
    const nav = document.querySelector('.lnb-nav');
    const current = nav?.querySelector('[aria-current="page"]');
    if (current && nav.scrollWidth > nav.clientWidth) {
      const outer = nav.getBoundingClientRect();
      const item = current.getBoundingClientRect();
      if (item.left < outer.left || item.right > outer.right) {
        nav.scrollLeft += item.left - outer.left;
      }
    }
  };
  revealNavigation();
  window.addEventListener('resize', revealNavigation);
  form.addEventListener('submit', (event) => {
    if (button.disabled) {
      event.preventDefault();
      return;
    }
    button.disabled = true;
    button.textContent = '분석 중…';
    progress.hidden = false;
    form.setAttribute('aria-busy', 'true');
  });
  window.addEventListener('pageshow', () => {
    button.disabled = false;
    button.textContent = '결과 갱신';
    progress.hidden = true;
    form.removeAttribute('aria-busy');
  });
})();
