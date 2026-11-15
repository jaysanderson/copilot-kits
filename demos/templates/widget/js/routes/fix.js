import { h, $ } from '../util.js';
import { mountAsk } from '../ask.js';
import { getJSON } from '../api.js';
import { hitCard, readout } from '../cards.js';

// The six causes, in the order they actually occur. Wording follows corpus/canonical/why-is-this-answer-wrong.md (lead's canonical guide);
// the "Ask the guide" button runs a REAL cited answer, so the page never asserts more than the knowledge box returns.
const CAUSES = [
  { t: 'The content does not contain the answer', tell: 'A retrieved passage is plainly on the right subject and does not hold the fact you asked for.', do: 'Read the passage. Derive your content from the questions real users ask, then ask them. If a question has no answer in your content, no setting will produce one, and you do not want one that invents it.', num: 'Measured on one build: ten documents averaging about 374 words could not answer what a practitioner types. The same ten at 800 to 1,100 words could.', q: 'What should I do when my content does not contain the answer to a question?' },
  { t: 'The answer is somewhere your retrieval is not looking', tell: 'A question that obviously has an answer gets none.', do: 'List what is inside the scope and read some of it. Check a scope by its contents, not by its definition. A filter wrong in shape can behave as no filter at all.', q: 'Why does a question with an obvious answer get none when I use filters or permission scoping?' },
  { t: 'Your application\'s floor is making the decision', tell: 'Nearly everything declines, including questions on your own subject.', do: 'Find the floor and write down which corpus it was set against. Set it from measurement over your own content. Never adjust it to silence one complaint.', num: 'A floor tuned on a corpus of a thousand documents will decline almost everything over a corpus of ten.', q: 'Why does my application decline almost every question and how do I set the floor?' },
  { t: 'Related is being mistaken for relevant', tell: 'The top-ranked document is about the subject and never holds the answer.', do: 'Read the reranker\'s score, not the retrieval rank. A high rank with a low rerank score is a statement about your content, not your threshold.', num: 'On one corpus, documents about the subject that did not hold the answer scored 0.03 to 0.07. One that did scored 0.877.', q: 'What is the difference between retrieval rank and reranker score when an answer is wrong?' },
  { t: 'The answer is right and the citation is not', tell: 'The wording is well supported but a citation points somewhere unhelpful.', do: 'Check whether the cited passage contains the claim beside it. If the prose names a source, the citation should follow that source, not whichever result scored highest.', q: 'What do I do when an answer is right but the citation points to the wrong place?' },
  { t: 'The quality score means less than you think', tell: 'A score looks high on a wrong answer, or low on a good one.', do: 'Read a low score as "the content did not support this wording" and a high one as "it did". Neither says the answer is true. Score against the full retrieved context, not only the cited excerpts.', q: 'What does the groundedness score measure and what does it not?' },
];
const SYMPTOMS = [['Almost everything declines', 3], ['On topic, but missing the fact', 1], ['The top result never answers', 4], ['It should have found it and did not', 2], ['Right answer, odd source', 5], ['The score looks wrong', 6]];

export async function mount(main, url) {
  const head = h('section', { class: 'phead askhead' }, h('div', { class: 'wrap' }, h('h1', {}, 'My answers are wrong'),
    h('p', {}, 'Work through it in order. The causes are listed the way they actually occur, and the first two account for most of it.')));
  main.append(head);
  const askHost = h('div', { style: 'margin-top:24px' }); head.firstChild.append(askHost);
  const ask = mountAsk(askHost, { autofocus: false });
  askHost.parentElement.parentElement.after(ask.answerHost);
  const page = h('div', { class: 'wrap page' }); main.append(page);
  const det = [];
  page.append(h('div', { class: 'sh' }, h('p', { class: 'eyebrow' }, 'Start with what you see'), h('div', { class: 'chips' }, ...SYMPTOMS.map(([l, n]) => h('button', { class: 'chip', type: 'button', onclick: () => { det.forEach((d, i) => (d.open = i === n - 1)); det[n - 1].scrollIntoView({ behavior: 'smooth', block: 'start' }); } }, l)))));
  CAUSES.forEach((c, i) => {
    const d = h('details', { class: 'cause', id: 'cause-' + (i + 1) }, h('summary', {}, h('span', { class: 'n' }, String(i + 1)), h('h3', {}, c.t)),
      h('div', { class: 'cb' }, h('dl', {}, h('dt', {}, 'How to tell'), h('dd', {}, c.tell), h('dt', {}, 'What to do'), h('dd', {}, c.do), ...(c.num ? [h('dt', {}, 'Measured'), h('dd', { class: 'mono' }, c.num)] : [])),
        h('p', { style: 'margin-top:14px' }, h('button', { class: 'btn btn-line btn-sm', type: 'button', onclick: () => { window.scrollTo({ top: 0, behavior: 'smooth' }); ask.ask(c.q); } }, 'Ask the guide about this'))));
    if (i < 2) d.open = true; det.push(d); page.append(d);
  });
  page.append(h('p', { style: 'margin-top:24px;font-size:17px' }, 'Been through all six? Then the useful question stops being "why is this answer wrong" and becomes "what would have to be true in my content for this answer to be right".'));
  const guide = h('div', { class: 'sec' }); page.append(guide);
  getJSON('/api/search?q=' + encodeURIComponent('why is this answer wrong diagnose retrieval'), { label: 'Fix: guides' }).then((j) => {
    const c = (j.hits || []).slice(0, 3); if (!c.length) return;
    guide.append(h('h3', {}, 'Read more in the library'), h('div', { class: 'suggest', style: 'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));max-width:none;margin-top:0' }, ...c.map((a, i) => hitCard(a, i))), readout(j._trace));
  }).catch(() => {});
  const hash = location.hash.match(/^#cause-(\d)$/); if (hash && det[+hash[1] - 1]) det[+hash[1] - 1].open = true;
  const q0 = url.searchParams.get('q'); if (q0) ask.ask(q0);
  return () => ask.destroy();
}
