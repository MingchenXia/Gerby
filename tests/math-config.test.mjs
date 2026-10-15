import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';

const context = {window: {}};
vm.runInNewContext(readFileSync(new URL('../site/assets/math-config.js', import.meta.url), 'utf8'), context);
const require = createRequire(import.meta.url);
const {init} = require('../vendor/node_modules/mathjax');

test('the reading configuration renders coloneqq as mathematics, including inside a definition', async () => {
  const config = JSON.parse(JSON.stringify(context.window.MathJax));
  const mathjax = await init({loader: {load: ['input/tex', 'output/chtml', ...config.loader.load]}, tex: config.tex});
  const result = mathjax.tex2mml(String.raw`\operatorname{nn}(\alpha)\coloneqq\{x:\nu(T,x)>0\}`);
  assert.ok(!result.includes('merror'), result);
  assert.ok(!result.includes('coloneqq'), result);
  assert.ok(result.includes('≔') || result.includes(':') || result.includes('&#x2254;'), result);
});
