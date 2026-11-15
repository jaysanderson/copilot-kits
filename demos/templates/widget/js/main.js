import { route, run } from './router.js';
import { mountTopbar, mountLensbar, mountFooter, markNav } from './chrome.js';
import { setLens } from './state.js';
import { loadTrial } from './trial.js';

const u = new URL(location.href);
setLens(u.searchParams.get('lens'));
mountTopbar(); mountFooter(); loadTrial();
route('/', () => import('./routes/home.js'));
route('/explore', () => import('./routes/explore.js'));
route('/watch', () => import('./routes/watch.js'));
route('/build', () => import('./routes/build.js'));
route('/fix', () => import('./routes/fix.js'));
route('/pricing', () => import('./routes/pricing.js'));
route('/fit', () => import('./routes/fit.js'));
route('/embed', () => import('./routes/embed.js'));
const TITLES = { '/': 'Progress Agentic RAG - ask the product', '/explore': 'Explore the library - Progress Agentic RAG', '/watch': 'Films - Progress Agentic RAG', '/build': 'Build with it - Progress Agentic RAG', '/pricing': 'Pricing and value model - Progress Agentic RAG', '/fit': 'Where it fits - Progress Agentic RAG', '/fix': 'Fix a wrong answer - Progress Agentic RAG', '/embed': 'Embed - Progress Agentic RAG' };
document.addEventListener('routed', (e) => {
  const p = e.detail.path;
  document.title = TITLES[p] || document.title;
  mountLensbar(p !== '/'); markNav(p);
  document.getElementById('main').focus({ preventScroll: true });
});
run();
