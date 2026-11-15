"""Visitor-facing text guard: DESIGN.md section 2 enforced on every string that leaves the server.

Two jobs:
  * `clean()`  - rewrite what can be rewritten safely (acronym, platform names, banned words, dashes).
  * `claims()` - find what must be DROPPED, never rewritten: a deployment-mode claim or an accuracy
                 percentage. A claim the GM has HELD is not made safe by changing a word.

The same compiled expressions are used by the runtime filter and by selftest.py (controls are built
from these objects, never from a retyped copy).
"""
import re

# Deployment-mode claims. HELD pending the GM (DESIGN.md s2 rule 3). Any clause matching is dropped.
DEPLOYMENT_RE = re.compile(
    r"on[- ]?prem(?:ise|ises)?|offline|air[- ]?gapped|self[- ]?host(?:ed|ing)?|"
    r"deployment (?:mode|modes|story|options? (?:include|are|such))|three (?:deployment )?modes|"
    r"\bhybrid\b(?!\s+(?:search|retrieval|ranking|results?|query|queries))|private[- ]cloud|"
    r"(?:data|documents?|content|corpus)\s+(?:stays?|never leaves?|remains?)\s+(?:with|in|on|inside)\b|"
    r"stays? with you|stay in your environment|keeps? your (?:data|documents?)|"
    r"nothing is stored|not stored in (?:our|the) cloud|never leaves your",
    re.I)

# A QUESTION about a held topic is answered by a fixed referral, before any retrieval or generation runs:
# a model asked about deployment can only repeat the held claim or invent one. DESIGN.md s2 rule 3.
HELD_TOPIC_RE = re.compile(
    DEPLOYMENT_RE.pattern + r"|data (?:residency|sovereignty|locali[sz]ation)|"
    r"where (?:is|are|does|do) (?:my|our|the) (?:data|documents?|content|corpus)(?: \w+)? (?:stored|kept|held|hosted|live|go)|"
    r"(?:is|are) (?:my|our) (?:data|documents?|content) (?:safe|secure|stored|private)|"
    r"(?:data|documents?|content) (?:leave|leaves|leaving) (?:my|our|the)|run\s+(?:it\s+)?(?:locally|in[- ]house|on my own)",
    re.I)

# An accuracy percentage (Field Rule 5): "95% accurate", "accuracy of 97%", "97 per cent accuracy".
ACCURACY_RE = re.compile(
    r"\b\d{1,3}(?:\.\d+)?\s?(?:%|per ?cent)\s+(?:accura\w*|precision|correct)|"
    r"accura\w*\s+(?:of|at|to|above|over|up to)?\s*\d{1,3}(?:\.\d+)?\s?(?:%|per ?cent)",
    re.I)

# SELF-NARRATION: the model describing its own inputs or its own limits inside an answer ("the context states",
# "it also mentions that", "not enough data to answer ..."). A visitor reads it as the corpus being thin or the product
# talking about itself. Withheld whole, like a held claim; an answer emptied by it is refused. A system prompt already
# failed once on this class (0 of 60 for one phrase, then the same register in other words), and a guard is testable.
SELF_NARRATION_RE = re.compile(
    r"\bnot enough (?:data|information)\b|\b(?:insufficient|no) (?:data|information) (?:to|is|was|provided)\b|"
    r"\bit (?:also )?(?:mentions|states|says|notes|describes|indicates)\b|"
    r"\b(?:the|this|these|those|provided) (?:context|passages?|text|excerpts?|documents?|sources?|information provided|provided (?:text|context|information)) "
    r"(?:states?|says?|describes?|mentions?|indicates?|shows?|notes?|provides?|provided|given)\b|"
    r"\b(?:according to|as (?:stated|described|mentioned|noted|shown) in|based on|from) the (?:provided |given )?(?:context|passages?|text|excerpts?|information)\b|"
    r"\bthe explicit (?:measure|score|metric|term)s? (?:described|mentioned|stated)\b|"
    r"\b(?:is|are|was|were) (?:described|characteri[sz]ed|portrayed|presented|said|stated|noted) (?:as|to)\b|"
    r"\bthe described (?:workflow|process|steps?|approach|mechanism|flow|setup)\b|\bsteps? implied\b|\bimplied by the\b|"
    r"\bI (?:do not|don't|cannot|can't) (?:have|find|see)\b",
    re.I)

# DOCUMENTATION SELF-REFERENCE: an answer narrating the document it came from ("the page plainly indicates", "the business
# case page itself", "as mentioned above", "in this mode"). Anchored on the DETERMINER and a narrating verb, never on the
# bare word, because page/document are legitimate product vocabulary ("a scanned page", "each document is indexed").
DOC_SELF_REFERENCE_RE = re.compile(
    r"\b(?:this|that|the|our) (?:\w+ ){0,3}(?:page|document|article|section|guide|chapter)\b(?: itself)?\s+"
    r"(?:plainly |also |clearly |explicitly |itself )?(?:states?|says?|indicates?|mentions?|notes?|describes?|explains?|covers?|lists?|recommends?|warns?|suggests?|makes? clear)\b|"
    r"\b(?:\w+ ){1,3}(?:page|document|article) itself\b|\bthis (?:page|document|article)\b|"
    r"\bas (?:mentioned|noted|stated|described|discussed|shown) (?:above|earlier|below|previously)\b|\bin this mode\b|\bin this (?:section|guide|article)\b|"
    # the SAME class with a different noun: the model talking about the text it was given ("the description is narrow by design").
    # Nouns that are never product vocabulary, so the broad verb list is safe here (unlike page/document).
    r"\bthe (?:description|summary|overview|write-?up|blurb|source text|source material)\b(?: \w+){0,2} (?:is|are|does|do|doesn't|has|have|lacks|omits|includes|contains|states|says|mentions|notes)\b",
    re.I)

