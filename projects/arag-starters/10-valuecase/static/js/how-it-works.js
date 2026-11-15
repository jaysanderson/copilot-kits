/**
 * "How this works" solution-architecture reveal (table-stakes gate 11).
 *
 * This tool is the one deliberate exception in the demo estate: it makes
 * ZERO ARAG API calls (see app.py's own module docstring) and holds no
 * ARAG account credential of any kind - it is a deterministic
 * value-engineering calculator. Per hard rule 3's corollary, where a surface routes through
 * no real ARAG call, the honest marker IS the deliverable - this reveal's
 * whole job is to say that plainly, not to imply retrieval or generation
 * that never happens. It is mounted once, fixed top-right, present above
 * every view this single-page app renders (dashboard, case list, case
 * detail, exports) - there is only one real "route" here, so one flow is
 * accurate everywhere it appears.
 */

const FLOW = {
  title: 'How this works',
  what: 'This tool makes no retrieval or generation calls at all. It is a deterministic value-engineering calculator - every figure on screen is computed from numbers a seller or buyer typed in, run through a fixed financial model.',
  steps: [
    {
      label: 'You enter the numbers',
      detail: 'Lever inputs, who supplied each one and when, the pricing tier and the conservative/expected/aggressive range are typed in during discovery - never inferred, never fetched from anywhere.',
    },
    {
      label: 'Deterministic math',
      detail: 'This tool’s own finance engine runs real time-phased NPV, IRR and payback-period calculations against exactly those numbers - the same formulas every time. No model call sits anywhere in this path.',
    },
    {
      label: 'Stored, not generated',
      detail: 'The case, its scenarios and every input’s provenance are saved to this tool’s own database, so the case survives past the meeting it was built in and can be revisited or handed to another seller.',
    },
    {
      label: 'Exports mirror the screen',
      detail: 'The branded PowerPoint and Word exports render exactly the same computed numbers shown here - nothing is added, summarised or reworded by a model on the way out.',
    },
  ],
  why: 'A business case has to survive a CFO’s scrutiny. That only works if every number traces to a real input and a fixed formula the seller can defend line by line - so this tool is deliberately honest that it is a calculator, not an AI-generated answer, and nothing in it needs independent verification against a corpus.',
};

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === 'class') node.className = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    node.append(c.nodeType ? c : document.createTextNode(c));
  }
  return node;
}

let active = 0;
let advanceTimer = null;
let track, dotsWrap;

function goTo(i) {
  active = i;
  track.querySelectorAll('.hiw-step').forEach((n, idx) => n.classList.toggle('is-active', idx === i));
  dotsWrap.querySelectorAll('.hiw-dot').forEach((n, idx) => n.classList.toggle('is-active', idx === i));
  const activeNode = track.querySelectorAll('.hiw-step')[i];
  if (activeNode) activeNode.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
}

function buildModal() {
  const modal = el('div', { class: 'hiw-modal', role: 'dialog', 'aria-modal': 'true', 'aria-label': FLOW.title });
  const closeBtn = el('button', { class: 'hiw-close', type: 'button', 'aria-label': 'Close', onclick: closeModal }, '×');
  const heading = el('h2', { class: 'hiw-title' }, FLOW.title);
  const what = el('p', { class: 'hiw-what' }, FLOW.what);

  track = el('div', { class: 'hiw-track' });
  FLOW.steps.forEach((s, i) => {
    track.append(el('div', { class: 'hiw-step' + (i === 0 ? ' is-active' : '') },
      el('div', { class: 'hiw-step-eyebrow' }, `Step ${i + 1} of ${FLOW.steps.length}`),
      el('div', { class: 'hiw-step-label' }, s.label),
      el('div', { class: 'hiw-step-detail' }, s.detail)));
    if (i < FLOW.steps.length - 1) track.append(el('div', { class: 'hiw-arrow' }, '→'));
  });

  dotsWrap = el('div', { class: 'hiw-dots' },
    ...FLOW.steps.map((_, i) => el('button', {
      class: 'hiw-dot' + (i === 0 ? ' is-active' : ''),
      type: 'button',
      'aria-label': `Go to step ${i + 1}`,
      onclick: () => goTo(i),
    })));

  const why = el('div', { class: 'hiw-why' },
    el('div', { class: 'hiw-why-label' }, 'Why it matters'),
    el('p', {}, FLOW.why));

  const footer = el('div', { class: 'hiw-footer' },
    'This is the real (and deliberately deterministic) mechanism behind every number this tool shows - not a marketing diagram.');

  modal.append(closeBtn, heading, what, track, dotsWrap, why, footer);
  return modal;
}

function openModal() {
  active = 0;
  document.getElementById('hiw-backdrop').hidden = false;
  document.body.style.overflow = 'hidden';
  clearInterval(advanceTimer);
  advanceTimer = setInterval(() => goTo((active + 1) % FLOW.steps.length), 2400);
}

function closeModal() {
  clearInterval(advanceTimer);
  const backdrop = document.getElementById('hiw-backdrop');
  if (backdrop) backdrop.hidden = true;
  document.body.style.overflow = '';
}

function mount() {
  const trigger = el('button', {
    class: 'hiw-trigger',
    type: 'button',
    'aria-label': 'How this works',
    onclick: openModal,
  }, el('span', { class: 'hiw-trigger-icon', 'aria-hidden': 'true' }, 'ⓘ'), el('span', { class: 'hiw-trigger-label' }, ' How this works'));
  document.body.append(trigger);

  const backdrop = el('div', {
    id: 'hiw-backdrop',
    class: 'hiw-backdrop',
    hidden: '',
    onclick: (e) => { if (e.target.id === 'hiw-backdrop') closeModal(); },
  });
  backdrop.append(buildModal());
  document.body.append(backdrop);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !backdrop.hidden) closeModal();
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mount);
} else {
  mount();
}
