"""Grounded question answering over a crawled site.

The platform answers and cites from the ingested pages. Some questions are about the site's STRUCTURE
(which pages lack markup, where facts conflict) and cannot be answered from page text, so the
application assembles those facts from its own analysis and hands them to the model as extra context.
That context is returned openly in `analysis_context`: it is an application service, not a platform feature."""
import re

from . import arag, store
from .schema import AskResponse, Citation

GAP_Q = re.compile(r"structured data|markup|json-?ld|schema|missing|invalid|coverage|gap", re.I)
CONFLICT_Q = re.compile(r"conflict|contradict|inconsisten|disagree|differ|mismatch", re.I)
ALIAS_Q = re.compile(r"(?:more than one|two|three|multiple|several|different|another|alternat\w+|other|both|variant|inconsistent\w*)\s+(?:\w+\s+){0,3}names?\b|\bnames?\s+(?:\w+\s+){0,3}(?:differ\w*|inconsisten\w*|vary|varies)|\bunder (?:another|a different|different|multiple|two|several|more than)\b|\bduplicat|\btwice\b|\bsame (?:\w+ ){0,3}(?:person|thing|entity|product|place|organi[sz]ation|company|one|item|record|event|service|people)|\bmerg|\bsynonym|\baliases?\b|\balso (?:known|called|written|named)|\ba\.?k\.?a\b|\brenam|\brebrand|referred to (?:\w+ ){0,3}(?:differently|inconsisten\w*|more than|by (?:different|two))|\b(?:called|named|written|spelt|spelled)\s+(?:\w+\s+){0,3}(?:differently|two|both)|\bunder (?:\w+ ){0,2}names?\b|\bmisspell|\bsame as\b|\bwhat to call\b|\bcall (?:the|this|that|it)\b.*\bdifferent", re.I)
DECLINE = re.compile(r"not enough (data|information)|don't have enough|do not have enough|cannot find|no information", re.I)


def _context(sid, question):
    """Facts the application computed itself, each tied to the pages it was computed from.
    Returns (items, structural) where item = {"text": str, "rids": [resource ids]}."""
    g = store.get("entities", sid) or {"nodes": [], "edges": [], "conflicts": []}
    pages = {p["id"]: p for p in store.all_("pages", sid)}
    by_url = {p["url"]: p for p in pages.values()}
    rid_of = lambda pid=None, url=None: (pages.get(pid) or by_url.get(url) or {}).get("rid")
    ql = question.lower()
    items = []

    def add(text, *rids, label="", values=(), need=0):
        r = [x for x in dict.fromkeys(rids) if x]
        if r:
            items.append({"text": text, "rids": r, "label": label, "values": [str(v) for v in values], "need": need})
    nodes = {n["id"]: n for n in g["nodes"]}
    hit = [n for n in g["nodes"] if n["type"] != "WebPage" and n["label"].lower() in ql]
    qa = _ascii(ql)
    for n in g["nodes"]:       # the question names a KIND of thing ('the cafes'): supply the entities of that type, with their type, so a product is never read as a cafe
        if n not in hit and n["type"] != "WebPage" and len(hit) < 12 and any(_plural_in(p_, qa) for p_ in _type_phrases(n["type"])):
            hit.append(n)
    for n in hit[:6]:
        for k, v in n["properties"].items():
            # cite a page of this entity whose own text states the value, never merely the first page it appears on
            vt = set(_toks(str(v)))
            src = next((x["page_id"] for x in n["pages"] if vt and vt <= set(_toks((pages.get(x["page_id"]) or {}).get("text") or ""))), None)
            if src:
                add(f"{n['label']} ({n['type']}) has {k}: {v}.", rid_of(pid=src), label=n["label"], values=[v], need=1)
    ids = {n["id"] for n in hit}
    for e in g["edges"]:
        if e["support"] != "navigation" and (e["source"] in ids or e["target"] in ids):
            add(f"{nodes[e['source']]['label']} {e['label'] or e['predicate']} {nodes[e['target']]['label']}.", rid_of(url=e["provenance"]["source_url"]), label=nodes[e["source"]]["label"], values=[nodes[e["target"]]["label"]], need=1)
    if not CONFLICT_Q.search(question):          # the conflict question below supplies them all; any other question still gets the ones about what it names
        for c in g["conflicts"]:
            if c["entity_label"].lower() in ql:
                vals = "; ".join(f"'{v['value']}' on {v['url']}" for v in c["values"])
                add(f"Conflict for {c['entity_label']} {c['property']}: {vals}.", *[rid_of(pid=v["page_id"]) for v in c["values"]],
                    label=c["entity_label"], values=list(dict.fromkeys(v["value"] for v in c["values"])), need=min(2, len(c["values"])))
    structural = bool(GAP_Q.search(question) or CONFLICT_Q.search(question))
    if GAP_Q.search(question):
        for p in pages.values():
            if p.get("status") == "ingested":
                add(f"Structured data on {p.get('title') or p['url']} ({p['url']}): {p.get('structured_data', 'none').replace('_', ' ')}."
                    + (f" Types: {', '.join(p.get('existing_types', []))}." if p.get("existing_types") else ""), p.get("rid"),
                    label=(p.get("title") or "").split(" | ")[0], need=0)
    if CONFLICT_Q.search(question):
        for c in g["conflicts"]:       # a conflict's evidence is BOTH sides of it
            vals = "; ".join(f"'{v['value']}' on {v['url']}" for v in c["values"])
            add(f"Conflict for {c['entity_label']} {c['property']}: {vals}.", *[rid_of(pid=v["page_id"]) for v in c["values"]],
                label=c["entity_label"], values=list(dict.fromkeys(v["value"] for v in c["values"])), need=min(2, len(c["values"])))
    return items[:60], structural