# INTERNAL API NOMENCLATURE in prose: endpoint, parameter and field names are our implementation vocabulary, not the
# product's. Tight anchors, so ordinary "ask a question" / "find the answer" stay quiet.
INTERNAL_API_RE = re.compile(
    r"\bask[- ]citations?\b|\bfilter_expression\b|\banswer_json_schema\b|\bpredict/remi\b|\bX-NUCLIA[\w-]*|\bX-Synchronous\b|"
    r"(?<![\w])/(?:ask|find|graph|catalog|resources?)\b|\b(?:the |its |our )?(?:ask|find|graph|catalog) (?:endpoint|API|call|route)\b|"
    r"\b(?:ask|find|graph)'s (?:response|output|result|payload)\b|\bservice[- ]account token\b|\bNUA key\b",
    re.I)

ACRONYM_RE = re.compile(r"\b(?:ARAG|PARAG)\b")
PLATFORM_NAME_RE = re.compile(r"\bnuclia(?:db)?\b", re.I)
KB_NAME_RE = re.compile(r"\bknowledge[ -]box(es)?\b", re.I)
ENDPOINT_RE = re.compile(r"(?<![\w.])/(?:ask|find|graph|catalog|predict|resources?)\b")
HOST_RE = re.compile(r"[\w.-]*rag\.progress\.cloud|aws-[a-z]+-[a-z]+-\d-\d|\bap-southeast-\d\b", re.I)

BANNED = {
    "delve": "dig", "delves": "digs", "delving": "digging", "delved": "dug",
    "leverage": "use", "leverages": "uses", "leveraging": "using", "leveraged": "used",
    "unlock": "open up", "unlocks": "opens up", "unlocking": "opening up", "unlocked": "opened up",
    "seamless": "smooth", "seamlessly": "smoothly",
    "game-changing": "significant", "game changing": "significant",
}
BANNED_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(BANNED, key=len, reverse=True)) + r")\b", re.I)


def _match_case(src, repl):
    return repl.capitalize() if src[:1].isupper() else repl


_US_STEMS = ("authoriz|organiz|summariz|analyz|optimiz|customiz|prioritiz|standardiz|normaliz|categoriz|utiliz|recogniz|minimiz|maximiz|"
             "initializ|finaliz|synchroniz|visualiz|personaliz|centraliz|emphasiz|realiz|apologiz|specializ|generaliz|monetiz|digitiz|"
             "capitaliz|characteriz|serializ|localiz|sanitiz|tokeniz|stabiliz|memoriz")
US_SPELLING_RE = re.compile(r"\b(?:" + _US_STEMS + r")(?:e|es|ed|ing|er|ers|ation|ations)\b|"
                            r"\b(?:label|model|cancel|travel|signal)(?:ed|ing)\b|"
                            r"(?<![-:\"'\w])(?:(?:behavior|color|favor|neighbor|honor|labor|flavor|rumor|humor|harbor)"
                            r"(?:s|ed|ing|able|ably|ite|ites|ful|fully|less|ist|ists|al|ally|hood|hoods)?|center(?:s|ed|ing)?|gray|defenses?)(?![:\w-])", re.I)
_AU = {"behavior": "behaviour", "behaviors": "behaviours", "color": "colour", "colors": "colours", "colored": "coloured", "favor": "favour",
       "favorite": "favourite", "favorites": "favourites", "neighbor": "neighbour", "honor": "honour", "labor": "labour", "flavor": "flavour",
       "center": "centre", "centers": "centres", "centered": "centred", "gray": "grey", "defense": "defence"}
_QUOTED_SPAN = re.compile(r'"[^"\n]{1,120}"|\u201c[^\u201d\n]{1,120}\u201d|`[^`\n]{1,120}`|->\s*[A-Z][A-Za-z]*')


def _au_word(m):
    w = m.group(0)
    lw = w.lower()
    r = _AU.get(lw)
    if r is None and re.match(r"(?:label|model|cancel|travel|signal)(?:ed|ing)$", lw):
        r = lw[:-2] + "l" + lw[-2:] if lw.endswith("ed") else lw[:-3] + "l" + lw[-3:]      # labeled -> labelled
    if r is None and re.match(r"(?:behavi|col|fav|neighb|hon|lab|flav|rum|hum|harb)or", lw):        # -or stems and every derived form: or -> our (favorable -> favourable)
        r = re.sub(r"^(behavi|col|fav|neighb|hon|lab|flav|rum|hum|harb)or", r"\1our", lw)
    elif r is None and lw.startswith("center"):
        r = "centring" if lw == "centering" else "centre" + lw[6:]
    elif r is None and lw == "defenses":
        r = "defences"
    if r is None:                               # -ize / -yze families: z -> s, in place, nothing deleted
        r = re.sub(r"([iy])z", r"\1s", lw, count=1)
    if w.isupper():
        return r.upper()
    return r.capitalize() if w[:1].isupper() else r


