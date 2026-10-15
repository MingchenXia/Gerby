const panel = document.querySelector('[data-comment-term]');
if (panel) {
  const button = panel.querySelector('[data-load-comments]');
  const status = panel.querySelector('.comment-status');
  const widget = panel.querySelector('.giscus');
  let started = false;
  function unavailable() {
    widget.hidden = true;
    status.textContent = 'Inline comments are currently unavailable. Use the GitHub links above to read or post a comment.';
    button.hidden = false;
    button.textContent = 'Retry loading comments';
    started = false;
  }
  function load() {
    if (started) return;
    started = true;
    widget.hidden = false;
    widget.replaceChildren();
    button.hidden = true;
    status.textContent = 'Loading comments…';
    const script = document.createElement('script');
    script.src = 'https://giscus.app/client.js';
    for (const key of ['repo', 'repoId', 'category', 'categoryId']) script.dataset[key] = panel.dataset[key];
    Object.assign(script.dataset, {
      mapping: 'specific', term: panel.dataset.commentTerm, strict: '1',
      reactionsEnabled: '1', emitMetadata: '1', inputPosition: 'top',
      theme: 'light', lang: 'en', loading: 'lazy',
    });
    script.crossOrigin = 'anonymous';
    script.async = true;
    script.addEventListener('error', unavailable, {once: true});
    widget.append(script);
  }
  button.addEventListener('click', load);
  window.addEventListener('message', event => {
    const frame = widget.querySelector('iframe');
    if (event.origin !== 'https://giscus.app' || event.source !== frame?.contentWindow || !event.data?.giscus) return;
    const data = event.data.giscus;
    if (data.error) {
      if (/not found|no discussion/i.test(data.error) && !/not installed|repository/i.test(data.error)) status.textContent = '';
      else unavailable();
    } else if (data.discussion) {
      status.textContent = '';
      const count = data.discussion.totalCommentCount;
      if (Number.isInteger(count)) panel.querySelector('[data-comment-count]').textContent = ` (${count})`;
    } else status.textContent = '';
  });
  const observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) { observer.disconnect(); load(); }
  }, {rootMargin: '200px'});
  observer.observe(panel);
}
