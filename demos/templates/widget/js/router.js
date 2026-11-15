const routes = new Map();
let cleanup = null;
export function route(path, loader) { routes.set(path, loader); }
export function navigate(url, { replace = false } = {}) { replace ? history.replaceState(null, '', url) : history.pushState(null, '', url); run(); }
export async function run() {
  shown = location.pathname + location.search;
  const u = new URL(location.href), path = routes.has(u.pathname) ? u.pathname : '/';
  if (!routes.has(u.pathname)) history.replaceState(null, '', '/' + u.search);
  document.dispatchEvent(new Event('routing'));
  if (cleanup) { try { cleanup(); } catch {} cleanup = null; }
  const main = document.getElementById('main');
  main.replaceChildren();
  window.scrollTo(0, 0);
  const mod = await routes.get(path)();
  cleanup = (await mod.mount(main, u)) || null;
  document.dispatchEvent(new CustomEvent('routed', { detail: { path } }));
}
document.addEventListener('click', (e) => {
  const a = e.target.closest('a[href]'); if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || a.target === '_blank') return;
  const u = new URL(a.href, location.href);
  // A same-page #fragment link (a citation marker, a section anchor) is the BROWSER's job: routing it re-mounted the page, wiping the answer the marker belonged to.
  if (u.origin === location.origin && u.pathname === location.pathname && u.search === location.search && u.hash) return;
  if (u.origin === location.origin && routes.has(u.pathname)) { e.preventDefault(); navigate(u.pathname + u.search + u.hash); }
});
// The browser also fires popstate for a fragment-only move; that is a scroll, not a navigation, and re-mounting wipes the page's state.
let shown = location.pathname + location.search;
// The page rewrites its own query (?q=) in place without navigating; that is the page it already shows, so it must not read as a new page when a fragment move follows.
const _replace = history.replaceState.bind(history);
history.replaceState = (...a) => { _replace(...a); shown = location.pathname + location.search; };
addEventListener('popstate', () => { const now = location.pathname + location.search; if (now === shown) return; run(); });