def australian(text):
    """US spelling to Australian, letter-for-letter, OUTSIDE quotation marks and code spans (a vendor's own capability
    name or a literal field name is not ours to respell). Substitution only: nothing is deleted."""
    out, pos = [], 0
    for m in _QUOTED_SPAN.finditer(text):
        out.append(US_SPELLING_RE.sub(_au_word, text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(US_SPELLING_RE.sub(_au_word, text[pos:]))
    return "".join(out)


# A run of two or more adjacent ALL-CAPS words, one of them 5+ letters ("a SINGLE SHARED knowledge box"), is emphasis copied out of
# a source document. Lowercased in place: case only, nothing deleted. Acronyms are short (PDF, MCP, REST API) so they stay.
_CAPS_RUN_RE = re.compile(r"\b(?:[A-Z]{3,}(?: |$)){2,}")


def _lower_caps_run(m):
    run = m.group(0)
    return run.lower() if any(len(w) >= 5 for w in run.split()) else run


def clean_content(text):
    """What a QUOTATION may not carry, as a rewrite: the substitutions of clean() EXCEPT the two that only change how the source's own words are cased
    or spelled (an all-caps run, a US spelling). Those are properties of the quoted text, not defects in it, and the US-spelling rule does not
    look inside quotation marks for the same reason. If this differs from the input, the quote would need a word removed or replaced to be shown."""
    t = text.replace("—", " - ").replace("–", "-")
    t = re.sub(r" {2,}-\s+ ", " - ", t)
    t = ACRONYM_RE.sub("Progress Agentic RAG", t)
    t = PLATFORM_NAME_RE.sub("Progress", t)
    t = HOST_RE.sub("", t)
    return BANNED_RE.sub(lambda m: _match_case(m.group(0), BANNED[m.group(0).lower()]), t)


def clean(text, verbatim=False):
    """Rewrite the safely-rewritable. Idempotent. `verbatim=True` (PRINTED answers, which are the verified document text) skips the wording normalisations that would make
    the served text differ from its source (the price-period rendering and the plain-language swap); the safety rewrites still apply."""
    if not text:
        return text
    t = _CAPS_RUN_RE.sub(_lower_caps_run, australian(text))
    t = t.replace("—", " - ").replace("–", "-")
    t = re.sub(r" {2,}-\s+ ", " - ", t)
    t = ACRONYM_RE.sub("Progress Agentic RAG", t)
    # "knowledge box" is Progress's own published term (pricing page, published asset titles): NOT rewritten.
    t = PLATFORM_NAME_RE.sub("Progress", t)
    # One rendering of a price period: the published page says "per month", and two parallel answers rendered "$750/month" and "$750 a month" (read 19).
    if not verbatim:
        t = re.sub(r"(\$\s?\d[\d,]*(?:\.\d+)?)\s*(?:/\s*(?:month|mo)\b|(?:a|each|every) month\b)", r"\1 per month", t, flags=re.I)
    # "a filter on a single dimension" is the factory's rule about entitlements, not a sentence for a buyer (read 19): say the plain thing.
    if not verbatim:
        t = re.sub(r"\ba filter on a single (?:dimension|axis)\b", "a filter", t, flags=re.I)
    t = HOST_RE.sub("", t)
    t = BANNED_RE.sub(lambda m: _match_case(m.group(0), BANNED[m.group(0).lower()]), t)
    return t


# Internal BUILD VOICE - grammar, not nouns (11 Oct 2026: 17 hits over 111 resources, README-derived): a standard named by
# code with a verdict, a brief or revert narrated, "this pass", a dated rebuild. Anchored (case-sensitive where a bare word
# would hit ordinary prose: "fail", "pass").
BUILD_VOICE_RE = re.compile(
    r"\bStandard [A-Z]\d{1,3}\b|\b[BF]\d{2}(?:/[BF]?\d{2})*\s+(?:FAIL|PASS)\b|\b(?:a|the) fresh brief\b|\bsilent(?:ly)? revert\b|"
    r"\bwas re-?run this pass\b|\b(?:rebuilt|revised|re-?seeded) (?:on )?\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\b|"
    r"\(rev \d+\)")
# A raw citation key that leaked as text. FITTED TO THE OBSERVED STRING "block-AC" (hyphen, fixture specimen
# stray-citation-key); a looser shape would delete legitimate "1: Isolation bay" style content, so it stays narrow.
# Invented quality vocabulary: the two measures are named groundedness and context relevance (read 8: "a confidence-grounded
# score"). Narrow on purpose - "confidence score" is legitimate elsewhere (a document-intelligence capability).
QUALITY_TERM_RE = re.compile(r"\bconfidence[- ]grounded\b|\bgrounded[- ]confidence\b", re.I)
CITATION_KEY_RE = re.compile(r"(?<![\w-])block-[A-Z]{1,3}\b")


# ---- sentences that send a visitor somewhere THIS site does not have (read 10: "Use the /audit-trail view ..." from another
# demo's entry). The corpus describes dozens of other products' routes, views and tabs, so any can be offered as ours.
# The allow-list is DERIVED FROM THE APP at startup (set_known_routes), never hand-typed; until it is set the rule is OFF and
# says so (route_guard_armed()), because a guard with an empty allow-list would hold every path.
_KNOWN = {"segments": None, "names": None}
ROUTE_TOKEN_RE = re.compile(r"(?<![\w/:.<>=-])/([a-z][a-z0-9_-]*)(?:/[\w.{}-]*)*")
VIEW_REF_RE = re.compile(r"\bthe ([A-Za-z][\w-]*(?: [A-Za-z][\w-]*)?) (view|tab|page|screen|dashboard)\b")
_GENERIC_PAGES = {"home", "landing", "main", "pricing", "fit", "explore", "watch", "build", "fix", "embed",
                  "published"}       # "the published page" names no route (it is how the corpus points at the pricing page); "the economics page" does, and this site has none


def set_known_routes(paths, names):
    """paths: every route path the app serves (e.g. '/api/ask', '/media/{asset_id}', '/explore'); names: its page names."""
    _KNOWN["segments"] = {p.strip("/").split("/")[0] for p in paths if p.strip("/")} | {n.strip("/") for n in names}
    _KNOWN["names"] = {n.lower() for n in names} | _GENERIC_PAGES


def route_guard_armed():
    return _KNOWN["segments"] is not None


def route_reference(sentence):
    """A route/view/tab/page reference this app does not have, or None."""
    if not route_guard_armed():
        return None
    for m in ROUTE_TOKEN_RE.finditer(sentence):
        if m.group(1) not in _KNOWN["segments"]:
            return m.group(0)
    for m in VIEW_REF_RE.finditer(sentence):
        words = {w.lower() for w in re.split(r"[ -]", m.group(1))}
        if not (words & _KNOWN["names"]):
            return m.group(0)
    return None


# ---- the default is ONE shared box; a sentence asserting a box per tenant/customer as the normal way is the inversion
# (reads 8-10: "One knowledge box per tenant is the normal starting point"; "else you keep one box per customer").
BOX_PER_RE = re.compile(r"\b(?:one |a |single |separate )?(?:knowledge )?box(?:es)? (?:per|for each|for every) (?:tenant|customer)\b", re.I)
DEFAULT_WORD_RE = re.compile(r"\b(?:normal|default|usual|standard|starting point|typical(?:ly)?|by default)\b", re.I)
ELSE_BOX_RE = re.compile(r"\b(?:else|otherwise|instead)\b[^.]{0,30}\b(?:keep|use|have|take)\b[^.]{0,20}box(?:es)? (?:per|for each|for every) (?:tenant|customer)\b", re.I)
_NEGATE_BEFORE_RE = re.compile(r"\b(?:not|never|instead of|rather than|exception|unlike)\b", re.I)


# ABSOLUTES ABOUT OUR OWN BEHAVIOUR (reads 15-17, each editorially cut and each returned on the next generation, because a cut corrects the artifact and not the generator).
# Two shapes, both inferences the corpus does not state: (1) a guarantee about what an agent or the system can SEE ("keeps the agent from seeing more than the
# requester" - a conditional about the customer's own application turned into our guarantee); (2) a citation absolute ("every answer ... with citations back
# to each one", "always includes citations" - citation presence is measured to vary per run). Held as whole sentences; advice ("rely on retrieval-time
# filtering") and the plain definition of a citation stay quiet.
VISIBILITY_GUARANTEE_RE = re.compile(r"\b(?:keeps?|prevents?|stops?|ensures?|guarantees?|means?|ensuring|preventing)\b[^.\n]{0,50}\b(?:seeing|accessing|reading|see|access)\b[^.\n]{0,40}"
                                     r"\b(?:more than|only|other|outside|beyond)\b|\b(?:cannot|can't|never|can not)\s+(?:see|access|read)\b[^.\n]{0,30}\bmore than\b", re.I)
CITATION_ABSOLUTE_RE = re.compile(r"\b(?:every|each|all)\s+(?:answer|response)s?\b[^.\n]{0,100}\b(?:with|has|have|carr(?:y|ies)|includes?|comes? with|returns?)\b[^.\n]{0,60}\bcitations\b|"
                                  r"\balways\b[^.\n]{0,30}\b(?:includes?|carr(?:y|ies)|comes? with|has|have|cites?|cited)\b[^.\n]{0,20}\bcitations?\b|"
                                  r"\bcitations?\b[^.\n]{0,30}\b(?:always|guaranteed)\b", re.I)


# (3) "content stays separate" / "data stays with you": one reading from the held claim that a customer's data stays in their environment (read 17, entry 1:
# "The integration sits behind your own server so content stays separate"). What the source supports is narrower - the proxy hides the API key - so say that.
CONTAINMENT_RE = re.compile(r"\b(?:content|data|documents?|information)\b[^.\n]{0,40}\b(?:stay(?:s|ing)?|(?:is|are|being)?\s*kept|remain(?:s|ing)?)\b[^.\n]{0,20}\b(?:separate|private|local|with you|yours|in your|on your|within)\b", re.I)


# (4) A role swap between the two mechanisms the isolation answer teaches (read 18): "a filter that labels each document". A LABEL labels; a FILTER filters. The partner copy
# of the same question said it correctly and the unscoped copy swapped them, so this is caught per sentence rather than only by the pair check.
ROLE_SWAP_RE = re.compile(r"\b(?:filters?|filtering)\b[^.\n;,]{0,12}\b(?:that |which |to )?label(?:s|led|ling)?\s+(?:each|every|all|the|your)\b|"
                          r"\blabels?\b[^.\n;,]{0,12}\b(?:that |which )filter(?:s)?\s+(?:each|every|all|the|your)\b", re.I)
# (5) A language-support claim no served document states (read 18, entry 1: "(or other supported languages)"). The corpus has no canonical statement of multilingual support,
# and a capability claim is verified against the knowledge box before it is made (hard rule 3). Held until a document states it.
LANGUAGE_CLAIM_RE = re.compile(r"\b(?:other|multiple|many|various|several|supported)\s+(?:supported\s+)?languages\b|\bmultilingual\b|\bin any language\b|\bsupports? \d+ languages\b", re.I)


# (6) A knowledge-box LIMIT or add-on PRICE with no plan named (read 19: "...limits to eight boxes" on the partner path; eight is the Pro cap and Enterprise is custom, so an ISV
# took away a ceiling that does not apply to them). Where a product is sold in tiers a limit names its tier or it asserts the best one, the same shape as the file-type claim.
_TIER_NAME_RE = re.compile(r"\b(?:starter|pro|enterprise|plans?|tiers?|subscription|free trial|trial)\b", re.I)
_BOX_LIMIT_RE = re.compile(r"\b(?:up to|capped at|cap of|limit(?:s|ed)?(?: to| of)?|maximum(?: of)?|max(?:imum)?|at most|no more than|only|in total|total of)\b[^.\n;]{0,25}\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b[^.\n;]{0,12}\bbox(?:es)?\b|"
                           r"\bbox(?:es)?\b[^.\n;]{0,30}\b(?:up to|capped at|limited to|maximum of|in total)\b[^.\n;]{0,12}\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b|"
                           r"\b(?:\d+|two|three|four|five|six|seven|eight|nine|ten)\s+(?:knowledge )?boxes\b[^.\n;]{0,25}\b(?:included|in total|maximum)\b|"
                           r"\$\s?750\b", re.I)


def unqualified_tier_limit(sentence):
    t = sentence or ""
    return bool(_BOX_LIMIT_RE.search(t)) and not _TIER_NAME_RE.search(t)


def behaviour_guarantee(sentence):
    t = sentence or ""
    return bool(VISIBILITY_GUARANTEE_RE.search(t) or CITATION_ABSOLUTE_RE.search(t) or CONTAINMENT_RE.search(t) or ROLE_SWAP_RE.search(t) or LANGUAGE_CLAIM_RE.search(t))


_FOREIGN = {"terms": frozenset()}
YOUR_WORD_RE = re.compile(r"\byour (?:own )?([a-z]{4,})\b", re.I)


def set_foreign_terms(terms):
    _FOREIGN["terms"] = frozenset(terms)


def other_build_vocabulary(sentence):
    """The word, when a sentence addresses the reader as "your <word>" and <word> belongs to another product's demo, never to our canonical documents."""
    for m in YOUR_WORD_RE.finditer(sentence or ""):
        w = m.group(1).lower()
        if w in _FOREIGN["terms"] or (w.endswith("s") and w[:-1] in _FOREIGN["terms"]):
            return w
    return None


def box_per_tenant_default(sentence):
    m = BOX_PER_RE.search(sentence)
    if ELSE_BOX_RE.search(sentence):
        return True
    return bool(m and DEFAULT_WORD_RE.search(sentence) and not _NEGATE_BEFORE_RE.search(sentence))


_CLAIM_SCAN = {"mod": None}


def _claim_scan_module():
    """THE deployment-claim scanner corpus-ingest maintains (corpus/claim_scan.py in the repo, server/data/claim_scan.py in the image), loaded by
    path so the server and the corpus gate cannot drift: shapes A to D, including shape D (the reassurance written as a persona/benefit line,
    "data in your own environment"). Never retyped here."""
    if _CLAIM_SCAN["mod"] is None:
        import importlib.util
        from . import config as _c
        f = _c.data_file("claim_scan.py")
        if f is None:
            raise RuntimeError("claim_scan.py missing: refusing to serve generated text without the deployment-claim scanner")
        spec = importlib.util.spec_from_file_location("claim_scan", f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _CLAIM_SCAN["mod"] = m
    return _CLAIM_SCAN["mod"]


# UNQUALIFIED TIER CAPABILITY (11-12 Oct 2026, the class that survived thirteen reads and came back in a different answer). Where a product is sold in
# tiers, a capability sentence names its tier or it asserts the best one: "PDFs, images, audio, video" is true of the top plan and false of the entry
# plan, which is text-based files only. Reading cannot find it (fluent, grounded, internally consistent), and a sweep for the QUALIFIER cannot find the
# ABSENCE of one, so this sweeps for the CLAIM first - a capability verb within reach of two or more file-type nouns - and then tests each hit for a
# tier word. A hit with none is held. Applied to GENERATED prose only (a quoted passage from our own document is evidence, handled by the passage rules).
_FILE_NOUN_RE = re.compile(r"\b(?:images?|photos?|audio|videos?|recordings?|pdfs?|spreadsheets?|decks?|slides?|scans?|office documents?|word documents?|powerpoint|excel|"
                           r"documents?|files?|file types?|formats?)\b", re.I)
_MEDIA_NOUN_RE = re.compile(r"\b(?:images?|photos?|audio|videos?|recordings?|pdfs?|spreadsheets?|decks?|scans?|office documents?|word documents?|powerpoint|excel)\b", re.I)
_CAPABILITY_VERB_RE = re.compile(r"\b(?:ingest(?:s|ed|ing)?|support(?:s|ed|ing)?|accept(?:s|ed|ing)?|handl(?:e|es|ed|ing)|process(?:es|ed|ing)?|read(?:s|ing)?|"
                                 r"upload(?:s|ed|ing)?|import(?:s|ed|ing)?|index(?:es|ed|ing)?|work(?:s|ing)? with|take(?:s)? in|load(?:s|ed|ing)?)\b", re.I)
_TIER_WORD_RE = re.compile(r"\b(?:starter|pro|enterprise|plans?|tiers?|trial|text-based|published page|per file|750\s?mb|1\.5\s?gb)\b", re.I)


def unqualified_tier_capability(sentence):
    """True when a sentence states what the product ingests/supports across two or more media/file nouns and names no plan or tier."""
    t = sentence or ""
    if not _CAPABILITY_VERB_RE.search(t):
        return False
    if len(set(m.group(0).lower() for m in _MEDIA_NOUN_RE.finditer(t))) < 2:
        return False
    return not _TIER_WORD_RE.search(t)


def claims(text):
    """Names of held-claim classes present in `text`. Empty list means none."""
    out = []
    if DEPLOYMENT_RE.search(text or "") or (text and _claim_scan_module().scan(text)):
        out.append("deployment-mode")
    if ACCURACY_RE.search(text or ""):
        out.append("accuracy-percentage")
    return out


# A sentence unit ends at terminal punctuation or a BLANK line, never at a single newline: a lead-in line
# ("It starts with") and the list items that complete it are one unit, so dropping the unit can never leave a
# dangling fragment ("It starts with added to your licence"). A mutilated sentence is worse than a missing one.
# A LIST ITEM is its own unit too (a line beginning with a bullet or a number): otherwise one offending bullet drops the whole
# list and leaves its lead-in standing alone ("follow these points:" and then nothing - read 7, 11 Oct 2026).
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*\u2022]|\d{1,2}[.)])\s+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])|\n[ \t]*\n+|\n(?=[ \t]*(?:[-*\u2022]|\d{1,2}[.)])[ \t])")


