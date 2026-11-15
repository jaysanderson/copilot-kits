# LinkedIn article draft - agentic retrieval in research technology

**DAM work item:** 6f7204d9001e496bb09d6a165eb27c0f
**Status:** DRAFT - outbound, Jay's sign-off required before posting (hard rule 10)
**Voice:** Jay's personal LinkedIn register (true em dashes kept, per the hard rule 2 exemption)

---

## PASTE FROM HERE (LinkedIn article body)

**Headline:** Agentic retrieval for research teams: where it earns its keep, and where I'd talk you out of it

Here is a question a research lead might type on a Monday morning: *did any of our internal phase II reports flag the liver enzyme signal that the new paper in last month's journal describes?*

Answering it properly means reading an internal trial report, a recorded lab meeting, a spreadsheet of assay results and one external paper published three weeks ago. Then reconciling them, which is the part nobody enjoys. A search bar finds documents. It doesn't reconcile.

I work on Progress Agentic RAG at Progress. Weigh everything below accordingly. But I've spent enough time around research and legal teams to have a firm view on where this category fits, and I'd rather give you the boundaries than the brochure.

**Who it suits**

Enterprise R&D. Corporate laboratories. Legal discovery. Institutional research groups. Anywhere a team needs a production-grade research intelligence layer and has no appetite for building multi-agent state machines to get one.

**Who it doesn't suit**

If your day job is inventing new retrieval algorithms, altering loss functions or reworking neural architectures, close this tab and go and use open-source libraries like LangGraph or AutoGen. You need the parts, not a finished car. I'd say the same to your face.

**The second place I'd talk you out of it** is latency. Agentic systems plan, retrieve, check their own work and retrieve again. That costs tokens and time. One preprint I read (Ferrazzi and colleagues, submitted January 2026 and revised April, so treat it as early) compared agentic and enhanced RAG. Its agentic setup needed an average of 3.3 times the input tokens and 1.9 times the output tokens, took about 1.5 times longer, and the authors put the cost at up to 3.6 times higher. They also concluded that a well-optimised enhanced RAG can match or exceed agentic performance while remaining more efficient. Take that seriously. If your users need an answer in under a second, a simpler pipeline is the right call and I'll happily lose the sale.

So when is the extra cost worth paying? When the question is the kind above. Four things decide it for me.

**1. Internal and external, in one pass.** Progress Agentic RAG's Smart Agent now includes a built-in web search tool, currently backed by Perplexity and Google Gemini. An agent can hold your isolated trial report next to a newly published finding and answer in a single response, with citations either way. Before this, someone did that by hand with two browser tabs and a lot of coffee.

**2. It has to be allowed to say no.** In research, a confident wrong answer does more damage than a blank one. Progress Agentic RAG scores interactions with REMi, an open-source evaluation model. Two of its measures matter most here. Groundedness asks whether the answer is supported by what was retrieved. Context Relevance asks a simpler thing: did retrieval match the question? A low groundedness score is logged as a hallucination event, which is a far better thing to have in an audit trail than a shrug. The product page describes the intent as an AI that says no: surfacing questions without enough context, so the system conjectures less when the knowledge isn't there.

**3. Messy inputs.** It ingests over 30 file formats, including documents, spreadsheets, audio and video, and enriches them with semantic chunking, entity extraction, labelling and metadata. Research material is never tidy. Half of it lives in a recording nobody transcribed.

**4. Permissions.** This is the one I'd press hardest on in a demo. Progress Agentic RAG encrypts data at rest with AES-256 and in transit with TLS, and lists SOC 2, ISO 27001 and GDPR on its security documentation. For access control, when your application passes the user's security groups with the query and enforcement is switched on, retrieval is scoped to authorised resources and anything outside that scope never enters the context window. Read the small print, though: the documentation says that when you sync content from a third-party service, the original access rights aren't preserved. Map your permissions deliberately. An agent that surfaces restricted molecular or financial data to the wrong person is a worse problem than no agent.

One more data point, and I want to keep two things apart. The benchmark is independent: MADQA is Snowflake AI Research's work, built with Oxford, UNC-Chapel Hill, CVC and Hugging Face. It has 2,250 human-written questions over 800 real documents, and it grades the whole search trajectory, every query and page view, rather than only the final answer. I like that it punishes lucky guesses. The rank is a different matter. In August we published that Progress Agentic RAG ranked first on it, and that is our claim, not a third party's. Go and check the board yourself.

Here's my actual opinion, and it's a slightly uncomfortable one for someone in my seat. Most research teams that say they want an agent want a better search bar with receipts. If that's you, buy the simplest thing that cites its sources. Reach for agentic retrieval only when your questions genuinely span sources and the answer has to survive a reviewer.

If you're weighing this up, two questions will tell you more than any feature list.

What specific compliance or security standards does your research pipeline have to meet — HIPAA, strict IP protection, something your sponsor imposed?

And are your researchers working with highly structured telemetry data, SQL or OpenEdge tables, alongside the unstructured text?

---

## NOT FOR PUBLICATION - verification record

