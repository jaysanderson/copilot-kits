"""Clinic Knowledge Desk - demo application.

Every answer on every surface is produced by a live call to Progress Agentic
RAG over Clinic's own published website content. The retrieval credential is
held server side only; the browser talks to this application's API and nothing
else.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

import arag  # noqa: E402  (needs the environment loaded first)
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

app = FastAPI(title="Clinic Knowledge Desk", docs_url=None, redoc_url=None)

INDEX = json.loads((ROOT / "corpus" / "index.json").read_text())
BY_RID = {d["rid"]: d for d in INDEX}
BY_URL = {d["url"]: d for d in INDEX}

ROUTES = ["/", "/vac-desk", "/surgeon-desk", "/market-access", "/claim-check", "/investor-signal",
          "/patient-guide", "/evidence-library"]

# ---------------------------------------------------------------- taxonomy
THEMES = [
    ("Regulatory and approvals", r"approval|clearance|\bfda\b|\btga\b|ce mark|registration|regulatory|510\(k\)|mdsap|iso 13485|licence|license|artg|health canada|\bmhra\b|reimbursement|tariff"),
    ("Intellectual property", r"patent|trademark|intellectual property"),
    ("Market entry and commercial", r"launch|distribut|sales|commercial|agreement|market|order|revenue|contract|partner|supply|expansion|momentum"),
    ("Clinical and evidence", r"clinical|trial|stud(y|ies)|publication|journal|surgeon|surgical|patient outcome|evidence|first case|implant|treat|therapy|repair|result"),
    ("Capital and corporate", r"placement|capital|share|entitlement|\bagm\b|appendix|annual report|quarterly|investor|director|financial|raise|cash flow|notice of meeting|board|appoint"),
    ("Manufacturing and operations", r"manufactur|facility|capacity|production|cleanroom|scale-up"),
    ("Media and analyst coverage", r"interview|podcast|\bmedia\b|\bvideo\b|coverage|equity research|research report|\bnews\b|crucible|spotlight|featured"),
    ("Recognition and events", r"award|conference|symposium|webinar|finalist|honour|honor|presents?\b|presentation"),
]


def theme_of(title: str) -> str:
    t = (title or "").lower()
    for name, pat in THEMES:
        if re.search(pat, t):
            return name
    return "Company update"


for _d in INDEX:
    _d["theme"] = theme_of(_d["title"]) if _d["doctype"] == "Announcement" else None

ANNOUNCEMENTS = sorted([d for d in INDEX if d["doctype"] == "Announcement" and d.get("date")],
                       key=lambda d: d["date"], reverse=True)

PRODUCTS = ["Remplir", "Striate+", "OrthoACI", "OrthoATI", "SMRTGRAFT"]


def _sources_payload(items: list[dict]) -> list[dict]:
    out = []
    top = max((s.get("score") or 0) for s in items) if items else 0
    for s in items:
        known = BY_RID.get(s.get("rid", "")) or BY_URL.get(s.get("url", "")) or {}
        title = s.get("title") or known.get("title") or "Clinic published page"
        url = s.get("url") or known.get("url") or ""
        # never render a raw internal key - fall back to the seeded record
        if not title or re.match(r"^[0-9a-f]{16,}", title):
            title = known.get("title", "Clinic published page")
        out.append({
            "title": title,
            "url": url,
            "excerpt": arag.tidy(s.get("excerpt", "") or known.get("excerpt", "")),
            "relevance": (round((s.get("score") or 0) / top, 3) if top else None),
            "doctype": known.get("doctype"),
            "products": known.get("products", []),
            "date": known.get("date"),
        })
    return out


# ------------------------------------------------------------------ models
class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=400)


class ClaimIn(BaseModel):
    claim: str = Field(min_length=8, max_length=600)


class MarketIn(BaseModel):
    product: str


class DigestIn(BaseModel):
    theme: str
    period: str | None = None


class SearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=200)
    product: str | None = None
    doctype: str | None = None
    audience: str | None = None


# ------------------------------------------------------------------ helpers
def support_contexts(sources: list[dict], paragraphs: list[str], limit: int = 10) -> list[str]:
    """Context set for the support check.

    Built from the BODIES of the retrieved pages, not only the scored paragraphs:
    a short page can genuinely ground an answer while contributing no scored
    paragraph, which makes a paragraph-only context set score a good answer badly.
    """
    out: list[str] = []
    for s in sources[:limit]:
        rec = BY_RID.get(s.get("rid", ""))
        body = (rec or {}).get("body") or s.get("excerpt") or ""
        if body:
            out.append(body[:3500])
    for p in paragraphs:
        if len(out) >= limit + 4:
            break
        out.append(p)
    return out


# ---------------------------------------------------- access-scoping guard
# A label filter is layer one and it can fail open: the grounded answer call
# does not honour filter_expression as reliably as retrieval does, so an
# excluded page can still ground an answer, intermittently. Layer two checks
# server-side what ACTUALLY grounded the answer and withholds the whole
# response if anything outside the entitlement did.
SCOPE_FIELD = {"Audience": "audience", "Document type": "doctype",
               "Product": "products", "Region": "region"}


def allowed_rids(pairs: list[tuple[str, str]]) -> set[str]:
    """The resources an entitlement genuinely covers, from the loaded record.

    Derived from the same (labelset, label) pairs that build the filter, so the
    guard and the filter cannot drift apart.
    """
    out = set()
    for d in INDEX:
        for labelset, label in pairs:
            value = d.get(SCOPE_FIELD.get(labelset, ""), None)
            if (label in value) if isinstance(value, list) else (value == label):
                out.add(d["rid"])
                break
    return out


def grounding_rids(data: dict) -> set[str]:
    """Every resource that contributed to this answer.

    Both halves matter: the citations are what the answer drew on, and the
    retrieval results are what sat in its context window. A context-expanding
    strategy can also cite a paragraph the retrieval event never listed, so the
    citation keys are parsed rather than looked up.
    """
    rids = set()
    for key in (data.get("citations") or {}):
        head = str(key).split("/")[0].strip()
        if head:
            rids.add(head)
    rids.update((data.get("retrieval_results") or {}).get("resources", {}).keys())
    return rids


def declined(answer: str, reason: str, scoped: bool) -> dict:
    """The ONE way this application emits a declined answer.

    Both decline reasons route through here, so no call site CAN emit a decline
    that still carries sources, sentences, a support reading or a confidence
    badge. That is the point of it being a function rather than a rule: the
    scope path was built this way from the start and the model-refusal path was
    not, so a refusal came back with the entire retrieved payload attached. On
    the patient desk that rendered a panel headed "Sources read for this
    answer" beneath a refusal about which hospitals offer the procedure, and
    the first card's excerpt named a real hospital and a real surgeon. Nothing
    was fabricated; a true sentence standing beside a withheld answer reads as
    the answer, and a patient reads those cards as the list they just asked
    for. Removing the option is what stops a third surface repeating it.

    The two events stay distinguishable, because they mean different things:
      "not_published" - the published material does not state it.
      "scope"         - it does, elsewhere, and this surface does not read that
                        part. Carrying the refusal's own "NOT IN PUBLISHED
                        CONTENT" prefix here would put a false claim in the
                        payload, so the client is TOLD which event this is
                        rather than pattern-matching the answer text.
    """
    return {
        "answer": answer,
        "sentences": [], "matched": 0, "statements": 0, "sources": [],
        "confidence": {"label": "Answer withheld", "tone": "unknown", "detail": ""},
        "retrieved": 0, "grounded_in": 0, "withheld": True,
        "decline": reason, "scoped": scoped,
    }


async def grounded_answer(question: str, filt=None, prompt=None, top_k=12,
                          allowed: set[str] | None = None,
                          withhold_reason: str = "", audit: dict | None = None) -> dict:
    data = await arag.ask(question, filt=filt, prompt=prompt, top_k=top_k)

    # Layer two. Runs before anything is composed, so nothing out of scope can
    # reach the response even partially.
    if allowed is not None:
        grounded = grounding_rids(data)
        outside = {r for r in grounded if r not in allowed}
        if audit is not None:
            audit["grounded"] = sorted(grounded)
            audit["outside"] = sorted(outside)
        if outside:
            return declined(withhold_reason or
                            "This is not something the published patient pages cover.",
                            "scope", filt is not None)

    answer = arag.tidy(data.get("answer") or "")

    # The model's own refusal is a decline, and a decline carries nothing. This
    # returns BEFORE anything is composed - the same place and for the same
    # reason as the scope cross-check above - so the sources, the citation
    # alignment, the statement count and the support reading are never even
    # computed for a refusal. Labelling the payload afterwards was the defect:
    # the response was fully composed, honestly labelled `not_published`, and
    # still shipped every retrieved card to the client.
    if answer.upper().startswith("NOT IN PUBLISHED CONTENT"):
        return declined(answer, "not_published", filt is not None)

    sources = arag.resources_from_find(data.get("retrieval_results") or {})
    contexts = support_contexts(sources, arag.contexts_from_ask(data))
    score = await arag.groundedness(question, answer, contexts)
    payload = _sources_payload(sources[:8])
    sentences = arag.place_citations(answer, payload)
    matched = sum(1 for x in sentences if x["source"] is not None)
    return {
        "answer": answer,
        # A scoped surface hands the model a filtered slice, so a decline there
        # can only mean the slice lacked it - it can never speak for the corpus.
        # The renderer needs to know which kind of surface this was.
        "scoped": filt is not None,
        # Unconditionally null: every decline returned above, so reaching here
        # means a real answer. The renderer keys its footer on (scoped, reason)
        # and resolves it only when a decline is actually rendering, so this
        # staying null on a normal answer is load-bearing, not decoration.
        "decline": None,
        "sentences": sentences,
        "matched": matched,
        "statements": len(sentences),
        "sources": payload,
        "confidence": arag.confidence_badge(score),
        "retrieved": len(sources),
        "grounded_in": len(contexts),
    }


DECLINE = ("If the supplied Clinic content does not contain the answer, reply with exactly: "
           "NOT IN PUBLISHED CONTENT - followed by one sentence naming what would be needed. "
           "Never state a clinical outcome, efficacy figure, approval, clearance, indication or "
           "safety conclusion that is not written in the supplied content. Do not infer, estimate "
           "or generalise. Australian English.")


# ------------------------------------------------------------------- routes
@app.get("/api/config")
async def config():
    return {
        "corpus": {
            "documents": len(INDEX),
            "announcements": len(ANNOUNCEMENTS),
            "practitioner": sum(1 for d in INDEX if d["audience"] == "Practitioner"),
            "patient": sum(1 for d in INDEX if d["audience"] == "Patient"),
            "earliest": min((d["date"] for d in ANNOUNCEMENTS if d.get("date")), default=""),
            "latest": max((d["date"] for d in ANNOUNCEMENTS if d.get("date")), default=""),
            "products": {p: sum(1 for d in INDEX if p in d["products"]) for p in PRODUCTS},
        }
    }



# 1 - VAC submission desk --------------------------------------------------
# The hospital approval application in Clinic's own published language is a
# Value Analysis Committee (VAC) submission. Every figure below is transcribed
# from a verbatim sentence in a real Clinic announcement, and every quote is
# re-verified against the loaded corpus at start-up - a point whose quote cannot
# be found in the real page is dropped rather than shown.
VAC_SERIES_RAW = [
    {"date": "2026-01-06", "approvals": 23, "in_progress": 61, "hospitals": None,
     "quote": "Submission of 61 applications to hospital Value Analysis Committees (VAC) in progress, of which 23 have been approved, ahead of schedule",
     "url": "https://clinic.com/clinic-records-seventh-consecutive-quarter-of-record-revenue-at-3-2m/"},
    {"date": "2026-04-19", "approvals": 32, "in_progress": 57, "hospitals": 115,
     "quote": "32 Value Analysis Committee (VAC) approvals secured, providing access to more than 115 hospitals, with a further 57 applications in progress",
     "url": "https://clinic.com/clinic-reports-continued-growth-and-strong-us-momentum-in-march-2026-quarter/"},
    {"date": "2026-07-13", "approvals": 44, "in_progress": 64, "hospitals": 151,
     "quote": "VAC approvals increased 38% to 44, providing access to 151 hospitals, with another 64 applications in progress",
     "url": "https://clinic.com/clinic-delivers-record-quarterly-and-full-year-revenue-as-global-commercial-momentum-accelerates/"},
]


def _verify_quotes(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        rec = BY_URL.get(r["url"]) or {}
        body = re.sub(r"\s+", " ", rec.get("body") or "")
        probe = re.sub(r"\s+", " ", r["quote"])[:70]
        if probe and probe in body:
            out.append({**r, "title": rec.get("title", "")})
    return out


VAC_SERIES = _verify_quotes(VAC_SERIES_RAW)

VAC_CONTEXT_RAW = [
    {"label": "US Department of Defence and Veterans Affairs",
     "quote": "The approval provides access to approximately 51 Department of Defence military hospitals and 170 Veterans Affairs medical centres across the United States.",
     "url": "https://clinic.com/clinic-secures-remplir-approval-across-u-s-department-of-defence-hospital-network/",
     "date": "2026-04-15"},
    {"label": "Submissions in flight, named by their own VP of Sales",
     "quote": "We currently have around 51 Value Analysis Committee (VAC) submissions, including major networks like the Cleveland Clinic.",
     "url": "https://clinic.com/qa-with-john-walker-vp-sales-us/", "date": "2026-07-30"},
]
VAC_CONTEXT = _verify_quotes(VAC_CONTEXT_RAW)

# Generic Value Analysis Committee evaluation criteria - real committee practice,
# not an invented Clinic document.
VAC_QUESTIONS = [
    {"criterion": "Clinical evidence",
     "q": "What published clinical evidence supports the use of Remplir in peripheral nerve repair, and what outcomes were reported?"},
    {"criterion": "Regulatory status",
     "q": "What is the regulatory status of Remplir in the United States, and what does that clearance cover?"},
    {"criterion": "Product and materials",
     "q": "What is Remplir made from, and what material or biological considerations should a committee be aware of?"},
    {"criterion": "Peer adoption",
     "q": "How widely has Remplir been adopted by surgeons and hospitals to date?"},
    {"criterion": "Manufacturing and quality",
     "q": "How is Remplir manufactured, and to what quality management standards?"},
    {"criterion": "Clinical application",
     "q": "In which surgical procedures can Remplir be used, and how is it applied?"},
]

VAC_PROMPT = (
    "You are drafting a response to a hospital Value Analysis Committee evaluating "
    "Clinic's Remplir for formulary approval, using only Clinic's own published "
    "material. Write in the register of a submission response: measured, specific, and "
    "attributable. Give the committee the published figure, publication or regulatory "
    "status where one exists, in the company's own terms. Never state a clinical outcome, "
    "efficacy figure, approval, indication, safety conclusion, price or comparative claim "
    "that is not written in the supplied content. Write the response body only - no "
    "salutation, no sign-off, no headings, two to four short paragraphs. " + DECLINE)

VAC_GAP_PROMPT = (
    "You are the reviewer checking a draft Value Analysis Committee submission response "
    "before it is filed. Identify what a hospital committee would reasonably ask for that "
    "Clinic's PUBLISHED material does not establish - be specific and conservative, and "
    "never assume a gap is filled by material you cannot see. For document types, name only "
    "GENERIC categories of document a submission would attach (for example 'the full "
    "published study', 'the current instructions for use'); never invent a document title, "
    "a hospital name, an application status or a regulatory decision. Australian English.")


@app.get("/api/vac-pipeline")
async def vac_pipeline():
    return {"series": VAC_SERIES, "context": VAC_CONTEXT, "criteria": VAC_QUESTIONS,
            "latest": VAC_SERIES[-1] if VAC_SERIES else None}


class VacIn(BaseModel):
    question: str = Field(min_length=6, max_length=400)


@app.post("/api/vac-desk/draft")
async def vac_draft(body: VacIn):
    """The drafted submission response. Split from the review below so each
    paints as soon as it lands - one slow call can never hide the other."""
    try:
        return await grounded_answer(body.question, prompt=VAC_PROMPT, top_k=16)
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))


@app.post("/api/vac-desk/review")
async def vac_review(body: VacIn):
    """The reviewer pass - what the published evidence does not establish."""
    try:
        found = await arag.find(body.question, top_k=14)
        retrieved = arag.resources_from_find(found)
        # Retrieval never returns empty, so threshold it: a review of nothing is
        # worse than no review.
        if not retrieved or (retrieved[0].get("score") or 0) < 0.35:
            return {"gaps": [], "attachments": [], "strongest_point": "",
                    "strongest_source": None, "declined": True}
        titles = [r["title"] for r in retrieved if r["title"]][:14] or ["No matching published page"]
        schema = {
            "name": "submission_review",
            "parameters": {
                "type": "object",
                "properties": {
                    "gaps": {
                        "type": "array",
                        "description": "What a hospital committee would ask for that the published material does not establish",
                        "items": {"type": "object", "properties": {
                            "gap": {"type": "string"},
                            "why_it_matters": {"type": "string"},
                        }, "required": ["gap", "why_it_matters"]},
                    },
                    "attachments": {
                        "type": "array",
                        "description": "Generic categories of document this submission should attach. Never a specific invented document title.",
                        "items": {"type": "string"},
                    },
                    "strongest_point": {"type": "string",
                                        "description": "The single strongest published sentence for this criterion, copied VERBATIM from the supplied content. Empty string if the content contains none."},
                    "source_title": {"type": "string", "enum": titles},
                },
                "required": ["gaps", "attachments", "strongest_point", "source_title"],
            },
        }
        review = await arag.ask_structured(
            f"Review a draft Value Analysis Committee submission response to: {body.question}",
            schema, prompt=VAC_GAP_PROMPT, top_k=14)
        parsed = review.get("answer_json") or {}

        # The reviewer is a SECOND generative call, so it gets the same
        # verification as the first - a guard applied to one call is not a guard.
        # The strongest point must be a sentence that genuinely appears in a
        # retrieved page; anything composed is dropped rather than shown.
        point = arag.tidy(parsed.get("strongest_point") or "")
        # a quoted executive remark is colour, not evidence a committee can use
        if re.match(r"^(i|we)[\s']", point, re.I) or re.search(r"delighted|pleased|excited|proud", point, re.I):
            point = ""
        by_title = {r["title"]: r for r in retrieved}
        src = by_title.get(parsed.get("source_title", ""))
        verified = None
        if point:
            probe = norm(point)[:80]
            if len(probe) >= 30:
                for r in retrieved:
                    rec = BY_RID.get(r["rid"]) or {}
                    if probe in norm(rec.get("body") or r.get("excerpt") or ""):
                        verified, src = point, r
                        break
        return {
            "gaps": parsed.get("gaps") or [],
            "attachments": parsed.get("attachments") or [],
            "strongest_point": verified or "",
            "strongest_source": _sources_payload([src])[0] if (verified and src) else None,
        }
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))


# 2 - Surgeon desk ---------------------------------------------------------
SURGEON_PROMPT = (
    "You are the Clinic clinical knowledge desk, answering a surgeon or theatre "
    "team member using only Clinic's own published material. Be precise and "
    "clinical. Quote product names exactly as published. " + DECLINE)


@app.post("/api/surgeon-desk")
async def surgeon_desk(body: AskIn):
    try:
        return await grounded_answer(body.question, prompt=SURGEON_PROMPT, top_k=14)
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))


# 2 - Market access --------------------------------------------------------
# A structured answer over a fused context will sometimes pair the right market
# with the wrong page, describe a different country in an entry, or simply
# decide not to mention a market that the pages genuinely state a position on -
# and that last failure is why the market SET is no longer the model's to
# decide at all (see attribute_markets). Every card is built server side,
# deterministically, from the genuinely retrieved pages' own sentences.
MARKET_ALIASES = {
    "united states": ["united states", "usa", "u.s.", "us fda", "fda", "510(k)"],
    "australia": ["australia", "australian", "tga", "artg", "therapeutic goods"],
    "new zealand": ["new zealand"],
    "canada": ["canada", "canadian", "health canada"],
    "ukraine": ["ukraine", "ukrainian"],
    "singapore": ["singapore"],
    "brazil": ["brazil", "brazilian", "anvisa"],
    "hong kong": ["hong kong"],
    "thailand": ["thai"],
    "united kingdom": ["united kingdom", "uk ", " uk", "britain", "mhra"],
    # "eu" bare was previously left out deliberately (an abbreviation is a
    # higher false-positive risk than a full phrase) - checked against the
    # whole corpus (18 hits, every one genuinely about the European Union,
    # zero false positives) after its absence broke the new title-shape guard
    # in quote_is_about below: the Remplir EU/UK doc's own headline contains
    # "EU" but not "european union"/"europe"/"ce mark"/"mdr", so without this
    # alias the guard read the headline as naming the UK ALONE and rejected
    # the genuine EU candidate sentence from the same document.
    "european union": ["european union", "europe", "ce mark", "mdr", "eu"],
    # A genuinely distinct territory from the European Union (30 members - the EU
    # plus Iceland, Liechtenstein and Norway) that this corpus states a SEPARATE
    # position for (Striate+'s 2023 MDR re-certification). Previously reachable
    # only because a generative call could propose it as free text; the fixed
    # alias list must name it explicitly or the market silently disappears -
    # found the hard way when the first deterministic pass dropped it outright.
    "european economic area": ["european economic area"],
    # Germany, Austria and Switzerland are NOT added as three separate country
    # aliases, deliberately - Clinic's own announcement states one first-sales
    # event across a named commercial region ("First Sales of Striate+ in DACH
    # Region"), not three independent country launches. Three country aliases
    # would each verify true against this one sentence and render three cards
    # off one statement - the exact defect class this file's EU/UK merge fixed,
    # in the opposite direction (see hard rule 3's "splitting one source
    # statement into N cards overstates it"). One canonical entry, taken from
    # the source's own region name, same as the EU/UK merge takes its label from
    # the source rather than a synonym table. If Clinic ever announces one of
    # these three countries alone, that is a new, separately dated document and
    # a different card - never a relabelling of this one.
    "dach region": ["dach"],
    "japan": ["japan", "japanese", "pmda"],
    "china": ["china", "chinese", "nmpa"],
    "malaysia": ["malaysia"],
    "south korea": ["korea"],
    "india": ["india"],
    "taiwan": ["taiwan"],
    "philippines": ["philippines"],
    "vietnam": ["vietnam"],
    "indonesia": ["indonesia"],
}


def alias_hit(text: str, alias: list[str]) -> int:
    """Word-boundary match. A substring match puts "Indiana" under India."""
    # the EARLIEST match across all aliases, not the first alias that happens to
    # match somewhere. Returning a late "Brazil" while "Brazilian" sat beside the
    # verb put the market 200 characters from its own status word and the
    # sentence was discarded as unrelated.
    low = (text or "").lower()
    best = -1
    for a in alias:
        m = re.search(r"(?<![a-z])" + re.escape(a.strip()) + r"(?![a-z])", low)
        if m and (best < 0 or m.start() < best):
            best = m.start()
    return best


# A sentence can NAME a market without being ABOUT it. Failure shapes found on
# live output: a Canadian release saying "approval in this market complements
# our FDA approval" filed under the United States; one Singapore sentence
# recapping five markets filed as five separate cards; and a cross reference
# to an approval held elsewhere read as this market's position.
DEICTIC = re.compile(r"\bthis (market|approval|clearance|licence|license|registration|submission)\b", re.I)
CROSSREF = re.compile(
    r"complement\w*|in addition to|builds? on|alongside|as well as|existing approvals?|"
    r"already (approved|cleared|secured)|previously (approved|cleared)|on top of|"
    r"following (its|our|the) [^.]{0,30}approval", re.I)
# A country named as the SITE of an activity CITED AS SUPPORTING EVIDENCE for
# a position stated elsewhere is not itself a status statement. A U.S. DoD
# hospital-network approval read "The approval also follows recent clinical
# use of Remplir in 23 surgical procedures...in Ukraine" and credited Ukraine
# with the U.S.'s own approval - no existing CROSSREF phrase caught it,
# because "follows" here governs "clinical use", not "approval" (found
# widening retrieval for the DACH fix, 30 Sep 2026; a real, shipped-if-unfixed
# no-fake risk on a medical-device surface).
# TWO NARROWING PASSES were needed, and both regressed a real card before the
# regex required the evidentiary VERB, not just the activity noun phrase:
# (1) an early, broader version rejected any market not named in a
# differently-titled document's own headline - which also rejected a genuine
# Singapore-titled document's real aside about Australia/New Zealand
# distribution ("sales have grown rapidly since launch"), an independent fact,
# not evidence FOR Singapore, and the title-shape rule could not tell the two
# apart. (2) matching the bare phrase "clinical use...in X" then rejected
# OrthoACI's own genuine restriction - "OrthoACI is not available for sale,
# distribution, or clinical use in the United States" - because that sentence
# ALSO contains "clinical use...in", with no evidentiary verb governing it: it
# states the US's own status directly, it does not cite the US as evidence for
# something else. The fix both times was to require the EVIDENTIARY VERB
# ("follows", "supported by", "based on", "demonstrated by") to introduce the
# activity phrase, which is present in the Ukraine sentence and absent from
# both the New Zealand and the OrthoACI ones.
ACTIVITY_SITE = re.compile(
    r"\b(follows?|followed by|informed by|supported by|based on|demonstrated by)\b[^.]{0,40}\b"
    r"(clinical use|surgical (procedures?|cases?)|case activity|field use|"
    r"real-world (use|performance)|deployment)\b[^.]{0,90}?\bin\b", re.I)


def markets_named(text: str) -> set[str]:
    return {k for k, al in MARKET_ALIASES.items() if alias_hit(text, al) >= 0}


def quote_is_about(quote: str, market_key: str, alias: list[str], source_title: str) -> bool:
    """Does this sentence state THIS market's position, or merely mention it?"""
    at = alias_hit(quote, alias)
    if at < 0:
        return False
    title_names_it = alias_hit(source_title or "", alias) >= 0

    # A coverage recap listing several markets is not a per-market statement.
    named = markets_named(quote)
    if len(named) >= 3 and not title_names_it:
        return False

    # "approval in this market" refers to the announcement's own subject. If the
    # source is about a different market, this sentence is about that one.
    if DEICTIC.search(quote) and not title_names_it:
        other = markets_named(source_title or "")
        if other and market_key not in other:
            return False

    # A mention that sits only inside a cross-reference clause is evidence of an
    # approval held SOMEWHERE ELSE, not of this market's position.
    if not title_names_it:
        for m in CROSSREF.finditer(quote):
            if m.start() < at < m.start() + 160:
                return False

    # The country is named as the SITE of an activity, not as the subject of a
    # status. Reject only when the alias sits inside (or just after) the
    # activity-site clause, not merely somewhere in the same sentence.
    for m in ACTIVITY_SITE.finditer(quote):
        if m.start() <= at < m.end() + 40:
            return False
    return True


