const input = document.querySelector('#collection-search');
const results = document.querySelector('#search-results');
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
