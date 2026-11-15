"""Measure, never assert: does walking the graph make an answer better than a plain ask?

Three arms per question, same pinned cheap model, same question:
  plain   - /ask as the app's own front door does it
  context - /ask with the walked relations passed as extra_context (no retrieval change)
  scoped  - /ask restricted to the pages the walk reached, plus the same extra_context
Reports sections and distinct pages cited per arm. Cost: 3 ask calls per question on the pinned flash-lite model.
"""
import asyncio, json, sys
from pathlib import Path
import httpx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seed.gk import KB_URL, H
from graphwalk import expand_page, PAGES, section

CASES = [
 ("study/international-students", "I'm an international student. What English test scores, scholarships and visa or health cover costs should I plan for?"),
 ("explore/life-culture/art-collection", "I'm studying at the Perth campus. What can I use outside class: housing, wellbeing support and sport?"),
 ("research/research-ethics-and-integrity", "I'm a PhD candidate working with animals. Which ethics approvals do I need and where can I get support?"),
 ("study/scholarships", "What funding and support exists for Aboriginal and Torres Strait Islander students, from entry to research?"),
 ("study/courses/study-areas", "How do veterinary students get hands-on experience, and what funding exists for them?"),
]
if "--round2" in sys.argv:
    # Round 2: start pages and questions fixed BEFORE reading round-1 answers; round 1 case 2 started on a
    # page the graph could barely read (the art-collection hole), which says nothing about the graph.
    CASES = [
     ("study/international-students", "I'm an international student. What English test scores, scholarships and visa or health cover costs should I plan for?"),
     ("explore/support-services", "I'm studying at the Perth campus. What can I use outside class: housing, wellbeing support and sport?"),
     ("study/fees", "I'm an international postgraduate. What will my first year cost and what scholarships could reduce it?"),
     ("research/research-ethics-and-integrity", "I'm a PhD candidate working with animals. Which ethics approvals do I need and where can I get support?"),
     ("study/scholarships", "What funding and support exists for Aboriginal and Torres Strait Islander students, from entry to research?"),
    ]
RUN = "compare_run2.json" if "--round2" in sys.argv else "compare_run.json"

def pid_for(path):
    for i, p in PAGES.items():
        if p["url"].rstrip("/").endswith("/" + path): return i
    raise SystemExit("no page " + path)

async def ask(c, q, extra=None, ids=None):
    body = {"query": q, "generative_model": "gemini-3.1-flash-lite", "citations": True}
    if extra: body["extra_context"] = extra
    if ids: body["resource_filters"] = ids
    r = await c.post(f"{KB_URL}/ask", json=body, headers=H, timeout=90)
    d = r.json()
    cites = {k.split("/")[0] for k in (d.get("citations") or {})}
    return {"status": d.get("status"), "answer": d.get("answer") or "", "cited": sorted(cites)}

async def main():
    out = []
    async with httpx.AsyncClient() as c:
        for path, q in CASES:
            pid = pid_for(path)
            ex = await expand_page(c, KB_URL, H, pid)
            ctx, ids = [], {pid}
            for l in ex["links"][:5]:
                names = [p["title"] for p in l["pages"][:4]]
                ctx.append(f"In the University site graph, '{ex['page']['title']}' and these pages are connected because they share the {l['kind'].lower()} '{l['value']}': " + "; ".join(names) + ".")
                ids |= {p["id"] for p in l["pages"][:4]}
            plain = await ask(c, q)
            context = await ask(c, q, extra=ctx)
            scoped = await ask(c, q, extra=ctx, ids=sorted(ids))
            row = {"start": ex["page"]["title"], "q": q, "walked_pages": len(ids), "arms": {}}
            for name, a in (("plain", plain), ("context", context), ("scoped", scoped)):
                row["arms"][name] = {"status": a["status"], "cited_pages": len(a["cited"]), "cited_sections": sorted({section(i) for i in a["cited"]}),
                                     "words": len(a["answer"].split()), "answer": a["answer"]}
            out.append(row)
            print(row["start"], "|", {k: (v["cited_pages"], v["cited_sections"]) for k, v in row["arms"].items()}, flush=True)
    Path(__file__).parent.parent.joinpath("graph", RUN).write_text(json.dumps(out, indent=1))
asyncio.run(main())