def aliases_for(market: str) -> list[str]:
    m = (market or "").strip().lower()
    for key, al in MARKET_ALIASES.items():
        if key in m or m in key:
            return al
    return [m] if m else []


def verbatim_sentence(bodies, alias, limit: int = 320, market_key: str = ""):
    """The single genuine, deterministic sentence stating this market's position.

    This is the ONLY path to a market card now (see attribute_markets) - no
    generative call is ever consulted for which markets exist, so this
    function's candidate selection has to be trustworthy on its own. Three
    disciplines earn that: the market name has to sit close to a status word
    (otherwise a passing mention gets promoted into a position statement); the
    sentence must itself resolve to a real status via status_from, not merely
    contain a status-shaped word nearby - "...documentation required for MDR
    certification" matches the "mdr" alias and sits next to "certification" but
    states no position at all, and admitting it as a candidate was the actual
    mechanism behind a market vanishing outright: with every genuine disqualifier
    tied, ranking fell through to comparing the two candidate sentences as raw
    text, and this one, having nothing to do with the market, sometimes won;
    and among what remains, a stated outcome on a more recent page beats an
    older anticipation - the reverse produced a card reading "application
    pending" for a market where the clearance had since been announced.
    """
    cands = []
    sidx = 0
    for rank, (r, body, _) in enumerate(bodies):
        rec = BY_RID.get(r["rid"]) or {}
        date = rec.get("date") or "0000-00-00"
        for chunk in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", body)):
            # An announcement body arrives as "<title> by Clinic <date> <lede>"
            # with no full stop between them, so the lede is unreachable behind a
            # 400-character run. A year followed by a capital is a safe boundary.
            for sent in re.split(r"(?<=\b\d{4})\s+(?=[A-Z])", chunk):
                sidx += 1
                sent = sent.strip()
                if not (60 <= len(sent) <= 420) or NAV_NOISE.match(sent):
                    continue
                # a fragment that starts mid-sentence reads as a broken quote
                if not (sent[0].isupper() or sent[0].isdigit()):
                    continue
                if "said:" in sent.lower() or "\u201c" in sent:
                    continue  # quoted speech is commentary, not a position statement
                at = alias_hit(sent, alias)
                if at < 0:
                    continue
                st = STATUS_WORDS.search(sent)
                if not st or abs(st.start() - at) > 110:
                    continue
                if not status_from(sent):
                    continue  # near a status word, but the sentence itself states no position
                if market_key and not quote_is_about(sent, market_key, alias, r.get("title", "")):
                    continue
                settled = 0 if CONDITIONAL.search(sent) else (1 if RECEIVED.search(sent) or RESTRICTED.search(sent) else 0)
                # a source whose own title names the market is the better attribution
                titled = 1 if alias_hit(r.get("title", ""), alias) >= 0 else 0
                # -sidx is the final tie-break - the earlier sentence in document
                # order wins. Deterministic, and it never falls back to comparing
                # the sentence text itself, which is meaningless and, on a
                # same-page tie, is exactly how the wrong sentence used to win.
                cands.append((settled, date, titled, -rank, -sidx, r, sent))
    if not cands:
        return None
    cands.sort(reverse=True)
    best = cands[0]
    return (best[5], "", ""), arag.tidy(best[6][:limit])


