// Iframe target for the embeddable widget. No key, public tier only; scope/lens/theme come from the URL.
import { mountAsk } from './ask.js';
import { setLens } from './state.js';
const q = new URL(location.href).searchParams;
if (q.get('theme') === 'dark') document.body.classList.add('dark');
setLens(q.get('lens'));
const scope = /^([a-z]+:)?[a-z-]+$/.test(q.get('scope') || '') ? q.get('scope') : null;
const host = document.getElementById('w');
const a = mountAsk(host, { scope, autofocus: false });
host.append(a.answerHost);
// Content height, not the document's: documentElement.scrollHeight is never smaller than the iframe, so it could never shrink.
const post = () => parent !== window && parent.postMessage({ type: 'agentic-rag-embed-height', height: Math.ceil(document.body.getBoundingClientRect().height) }, '*');
new ResizeObserver(post).observe(document.body);