def split_sentences(text):
    """[(start, end, sentence)] with offsets into `text`. Splits on terminal punctuation and newlines."""
    out, pos = [], 0
    for m in _SENT_SPLIT.finditer(text):
        out.append((pos, m.start(), text[pos:m.start()]))
        pos = m.end()
    if pos < len(text):
        out.append((pos, len(text), text[pos:]))
    return out


def clean_answer(text, verbatim=False):
    """Sentence-level hold for generated prose.

    Returns (new_text, offset_map, held) where `held` lists [(class, unit_index)] of withheld units and
    `offset_map(old_offset)` -> new offset or None when that offset fell in a dropped unit. Units are sentences,
    paragraphs and LIST ITEMS. A unit comes back whole or not at all, and a LEAD-IN (a unit ending in a colon, or
    followed by list items) whose items were all withheld is withheld with them: a stem that promises a list and
    delivers nothing is worse than a refusal.
    """
    sents = split_sentences(text)
    n = len(sents)
    cls = [None] * n
    for i, (s, e, sent) in enumerate(sents):
        c = claims(sent) or (["platform-string"] if HOST_RE.search(sent) else []) or (["self-narration"] if SELF_NARRATION_RE.search(sent) else []) \
            or (["doc-self-reference"] if DOC_SELF_REFERENCE_RE.search(sent) else []) or (["internal-nomenclature"] if INTERNAL_API_RE.search(sent) else []) \
            or (["build-voice"] if BUILD_VOICE_RE.search(sent) else []) or (["citation-key"] if CITATION_KEY_RE.search(sent) else []) \
            or (["invented-quality-term"] if QUALITY_TERM_RE.search(sent) else []) \
            or (["route-reference"] if route_reference(sent) else []) or (["box-per-tenant-default"] if box_per_tenant_default(sent) else []) \
            or (["unqualified-tier-capability"] if unqualified_tier_capability(sent) else []) \
            or (["other-build-vocabulary"] if other_build_vocabulary(sent) else []) or (["behaviour-guarantee"] if behaviour_guarantee(sent) else []) \
            or (["unqualified-tier-limit"] if unqualified_tier_limit(sent) else [])
        cls[i] = c[0] if c else None
    # orphaned lead-ins, to a fixed point
    changed = True
    while changed:
        changed = False
        for i in range(n):
            t = sents[i][2].rstrip()
            if cls[i] or _LIST_ITEM_RE.match(sents[i][2]) or not t:
                continue
            if not t.endswith(":") and t[-1:] in ".!?":
                continue
            j = i + 1
            followers = []
            while j < n and _LIST_ITEM_RE.match(sents[j][2]):
                followers.append(j)
                j += 1
            if not followers and j < n:
                followers = [j]
            if t.endswith(":") and (not followers or all(cls[k] for k in followers)):
                cls[i] = "orphaned-lead-in"
                changed = True
            elif followers and _LIST_ITEM_RE.match(sents[followers[0]][2]) and not t.endswith(":") and t[-1:] not in ".!?" and any(cls[k] for k in followers):
                # an unpunctuated stem ("It starts with") continues INTO its items: losing one item changes what it says
                cls[i] = "orphaned-lead-in"
                changed = True
    for i in range(n):                           # the items of a withheld lead-in go with it: a bullet with no stem is a fragment
        if cls[i] == "orphaned-lead-in":
            j = i + 1
            while j < n and _LIST_ITEM_RE.match(sents[j][2]):
                cls[j] = cls[j] or "orphaned-item"
                j += 1
    kept, held, spans = [], [], []
    cur = 0
    prev_end = None
    for i, (s, e, sent) in enumerate(sents):
        if cls[i]:
            held.append((cls[i], i))
            spans.append((s, e, None, None))
            prev_end = e
            continue
        cs = clean(sent, verbatim)
        if kept:
            gap = text[prev_end:s] if prev_end is not None else ""
            sep = gap if gap and gap.strip() == "" else " "      # keep the ORIGINAL separator, so a model's list stays a list
            kept.append(sep)
            cur += len(sep)
        spans.append((s, e, cur, len(cs)))
        kept.append(cs)
        cur += len(cs)
        prev_end = e
    new_text = "".join(kept)

    def offset_map(old):
        for s, e, ns, nl in spans:
            if s <= old <= e:
                return None if ns is None else ns + min(nl, max(0, old - s))
        # Past the end of the text (the platform's citation spans can run a few characters beyond the
        # answer it returned): attach to the end of the last sentence if that one was kept, else drop.
        if spans and old > spans[-1][1] and spans[-1][2] is not None:
            return spans[-1][2] + spans[-1][3]
        return None
    return new_text, offset_map, held