RESTRICTED = re.compile(
    r"not (currently )?(included|listed|registered|available)|not on the artg|"
    r"special access|\bsas\b|exempt|each treatment requires|unapproved|"
    r"not available for sale", re.I)
# An explicit receipt of approval. Anything short of this is still pending.
RECEIVED = re.compile(
    r"(has |have |now )?(received|been granted|granted|gained|secured|obtained|achieved)\b[^.]{0,60}"
    r"(approval|clearance|licen[cs]e|certification|authorisation|authorization)|"
    r"(approval|clearance|licen[cs]e|certification|authorisation)\b[^.]{0,40}"
    r"(was |were |has been )?(secured|received|granted|obtained|achieved|confirmed)|"
    r"following [^.]{0,50}(approval|clearance|licen[cs]e)|"
    r"['\u2019]s approval\b|to gain regulatory|complements existing approvals|"
    r"\bis approved\b|\bwas approved\b|\bnow approved\b|\bare approved\b|"
    r"\bhas been (approved|cleared)\b|\bwas cleared\b|\bgrants? 510\(k\)|"
    r"receives? regulatory approval|included on the artg|listed on the australian register", re.I)
PENDING = re.compile(
    r"\bsubmi\w*|\bapplied\b|\bapplication\b|\bpending\b|\blodged\b|under review|"
    r"in preparation|\bseeks?\b|\bexpected\b|\banticipat\w*|\bawait\w*", re.I)
