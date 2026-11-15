"""Section hubs: a landing page for one part of the University site with the ask widget mounted inline.

Add-only module. The page list is the knowledge base's own page directory (graphwalk.PAGES, built from
the crawled pages), filtered by URL path. The ask is the shared widget calling /api/answer with the
section's allow-listed scope; scoping and the cited-source cross-check are enforced server-side in app.py.
The keys here MUST be keys of app.SCOPES.
"""
import re

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

import graphwalk as gw

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# key -> display name, URL path prefix, the section's real home on university.edu.au, lead sentence,
# and starter questions in the widget's four languages (user-side input, not claims).
HUBS = {
    "scholarships": {
        "name": "Scholarships", "prefix": "study/scholarships", "home": "https://www.university.edu.au/study/scholarships",
        "lead": "Ask about scholarships and the answer is drawn only from the Scholarships pages.",
        "chips": {
            "en": ["What scholarships are available for international students?", "How do I apply for a scholarship?", "Are there scholarships for research degrees?"],
            "zh": ["国际学生有哪些奖学金？", "如何申请奖学金？", "研究型学位有奖学金吗？"],
            "ar": ["ما المنح الدراسية المتاحة للطلاب الدوليين؟", "كيف أتقدم بطلب للحصول على منحة دراسية؟", "هل توجد منح للدرجات البحثية؟"],
            "id": ["Beasiswa apa yang tersedia untuk mahasiswa internasional?", "Bagaimana cara mengajukan beasiswa?", "Apakah ada beasiswa untuk program riset?"],
        },
    },
    "how-to-apply": {
        "name": "How to apply", "prefix": "study/how-to-apply", "home": "https://www.university.edu.au/study/how-to-apply",
        "lead": "Ask about applying and the answer is drawn only from the How to apply pages.",
        "chips": {
            "en": ["What are the entry requirements for undergraduate study?", "How do I accept my offer?", "What are the English language requirements?"],
            "zh": ["本科入学要求是什么？", "如何接受录取通知？", "英语语言要求是什么？"],
            "ar": ["ما شروط القبول للدراسة الجامعية؟", "كيف أقبل العرض الذي حصلت عليه؟", "ما متطلبات اللغة الإنجليزية؟"],
            "id": ["Apa persyaratan masuk untuk program sarjana?", "Bagaimana cara menerima tawaran saya?", "Apa persyaratan bahasa Inggris?"],
        },
    },
    "international": {
        "name": "International students", "prefix": "study/international-students", "home": "https://www.university.edu.au/study/international-students",
        "lead": "Ask about studying from overseas and the answer is drawn only from the International students pages.",
        "chips": {
            "en": ["How do I apply as an international student?", "What is life on campus like?", "Can I work while I study?"],
            "zh": ["国际学生如何申请？", "校园生活是什么样的？", "我可以边学习边工作吗？"],
            "ar": ["كيف أتقدم بطلب كطالب دولي؟", "كيف تبدو الحياة في الحرم الجامعي؟", "هل يمكنني العمل أثناء الدراسة؟"],
            "id": ["Bagaimana cara mendaftar sebagai mahasiswa internasional?", "Seperti apa kehidupan di kampus?", "Bisakah saya bekerja saat kuliah?"],
        },
    },
}


def section_pages(prefix: str) -> list:
    out = {}
    for p in gw.PAGES.values():
        if p.get("alias"):
            continue
        path = "/".join(p["url"].split("/")[3:]).strip("/")
        if path == prefix or path.startswith(prefix + "/"):
            title = re.sub(r"\s*\|\s*The university\s*$", "", p.get("title") or "").strip() or path
            out[p["url"]] = {"title": title, "url": p["url"]}
    return sorted(out.values(), key=lambda x: x["title"].lower())


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/section/{key}", response_class=HTMLResponse)
    async def section_hub(request: Request, key: str):
        hub = HUBS.get(key)
        if not hub:
            return RedirectResponse("/", status_code=307)
        pages = section_pages(hub["prefix"])
        return templates.TemplateResponse(request, "section.html", {"key": key, "hub": hub, "pages": pages, "hubs": HUBS})

    return router


router = build_router()