Checked 10 Oct 2026 by live fetch (the nuclia-mcp connector's one search returned only a generic no-answer sentence; everything below rests on the live pages).

| Claim in article | URL | What the page actually said | Checked |
|---|---|---|---|
| Smart Agent built-in web search, Perplexity and Gemini, internal plus external, citations | progress.com/blogs/smart-agent-is-here--retrieval-that-plans--verifies--and-reaches-beyond-your-knowledge | "Smart Agent now includes a built-in web search tool — currently backed by Perplexity and Google Gemini"; "answers that combine internal and external context in a single response"; "and still comes back with citations either way". Dated 2 Oct 2026 | 10 Oct 2026 |
| REMi measures; groundedness / context relevance definitions; low groundedness = logged hallucination | progress.com/blogs/ai-governance-and-auditability-benefits-in-progress-agentic-rag | "Groundedness asks whether the generated answer is supported by what was retrieved. A low score is a logged hallucination event."; "Context Relevance measures whether the documents retrieved matched what the user asked."; REMi "an open-source evaluation model scoring every interaction across three failure modes called the RAG Triad" | 10 Oct 2026 |
| "Says no" / less conjecture | progress.com/agentic-rag/features/remi-rag-evaluation-model | "AI That Says 'No'"; surfaces questions lacking sufficient context, "resulting in less conjecture by the system when knowledge is missing". The page gives NO configuration instructions, so the draft says "describes the intent" and does NOT claim a configurable refusal | 10 Oct 2026 |
| 30+ formats, documents/spreadsheets/audio/video | progress.com/agentic-rag | "Ingest 30+ file formats, including documents, spreadsheets, audio, video and more" | 10 Oct 2026 |
| Semantic chunking, entity extraction, labelling, metadata | progress.com/blogs/what-is-agentic-rag | "This includes semantic chunking, entity extraction, labeling and metadata enrichment." (posted 19 Nov 2025). That page does NOT state 30+ formats or token multipliers | 10 Oct 2026 |
| AES-256 at rest, TLS in transit | docs.rag.progress.cloud/docs/management/security/overview/ | "encrypted using Advanced Encryption Standard (AES-256)"; TLS in transit | 10 Oct 2026 |
| SOC 2, ISO 27001, GDPR | same docs page | Lists GDPR, "SOC 2", ISO 27001. "SOC 2 Type II" is NOT on the docs page (it is on progress.com/agentic-rag: "SOC 2 Type II and ISO 27001"); article uses plain "SOC 2" as the safer wording. HIPAA is NOT stated anywhere checked | 10 Oct 2026 |
| Permission-scoped retrieval | ai-governance blog above | "When the application passes user security groups with the query and enables enforce_security, retrieval scopes to authorized resources. Documents outside that scope never enter the context window." | 10 Oct 2026 |
| Third-party sync caveat | docs security overview | Original access rights are not preserved on sync; Reader or higher can view all contents (paraphrased in article) | 10 Oct 2026 |
| Token/cost figures | arxiv.org/html/2601.07711v2 (current, revised 20 Apr 2026; Ferrazzi, Cvjeticanin, Piraccini, Giannuzzi, "Is Agentic RAG worth it?") | Per the lead's read of v2 body: "an average of 3.3x more input tokens" and "1.9x more output tokens among datasets"; "1.5x more time" averaged; conclusion: "Agentic RAG is systematically more expensive - up to 3.6 times more"; "a well-optimized Enhanced RAG can match or exceed Agentic performance while remaining more efficient". Article uses the averages for tokens and 3.6x for cost only (3.6x is also CQADupStack-EN input ratio in Table 9 - not stated twice). TRAPS: the abstract carries NO figures in either version; figures live in the body; v1 carried different per-dataset numbers (CQADupStack-EN 3.9x/2.0x vs 3.6x/1.8x in v2), so the version matters. The earlier brief "1.7x-3.6x" blended metrics. | 10 Oct 2026 |
| MADQA #1 (Progress's own claim) | progress.com/blogs/how-progress-agentic-rag-reached--1-on-the-snowflake-madqa-leaderboard | "officially ranked as the #1 top result on the Snowflake MADQA Leaderboard"; dated 7 Aug 2026; 2,250 questions, 800 documents; no scores published. Public leaderboard (huggingface.co/spaces/Snowflake/MADQA-Leaderboard) is JS-rendered; I could NOT read the table, so rank is attributed to Progress only | 10 Oct 2026 |
| Answer Relevance (NOT in article, deliberately) | ai-governance blog above | REMi's RAG Triad includes Answer Relevance as well as Groundedness and Context Relevance. Deliberately not surfaced: this factory measured it as unstable (CLAUDE.md, REMi note). Do not restore it on a later pass. Article says 'two of its measures matter most here', which is accurate | 10 Oct 2026 |
| MADQA provenance (independent) | arxiv.org/abs/2603.12180 (per independent claim-check; I did not fetch it) | MADQA is Snowflake AI Research with Oxford, UNC-Chapel Hill, CVC and Hugging Face. Benchmark independent; Progress's rank on it is Progress's own published claim. Neither of us could read the client-side leaderboard, so nothing implies what it currently shows | 10 Oct 2026 |
| ISO 27001 wording (do not strengthen) | docs security overview | Docs say the product 'adheres to' ISO 27001; no certificate or issuing body named. Article says Progress 'lists SOC 2, ISO 27001 and GDPR on its security documentation' - report what is listed, never 'certified'. Keep plain 'SOC 2' | 10 Oct 2026 |