# ---- EXCERPT hygiene: a derived surface (source-card passages, asset excerpts) shows a fragment of a resource, and a resource
# legitimately carries things a visitor must never see in a fragment: markdown tables, emphasis markers, and PRODUCTION
# DIRECTIONS from a film script ([pause], [beat], [music], timecodes). Nothing that scans answers, served corpus text or detail
# pages reads the excerpt field (round-2 tester, 11 Oct 2026), so it is cleaned here and scanned as its own population.
_TABLE_LINE_RE = re.compile(r"^\s*\|.*$|^[^|\n]*\|[^|\n]*\|.*$", re.M)
_TABLE_SEP_RE = re.compile(r"^[\s|:-]{3,}$", re.M)
DIRECTION_RE = re.compile(
    r"\[\s*(?:pause|beat|music|sfx|sound|silence|cut|b-?roll|vo|v/o|voice-?over|narrator|on[- ]?screen|text on screen|transition|fade[^\]]{0,20}|"
    r"long pause|short pause|breath|laughs?|applause|s\d{1,2} [a-z]{3,20})\b[^\]]{0,40}\]|"
    r"\[\s*\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?\s*(?:-+|\u2013)?\s*(?:\d{1,2}:\d{2}(?::\d{2})?)?\s*\]|"
    r"\((?:pause|beat|music|sfx|silence)\)|^\s*\d{1,2}:\d{2}(?::\d{2})?\s+(?=[A-Z])", re.I | re.M)
