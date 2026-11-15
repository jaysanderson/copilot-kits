"""Presenter run-sheet at /run: what to open, type and expect for each surface, in running order.

Add-only module, one route and one template. Unlinked from every public surface. Content is operational
only (what a surface does, what to type, what to expect); it holds no credentials and makes no call.
Every question below was run against the live demo on 9 Oct 2026 or is a suggested question the surface
itself offers. Keep it current with the surfaces: a caution that has been fixed must be removed here.
"""
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def ans(q: str, lang: str) -> str:
    return f"/answers?q={quote(q)}&lang={lang}"


def Q(text: str, lang: str = "en", prefill: bool = False, label: str = "") -> dict:
    return {"text": text, "lang": lang, "dir": "rtl" if lang == "ar" else "ltr",
            "label": label or {"en": "English", "zh": "Chinese", "ar": "Arabic", "id": "Bahasa Indonesia"}[lang],
            "open": ans(text, lang) if prefill else ""}


APPLY = "How do I apply as an international student?"
STEPS = [
    {"n": "1", "title": "Open on their homepage", "id": "home",
     "does": "Shows the site visitors already use, with one change: a question box.",
     "where": [("Homepage", "/")], "type": [],
     "expect": "The homepage loads as the university's own. Nothing on screen names the platform.",
     "say": ["This is your homepage. The only thing we have changed is that you can ask it something."]},
    {"n": "2", "title": "Ask a real student question", "id": "ask",
     "does": "A cited answer, built from the university's own pages, with the pages it searched shown first.",
     "where": [("Open the pre-filled conversation", ans(APPLY, "en"))], "type": [Q(APPLY, "en", True)],
     "expect": "The pages searched appear in about a second, with their photographs. The answer writes itself behind them and is complete in roughly ten seconds. Numbered citations sit at the claims. Below the answer, \"Where to next\" buttons link to the university's own live pages, and only appear when the answer named something. A follow-up question keeps the conversation.",
     "say": ["Those are the pages it searched, live, on your site.",
             "Every one of those numbers is a link to your page. It is telling them what University says.",
             "It answered the question, and moved them one click closer to applying."]},
    {"n": "3", "title": "Ask in Arabic", "id": "arabic",
     "does": "Answers in the visitor's own language from English pages, with nothing translated in advance.",
     "where": [("Open in Arabic", ans("كيف أتقدم بطلب كطالب دولي؟", "ar"))],
     "type": [Q("كيف أتقدم بطلب كطالب دولي؟", "ar", True), Q("ما هي المنح الدراسية المتاحة للطلاب الدوليين؟", "ar", True, "Arabic, scholarships"),
              Q("国际学生如何申请？", "zh", True), Q("Bagaimana cara mendaftar sebagai mahasiswa internasional?", "id", True)],
     "expect": "The answer comes back in Arabic, right to left, citing the same English pages, in about the same time as English. Pause and let the room read it. The Chinese and Bahasa Indonesia links do the same in those languages.",
     "say": ["Your website is in English. Your corpus is in English. Nobody translated anything.",
             "A student in Dubai asks in Arabic and gets your answer, citing your pages."]},
    {"n": "4", "title": "Ask something it cannot answer", "id": "decline",
     "does": "Declines honestly when the university's content does not cover the question.",
     "where": [("Open the pre-filled conversation", ans("What is the best pizza restaurant near the Perth campus?", "en"))],
     "type": [Q("What is the best pizza restaurant near the Perth campus?", "en", True)],
     "expect": "After roughly eight seconds it declines and offers a contact route. No answer text and no sources appear.",
     "say": ["It did not invent a plausible answer. If it cannot ground it in your content, it says so."]},
    {"n": "5", "title": "Open \"How this works\"", "id": "reveal",
     "does": "Shows this surface's real request flow: browser, the app's own server, the platform, the answer with its sources.",
     "where": [("Any page, button at the top right", "/")], "type": [],
     "expect": "A panel opens with the architecture. It is the one place the product is named, on purpose.",
     "say": ["This is the whole architecture. Your browser, our proxy, Progress Agentic RAG against your content, the answer with its sources."]},
    {"n": "6", "title": "The veterinary portal", "id": "vet",
     "does": "The same platform for a different audience: a faculty's protocols, case material and teaching notes.",
     "where": [("Open the veterinary portal, then Ask (new site)", "/faculty")],
     "type": [Q("How is a horse with fever and neurological signs isolated and sampled?"),
              Q("How many hours can a student work on clinical rotation before fatigue rules apply, and what are the rest requirements?")],
     "expect": "You can type freely here. While the answer is written the portal shows its own working steps: Reading your question, Searching the corpus, Writing the answer, Checking the figures, Scoring the answer, with the documents it is reading named underneath. The answer is complete in roughly seven to twelve seconds. Both questions above were run on the live portal and returned a cited answer. The banner on the page says the content is synthetic.",
     "say": ["Same platform, different problem, different audience.",
             "That is the platform showing its working while it answers, not a spinner.",
             "This content is invented, and it says so. Give us yours and this is a week's work, not a project."]},
    {"n": "6b", "title": "Open the answer quality disclosure", "id": "quality",
     "does": "The platform scores its own answer and shows the working, so a reader can see how firmly the answer is supported before relying on it.",
     "where": [("Open the veterinary portal, then Ask (new site)", "/faculty")],
     "type": [Q("Which antimicrobial classes need senior approval before dispensing?")],
     "expect": ["Once an answer returns, find the small icon on the answer's action row: the first of the three icons on the right, ahead of copy and retry.",
                "Three looks: a quiet grey shield with a tick means high confidence, an amber triangle means moderate, and only a low score spells itself out in words and colour. A low score was not seen in testing.",
                "Click it. It opens a headline such as Moderate confidence, the portal's own check of the answer against the cited texts, and three five-segment meters: Relevance, Groundedness and Context.",
                "Two different assessments back to back: on 9 October 2026 the horse question in step 6 gave the grey shield on both runs, with a green \"1 figure checked\" chip beside it, and the question above gave the amber triangle on both runs. That is the usual result, not a guarantee, so check the icon before relying on it.",
                "On the right, \"Retrieved, but not cited in the answer\" lists passages the search found and the answer did not use, each with a match percentage. \"Show retrieved sources\" under the answer shows the same, with a count such as 7 retrieved, 1 cited."],
     "say": ["The platform scores its own answer and shows the working.",
             "There are two checks here. The platform's own score, and the portal's check of the figures against the cited texts. They can disagree, and when they do it tells you.",
             "This is not an accuracy figure. It is the platform's assessment of how firmly this answer is supported, shown beside the sources so you can judge it yourself."]},
    {"n": "7", "title": "Ask inside one section", "id": "hubs",
     "does": "The ask placed in the middle of a section page, answering only from that section.",
     "where": [("Scholarships", "/section/scholarships"), ("How to apply", "/section/how-to-apply"), ("International students", "/section/international")],
     "type": [Q("What scholarships are available for international students?"), Q("ما المنح الدراسية المتاحة للطلاب الدوليين؟", "ar")],
     "expect": "The suggested questions on the page also work, and follow the language you pick. The answer opens in place, with a chip saying it comes from this section only. Every source sits inside the section. The button at the top goes to the university's own page.",
     "say": ["The same ask, limited to one section of the site. The official page is one click away."]},
    {"n": "8", "title": "The builder's kit", "id": "embed",
     "does": "The ask as two lines of HTML that a web team pastes into any page, on a site that looks nothing like the university's.",
     "where": [("Open the embed demonstration", "/embed")],
     "type": [Q("What counselling and wellbeing support services does University offer?")],
     "expect": "Type the same question into both boxes. The left box answers from across the site. The right box is scoped to one section, so its sources differ. The page also shows the two pasted lines and which attributes change what.",
     "say": ["Two lines of HTML. Your brand, your languages, your scope.",
             "There is no key, no token and no endpoint name in anything the page downloads."]},
    {"n": "9", "title": "Browse by what pages share", "id": "wander", "optional": "If someone owns the website",
     "does": "Finding pages without knowing the right words, by following the topics pages share rather than the menu.",
     "where": [("Open the graph", "/wander")], "type": [],
     "expect": "Start from a suggested page and follow the shared threads. The page computes and shows its own figures from the crawl, so read the numbers off the screen rather than from memory.",
     "say": ["Your menu is a filing cabinet. These threads cross it.", "Those figures are computed live from the crawl, not typed into a slide."]},
    {"n": "10", "title": "Ask a single page", "id": "page", "optional": "If the room wants to see depth on one document",
     "does": "Talking to one page, with the passage the answer used highlighted in the page body.",
     "where": [("Open the page view", "/page"), ("Scholarships page", "/page?p=scholarships")], "type": [],
     "expect": "Pick a page, then use the suggested questions shown for it. The answer highlights its quotes in the page.",
     "say": ["Same engine, pointed at one page. The answer shows the passage it came from."]},
    {"n": "11", "title": "What people were trying to find out", "id": "insights",
     "does": "The questions visitors asked, in their own words and languages, and where the content did not answer them.",
     "where": [("Open the insights view", "/insights")], "type": [],
     "expect": "Rows tagged as team traffic are counted separately and labelled. Questions you asked earlier in the session appear as direct rows. The page states what it stores and what it does not.",
     "say": ["Your analytics tell you which pages were visited. This tells you what people were trying to find out, and where your content did not answer them.",
             "We drove most of these ourselves, and the page labels every one of them. What you are looking at is the shape.",
             "The question I asked five minutes ago is in this list."]},
    {"n": "12", "title": "Close on their content", "id": "close",
     "does": "Moves from the demonstration to an evaluation on the university's own material.",
     "where": [], "type": [], "expect": "No surface. Say it and stop.",
     "say": ["Everything you have seen ran on your own public pages, crawled once, with nothing tuned for this meeting. Give us a corpus you actually care about, and we will stand it up on your content so you can judge it on your own material."]},
]
KEEP = [
    "Do not quote an accuracy percentage. The platform publishes none. Point at the citations and offer to run it on their content.",
    "Do not name another customer or quote revenue or pipeline.",
    "Do not promise that source documents stay with the customer in a hybrid deployment. Progress has told us what runs in its cloud, not where source documents are stored.",
    "Stay inside the University portal on the veterinary site. Other demonstrations share that host.",
    "The veterinary content is synthetic and says so on every page. Say it before anyone asks.",
    "Describe the answer-quality meters as the platform's own self-assessment. Never call them accuracy, and never quote a score or percentage as a measure of correctness.",
]

router = APIRouter()


@router.get("/run", response_class=HTMLResponse)
async def run_sheet(request: Request):
    return templates.TemplateResponse(request, "run.html", {"steps": STEPS, "keep": KEEP},
                                      headers={"X-Robots-Tag": "noindex, nofollow", "Cache-Control": "no-cache"})
