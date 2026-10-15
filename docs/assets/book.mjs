const input = document.querySelector('#book-search');
const results = document.querySelector('#search-results');
let index;
let request = 0;
input?.addEventListener('input', async () => {
  const currentRequest = ++request;
  const query = input.value.trim().toLowerCase();
  results.replaceChildren();
  if (query.length < 2) return;
  try {
    index ??= await fetch(document.documentElement.dataset.searchIndex).then(response => {
      if (!response.ok) throw new Error('Search index unavailable');
      return response.json();
    });
    if (currentRequest !== request) return;
    const matches = index.filter(item => `${item.tag} ${item.label} ${item.title} ${item.text}`.toLowerCase().includes(query));
    const summary = document.createElement('p');
    summary.textContent = `${matches.length} matching tag${matches.length === 1 ? '' : 's'}`;
    results.append(summary);
    for (const item of matches.slice(0, 20)) {
      const anchor = document.createElement('a');
      anchor.href = `${document.documentElement.dataset.bookRoot}tag/${item.tag}/`;
      anchor.textContent = `${item.title} [${item.tag}]`;
      results.append(anchor);
    }
  } catch {
    if (currentRequest === request) results.textContent = 'Search is temporarily unavailable.';
  }
});
