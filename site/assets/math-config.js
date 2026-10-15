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