_EMPH_RE = re.compile(r"(\*\*|__|`)")


def excerpt_clean(text):
    """Raw resource text -> text safe to show as a fragment. Removes markdown table rows and separators, production directions
    (as a CLASS: any bracketed pause/beat/music/sfx/narrator/on-screen direction, bracketed or leading timecodes) and emphasis
    markers. Substitution and deletion only: it never rewrites a sentence's wording."""
    t = text or ""
    t = _TABLE_SEP_RE.sub("", _TABLE_LINE_RE.sub("", t))
    t = DIRECTION_RE.sub(" ", t)
    t = _EMPH_RE.sub("", t)
    t = re.sub(r"^\s{0,3}#{1,6}\s+", "", t, flags=re.M)
    return re.sub(r"[ \t]{2,}", " ", t)


def excerpt_violations(text):
    """What a shown excerpt must NOT contain; used by the scan and the selftest. Names the class, never silently passes."""
    out = []
    if "|" in (text or ""):
        out.append("table-fragment")
    if DIRECTION_RE.search(text or ""):
        out.append("production-direction")
    if "**" in (text or "") or "__" in (text or "") or "`" in (text or ""):
        out.append("markdown-emphasis")
    if re.search(r"(?m)^\s*#{1,6}\s", text or ""):
        out.append("heading-marker")
    return out