APPROVED = re.compile(r"approv|clear(ed|ance)|licen[cs]e|granted|registered|510\(k\)", re.I)
# "Once Singapore and Brazil applications are approved, Striate+ will be
# available..." is a conditional about a PENDING application. Read as an approval
# it puts a green badge on a market that has not cleared.
CONDITIONAL = re.compile(
    r"^\s*(once|if|when|should)\b|\bwill be (available|approved|cleared|sold)\b|"
    r"\bsubject to\b|\bpending (approval|clearance|registration)\b|\bupon (approval|clearance)\b", re.I)
LAUNCHED = re.compile(r"commence sales|launch|now available|first sales|on sale", re.I)
DISTRIB = re.compile(r"distributor|distribution|supply agreement", re.I)
STATUS_WORDS = re.compile(
    r"approv|clear|licen[cs]|registrat|regulator|launch|distribut|commence|submi|"
    r"applic|available|special access|scheme|artg|certification|authorisation", re.I)
NAV_NOISE = re.compile(r"^(asx announcements|company news|news|home|menu)\b", re.I)


def status_from(quote: str, proposed: str = "") -> str:
    """Derive the status from the words actually shown on the card.

    The model proposes a status, but the card's text may have been re-sourced
    during verification - and a status that contradicts its own quote (an
    "approved" badge over a sentence saying "not currently included on the
    ARTG") is the single worst thing this surface could show.
    """
    q = quote or ""
    if RESTRICTED.search(q):
        return "Restricted or special access pathway stated"
    if CONDITIONAL.search(q):
        return "Submission or application stated, outcome not stated"
    if RECEIVED.search(q):
        return "Regulatory approval or clearance stated"
    if PENDING.search(q):
        return "Submission or application stated, outcome not stated"
    if APPROVED.search(q):
        return "Regulatory approval or clearance stated"
    if LAUNCHED.search(q):
        return "Commercially available or launched"
    if DISTRIB.search(q):
        return "Distribution or supply arrangement stated"
    return proposed  # empty means the wording states no position - drop the entry


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


