/* One presentation snapshot for saved local profile names, colors and ordering. */
(() => {
  function apply(sources) {
    const byId = new Map(sources.map(source => [String(source.id), source]));
    document.querySelectorAll('[data-profile-id]').forEach(node => {
      const source = byId.get(node.dataset.profileId);
      if (source) node.dataset.profileColor = source.color;
    });
    document.querySelectorAll('[data-profile-label]').forEach(node => {
      const source = byId.get(node.dataset.profileLabel);
      if (source) node.textContent = source.name;
    });
    document.querySelectorAll('[data-profile-filters]').forEach(nav => {
      const links = new Map([...nav.querySelectorAll('[data-profile-id]')].map(node => [node.dataset.profileId, node]));
      sources.forEach(source => {
        const id = String(source.id);
        let link = links.get(id);
        if (!link) {
          const all = nav.querySelector('a');
          link = document.createElement('a');
          const url = new URL(all.href, location.href); url.searchParams.set('source', id); url.searchParams.delete('page');
          link.href = url.href;
          if (nav.classList.contains('usage-source-control')) {
            link.dataset.usageScopeLink = ''; link.dataset.usageControl = 'source'; link.dataset.usageValue = id;
          }
          link.dataset.profileId = id; link.dataset.profileLabel = id;
        }
        link.textContent = source.name; link.dataset.profileColor = source.color;
        nav.append(link);
      });
    });
    document.dispatchEvent(new CustomEvent('localbrain-profiles-changed', {detail: {sources}}));
  }
  window.LocalBrainProfiles = {apply};
})();
