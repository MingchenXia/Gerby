const input = document.querySelector('#collection-search');
const results = document.querySelector('#search-results');
const chapters = document.querySelector('.chapter-navigation');
const compactLayout = window.matchMedia('(max-width: 1099px)');

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

let index;
let request = 0;
input?.addEventListener('input', async () => {
  const current = ++request;
  const query = input.value.trim().toLowerCase();
  results.replaceChildren();
  if (query.length < 2) return;
  try {
    index ??= await fetch(document.documentElement.dataset.searchIndex).then(response => {
      if (!response.ok) throw new Error('Search unavailable');
      return response.json();
    });
    if (current !== request) return;
    const matches = index.filter(item => `${item.title} ${item.tag} ${item.topic} ${item.aliases.join(' ')} ${item.text}`.toLowerCase().includes(query));
    const summary = document.createElement('p');
    summary.textContent = `${matches.length} matching entr${matches.length === 1 ? 'y' : 'ies'}`;
    results.append(summary);
    for (const item of matches.slice(0, 30)) {
      const anchor = document.createElement('a');
      anchor.href = `${document.documentElement.dataset.collectionRoot}tag/${item.tag}/`;
      anchor.textContent = `${item.title} · ${item.topic}`;
      results.append(anchor);
    }
  } catch {
    if (current === request) results.textContent = 'Search is temporarily unavailable.';
  }
});

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
