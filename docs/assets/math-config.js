window.MathJax = {
  loader: {load: ['[tex]/html', '[tex]/textmacros']},
  tex: {
    packages: {'[+]': ['html', 'textmacros']},
    inlineMath: [['$', '$'], ['\\(', '\\)']], processEscapes: true,
    macros: {
      mathds: ['\\mathbb{#1}', 1],
      xlongrightarrow: ['\\xrightarrow{#1}', 1],
      adjustlimits: '',
      index: ['', 1],
      footnotemark: '^{\\ast}',
      fint: '\\mathop{\\rlap{-}\\!\\int}\\nolimits'
    }
  },
  options: {skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']},
  chtml: {scale: 1}
};
if (typeof document !== 'undefined' && document.documentElement.dataset.readingMode === 'continuous') {
  window.MathJax.loader.load.push('ui/lazy');
}