# canonical.title() mis-cases an acronym region name ("Dach Region"). Override
# display text only where the mechanical title-case is wrong - every other
# canonical key already title-cases correctly.
DISPLAY_NAME = {"dach region": "DACH Region"}


def market_label(canonical: str) -> str:
    return DISPLAY_NAME.get(canonical, canonical.title().replace("Of", "of"))


def attribute_markets(retrieved: list[dict]) -> tuple[list[dict], list[str], list[str]]:
    """Every market card is derived deterministically from the retrieved pages'
    own sentences. No generative call is ever consulted for WHICH markets
    exist - a structured call proposing markets was the original design here,
    and it let the market SET vary run to run: Remplir's EU position could
    disappear outright when the model simply did not name it that run, and
    Striate+'s EEA position was present in 2 of 3 runs and absent in the third
    (DAM 89dcd627, 30 Sep 2026). Re-verifying whatever the model proposed could
    never fix this, and neither could a better merge - by the time two entries
    exist to merge, the model has already decided there ARE two entries. So
    every canonical market is checked against these same pages on every run,
    with no generative step in between: same retrieved pages, same output,
    every time. A market with no genuine position-bearing sentence in the
    retrieved pages gets no card - on a regulatory surface a missing market is
    safer than a wrong one, but it must be the SAME missing market every time,
    not a coin toss.
    """
    bodies = []
    for r in retrieved:
        rec = BY_RID.get(r["rid"]) or {}
        body = rec.get("body") or r.get("excerpt") or ""
        bodies.append((r, body, norm(body)))

    out, seen, mentioned = [], set(), []
    for canonical, alias in MARKET_ALIASES.items():
        if len(out) >= 9:
            break
        fb = verbatim_sentence(bodies, alias, market_key=canonical)
        if fb is None:
            # named somewhere in the retrieved text, but with no sentence that
            # itself states a position - shown separately, never as a card
            if any(alias_hit(body, alias) >= 0 for (_, body, _) in bodies):
                mentioned.append(market_label(canonical))
            continue
        match, quote = fb
        status = status_from(quote)
        if not status:
            continue  # defensive - verbatim_sentence already requires this
        seen.add(canonical)
        out.append({
            "market": market_label(canonical),
            "status": status,
            "position": quote,
            "source": _sources_payload([match[0]])[0],
        })
    out, notes = collapse_shared_statements(out)
    return out, sorted(mentioned), notes



