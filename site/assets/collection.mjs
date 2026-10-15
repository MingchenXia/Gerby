const chapters = document.querySelector('.chapter-navigation');
const compactLayout = window.matchMedia('(max-width: 999px)');

// Keep the reading column clear on small screens, including after a rotation.
function arrangeNavigation() {
  if (chapters) chapters.open = !compactLayout.matches;
}
compactLayout.addEventListener('change', arrangeNavigation);
arrangeNavigation();

// An inline formula can be wider than a phone even when display math fits.
// Give only those formulas their own scrollable line, keeping TeX intact.
function fitMathematics() {
  const content = document.querySelector('main');
  if (!content) return;
  for (const container of content.querySelectorAll('mjx-container:not([display="true"])')) {
    if (container.closest('.source-table')) continue;
    const math = container.querySelector('mjx-math');
    if (!math) continue;
    let block = container.parentElement;
    while (block !== content && ['inline', 'contents'].includes(getComputedStyle(block).display)) {
      block = block.parentElement;
    }
    const style = getComputedStyle(block);
    const available = block.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    container.classList.toggle('wide-math', math.getBoundingClientRect().width > available + 1);
  }
}
const content = document.querySelector('main');
if (content) new ResizeObserver(fitMathematics).observe(content);
window.MathJax?.startup?.promise?.then(fitMathematics);
document.fonts?.ready.then(fitMathematics);

const {exactEntry, searchEntries} = await import(`./search.mjs?v=${document.documentElement.dataset.assetRevision}`);

let indexPromise;
function loadIndex() {
  return indexPromise ??= fetch(document.documentElement.dataset.searchIndex).then(response => {
    if (!response.ok) throw new Error('Search unavailable');
    return response.json();
  }).catch(error => { indexPromise = null; throw error; });
}
function bindSearch(input, results, fullPage = false) {
  if (!input || !results) return;
  let request = 0;
  async function update() {
    const current = ++request;
    const query = input.value.trim();
    results.replaceChildren();
    if (query.length < 2) return;
    results.textContent = 'Searching…';
    try {
      const index = await loadIndex();
      if (current !== request) return;
      const matches = searchEntries(index, query);
      results.replaceChildren();
      const summary = document.createElement('p');
      summary.textContent = `${matches.length} matching entr${matches.length === 1 ? 'y' : 'ies'}`;
      results.append(summary);
      let shown = 0;
      const more = document.createElement(fullPage ? 'button' : 'a');
      if (fullPage) more.type = 'button';
      else more.href = `${document.documentElement.dataset.collectionRoot}search/?q=${encodeURIComponent(query)}`;
      function append() {
        const end = Math.min(shown + (fullPage ? 50 : 8), matches.length);
        for (const item of matches.slice(shown, end)) {
          const anchor = document.createElement('a');
          anchor.href = `${document.documentElement.dataset.collectionRoot}tag/${item.tag}/`;
          const title = document.createElement('strong');
          title.textContent = item.title;
          const context = document.createElement('small');
          context.textContent = item.section ?? item.topic;
          anchor.append(title, context);
          results.insertBefore(anchor, more.parentElement ? more : null);
        }
        shown = end;
        more.textContent = fullPage ? `Show more (${shown} of ${matches.length})` : 'View all search results';
        if (shown < matches.length) results.append(more);
        else more.remove();
      }
      more.addEventListener('click', fullPage ? append : () => {});
      append();
    } catch {
      if (current === request) results.textContent = 'Search is temporarily unavailable. Please try again.';
    }
  }
  input.addEventListener('input', update);
  input.form?.addEventListener('submit', async event => {
    event.preventDefault();
    try {
      const match = exactEntry(await loadIndex(), input.value);
      if (match) location.href = `${document.documentElement.dataset.collectionRoot}tag/${match.tag}/`;
      else if (fullPage) { history.replaceState(null, '', `?q=${encodeURIComponent(input.value)}`); update(); }
      else location.href = `${document.documentElement.dataset.collectionRoot}search/?q=${encodeURIComponent(input.value)}`;
    } catch { update(); }
  });
  input.addEventListener('keydown', event => { if (event.key === 'Escape' && !fullPage) results.replaceChildren(); });
  if (fullPage) { input.value = new URLSearchParams(location.search).get('q') ?? ''; update(); }
}
bindSearch(document.querySelector('#collection-search'), document.querySelector('#search-results'));
bindSearch(document.querySelector('#page-search'), document.querySelector('#page-search-results'), true);

document.querySelectorAll('[data-toc]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.toc-chapter').forEach(chapter => { chapter.open = button.dataset.toc === 'expand'; });
}));
const tagSwitch = document.querySelector('[data-show-tags]');
try { if (tagSwitch) tagSwitch.checked = localStorage.getItem('gerby-show-tags') === 'true'; } catch {}
function showTags() {
  document.documentElement.dataset.showTags = String(Boolean(tagSwitch?.checked));
  try { localStorage.setItem('gerby-show-tags', String(Boolean(tagSwitch?.checked))); } catch {}
}
tagSwitch?.addEventListener('change', showTags);
showTags();
document.querySelectorAll('[data-copy-link], [data-copy-citation]').forEach(button => button.addEventListener('click', async () => {
  const value = button.dataset.copyLink ?? document.querySelector('#citation-text').value;
  const status = button.parentElement.querySelector('.copy-status');
  try { await navigator.clipboard.writeText(value); status.textContent = 'Copied.'; }
  catch { status.textContent = 'Select and copy the permalink or citation above.'; }
}));

// A clause permalink may target a retained source version that is collapsed.
function revealFragment() {
  if (!location.hash) return;
  let target;
  try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
  catch { return; }
  if (!target) return;
  for (let node = target.parentElement; node; node = node.parentElement) {
    if (node.tagName === 'DETAILS') node.open = true;
  }
  target.scrollIntoView({block: 'start'});
}
window.addEventListener('hashchange', revealFragment);
revealFragment();