QUOTE_LIMIT = 320
# A "sentence end" that is really an initial or an abbreviation ("D. Kwan", "e.g.", "Inc.") is not a boundary a quote may stop at.
_ABBREV_TAIL_RE = re.compile(r"(?:^|\s)(?:[A-Z]|e\.g|i\.e|vs|etc|Inc|Ltd|Dr|Mr|Ms|Mrs|No|approx|Fig|St)\.$")


def quote_window(flat, limit=QUOTE_LIMIT):
    """The quotation shown for a source paragraph: it STARTS at the paragraph start (choosing where a quote begins is selection, and selecting the
    sentence that best supports a claim is cherry-picking dressed as evidence) and ENDS at the last COMPLETE sentence inside `limit` characters.
    A character cut severs a figure from its unit and leaves a stem with nothing after it (the same defect as a history window cut by characters).
    A paragraph that fits whole is shown whole. If no complete sentence fits, returns "" and the paragraph is not a source: a fragment is not shown."""
    flat = " ".join((flat or "").split())
    if len(flat) <= limit:
        return flat
    end = 0
    for m in re.finditer(r"[.!?][\"')\]]*(?=\s|$)", flat[:limit + 1]):
        stop = m.end()
        if stop <= limit and not _ABBREV_TAIL_RE.search(flat[:stop]):
            end = stop
    return flat[:end].strip()


