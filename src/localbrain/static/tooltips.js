// One control-anchored help surface for the shared shell, in both hosts.
(() => {
  const root = document.documentElement;
  const tooltip = document.createElement('div');
  tooltip.id = 'shell-tooltip';
  tooltip.className = 'shell-tooltip';
  tooltip.setAttribute('role', 'tooltip');
  tooltip.hidden = true;
  document.body.append(tooltip);
  // WKWebView can execute this before its stylesheet is ready. Read timing
  // when it is used, and measure resolved pixels only when showing a hint.
  const timing = name => parseFloat(getComputedStyle(root).getPropertyValue(name)) || 0;
  let active, hovered, focused, showTimer, hideTimer;
  const eligible = anchor => anchor?.isConnected
    && (!anchor.matches(':disabled, [aria-disabled="true"]') || anchor.hasAttribute('data-tooltip-when-disabled'))
    && (!anchor.hasAttribute('data-tooltip-compact') || root.classList.contains('sidebar-collapsed'))
    && !anchor.closest('[inert]')
    && !document.querySelector('dialog[open], [aria-modal="true"]');
  const describe = (anchor, add) => {
    const ids = new Set((anchor.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean));
    add ? ids.add(tooltip.id) : ids.delete(tooltip.id);
    if (ids.size) anchor.setAttribute('aria-describedby', [...ids].join(' '));
    else anchor.removeAttribute('aria-describedby');
  };
  function hide() {
    clearTimeout(showTimer); clearTimeout(hideTimer);
    if (active) describe(active, false);
    active = null;
    tooltip.hidden = true;
    tooltip.style.visibility = 'hidden';
    observer.disconnect();
  }
  function render() {
    tooltip.style.visibility = 'hidden';
    const style = getComputedStyle(tooltip);
    if (style.position !== 'fixed') return false;
    const gap = parseFloat(style.paddingTop);
    const width = root.clientWidth, height = root.clientHeight;
    if (!Number.isFinite(gap) || width <= gap * 2 || height <= gap * 2) return false;
    const label = document.createElement('span');
    label.className = 'shell-tooltip-label';
    label.textContent = active.dataset.shellTooltip;
    tooltip.replaceChildren(label);
    if (active.dataset.shortcutKeys) {
      const keys = document.createElement('span');
      keys.className = 'shell-tooltip-keys';
      for (const key of JSON.parse(active.dataset.shortcutKeys)) {
        const cap = document.createElement('kbd');
        cap.textContent = key;
        keys.append(cap);
      }
      tooltip.append(keys);
    }
    // Measure invisibly, with the layout viewport rather than the scrollbar-
    // inclusive innerWidth. Lock the measured width before moving to an edge.
    tooltip.style.maxWidth = `min(var(--tooltip-max-width), ${width - gap * 2}px)`;
    tooltip.style.removeProperty('width');
    tooltip.style.left = '0px'; tooltip.style.top = '0px';
    tooltip.hidden = false;
    const anchor = active.getBoundingClientRect(), rect = tooltip.getBoundingClientRect();
    if (![anchor.x, anchor.y, anchor.width, anchor.height, rect.width, rect.height].every(Number.isFinite)) return false;
    let left, top, side = active.dataset.tooltipSide || 'bottom';
    if (side === 'right') {
      left = anchor.right + gap; top = anchor.top + (anchor.height - rect.height) / 2;
      if (left + rect.width > width - gap) {left = anchor.left - gap - rect.width; side = 'left';}
    } else {
      left = anchor.left + (anchor.width - rect.width) / 2; top = anchor.bottom + gap;
      if (top + rect.height > height - gap) {top = anchor.top - gap - rect.height; side = 'top';}
    }
    tooltip.style.width = `${rect.width}px`;
    tooltip.style.left = `${Math.max(gap, Math.min(left, width - rect.width - gap))}px`;
    tooltip.style.top = `${Math.max(gap, Math.min(top, height - rect.height - gap))}px`;
    tooltip.dataset.side = side;
    tooltip.style.visibility = 'visible';
    return true;
  }
  const observer = new MutationObserver(() => {
    if (!eligible(active) || !render()) hide();
  });
  function show(anchor) {
    hide();
    if (!eligible(anchor)) return;
    active = anchor;
    if (!render()) {hide(); return;}
    describe(anchor, true);
    observer.observe(document.body, {subtree: true, attributes: true,
      attributeFilter: ['inert', 'open', 'aria-modal', 'disabled', 'aria-disabled', 'data-shell-tooltip', 'data-shortcut-keys']});
  }
  const enter = (anchor, immediate = false) => {
    clearTimeout(showTimer); clearTimeout(hideTimer);
    if (anchor === active) return;
    hide();
    if (eligible(anchor)) showTimer = setTimeout(() => show(anchor), immediate ? 0 : timing('--duration-deliberate'));
  };
  const leave = () => {
    clearTimeout(showTimer); clearTimeout(hideTimer);
    if (!hovered && focused && focused !== active) enter(focused, true);
    else if (!hovered && !focused) hideTimer = setTimeout(hide, timing('--duration-fast'));
  };
  const trigger = element => {
    const target = element instanceof Element ? element.closest('[data-shell-tooltip], .shell-control') : null;
    return target?.matches('.shell-control') ? target.querySelector('[data-shell-tooltip]') : target;
  };
  document.addEventListener('pointerover', event => {
    if (event.pointerType === 'touch') return;
    if (tooltip.contains(event.target)) {clearTimeout(hideTimer); return;}
    const anchor = trigger(event.target);
    if (anchor === hovered) return;
    hovered = anchor;
    if (anchor) enter(anchor);
  });
  document.addEventListener('pointerout', event => {
    if (tooltip.contains(event.target)) {
      if (!tooltip.contains(event.relatedTarget)) leave();
      return;
    }
    const anchor = trigger(event.target);
    if (!anchor || anchor.contains(event.relatedTarget)) return;
    hovered = null;
    if (tooltip.contains(event.relatedTarget)) clearTimeout(hideTimer);
    else leave();
  });
  document.addEventListener('focusin', event => {
    const anchor = trigger(event.target);
    focused = anchor?.matches(':focus-visible') ? anchor : null;
    if (focused) enter(focused, true);
  });
  document.addEventListener('focusout', () => {focused = null; leave();});
  document.addEventListener('pointerdown', () => {focused = null; hide();}, true);
  document.addEventListener('keydown', event => {
    if (event.isComposing || event.keyCode === 229) return;
    if (event.key === 'Escape' && active) {
      event.preventDefault(); event.stopPropagation();
    }
    if (!['Shift', 'Control', 'Alt', 'Meta'].includes(event.key)) {
      if (event.key !== 'Tab') focused = null;
      hide();
    }
  }, true);
  // Tab may scroll a clipped menu item into view after focusin. Reanchor its
  // keyboard hint after that scroll; explicit wheel/key movement dismisses it.
  window.addEventListener('scroll', () => {
    hovered = null;
    const anchor = focused;
    hide();
    if (anchor === document.activeElement && eligible(anchor)) enter(anchor, true);
  }, true);
  window.addEventListener('wheel', () => {hovered = focused = null; hide();}, {capture: true, passive: true});
  for (const event of ['resize', 'pagehide', 'blur']) window.addEventListener(event, () => {
    hovered = focused = null;
    hide();
  });
  window.addEventListener('load', () => {
    const anchor = hovered || focused;
    if (anchor) enter(anchor, anchor === focused);
  }, {once: true});
})();
