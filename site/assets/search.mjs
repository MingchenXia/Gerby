const normalize = value => String(value ?? '').toLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
const prepared = new WeakMap();
function documentFor(item) {
  if (!prepared.has(item)) prepared.set(item, normalize(`${item.title} ${item.search_title ?? ''} ${item.tag} ${item.aliases.join(' ')} ${item.topic} ${item.section ?? ''} ${item.text}`));
  return prepared.get(item);
}

export function exactEntry(index, query) {
  const term = normalize(query.trim());
  const matches = index.filter(item => [item.tag, ...item.aliases].some(value => normalize(value) === term));
  return matches.length === 1 ? matches[0] : null;
}

export function searchEntries(index, query) {
  const term = normalize(query.trim());
  if (term.length < 2) return [];
  const words = term.split(/\s+/);
  return index.map((item, position) => {
    const title = normalize(item.title);
    const names = normalize(item.search_title);
    const aliases = normalize([item.tag, ...item.aliases].join(' '));
    const context = normalize(`${item.topic} ${item.section ?? ''}`);
    if (!words.every(word => documentFor(item).includes(word))) return null;
    const score = exactEntry([item], term) ? 100 : title === term ? 90 : names === term ? 80 : title.includes(term) ? 70 : names.includes(term) ? 60 : aliases.includes(term) ? 50 : context.includes(term) ? 20 : 1;
    return {item, score, position};
  }).filter(Boolean).sort((a, b) => b.score - a.score || a.position - b.position).map(result => result.item);
}
