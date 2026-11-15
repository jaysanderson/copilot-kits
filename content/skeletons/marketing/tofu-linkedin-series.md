# LinkedIn series - The RAG maintenance treadmill (4 posts)

**Voice:** `jay` register (personal LinkedIn - em dashes allowed here only, per hard rule 2's exemption). Post in sequence, roughly 2-4 days apart. Each stands alone.

---

## Post 1 - The treadmill

Building a RAG pipeline takes a weekend.

Maintaining one takes a team.

I keep meeting technical leads who built a working retrieval demo in a few days — vector database, a framework, an API key — and got genuinely excited. Fair enough. It's impressive.

Then it goes into production, and the real list shows up: connectors that have to keep working as source systems change shape, parsing that has to survive scanned PDFs and merged-cell spreadsheets, chunking and indexing decisions nobody remembers making, reranking, evaluation, monitoring for silent quality drift, permissions and governance, scaling — and then a new embedding model ships and half of it needs re-testing.

None of that is in the demo. All of it is on the on-call roster twelve months later.

The build was never the hard part.

What's your plan for month eighteen?

---

## Post 2 - Measurable trust

You cannot improve what you cannot measure.

Most RAG teams I talk to have never actually scored an answer. They've read a few, decided it "seems right," and moved on. That's not quality assurance — that's a vibe wearing a lab coat.

Here's what changes it: score every answer, every query, on three things — is it grounded in the real source, was the retrieved context actually relevant, is the answer relevant to the question that was asked. Not a monthly sample. Every single query.

Do that and something useful happens. A bad answer stops being a mystery and starts being a diagnosis. Low groundedness with good context? Generation problem. Low context relevance? Retrieval problem. Two completely different fixes — and now you know which one you need.

Trust in an AI answer isn't a feeling. It's a number you can point to. Or it should be.

Is anyone on your team actually scoring answer quality per query — or is "it looks right" still the bar?

---

## Post 3 - Confidently wrong

The scariest failure mode in RAG isn't a crash. It's a system that's confidently, quietly wrong.

A retrieval pipeline can pass every test your team thought to write and still hand a user a fluent, well-formatted, completely ungrounded answer. Nothing breaks. No error. No alert. Someone just acts on bad information — and you find out about it from a complaint, not a dashboard.

That's the gap between "it works in the demo" and "it works." The demo shows you the ten questions your team tested. Production shows you the four thousand questions real people actually ask — including the ones your corpus doesn't cover, the ambiguous ones, and the ones where a wrong answer does more damage than no answer at all.

If your RAG system can be confidently wrong without you knowing, you haven't shipped a feature. You've shipped a liability with good UX.

What would it actually take for your team to notice a bad answer before a customer does?

---

## Post 4 - The honest complication

Here's the honest complication in all of this — I'm not telling you not to build your own RAG stack.

Plenty of teams should own every layer — a genuinely novel retrieval problem, a hard regulatory reason to control each component, an existing platform investment that makes it the cheaper path. DIY is a legitimate call. I'd never tell someone their engineering team can't do it.

What it isn't, is a free call. The maintenance list — connectors, parsing, indexing, reranking, monitoring, governance, scaling, every model upgrade — is real whether you assemble it yourself or buy a platform built for it. The only question that actually matters is who owns that list in eighteen months, and whether you'll have a number for "is this still working," or just an opinion.

Retrieval isn't hard to demo anymore. Anyone can do that in an afternoon. It's hard to keep trustworthy, in production, for years, while the ground underneath it keeps moving.

Budget for that job. Not the demo.

What's the real maintenance cost your team is carrying on its RAG stack right now — and does anyone actually know the number?
