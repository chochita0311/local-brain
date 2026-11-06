// The language option belongs to the shared Docs navigation, with ordinary links.
const docsLanguage = document.querySelector('[data-docs-language]');
if (docsLanguage) {
  document.addEventListener('click', event => {
    if (!docsLanguage.contains(event.target)) docsLanguage.open = false;
  });
  docsLanguage.addEventListener('keydown', event => {
    if (event.key === 'Escape' && docsLanguage.open) {
      event.preventDefault();
      event.stopPropagation();
      docsLanguage.open = false;
      docsLanguage.querySelector('summary').focus();
    }
  });
}