# Two canonical markets can genuinely resolve to the SAME sentence (Remplir's
# EU and UK position is one combined submission, stated in one sentence), which
# SPLITS a single regulatory position into two cards and implies two independent
# ones. Both cards are individually true and the pair overstates - the
# composition asserting more than its parts. Collapsing is the correction, not
# a tidy-up.
# It is done from the SOURCE'S OWN WORDING rather than a synonym table, because
# a table is false somewhere in this same corpus: Remplir's EU and UK position
# is one combined submission, while Striate+ has a genuinely EU-only
# re-certification with no UK in it.

# A designation names a TERRITORY. These name a mark, a route or an outcome, and
# a span carrying one would read as a regulatory term of art the source never
# used as a market name.
NOT_A_TERRITORY = re.compile(
    r"\bce\b|\bukca\b|certification|certificate|approval|clearance|licen[cs]e|"
    r"\bmdr\b|regulation|registration|submission|application|notified body|\bbsi\b", re.I)


def source_designation(text: str, markets: list[str]) -> str:
    """The shortest verbatim span of the source that names all these markets.

    Returns "" unless every market in the group appears, so a partial span can
    never stand in for the whole group.
    """
    if not text:
        return ""
    spans = []
    for m in markets:
        hit = -1
        for a in aliases_for(m):
            mm = re.search(r"(?<![a-z])" + re.escape(a.strip()) + r"(?![a-z])", text.lower())
            if mm and (hit < 0 or mm.start() < hit):
                hit, end = mm.start(), mm.end()
        if hit < 0:
            return ""
        spans.append((hit, end))
    start, stop = min(a for a, _ in spans), max(b for _, b in spans)
    span = text[start:stop].strip(" ,.:;-")
    if not span or len(span) > 40 or NOT_A_TERRITORY.search(span):
        return ""
    return span


def collapse_shared_statements(cards: list[dict]) -> tuple[list[dict], list[str]]:
    """One statement, one card. Grouped on (source resource, quote)."""
    groups: dict[tuple, list[dict]] = {}
    order: list[tuple] = []
    for c in cards:
        key = ((c.get("source") or {}).get("url", ""), norm(c["position"])[:120])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(c)

    out, notes = [], []
    for key in order:
        group = groups[key]
        if len(group) == 1:
            out.append(group[0])
            continue
        # Grouping on (source, quote) SHOULD make the status identical. Assert it
        # rather than assume it - this whole defect was found by asserting
        # something expected to be trivially true.
        statuses = {c["status"] for c in group}
        if len(statuses) > 1:
            notes.append("One statement carried differing statuses and was left "
                         "as separate cards: " + ", ".join(sorted(c["market"] for c in group)))
            out.extend(group)
            continue
        names = [c["market"] for c in group]
        src = group[0].get("source") or {}
        label = (source_designation(src.get("title", ""), names)
                 or source_designation(group[0]["position"], names)
                 or " and ".join(dict.fromkeys(names)))
        out.append({**group[0], "market": label, "merged_from": names})
    return out, notes


MARKET_PROMPT = (
    "You are reviewing Clinic's own published announcements and product pages for "
    "an Clinic product's market access position. Your only job is to record GAPS: "
    "aspects a reader would reasonably expect a market access position to cover (for "
    "example regulatory status in a major market, CE mark, FDA clearance, a "
    "distribution agreement) that the supplied content does not state. Never infer "
    "that a gap has been closed - report it as a gap unless the content explicitly "
    "states the position. Australian English.")


def _market_query(product: str) -> str:
    return (f"{product} regulatory approval, FDA clearance, TGA registration, CE mark, "
            f"licence agreement, market entry, launch, distributor appointment and "
            f"availability by country")


# top_k=26 genuinely misses a real, correctly-labelled page for this exact query -
# not a truncation of a fixed ranked list, a narrower candidate SET: the same
# query against the same filter returned 11 results at top_k=26 and 17 at
# top_k=50, four calls each, stable both times, with Striate+'s "First Sales...
# in DACH Region" page (relevance 0.211, rank 14 of 17) absent below top_k=40 and
# present at and above it. Raising top_k widens Nuclia's own candidate fan-out,
# not just how many of a fixed list get returned. MARKET_TOP_K carries margin
# above the measured 40-result floor.
MARKET_TOP_K = 50


@app.post("/api/market-access/pages")
async def market_access_pages(body: MarketIn):
    """Stage one - retrieval only. Returns in about a second so the surface can
    paint the real page count and source list while composition is still running."""
    if body.product not in PRODUCTS:
        raise HTTPException(400, "Unknown product.")
    try:
        found = await arag.find(_market_query(body.product),
                                filt=arag.label_filter([("Product", body.product)]), top_k=MARKET_TOP_K)
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))
    retrieved = arag.resources_from_find(found)
    return {"product": body.product, "retrieved": len(retrieved),
            "sources": _sources_payload(retrieved[:8])}