def _ascii(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _type_phrases(tp):
    """'CafeOrCoffeeShop' -> ['cafe', 'coffee shop']; 'Person' -> ['person', 'people']."""
    if tp in ("Thing", "WebPage", "Place", "Organization"):
        return []                                            # too broad to mean 'the question named this kind'
    out = [" ".join(re.findall(r"[A-Z][a-z]+", x)).lower() for x in re.split(r"Or(?=[A-Z])", tp)]
    return out + (["people", "staff", "employee", "team member"] if tp == "Person" else [])


def _plural_in(phrase, qa):
    return bool(phrase) and bool(re.search(r"\b" + re.escape(phrase) + r"(?:s|es)?\b", qa))


def _computed_notes(sid, question, items):
    """For each entity the question names, say what the application computed: a conflict the detector found (those are items, above),
    none where it found none, and any flagged possible duplicate. Silence would leave the model to decide for itself whether two
    figures contradict. Not attributable items: they support no sentence."""
    g = store.get("entities", sid) or {}
    ql = question.lower()
    named = [n for n in g.get("nodes", []) if n["type"] != "WebPage" and n["label"].lower() in ql]
    have = {c["entity_label"].lower() for c in g.get("conflicts", [])}
    out = [f"No disagreement between pages was computed for {n['label']}. Two different figures about different things (a part and a whole, a seasonal and a standing figure) are not a disagreement."
           for n in named[:4] if n["label"].lower() not in have]
    for a in g.get("ambiguities", []):
        if a.get("status") == "needs_review" and any(lbl.lower() in ql for lbl in a["labels"]):
            out.append(f"Possible duplicate flagged for review (not confirmed): {a['reason']}")
    return out[:8]


PROP_WORDS = {"maximumAttendeeCapacity": "capacity seats seating attendee attendees", "memberCount": "members member membership", "openingHours": "hours open opening opens closes",
              "price": "price cost costs prices", "offers": "price cost costs prices offer", "telephone": "phone telephone number", "email": "email",
              "startDate": "date dates start starts", "endDate": "date dates end ends", "foundingDate": "founded founding established", "jobTitle": "role title position",
              "address": "address location", "numberOfEmployees": "employees staff"}
CONFLICT_WORD = re.compile(r"\b(?:conflict\w*|contradict\w*|inconsisten\w*|disagree\w*|discrepan\w*)\b", re.I)


def _conflict_guard(sid, text, question=""):
    """A generated sentence may say two pages conflict only where the application's own detector found two statements about the
    same property of the same entity. The model does not get to decide what a contradiction is. A sentence that says it and
    names no computed (entity, property) pair is withheld. Returns (text, withheld_count)."""
    from .resolve import norm_name
    g = store.get("entities", sid) or {}
    conflicts = g.get("conflicts", [])
    phr = lambda x: " " + norm_name(x) + " "
    cut = []
    for start, end, seg, ctx in _claims(text):
        if not CONFLICT_WORD.search(seg):
            continue
        ns = " " + " ".join(re.findall(r"\w+", (ctx + " " + seg).lower())) + " "
        words = set(re.findall(r"\w+", (ctx + " " + seg + " " + question).lower()))
        ok = False
        for c in conflicts:
            if phr(c["entity_label"]) not in ns:
                continue
            prop = c["property"]
            syn = set(PROP_WORDS.get(prop, "").split()) | {w.lower() for w in re.findall(r"[A-Z]?[a-z]+", prop)}
            if syn & words:
                ok = True
                break
        if not ok:
            cut.append((start, end))
    for start, end in reversed(cut):
        text = text[:start] + text[end:]
    return re.sub(r"\n{3,}", "\n\n", text).strip(), len(cut)


ABSENCE = re.compile(r"\b(?:does|do|did) not (?:say|state|specify|provide|mention|list|give|include|name|describe|show|contain|have)\b|\bnot (?:stated|specified|provided|mentioned|listed|given|available)\b|\bno (?:address|location|price|information|details?|hours|phone|dates?)\b|\bunknown\b|\bdoes(?:n't| not) say\b", re.I)
INFO_KINDS = {"opened": (r"\b(?:opened|opening dates?|open dates?|founded|founding|established|when did|when was)\b", ("foundingDate", "startDate"),
                         r"\b(?:opened|founded|established|since|launched)\b[^.]{0,40}\b(?:19|20)\d{2}\b"),
              "address": (r"\b(?:where|located|locations?|situated|address(?:es)?|based)\b", ("address", "location", "containedInPlace"),
                          r"\b\d+[A-Za-z]?\s+[A-Z][a-z]+|\b(?:at|in|on|near|off|under)\s+(?:the\s+)?(?:[a-z]+\s+){0,3}[A-Z][a-z]+"),
              "price": (r"\b(?:prices?|cost|costs|how much)\b", ("price", "offers"), r"[A-Z]?\$\s?\d|\b\d+\.\d{2}\b"),
              "hours": (r"\b(?:hours|opening hours|closes?|closing|opens at)\b", ("openingHours",),
                        r"\b\d{1,2}[:.]\d{2}\b|\b\d{1,2}\s?(?:am|pm)\b|\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\b"),
              "title": (r"\b(?:job titles?|titles?|roles?|positions?)\b", ("jobTitle",),
                        r"\b(?:Head|Chief|Senior|Junior|Deputy|Assistant|Managing|General|Technical|Volunteer|Executive|Founder|Director|Manager|Curator|Coordinator|Officer|Roaster|Barista|Chair\w*|President|Secretary|Treasurer|Trustee|Engineer|Librarian)\b"),
              "phone": (r"\b(?:phone|telephone|number)\b", ("telephone",), r"\b\d{4}\s?\d{4}\b|\+?\d[\d ()-]{7,}"),
              "email": (r"\b(?:email|e-mail)\b", ("email",), r"@")}
CAPRUN = re.compile(r"[A-Z][\w'-]+(?:\s+[A-Z][\w'-]+)*")
SKIP_RUNS = {"the", "site", "text", "pages", "page", "website", "it", "this", "however", "also"}


def _norm_words(s):
    return " ".join(re.findall(r"\w+", _ascii(s).lower()))


def _absence_status(g, pages, seg, tail="", rest=""):
    """Is the fact a denial says is missing held by the application or by the page text?
    'held' - it is, so the denial is false; 'absent' - the entity (or kind of thing) is identified and neither the graph nor any page
    states the fact, so the denial is verified; 'unknown' - the sentence does not identify what it is about, so it cannot be checked."""
    sa = _ascii(seg).lower()
    nodes = [n for n in g.get("nodes", []) if n["type"] != "WebPage"]
    kinds = [k for k, v in INFO_KINDS.items() if re.search(v[0], sa)]
    # the graph's own property set decides what else is answerable: a denial that names any property the graph records (by its
    # name or its everyday words) is judged against the graph, with no page-text pattern for kinds not listed above
    known_props = {p for n in nodes for p in n["properties"]} - {"name", "url", "image", "description", "@type"}
    covered = {p for k in kinds for p in INFO_KINDS[k][1]}
    dyn = {}
    for p in known_props - covered:
        words = PROP_WORDS.get(p, "").split() or [w.lower() for w in re.findall(r"[A-Z]?[a-z]{4,}", p)]
        if words and re.search(r"\b(?:" + "|".join(map(re.escape, words)) + r")s?\b", sa):
            dyn[p] = (None, (p,), None)
    if not kinds and not dyn:
        return "unknown"
    loc_src = {e["source"] for e in g.get("edges", []) if e["predicate"] in ("location", "containedInPlace")}
    runs = [_norm_words(m.group()) for m in CAPRUN.finditer(seg + " " + tail)]
    runs = [r for r in runs if r and r not in SKIP_RUNS]
    chosen = [n for n in nodes if any(r and (" " + r + " ") in (" " + _norm_words(n["label"]) + " ") for r in runs)]
    other = bool(re.search(r"\b(?:beyond|other than|besides|except|apart from|aside from|others?|remaining|rest of)\b", sa)) and any(
        _plural_in(p_, sa) for n in nodes for p_ in _type_phrases(n["type"]))
    if other:                   # 'any staff job titles beyond Tamsin': the entities of that kind OTHER than the ones named
        named_w = set(_norm_words(seg + " " + tail + " " + rest).split())
        GENERIC_W = ("cafe", "coffee", "shop", "the", "and")
        chosen = [n for n in nodes if any(_plural_in(p_, sa) for p_ in _type_phrases(n["type"]))
                  and not all(w in named_w for w in ([x for x in _norm_words(n["label"]).split() if x not in GENERIC_W] or _norm_words(n["label"]).split()))]
    if other and not chosen:    # nobody else of that kind is in the graph: the page text could still hold them, so this cannot be verified here
        return "unknown"
    if not chosen:              # 'the other cafes': every entity of the kind the sentence names, except those the rest of the answer already addresses
        rest_w = set(_norm_words(rest).split())
        for n in nodes:
            distinct = [w for w in _norm_words(n["label"]).split() if w not in ("cafe", "coffee", "shop", "the", "and")]
            if any(_plural_in(p_, sa) for p_ in _type_phrases(n["type"])) and distinct and not all(w in rest_w for w in distinct):
                chosen.append(n)
    if not chosen:
        return "unknown"
    for n in chosen:
        lab = _norm_words(n["label"])
        for k in kinds + list(dyn):
            spec = INFO_KINDS.get(k) or dyn[k]
            if any(n["properties"].get(p) for p in spec[1]) or (k == "address" and n["id"] in loc_src):
                return "held"
            if spec[2] is None:
                continue
            for pg in pages:                                  # the page text may state it where extraction did not
                for sn in _sentences(pg.get("text") or ""):
                    if (" " + lab + " ") in (" " + _norm_words(sn) + " ") or all(w in _norm_words(sn).split() for w in lab.split()[:2]):
                        body = re.sub(re.escape(n["label"]), " ", sn, flags=re.I)
                        if re.search(spec[2], body):
                            return "held"
    return "absent"


def _absence_guard(sid, text, pages=()):
    """'The site does not say X' is itself a claim, and it is false when the application or the page text holds X for that entity.
    Such a denial is withheld, never shown above a citation that contains the fact. Returns (text, withheld_count)."""
    g = store.get("entities", sid) or {}
    cut = []
    for start, end, seg, ctx in _claims(text):
        if not ABSENCE.search(seg):
            continue
        tail = ""
        if seg.rstrip().endswith(":"):       # 'does not provide their addresses:' denies for the entities in the list that follows
            keep = []
            for ln in text[end:].split("\n")[1:]:
                if not re.match(r"\s*(?:[-*\u2022]|\d+[.)])\s", ln):
                    break
                keep.append(ln)
            tail = " ".join(keep)
        if _absence_status(g, pages, seg, tail, text[:start] + text[end:]) == "held":
            cut.append((start, end))
    for start, end in reversed(cut):
        text = text[:start] + text[end:]
    return re.sub(r"\n{3,}", "\n\n", text).strip(), len(cut)


def _value_tokens(prop, s):
    """The comparable values a sentence states for a property: times for hours, money for prices, years/dates for dates, digit runs otherwise."""
    s = _ascii(s)
    if prop == "openingHours":
        out = set()
        for m in re.finditer(r"\b(\d{1,2})(?:[:.](\d{2}))?\s?(am|pm)?\b", s, re.I):
            h, mi, ap = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower()
            if m.group(2) is None and not ap:
                continue
            if ap == "pm" and h < 12:
                h += 12
            if ap == "am" and h == 12:
                h = 0
            if h < 24 and mi < 60:
                out.add(f"{h:02d}:{mi:02d}")
        return out
    if prop in ("price", "offers"):
        return {f"{float(x.replace(',', '')):.2f}" for x in re.findall(r"(?:\$|aud\s?)\s?(\d+(?:[.,]\d+)?)", s, re.I)} | {f"{float(x):.2f}" for x in re.findall(r"\b(\d+\.\d{2})\b", s)}
    if prop in ("foundingDate", "startDate", "endDate"):
        return set(re.findall(r"\b(?:19|20)\d{2}\b", s))
    return {x for x in re.findall(r"\b\d{2,}\b", s)}


def _conflict_values_guard(sid, text, question=""):
    """Where a conflict is computed, the values an answer attributes to that entity and property must be the computed ones. A value the
    detector did not hold (for example another entity's hours) is a fabrication inside a true statement, and is withheld.
    Returns (text, withheld_count)."""
    from .resolve import norm_name
    g = store.get("entities", sid) or {}
    cut = []
    for start, end, seg, ctx in _claims(text):
        ns = " " + " ".join(re.findall(r"\w+", _ascii(ctx + " " + seg).lower())) + " "
        words = set(re.findall(r"\w+", (ctx + " " + seg + " " + question).lower()))
        for c in g.get("conflicts", []):
            if (" " + " ".join(re.findall(r"\w+", _ascii(c["entity_label"]).lower())) + " ") not in ns:
                continue
            prop = c["property"]
            if not ((set(PROP_WORDS.get(prop, "").split()) | {w.lower() for w in re.findall(r"[A-Z]?[a-z]+", prop)}) & words):
                continue
            stated = _value_tokens(prop, seg)
            computed = set().union(*[_value_tokens(prop, str(v["value"])) for v in c["values"]]) if c["values"] else set()
            if stated and computed and not stated <= computed:
                cut.append((start, end))
                break
    for start, end in reversed(cut):
        text = text[:start] + text[end:]
    return re.sub(r"\n{3,}", "\n\n", text).strip(), len(cut)


GENERIC_CLAIM = set("price prices cost costs costing listed lists list section sections bag bags per another additional mentions shows states line row table page pages one two both".split())
STOP = set("the a an and or of to in on at for by with from is are was were be been it its this that these those as which who what where when how not no do does did has have had can will may also than then there their they them his her he she we our you your i me my provided text context information contains contain conflicting regarding following according states state page pages site website one two both however additionally also".split())


def _toks(s):
    out = []
    for x in re.findall(r"[a-z0-9$][a-z0-9.'$-]*", s.lower().replace("\u2019", "'")):
        x = re.sub(r"^(?:a|au|us|nz)?\$", "", x.strip(".'-"))        # A$15.50 and 15.50 are the same token
        if x and x not in STOP and len(x) > 1:
            out.append(x)
    return out


ABBR = re.compile(r"\b(?:[A-Z]|Dr|Mr|Mrs|Ms|Prof|St|Mt|No|vs|etc|e\.g|i\.e)\.(?=\s)")


def _protect(t):
    """Stop an initial or title abbreviation ('T. Hartley', 'Dr. Rao') being read as the end of a sentence."""
    return ABBR.sub(lambda m: m.group()[:-1] + "\u2024", t)


def _restore(t):
    return t.replace("\u2024", ".")


def _sentences(body):
    return [_restore(x).strip() for x in re.split(r"(?<=[.!?])\s+|\n+", _protect(body)) if x.strip()]


def _words(s):
    return set(re.findall(r"\w+", s.lower()))


def _claims(text):
    """Split an answer into checkable claims: list items and sentences, with character offsets and the enclosing
    heading/bullet chain as context (a nested bullet often carries its subject in the line above)."""
    out, stack = [], []
    for m in re.finditer(r"[^\n]+", text):
        raw = m.group()
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        ctx = " ".join(x[1] for x in stack) + " " + line
        stack.append((indent, line))
        is_item = bool(re.match(r"[-*\u2022]|\d+[.)]", line))
        praw = _protect(raw)
        for sm in re.finditer(r"(?:[^.!?]|[.!?](?!\s|$))+(?:[.!?]+(?=\s|$)|$)", praw):
            seg = _restore(sm.group())
            if len(_toks(seg)) >= (1 if is_item else 2):
                out.append((m.start() + sm.start(), m.start() + sm.start() + len(seg.rstrip()), seg.strip(), ctx))
    return out


LEAD_IN = re.compile(r"^(?:based on|according to|from|using) the (?:provided|retrieved|available|given|supplied|above)?\s*(?:text|context|information|pages?|content|excerpts?|sources?)\b", re.I)
INTRODUCES = re.compile(r"\b(?:as follows|the following|listed below|see below|here (?:is|are)|details? (?:is|are) (?:below|as follows))\b", re.I)
HEDGE = re.compile(r"\b(?:only )?partly (?:cover|answer)", re.I)      # a denial ('the site does not say X') is NOT here: it asserts an absence and must be checked


def _non_assertion(seg):
    """A sentence that asserts no fact about the site: it introduces a list, opens with 'based on the provided text', or says
    the pages are silent. It has nothing to be sourced from, so it is neither supported nor unsupported. The test is narrow on
    purpose: any figure, or any proper name other than the sentence's first word, makes it a claim again."""
    s = seg.strip()
    if any(ch.isdigit() for ch in s):
        return False
    if s.endswith(":") and len(s.split()) <= 30:                  # 'The site states that the cafes are located in the following places:' introduces the list that carries the facts
        return True
    if re.search(r"(?<=[a-z,;] )[A-Z][\w'-]+", s):             # a capitalised word mid-sentence names something
        return False
    if INTRODUCES.search(s) or HEDGE.search(s):
        return True
    m = LEAD_IN.match(s)
    return bool(m and not _toks(s[m.end():]))


def _attribute(text, candidates, items=(), items_first=False, detail=None, absence_check=None, record_check=None):
    """Per-claim citation, assembled and checked by the application. A page supports a claim only when it contains the
    claim's distinctive words; an application-computed fact supports a claim the same way and then cites every page it was
    computed from (both sides of a conflict). The platform's own span-to-paragraph mapping attributed every span to every
    retrieved paragraph on multi-page answers, so it is not trusted for placement.
    Returns (marked_text, citations, unsupported, used_items)."""
    sources = []   # (words, [rids], title tokens, kind)
    for rid, p in candidates:
        sources.append((set(_toks((p.get("title") or "") + " " + (p.get("text") or ""))), [rid], set(_toks(p.get("title") or "")), "page"))
    isrc = [(it, set(_toks(it["text"])), it["rids"]) for it in items]
    pmap = {rid: p for rid, p in candidates}
    title_toks = {rid: set(_toks(p.get('title') or '')) for rid, p in candidates}   # a page about one thing supplies the subject of its figures
    sent_toks = {rid: [(x, set(_toks(x))) for x in _sentences(p.get('text') or '') if not x.lstrip().startswith('#')] for rid, p in candidates}
    chosen, per_claim, unsupported, used_items = {}, [], 0, 0
    nonassert, with_figure, unsupported_segs, verified_absence, traced = 0, 0, [], 0, 0
    for start, end, seg, line in _claims(text):
        ct = set(_toks(seg))
        lt = set(_toks(line))
        line_ctx = line
        scored = []
        for rank, (it, words, rids) in enumerate(isrc):       # computed facts: matched on the entity and its values (read at line level)
            lab = _words(it["label"])
            phrase = " " + " ".join(re.findall(r"\w+", it["label"].lower())) + " "     # the name as a whole phrase: 'Our coffee' is not in 'Our story ... Coffee'
            if lab and phrase in " " + " ".join(re.findall(r"\w+", line_ctx.lower())) + " ":
                hits = sum(1 for v in it["values"] if set(_toks(v)) and set(_toks(v)) <= lt)
                if hits >= it["need"] and (hits or not it["values"]):
                    scored.append((-1.0, -len(it["label"].split()), rank, rids, "item"))
        if not scored:
            for rank, (words, rids, tt, kind) in enumerate(sources):
                sc = len(ct & words) / len(ct)
                nums = {t for t in ct if any(ch.isdigit() for ch in t)}
                sts = sent_toks.get(rids[0], [])
                distinct = ct - nums - GENERIC_CLAIM
                if nums:   # the evidence unit is a sentence, a table row or a list item: it must hold every figure and share the claim's subject
                    unit_ok = any(nums <= st and len(ct & st) >= 2 and (not distinct or bool(distinct & (st | title_toks.get(rids[0], set())))) for _x, st in sts)
                    ok = unit_ok
                else:
                    carry = max((len(ct & st) for _x, st in sts), default=0)
                    ok = sc >= 0.75 and carry >= max(2, (len(ct) + 1) // 2)
                if ok:
                    scored.append((-sc, -len(ct & tt), rank, rids, kind))
        scored.sort()
        if scored and scored[0][4] == "item":
            scored = [x for x in scored if x[1] == scored[0][1]]         # the most specific entity name wins (not a shorter word inside it)
            vals = [v for it in [isrc[x[2]][0] for x in scored] for v in it["values"]]
            if vals and not any(set(_toks(v)) and set(_toks(v)) <= ct for v in vals) and ct != lt:
                scored = []                                              # in a multi-sentence line, mark the sentence that carries the value
        picked, seen_r = [], set()
        for *_x, rids, kind in (scored if scored and scored[0][4] == "item" else scored[:2]):
            used_items += kind == "item"
            for r in rids:
                if r not in seen_r:
                    seen_r.add(r)
                    picked.append(r)
        if not picked and record_check is not None and record_check(seg, line) and not any(ch.isdigit() for ch in seg):
            traced += 1                                     # a statement about the relationship between pages, supported by the site's own conflict record
            per_claim.append((end, seg, picked))
            continue
        if not picked and absence_check is not None and ABSENCE.search(seg) and not _non_assertion(seg):
            tail_ = ""
            if seg.rstrip().endswith(":"):
                tail_ = " ".join(ln for ln in text[end:].split("\n")[1:3])
            if absence_check(seg, tail_, text[:end - len(seg)] + text[end:]) == "absent":
                verified_absence += 1                      # identified, and neither the graph nor any page states it: the denial is true, so it is supported
                per_claim.append((end, seg, picked))
                continue
        if not picked:
            if _non_assertion(seg):
                nonassert += 1
            else:
                unsupported += 1
                unsupported_segs.append(seg)
                with_figure += any(ch.isdigit() for ch in seg)
        per_claim.append((end, seg, picked))
        for r in picked:
            chosen.setdefault(r, len(chosen) + 1)
    marked, last = [], 0
    for end, seg, picks in per_claim:
        while text[end:end + 1] in ('"', "'", ")", "*", "\u201d") and text[end:end + 1]:
            end += 1                                  # keep the marker outside a closing quote or bracket
        marked.append(text[last:end])
        marked.append("".join(f"[{chosen[r]}]" for r in picks))
        last = end
    marked.append(text[last:])
    cites = []
    for rid, n in sorted(chosen.items(), key=lambda kv: kv[1]):
        p = pmap.get(rid)
        if p is None:
            continue
        claims = [seg for _e, seg, picks in per_claim if rid in picks]
        body = p.get("text") or ""
        ct = set(_toks(" ".join(claims))) if claims else set()
        cands_ = [re.sub(r"^[#>*\-\s]+", "", x).strip() for x in _sentences(body) if not x.lstrip().startswith("#")]
        cands_ = [x for x in cands_ if len(x) > 12] or [re.sub(r"^[#>*\-\s]+", "", x).strip() for x in body.split("\n") if x.strip()]
        nums_c = {t for t in ct if any(ch.isdigit() for ch in t)}
        long_ = [u for u in cands_ if len(u) >= 15] or cands_          # a two-word fragment ('Pelling Cove.') is not an excerpt
        best = max(long_, key=lambda x: (nums_c <= set(_toks(x)), len(ct & set(_toks(x))), -len(x)), default="")     # a sentence that carries the claim's words, never a heading
        # several claims can cite one page, so the union of their figures sits in no single unit: judge each claim on its own and show the
        # unit that carries a claim's figures (a price row, not the sentence that merely names the product)
        scored_units = []
        for cl in claims:
            cl_t = set(_toks(cl))
            cl_n = {x for x in cl_t if any(ch.isdigit() for ch in x)}
            if not cl_n:
                continue
            for u in long_:
                ut = set(_toks(u))
                if cl_n <= ut and len(cl_t & ut) >= 2:
                    scored_units.append((len(cl_n), len(cl_t & ut), -len(u), u))
        if scored_units:
            best = max(scored_units)[3]
        else:
            # none of the claims' figures sits in any one unit of this page (the page supports the claim's subject, not its figure):
            # show the unit that shares the most WORDS with a single claim, never a unit that merely contains one of the digits
            by_words = []
            for cl in claims:
                cl_w = {x for x in _toks(cl) if not any(ch.isdigit() for ch in x)}
                for u in long_:
                    ov = len(cl_w & {x for x in _toks(u) if not any(ch.isdigit() for ch in x)})
                    if ov >= 2:
                        by_words.append((ov, -len(u), u))
            if by_words:
                best = max(by_words)[2]
        cites.append(Citation(n=n, page_id=p["id"], url=p["url"], title=p.get("title"), resource_id=rid, excerpt=best[:300], claims=claims[:6]))
    if detail is not None:
        detail.update(traced_to_record=traced, verified_absences=verified_absence, non_assertions=nonassert, unsupported_with_figure=with_figure, unsupported_sentences=unsupported_segs)
    return "".join(marked), cites, unsupported, used_items, len(per_claim) - nonassert


TYPE_WORDS = {"person": ("people", "person", "persons", "staff", "humans", "who", "someone", "anyone", "individuals"),
              "product": ("products", "product", "blends", "coffees", "items", "goods"),
              "place": ("places", "place", "locations", "location", "venues", "venue", "cafes", "cafe", "galleries", "rooms", "buildings", "sites"),
              "org": ("organisations", "organizations", "organisation", "organization", "companies", "company", "orgs", "groups", "bodies", "teams", "departments"),
              "event": ("events", "event", "exhibitions", "exhibition", "shows"),
              "service": ("services", "service", "courses", "course", "programmes", "programs")}
GENERIC_FIRST = {"the", "our", "new", "open", "old", "great", "main", "city", "north", "south", "east", "west"}


def _label_mentioned(label, qnorm, qtoks):
    from .resolve import norm_name
    ln = norm_name(label)
    if not ln:
        return False
    if " " + ln + " " in qnorm:
        return True
    toks = ln.split()
    return len(toks) >= 2 and len(toks[0]) >= 3 and toks[0] not in GENERIC_FIRST and toks[0] in qtoks


def _alias_answer(sid, pages, question=""):
    """Questions about names are answered from the ambiguities and merged names the application already computed, not by a
    model, which invents aliases. The answer respects the question's scope (the kinds of thing it names, or the specific
    names it mentions), says plainly when the answer is none, and cites the sentences where the names appear."""
    from .resolve import group_of, norm_name
    g = store.get("entities", sid) or {}
    nodes = {n["id"]: n for n in g.get("nodes", [])}
    by_pid = {p["id"]: p for p in pages}
    qnorm = " " + " ".join(re.findall(r"\w+", question.lower())) + " "
    qtoks = set(qnorm.split())
    wanted = {grp for grp, words in TYPE_WORDS.items() if any(w in qtoks for w in words)}
    if "person" in wanted and len(wanted) > 1 and "who" in qtoks and not (qtoks & {"people", "person", "persons", "staff"}):
        wanted.discard("person")                   # a bare 'who' alongside another named kind does not mean 'people only'
    kind_phrase = "people" if wanted == {"person"} else "entities of that kind" if wanted else "entities"

    def in_scope(eids):
        if not wanted:
            return True
        return any(group_of(nodes[e]["type"]) in wanted for e in eids if e in nodes)

    named = [n for n in nodes.values() if n["type"] != "WebPage" and _label_mentioned(n["label"], qnorm, qtoks)]
    named_ids = {n["id"] for n in named}
    amb_all = [a for a in g.get("ambiguities", []) if a["status"] == "needs_review"]
    lines, merged = [], []
    head = ""
    if len(named) >= 2 or (named and re.search(r"\bsame\b|\bone\b|\bsynonym|\bidentical", question.lower())):
        pairs = [a for a in amb_all if len(set(a["entity_ids"]) & named_ids) >= (2 if len(named) >= 2 else 1)]
        labels = " and ".join(f"'{n['label']}'" for n in named[:3])
        if pairs:
            head = f"Possibly. SemanticSite has flagged {labels} as possibly the same thing. They have not been merged; a reviewer decides."
            lines = [(a["reason"], list(dict.fromkeys(x["page_id"] for e in a["entity_ids"] for x in nodes.get(e, {}).get("pages", [])))[:4], a["labels"]) for a in pairs]
        else:
            others = [a for a in amb_all if set(a["entity_ids"]) & named_ids]
            head = f"No. SemanticSite has not flagged {labels} as the same thing. This covers only the names it extracted and compared."
            if others:
                lines = [(a["reason"], list(dict.fromkeys(x["page_id"] for e in a["entity_ids"] for x in nodes.get(e, {}).get("pages", [])))[:4], a["labels"]) for a in others]
                head += " It has flagged these related pairs:"
    else:
        for a in amb_all:
            if not in_scope(a["entity_ids"]):
                continue
            lines.append((a["reason"], list(dict.fromkeys(x["page_id"] for e in a["entity_ids"] for x in nodes.get(e, {}).get("pages", [])))[:4], a["labels"]))
        for n in nodes.values():
            if n["type"] != "WebPage" and n.get("aliases") and in_scope([n["id"]]):
                merged.append((f"'{n['label']}' is also written as {', '.join(repr(x) for x in n['aliases'][:5])}; the pages use these names for the same thing.",
                               [x["page_id"] for x in n["pages"]][:4], [n["label"]] + n["aliases"][:5]))
    if not lines and not merged and not head.startswith("Yes"):
        scope_txt = f"No {kind_phrase} appear" if wanted else "No entity appears"
        txt = head or f"{scope_txt} under more than one name, and SemanticSite has no pair of names it could not settle, among the pages it read. This covers only the names it extracted."
        if head:
            txt = head
        return AskResponse(answer=txt, citations=[], grounded=True, basis="site analysis", quality=None, attempts=0, cost={})
    order, out = {}, []

    def render(items):
        for text, pids, labels in items[:20]:
            marks = ""
            for pid_ in pids:
                p = by_pid.get(pid_)
                if p and any(_carries(p, labels)):
                    order.setdefault(pid_, len(order) + 1)
                    marks += f"[{order[pid_]}]"
            out.append(f"- {text}{marks}")
    if head:
        out.append(head)
    elif lines:
        out.append("These names may refer to the same thing. They have not been merged; a reviewer decides." if not wanted else
                   f"Among {kind_phrase}, these names may refer to the same thing. They have not been merged; a reviewer decides.")
    render(lines)
    if merged:
        out += ["", "These names were treated as one entity."]
        render(merged)
    cites = []
    for pid_, n in sorted(order.items(), key=lambda kv: kv[1]):
        p = by_pid[pid_]
        labs = [l for t, ps, lab in lines + merged if pid_ in ps for l in lab]
        best = max(_carries(p, labs), key=lambda x: len(x), default="")
        mine = [t for t, ps, lab in lines + merged if pid_ in ps]
        cites.append(Citation(n=n, page_id=p["id"], url=p["url"], title=p.get("title"), resource_id=p.get("rid"), excerpt=best[:300], claims=mine[:6]))
    return AskResponse(answer="\n".join(out), citations=cites, grounded=True, basis="site analysis", quality=None, attempts=0,
                       unsupported_claims=0, analysis_context=[t for t, _p, _l in (lines + merged)[:20]], cost={})


INTERNAL_TERMS = re.compile(r"\b(?:the )?(?:conflict|analysis|computed|supplied|extra)[ -](?:metadata|context)\b", re.I)


def _scrub_internal(text):
    """The answerer sometimes echoes the labels of the context it was given ('Conflict metadata'). They are internal wording, not the site's."""
    return INTERNAL_TERMS.sub(lambda m: "the conflict check" if "conflict" in m.group().lower() else "the site analysis", text)


RELATION_LANGUAGE = re.compile(r"\b(?:two|three|both|several|multiple|different|differ\w*|conflict\w*|inconsisten\w*|disagree\w*|discrepan\w*|contradict\w*|whereas|while|another page|other page)\b", re.I)


def _record_check(sid, question):
    """Is this sentence a statement about a disagreement between pages that the application's OWN conflict record contains? It names an entity and
    a property for which a conflict was computed, and says so in relational language. No single page can carry such a sentence, so it is supported
    by the record, not by a page; the band names that basis. A sentence with a figure never qualifies (figures must come from a page)."""
    g = store.get("entities", sid) or {}
    conflicts = g.get("conflicts", [])

    def check(seg, ctx):
        if not conflicts or not RELATION_LANGUAGE.search(seg):
            return False
        ns = " " + " ".join(re.findall(r"\w+", _ascii(ctx + " " + seg).lower())) + " "
        words = set(re.findall(r"\w+", (ctx + " " + seg + " " + question).lower()))
        for c in conflicts:
            if (" " + " ".join(re.findall(r"\w+", _ascii(c["entity_label"]).lower())) + " ") not in ns:
                continue
            prop = c["property"]
            if (set(PROP_WORDS.get(prop, "").split()) | {w.lower() for w in re.findall(r"[A-Z]?[a-z]+", prop)}) & words:
                return True
        return False
    return check


def _no_conflict_answer(sid, pages, question):
    """'Do X and Y have conflicting prices?' where the detector computed no such conflict: say so plainly, from the detector, and show what each
    page states. A decline or an empty panel on an answerable question reads as the product failing; 'none was found' is a true statement the
    application can make deterministically. Returns an AskResponse, or None when the question is not of this shape or a conflict exists."""
    if not CONFLICT_Q.search(question):
        return None
    g = store.get("entities", sid) or {}
    qa = " " + " ".join(re.findall(r"\w+", _ascii(question).lower())) + " "
    named = [n for n in g.get("nodes", []) if n["type"] != "WebPage" and (" " + " ".join(re.findall(r"\w+", _ascii(n["label"]).lower())) + " ") in qa]
    if not named:
        return None
    qwords = set(qa.split())
    props, noun = [], ""
    for p_, words in PROP_WORDS.items():
        hit = [w for w in words.split() if w in qwords or (w + "s") in qwords]
        if hit:
            props.append(p_)
            noun = noun or hit[0]
    ids = {n["id"] for n in named}
    for c in g.get("conflicts", []):
        if c["entity_id"] in ids and (not props or c["property"] in props):
            return None                                   # a conflict exists: the ordinary path reports it with both sides
    labels = [n["label"] for n in named[:4]]
    who = labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + " and " + labels[-1]
    what = f"{noun}s" if noun and not noun.endswith("s") else (noun or "values")
    head = (f"No conflicting {what} were found for {who}. SemanticSite compares what each page states for the same property of the same entity, "
            f"and none of the values it holds disagreed among the pages it read. This covers only what it extracted.")
    out, cites, order = [head], [], {}
    by_pid = {p["id"]: p for p in pages}
    for n in named[:4]:
        for p_ in props:
            v = n["properties"].get(p_) or (n["properties"].get("price") if p_ == "offers" else None)
            if not v:
                continue
            cur = n["properties"].get("priceCurrency") if p_ in ("price", "offers") else None
            shown = f"{v} {cur}".strip() if cur else str(v)
            vt = set(_toks(str(v)))
            mark = ""
            for x in n["pages"]:
                pg = by_pid.get(x["page_id"])
                if not pg:
                    continue
                unit = next((u for u in _sentences(pg.get("text") or "") if vt and vt <= set(_toks(u)) and not u.lstrip().startswith("#")), None)
                if unit:
                    order.setdefault(pg["id"], (len(order) + 1, pg, unit, []))
                    order[pg["id"]][3].append(f"{n['label']}: {shown}")
                    mark = f"[{order[pg['id']][0]}]"
                    break
            line = f"- {n['label']}: {shown}.{mark}"
            if line not in out:                                # 'price' and 'offers' both name one property of the Offer
                out.append(line)
    for pid_, (num, pg, unit, claims) in order.items():
        cites.append(Citation(n=num, page_id=pg["id"], url=pg["url"], title=pg.get("title"), resource_id=pg.get("rid"), excerpt=re.sub(r"^[#>*\-\s]+", "", unit).strip()[:300], claims=claims[:6]))
    return AskResponse(answer="\n".join(out), citations=cites, grounded=True, basis="site analysis", quality=None, attempts=0, unsupported_claims=0,
                       analysis_context=[f"No conflict computed for {l}." for l in labels], cost={})


def _carries(page, labels):
    """Sentences of the page that actually use one of the names (a bare label or a heading carries nothing)."""
    from .resolve import norm_name
    phr = [" " + norm_name(l) + " " for l in labels if norm_name(l)]
    out = []
    for x in _sentences(page.get("text") or ""):
        if x.lstrip().startswith("#") or len(x) < 30 or len(x.split()) < 5:
            continue
        nx = " " + " ".join(re.findall(r"\w+", x.lower())) + " "
        if any(p_ in nx for p_ in phr):
            out.append(re.sub(r"^[#>*\-\s]+", "", x).strip())
    return out


def answer(sid, question):
    pages = [p for p in store.all_("pages", sid) if p.get("rid") and p.get("status") == "ingested"]
    if not pages:
        return AskResponse(answer="", citations=[], grounded=False, error="This site has no indexed pages yet.")
    if ALIAS_Q.search(question) and not GAP_Q.search(question):
        return _alias_answer(sid, pages, question)
    nc = _no_conflict_answer(sid, pages, question)
    if nc is not None:
        return nc
    by_rid = {p["rid"]: p for p in pages}
    meter = arag.Meter()
    items, structural = _context(sid, question)
    ctx = [it["text"] for it in items]
    ctx += _computed_notes(sid, question, items)
    attempts, d, text = 0, {}, ""
    for attempts in (1, 2):             # grounding varies run to run on the platform: one deliberate retry before declining
        try:
            d = arag.ask(meter, question, list(by_rid), extra_context=ctx or None)
        except arag.ArError:
            if attempts == 2:
                return AskResponse(answer="", citations=[], grounded=False, error="The answer service did not respond. Try again.",
                                   cost=meter.snapshot(), attempts=attempts)
            continue
        text = (d.get("answer") or "").strip()
        if text and d.get("status") in (None, "success") and not DECLINE.search(text[:160]):
            break
    else:
        d = d or {}
    res = (d.get("retrieval_results") or {}).get("resources") or {}
    outside = [r for r in list(res) + [k.split("/")[0] for k in (d.get("citations") or {})] if r not in by_rid and not r.startswith("USER_CONTEXT")]   # extra_context items appear under their own ids
    retrieved = [r for r in res if r in by_rid]
    cited = list(dict.fromkeys(k.split("/")[0] for k in (d.get("citations") or {}) if k.split("/")[0] in by_rid))
    # candidates: cited and retrieved pages first, then every other page of THIS site; the lexical support check decides
    cand = [(r, by_rid[r]) for r in dict.fromkeys(cited + retrieved + list(by_rid))]
    text = _scrub_internal(text) if text else text
    text, withheld = _alias_guard(sid, text) if text else (text, 0)
    text, w2 = _conflict_guard(sid, text, question) if text else (text, 0)
    withheld += w2
    text, w3 = _absence_guard(sid, text, pages) if text else (text, 0)
    withheld += w3
    text, w4 = _conflict_values_guard(sid, text, question) if text else (text, 0)
    withheld += w4
    det = {}
    marked, cites, unsupported, used_items, total = _attribute(text, cand, items, items_first=structural, detail=det, record_check=_record_check(sid, question), absence_check=lambda sg, tl, rs: _absence_status(store.get("entities", sid) or {}, pages, sg, tl, rs)) if text else (text, [], 0, 0, 0)
    quality = None
    # The visible band is a deterministic measure of the answer itself: is every sentence traced to a page sentence that
    # carries it. The platform's score (which varies between runs and judges the wording, not the figures) sits beneath it
    # and is only requested when nothing is unsourced. Answers built from computed facts carry no score at all.
    if text and d.get("status") in (None, "success") and not outside and not (structural and ctx):
        quality = _band_det(total, unsupported, len(cites), det.get("unsupported_with_figure", 0), det.get("non_assertions", 0), det.get("traced_to_record", 0))
        if unsupported == 0 and cites:
            ordered = [c.resource_id for c in cites] + [r for r, _ in cand if r not in {c.resource_id for c in cites}]
            ctxs = [(by_rid[r].get("text") or "")[:2500] for r in ordered[:8] if by_rid[r].get("text")] + ctx[:6]
            try:
                sc = arag.remi(meter, question, text, ctxs) if ctxs else None
            except arag.ArError:
                sc = None
            quality["platform_score"] = _platform_score(sc)
    declined = (d.get("status") not in (None, "success")) or not text or bool(DECLINE.search(text[:160])) or bool(outside) \
        or not cites
    if declined:                       # withhold the whole response, not just the sources
        return AskResponse(answer="", citations=[], grounded=False, declined=True, cost=meter.snapshot(), attempts=attempts)
    basis = "site analysis" if used_items and structural else ("pages and site analysis" if used_items else "pages")
    return AskResponse(answer=marked, citations=cites, grounded=True, basis=basis, analysis_context=ctx, quality=quality,
                       unsupported_claims=unsupported, unsourced_sentences=det.get("unsupported_sentences", []), non_assertions=det.get("non_assertions", 0), withheld_claims=withheld, attempts=attempts, cost=meter.snapshot())


def _band_det(total, unsupported, ncites, with_figure=0, non_assertions=0, traced=0):
    """The headline: how much of this answer can be traced. Deterministic, so identical answers get identical bands.
    `total` counts sentences that assert a fact; lead-ins and hedges are reported, not counted. The band is proportional:
    none unsupported is high; a minority unsupported is partial; unsourced is for an answer whose factual sentences are
    substantially unsupported, or in which an unsupported sentence carries a figure (a wrong price or date is the costly error,
    so one is never rounded down to 'mostly fine'). The count is always stated."""
    skipped = (f" {non_assertions} lead-in or hedging sentence{'s' if non_assertions != 1 else ''} state{'' if non_assertions != 1 else 's'} no fact and "
               f"{'were' if non_assertions != 1 else 'was'} not checked.") if non_assertions else ""
    if not total or not ncites:
        return {"band": "unscored", "label": "No sentence could be traced to a page", "claims": total, "unsupported": total, "non_assertions": non_assertions,
                "note": "Nothing in this answer was matched to a sentence on a page." + skipped}
    if unsupported == 0:
        basis = (f" {traced} sentence{'s' if traced != 1 else ''} describe{'' if traced != 1 else 's'} a disagreement between pages; no single page can carry that, so "
                 f"{'they are' if traced != 1 else 'it is'} traced to the site's own conflict record instead.") if traced else ""
        skipped = skipped + basis
        return {"band": "high", "label": "Every sentence traced to a page" + (" or to the site's own conflict record" if traced else ""), "traced_to_record": traced, "claims": total, "unsupported": 0, "non_assertions": non_assertions,
                "note": "Each sentence that states a fact was matched to a sentence or table row on a cited page that carries it." + skipped + " This describes this answer, not the question: asking again can word the answer differently. It shows traceability, not that the page is correct. The check confirms each sentence was matched to a cited page; it does not detect a sentence that contradicts the page it cites."}
    label = f"{unsupported} of {total} sentences have no source page"
    if with_figure == 0 and unsupported * 4 <= total:
        return {"band": "partial", "label": label, "claims": total, "unsupported": unsupported, "non_assertions": non_assertions,
                "note": "Most sentences were traced to a page; the ones without a source are marked. They carry no figure, but treat them as unverified." + skipped + " This describes this answer, not the question. The check confirms each sentence was matched to a cited page; it does not detect a sentence that contradicts the page it cites."}
    why = " At least one of them carries a figure, and a figure is never rounded down to mostly fine." if with_figure else ""
    return {"band": "unsourced", "label": label, "claims": total, "unsupported": unsupported, "non_assertions": non_assertions,
            "note": "Those sentences, and any figures in them, could not be matched to a page sentence or table row." + why + skipped + " This describes this answer, not the question: asking again can word it differently. Treat them as unverified."}


def _platform_score(sc):
    if not sc or sc.get("groundedness") is None:
        return None
    return {"groundedness": sc["groundedness"], "context_relevance": sc.get("context_relevance"), "varies_between_runs": True,
            "note": "The platform's evaluation score. It judges the wording against the retrieved text, not each figure, and it varies between runs on identical input; read it as a secondary signal."}


ALIAS_CLAIM = re.compile(r"\b(?:also (?:known|called|written|named|referred)|known as|a\.?k\.?a|is the same as|are the same|the same (?:person|thing|entity|product|place|item|organi[sz]ation)|goes by|aliases?|other names?|another name|alternative names?|formerly|previously (?:known|called)|renamed|synonym(?:ous)?)\b", re.I)


def _alias_guard(sid, text):
    """A sentence that says two names denote the same thing is withheld unless that pair is one the application computed.
    The model cannot assert an alias on this path, whatever the question was; the routing list only decides whether the
    reader gets the better composed answer. Returns (text, withheld_count)."""
    from .resolve import norm_name
    g = store.get("entities", sid) or {}
    pairs = [a["labels"] for a in g.get("ambiguities", [])]
    for n in g.get("nodes", []):
        if n["type"] != "WebPage" and n.get("aliases"):
            pairs.append([n["label"]] + n["aliases"])
    phr = lambda x: " " + norm_name(x) + " "
    cut = []
    for start, end, seg, _ctx in _claims(text):
        if not ALIAS_CLAIM.search(seg):
            continue
        ns = " " + " ".join(re.findall(r"\w+", seg.lower())) + " "
        ok = any(sum(1 for l in lab if norm_name(l) and phr(l) in ns) >= 2 for lab in pairs)
        if not ok:
            cut.append((start, end))
    for start, end in reversed(cut):
        text = text[:start] + text[end:]
    return re.sub(r"\n{3,}", "\n\n", text).strip(), len(cut)