_KIND_NOUN = r"(?:slide deck|deck|film|video|demo|guide|document|whitepaper|white paper|podcast|calculator|reference|primer|walkthrough)"


def _nz(t):
    return re.sub(r"[^a-z0-9 ]", "", " ".join((t or "").lower().split()))


def strip_description_prefix(text, description):
    """The paragraph with OUR OWN inserted card description removed when it is a byte-for-byte PREFIX of it. (13 Oct 2026, lead's ruling.)
    Every released body opens with its card description, and the platform paginates by length and sentence rather than by newline, so the
    first paragraph it hands back is our insert GLUED to the document's real first paragraph. Stripping our insert restores the source's own
    boundary; it does not choose a start inside the source, which is why this is not the selected-quotation act that is forbidden.
    MECHANICAL, never judgement: the exact description string must begin the text, only the separator whitespace after it goes too, and a
    text that does not begin with it is returned untouched. Returns "" when nothing remains (the paragraph WAS the description)."""
    d = (description or "").strip()
    if not d or not text or not text.startswith(d):
        return text
    return text[len(d):].lstrip()


def is_description_echo(window, title="", description=""):
    """True when a paragraph is the asset's OWN CARD COPY rather than evidence from it: it begins with the asset's card description, or it is
    the title, or it is the title followed by "is a <kind>". Our own marketing line quoted back to the visitor as the support for a claim is a
    complete sentence and not a supporting one (read of 12 Oct 2026); after the corpus release every asset body OPENS with its description,
    so without this rule every asset-sourced citation would quote it."""
    w = _nz(window)
    if not w:
        return False
    d = _nz(description)
    if d and len(d) >= 30 and (w.startswith(d[:80]) or d.startswith(w[:80]) and len(w) >= 30):
        return True
    t = _nz(title)
    if t and (w == t or re.match(re.escape(t) + r"\s+(?:is|are)\s+(?:a|an|the)\b", w)):
        return True
    return bool(re.match(r"^.{0,90}?\bis (?:a|an) " + _KIND_NOUN + r"\b", w))


def without_held(text, held):
    """The raw generated text with the withheld units removed and NOTHING else changed: what the model wrote, minus what was held."""
    idx = {i for _c, i in held}
    return " ".join(sent for i, (_s, _e, sent) in enumerate(split_sentences(text)) if i not in idx)


def normalisations(text, held):
    """Kinds of deterministic, presentational post-generation edits clean() made to the units that were KEPT, for the
    provenance record: so the store never implies the model wrote text it did not write."""
    idx = {i for _c, i in held}
    kinds = set()
    for i, (_s, _e, sent) in enumerate(split_sentences(text)):
        if i in idx:
            continue
        s1 = _CAPS_RUN_RE.sub(_lower_caps_run, sent)
        s2 = australian(s1)
        if s1 != sent:
            kinds.add("capitalised-emphasis-lowercased")
        if s2 != s1:
            kinds.add("us-spelling-respelled")
        if clean(sent) != s2:
            kinds.add("wording-substituted")
    return sorted(kinds)


def mostly_withheld(raw, new, threshold=0.5):
    """True when withholding removed more than `threshold` of the answer: what remains no longer represents it."""
    return bool(raw) and len(new.strip()) < threshold * len(raw.strip())


def leaks(text):
    """Strings that must never reach a client. Used by selftest and by the response scrubber."""
    found = []
    for name, rx in (("acronym", ACRONYM_RE), ("platform-name", PLATFORM_NAME_RE),
                     ("endpoint", ENDPOINT_RE), ("host", HOST_RE), ("banned-word", BANNED_RE)):
        if rx.search(text or ""):
            found.append(name)
    found += claims(text)
    if "—" in (text or ""):
        found.append("em-dash")
    return found