@app.post("/api/market-access")
async def market_access(body: MarketIn):
    if body.product not in PRODUCTS:
        raise HTTPException(400, "Unknown product.")
    filt = arag.label_filter([("Product", body.product)])
    query = _market_query(body.product)
    try:
        found = await arag.find(query, filt=filt, top_k=MARKET_TOP_K)
        retrieved = arag.resources_from_find(found)
        titles = [r["title"] for r in retrieved if r["title"]][:26]
        if not titles:
            return {"product": body.product, "markets": [], "sources": [],
                    "note": "No published Clinic content was retrieved for this product."}
        # The market cards themselves are never asked of the model - see
        # attribute_markets. This call has exactly one job left: the gaps panel.
        schema = {
            "name": "market_access_gaps",
            "parameters": {
                "type": "object",
                "properties": {
                    "not_stated": {
                        "type": "array",
                        "description": "Aspects a reader might expect but which the published content does not state",
                        "items": {"type": "string"},
                    },
                },
                "required": ["not_stated"],
            },
        }
        data = await arag.ask_structured(query, schema, filt=filt, prompt=MARKET_PROMPT, top_k=24)
        parsed = data.get("answer_json") or {}
        markets, mentioned, notes = attribute_markets(retrieved)
        return {
            "product": body.product,
            "markets": markets,
            "not_stated": parsed.get("not_stated") or [],
            "mentioned_only": mentioned,
            "notes": notes,
            "sources": _sources_payload(retrieved[:8]),
            "retrieved": len(retrieved),
        }
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))


# 3 - Claim check ----------------------------------------------------------
CLAIM_PROMPT = (
    "You are the Clinic claim substantiation check. A colleague has drafted a "
    "statement for use in sales or marketing material. Decide whether Clinic's own "
    "published content supports it. Be conservative: a statement is supported only if "
    "the content states it, not if the content merely makes it plausible. A claim about "
    "a clinical outcome, efficacy figure, regulatory status, indication or safety "
    "conclusion is NOT supported unless the content states that exact thing. Quote the "
    "supporting or contradicting wording verbatim from the content. Australian English.")


@app.post("/api/claim-check")
async def claim_check(body: ClaimIn):
    try:
        found = await arag.find(body.claim, top_k=14)
        retrieved = arag.resources_from_find(found)
        # Retrieval never comes back empty - it comes back with scored junk
        # trailing towards zero - so it has to be thresholded. Without this the
        # desk ran the substantiation call against whatever arrived and returned
        # a verdict plus six "pages checked" cards that had nothing to do with
        # the claim, which reads as the evidence behind the verdict. Same
        # threshold and the same reason as the submission reviewer above.
        if not retrieved or (retrieved[0].get("score") or 0) < 0.35:
            return {
                "claim": body.claim, "declined": True,
                # Deliberately NOT the "Not supported by published content"
                # verdict. That verdict is a claim ABOUT the published content,
                # and nothing came back closely enough to support any claim
                # either way - including that one. Asserting it here would be
                # the same defect in the opposite direction: a confident
                # finding generated out of an absence of evidence.
                "verdict": "", "explanation": "", "evidence_quote": "",
                "source": None, "sources": [], "unsupported_elements": [],
                "safer_wording": "", "retrieved": 0,
            }
        titles = [r["title"] for r in retrieved if r["title"]][:14] or ["No matching published page"]
        schema = {
            "name": "claim_substantiation",
            "parameters": {
                "type": "object",
                "properties": {
                    "verdict": {"type": "string", "enum": [
                        "Supported by published content",
                        "Partly supported - wording goes further than the content",
                        "Not supported by published content",
                    ]},
                    "explanation": {"type": "string",
                                    "description": "Two or three sentences explaining the verdict"},
                    "evidence_quote": {"type": "string",
                                       "description": "The closest wording in the published content, quoted verbatim. Empty string if there is none."},
                    "source_title": {"type": "string", "enum": titles},
                    "unsupported_elements": {
                        "type": "array",
                        "description": "Specific parts of the drafted claim the published content does not state",
                        "items": {"type": "string"},
                    },
                    "safer_wording": {"type": "string",
                                      "description": "A rewrite that stays inside what the published content actually states. Empty string if nothing can be claimed."},
                },
                "required": ["verdict", "explanation", "evidence_quote", "source_title",
                             "unsupported_elements", "safer_wording"],
            },
        }
        data = await arag.ask_structured(
            f"Is this statement supported by Clinic's published content? Statement: {body.claim}",
            schema, prompt=CLAIM_PROMPT, top_k=14)
        parsed = data.get("answer_json") or {}
        by_title = {r["title"]: r for r in retrieved}
        src = by_title.get(parsed.get("source_title", ""))
        q = arag.tidy(parsed.get("evidence_quote") or "")
        parsed["evidence_quote"] = q.strip('"\u201c\u201d\u2018\u2019\'').strip()
        return {
            "claim": body.claim,
            **parsed,
            "source": _sources_payload([src])[0] if src else None,
            "sources": _sources_payload(retrieved[:6]),
            "retrieved": len(retrieved),
        }
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))


# 4 - Investor signal ------------------------------------------------------
@app.get("/api/investor-signal")
async def investor_signal():
    by_year: dict[str, Counter] = defaultdict(Counter)
    for a in ANNOUNCEMENTS:
        by_year[a["date"][:4]][a["theme"]] += 1
    years = sorted(by_year)
    themes = [t for t, _ in THEMES] + ["Company update"]
    themes = [t for t in themes if any(by_year[y][t] for y in years)]
    return {
        "total": len(ANNOUNCEMENTS),
        "years": years,
        "themes": themes,
        "matrix": {y: {t: by_year[y][t] for t in themes} for y in years},
        "theme_totals": {t: sum(by_year[y][t] for y in years) for t in themes},
        "recent": [{"title": a["title"], "url": a["url"], "date": a["date"], "theme": a["theme"]}
                   for a in ANNOUNCEMENTS[:12]],
    }


@app.post("/api/investor-digest")
async def investor_digest(body: DigestIn):
    theme = body.theme
    scoped = [a for a in ANNOUNCEMENTS if a["theme"] == theme]
    if body.period:
        scoped = [a for a in scoped if a["date"][:4] == body.period]
    if not scoped:
        raise HTTPException(400, "No announcements in that selection.")
    period = f" during {body.period}" if body.period else ""
    question = (f"Across Clinic's announcements{period}, what did the company announce "
                f"in relation to {theme.lower()}? Summarise the specific developments that were announced.")
    prompt = ("You are briefing an investor using only Clinic's own published announcements. "
              "Report only developments the announcements state, with the company's own wording for "
              "any figure, approval or milestone. Do not forecast, value or interpret. " + DECLINE)
    scope = [("Document type", "Announcement")]
    filt = arag.label_filter(scope)
    try:
        # This surface tells the reader it is scoped to announcements, so the
        # same cross-check runs here - a claim the app makes about its own
        # scope should be enforced, not asserted.
        result = await grounded_answer(
            question, filt=filt, prompt=prompt, top_k=16,
            allowed=allowed_rids(scope),
            withhold_reason=("This briefing is drawn only from Clinic's published "
                             "announcements, and this question is covered in their "
                             "other published material."))
        result["scope"] = {"theme": theme, "period": body.period, "announcements": len(scoped)}
        return result
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))


