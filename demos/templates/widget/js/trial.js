// The trial offer. The URL is the server's own redirect (one place knows the destination). Anything with a NUMBER in it - "14-day" - is read from
// GET /api/pricing (self_serve) at run time, never typed here: a hand copy of a published figure drifts silently, and did (the knowledge-box row).
// Until the endpoint answers (or if it is unavailable) the copy is the generic "free trial", which asserts no number.
import { getJSON } from './api.js';
export const TRIAL = { url: '/go/signup', short: 'Start free trial', cta: 'Start free trial', offer: null, appliesTo: null, loaded: false };
let memo = null;
export const pricingData = () => (memo = memo || getJSON('/api/pricing', { label: 'pricing' }).catch((e) => { memo = null; throw e; }));
export async function loadTrial() {
  try {
    const P = await pricingData(); const s = P && P.self_serve;
    if (s && typeof s.cta_copy === 'string' && s.cta_copy) { TRIAL.cta = s.cta_copy; TRIAL.offer = s.offer || null; TRIAL.appliesTo = s.applies_to || null; TRIAL.loaded = true; }
  } catch { /* the generic copy stays; the pricing page shows its own honest state */ }
  document.querySelectorAll('[data-trial-cta]').forEach((n) => { n.textContent = TRIAL.cta; });
  return TRIAL;
}
// A call-to-action whose label follows the published copy as soon as it is known.
export const trialLabel = () => TRIAL.cta;
// "a 14-day free trial" when the endpoint said so, otherwise "a free trial": the sentence never states a number it was not given.
export const trialOffer = () => (TRIAL.offer ? `a ${TRIAL.offer}` : 'a free trial');
