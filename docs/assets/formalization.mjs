export function badgeDetails(entry, unavailable = false) {
  if (unavailable) return { text: 'Status unavailable', icon: '!', state: 'unavailable', title: 'Formalization status could not be loaded.' };
  if (!entry) return { text: 'Not recorded', icon: '○', state: 'not-recorded', title: 'No formalization has been recorded for this tag.' };
  if (entry.state === 'verified' && /^[a-f0-9]{40}$/.test(entry.commit || '')) {
    return { text: '0 sorry', icon: '✓', state: 'verified', href: `${entry.repository}/tree/${entry.commit}`, title: `${entry.declaration} · ${entry.file} · checked at ${entry.commit.slice(0, 12)}` };
  }
  return { text: 'Pending verification', icon: '◷', state: 'pending', href: entry.repository, title: 'The current source revision has not passed verification.' };
}

export async function installBadges(root = document) {
  const targets = [...root.querySelectorAll('[data-gerby-tag]')];
  if (!targets.length) return;
  let entries = [], unavailable = false;
  try {
    const response = await fetch(new URL('../formalizations.json', import.meta.url));
    if (!response.ok) throw new Error('Registry unavailable');
    const registry = await response.json();
    if (registry.version !== 1 || !Array.isArray(registry.entries)) throw new Error('Invalid registry');
    entries = registry.entries;
  } catch {
    unavailable = true;
  }
  for (const target of targets) {
    if (target.querySelector('[data-formalization-badge]')) continue;
    const book = target.closest('[data-gerby-book]')?.dataset.gerbyBook;
    const entry = entries.find(item => item.book === book && item.tag === target.dataset.gerbyTag);
    const badge = badgeDetails(entry, unavailable);
    const element = document.createElement(badge.href ? 'a' : 'span');
    element.className = `formalization-badge ${badge.state}`;
    element.dataset.formalizationBadge = '';
    element.textContent = `${badge.icon} ${badge.text}`;
    element.title = badge.title;
    element.setAttribute('aria-label', `${badge.text}: ${badge.title}`);
    if (badge.href) element.href = badge.href;
    target.append(element);
  }
}

if (typeof document !== 'undefined') installBadges();