# 5 - Patient guide --------------------------------------------------------
PATIENT_PROMPT = (
    "You are answering a patient or carer using only Clinic's own published "
    "patient-facing material. Use plain language a non-clinician can follow, short "
    "sentences, no jargon without explaining it. Never give medical advice, never "
    "suggest a treatment is right for this person, never state an outcome, success "
    "rate or recovery time that is not written in the supplied content. Always finish "
    "by pointing the reader to their own surgeon or treating clinician. " + DECLINE)

# The entitlement is ONE rule, on the axis the surface actually promises.
# It used to be an OR across audience and document type, and the sanity check
# found that leaky in the SCOPE DEFINITION rather than in the guard: a page at
# /practitioners/<product>/patient-information/ carries doctype "Patient
# information" while its audience is Practitioner, so it satisfied the OR on a
# document-type coincidence and was admitted to a patient-scoped surface. Four
# pages entered that way. Audience alone cannot be satisfied by coincidence,
# and every patient story already carries it.
PATIENT_SCOPE = [("Audience", "Patient")]
PATIENT_FILTER = arag.label_filter(PATIENT_SCOPE)
PATIENT_ALLOWED = allowed_rids(PATIENT_SCOPE)
PATIENT_SAFETY = ("This is general information from Clinic's published patient pages. "
                  "It is not medical advice. Talk to your surgeon or treating clinician "
                  "about your own situation.")
# Asserts nothing about a reply that does not exist - it only routes the reader
# on, which is the one thing still true when this desk declines.
PATIENT_SAFETY_DECLINED = ("Your surgeon or treating clinician is the right person to ask "
                           "about your own situation.")
PATIENT_WITHHOLD = ("This desk answers only from the pages Clinic publishes for patients, "
                    "and this question is covered in their other published material. Please ask "
                    "your surgeon or treating clinician about it.")


@app.post("/api/patient-guide")
async def patient_guide(body: AskIn):
    try:
        result = await grounded_answer(body.question, filt=PATIENT_FILTER,
                                       prompt=PATIENT_PROMPT, top_k=10,
                                       allowed=PATIENT_ALLOWED,
                                       withhold_reason=PATIENT_WITHHOLD)
        # The safety rail describes the answer it sits under, so it cannot be
        # the same sentence when there is no answer. "This is general
        # information from Clinic's published patient pages" has no "this"
        # to refer to on a decline - nothing was provided - and it told a
        # patient that a reply they cannot see is general information from the
        # patient pages. Same shape as the decline footer that asserted what the
        # corpus contains: true when written, because it was only ever written
        # for the answer path. The clinician route matters MORE on a decline,
        # not less, so only the false half goes.
        result["safety"] = (PATIENT_SAFETY_DECLINED if result.get("decline")
                            else PATIENT_SAFETY)
        return result
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))


# 6 - Evidence library -----------------------------------------------------
@app.get("/api/library")
async def library():
    def counts(key):
        c = Counter()
        for d in INDEX:
            v = d[key]
            for x in (v if isinstance(v, list) else [v]):
                c[x] += 1
        return dict(c.most_common())

    rails = []
    for p in PRODUCTS:
        items = [d for d in INDEX if p in d["products"]]
        if items:
            rails.append({"title": p, "kind": "Product", "count": len(items),
                          "items": [_card(d) for d in sorted(items, key=_recency)[:12]]})
    for dt in ["Product page", "Instructions for use", "Surgical technique",
               "Clinical evidence", "Patient information", "Practitioner resource",
               "Patient story"]:
        items = [d for d in INDEX if d["doctype"] == dt]
        if items:
            rails.append({"title": dt, "kind": "Document type", "count": len(items),
                          "items": [_card(d) for d in sorted(items, key=_recency)[:12]]})
    rails.append({"title": "Latest announcements", "kind": "Document type",
                  "count": len(ANNOUNCEMENTS),
                  "items": [_card(d) for d in ANNOUNCEMENTS[:12]]})
    return {
        "total": len(INDEX),
        "facets": {"Product": counts("products"), "Document type": counts("doctype"),
                   "Audience": counts("audience")},
        "rails": rails,
    }


def _recency(d):
    return (d.get("date") or "0000", )


def _card(d):
    return {"title": arag.tidy(d["title"]), "url": d["url"], "doctype": d["doctype"],
            "products": d["products"], "audience": d["audience"], "date": d.get("date"),
            "excerpt": arag.tidy(d["excerpt"]), "chars": d["chars"]}


@app.post("/api/library/search")
async def library_search(body: SearchIn):
    pairs = []
    if body.product:
        pairs.append(("Product", body.product))
    if body.doctype:
        pairs.append(("Document type", body.doctype))
    if body.audience:
        pairs.append(("Audience", body.audience))
    # an AND of separate labelsets, built as nested filter expressions
    filt = None
    if pairs:
        terms = [{"prop": "label", "labelset": ls, "label": lb} for ls, lb in pairs]
        filt = {"field": terms[0] if len(terms) == 1 else {"and": terms}}
    try:
        found = await arag.find(body.query, filt=filt, top_k=24)
    except arag.UpstreamError as exc:
        raise HTTPException(503, str(exc))
    results = []
    for r in arag.resources_from_find(found):
        known = BY_RID.get(r["rid"]) or {}
        # client-side threshold: this retrieval never returns an empty set
        if r["score"] < 0.35:
            continue
        results.append({**_card({**known, "excerpt": r["excerpt"] or known.get("excerpt", "")}),
                        "relevance": r["score"]} if known else None)
    return {"results": [r for r in results if r], "query": body.query}


# ------------------------------------------------------------------ static
STATIC = ROOT / "static"
# The build stamp is appended to every asset URL and the assets are served
# no-cache, so a browser can never run an older bundle against a newer server.
BUILD = str(int((STATIC / "app.js").stat().st_mtime))


class NoCacheStatic(StaticFiles):
    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-cache, must-revalidate"
        return resp


app.mount("/assets", NoCacheStatic(directory=STATIC), name="assets")


def shell() -> HTMLResponse:
    html = (STATIC / "index.html").read_text()
    html = html.replace("/assets/app.css", f"/assets/app.css?v={BUILD}")
    html = html.replace("/assets/app.js", f"/assets/app.js?v={BUILD}")
    return HTMLResponse(html, headers={"Cache-Control": "no-cache, must-revalidate"})


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.exception_handler(arag.UpstreamError)
async def upstream_handler(_request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


for _route in ROUTES:
    app.get(_route, include_in_schema=False)((lambda: shell()))


@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(404, "Not found")
    return shell()
