"""Collect REAL markdown as the product emits it (model answers on three surfaces, page bodies from the
crawl) into tests/md_fixture.json. Run with the app's venv from apps/university-demo. Costs ~25 answers."""
import json, re, sys, asyncio
sys.path.insert(0, ".")
import httpx, os
import app as A, pagemode as P
from fastapi.testclient import TestClient
c = TestClient(A.app)
items = []
def add(kind, lang, text):
    if text and text.strip() and not any(i["text"] == text for i in items):
        items.append({"kind": kind, "lang": lang, "text": text})
PQ = [("apply", "Who can help me?", "en"), ("apply", "من يمكنه مساعدتي؟", "ar"), ("apply", "有谁可以帮助我？", "zh"),
      ("scholarships", "Who can I contact?", "en"), ("scholarships", "Bagaimana mencari pendanaan?", "id"),
      ("international", "ما المنح المتاحة؟", "ar"), ("international", "What support is there for international students?", "en"),
      ("perth", "校园里有哪些帮助？", "zh"), ("perth", "How do I get to the campus?", "en"), ("perth", "ما هي المرافق الصحية؟", "ar")]
for k, q, l in PQ:
    d = c.post("/api/page-ask", json={"page": k, "q": q, "lang": l}).json()
    add("page-answer", l, d.get("answer"))
HQ = [("What are the tuition fees and is there a calculator?", "en"), ("Who do I contact about entry requirements?", "en"),
      ("ما هي رسوم الدراسة وكيف أتصل بكم؟", "ar"), ("如何联系国际学生团队？", "zh"), ("What scholarships are there?", "en")]
for q, l in HQ:
    d = c.post("/api/answer", json={"q": q, "lang": l}).json()
    add("home-answer", l, d.get("answer"))
s = c.post("/api/wander/start", json={"q": "tuition fees"}).json()
ids = [p["id"] for p in s.get("pages", [])][:4]
for q in ["What are the fees and how do I calculate them?", "Who do I contact?"]:
    d = c.post("/api/wander/answer", json={"q": q, "ids": ids, "context": []}).json()
    add("wander-answer", "en", d.get("answer"))
async def pages():
    async with httpx.AsyncClient() as cl:
        for k in P.PAGES:
            p = await P.load_page(cl, A.KB_URL, A.HEADERS, k)
            lo, hi = p["blocks"][0]["s"], p["blocks"][-1]["e"]
            raw = p["full"][lo:hi]
            for blk in re.split(r"\n\s*\n", raw):
                if re.search(r"^#{1,6}\s|\\[*_#]|\]\(|^\s*[*+-]\s", blk, re.M):
                    add("page-body", "en", blk)
asyncio.run(pages())
json.dump(items, open("tests/md_fixture.json", "w"), ensure_ascii=False, indent=1)
from collections import Counter
print(len(items), Counter(i["kind"] for i in items))
