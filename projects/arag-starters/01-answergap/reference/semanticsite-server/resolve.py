"""Entity resolution, relationship merging, conflict detection and confidence signals.

Resolution is deliberately conservative. Two mentions are merged only when they share a JSON-LD
@id or the same normalised name (and compatible type). Anything that merely looks similar is NOT
merged: it becomes an Ambiguity that needs a human (PRD s8: ambiguous entity matches require review)."""
import hashlib
import itertools
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher, get_close_matches

from . import compare, vocab
from .schema import Ambiguity, Check, Confidence, Conflict, Edge, Node, Provenance

HONORIFICS = {"dr", "mr", "mrs", "ms", "miss", "prof", "professor", "sir", "dame", "mx"}
COMPANY = {"pty", "ltd", "limited", "inc", "llc", "co", "company"}
COMPARE = ("price", "openingHours", "telephone", "email", "address", "foundingDate", "jobTitle", "startDate", "endDate", "maximumAttendeeCapacity", "memberCount", "numberOfEmployees")


def norm_name(s):
    s = re.sub(r"[^\w\s]", " ", (s or "").lower())
    toks = [t for t in s.split() if t not in HONORIFICS and t not in COMPANY]
    if toks and toks[0] == "the":
        toks = toks[1:]
    return " ".join(toks)


def _phr(s_):
    return " " + " ".join(re.findall(r"\w+", s_.lower())) + " "


def _same_name(na, nb, ma, mb):
    """Names that can be one entity: equal, one inside the other, or a declared alias."""
    if na == nb:
        return True
    ta, tb = set(na.split()), set(nb.split())
    if ta and tb and (ta <= tb or tb <= ta):
        return True
    return norm_name(mb["name"]) in {norm_name(a) for a in ma.get("aliases", [])} or norm_name(ma["name"]) in {norm_name(a) for a in mb.get("aliases", [])}


GENERIC_TOKENS = {"the", "and", "of", "for", "film", "coffee", "roasters", "museum", "cafe", "gallery", "room", "store", "house", "hall", "centre", "center",
                  "team", "group", "street", "lane", "road", "park"}


def _site_org(entities):
    """The organisation that owns the site ('our' refers to it): the one extracted Organization (not a place) on the shallowest page."""
    best = []
    for e in entities.values():
        if e["group"] != "org" or "Place" in vocab.ancestors(e["type"]):
            continue
        for m in e["mentions"]:
            if m["kind"] == "extracted" and m.get("jsonld_id"):
                best.append((len(m["url"].split("//", 1)[-1].rstrip("/").split("/")), e["id"]))
    if not best:
        return None
    best.sort()
    top = {eid for d_, eid in best if d_ == best[0][0]}
    return next(iter(top)) if len(top) == 1 else None


STRUCTURAL_PREDICATES = {"department", "subOrganization", "parentOrganization", "isPartOf", "hasPart", "memberOf", "worksFor", "employee", "containedInPlace", "founder"}
SEPARATION = re.compile(r"\b(?:separate (?:from|to)|independent(?:ly)? of|not part of|not run by|not operated by|not owned by|distinct from|unconnected (?:to|with)|unrelated to|apart from|is not the same as)\b", re.I)


def _pos(ent, text, entities):
    """Where in the text the entity is mentioned (full name, alias or short form); -1 if it is not."""
    low = text.lower()
    for n_ in [ent["label"]] + list(ent["aliases"]):
        i = low.find(n_.lower()) if n_ else -1
        if i >= 0:
            return i
    sf = _short_form(ent, text, entities)
    if sf:
        i = low.find(sf.lower())
        if i >= 0:
            return i
    return -1


def _short_form(ent, ev, entities):
    """The name used on its own: a capitalised first or last word ('Sitecrawl', 'the Trust'), or a trailing part of the name after
    'the' ('the museum', 'the Picture House'), where no other entity's name shares it. Returns the form found, or None."""
    ev = ev or ""
    others = [e2["label"].lower() for e2 in entities.values() if e2["id"] != ent["id"] and e2["group"] != "page"]
    toks = ent["label"].split()
    if len(toks) < 2:
        return None
    for t in {toks[0], toks[-1]}:
        if len(t) >= 5 and t[:1].isupper() and t.lower() not in GENERIC_TOKENS and re.search(r"\b" + re.escape(t) + r"\b", ev) \
                and not any(re.search(r"\b" + re.escape(t.lower()) + r"\b", o_) for o_ in others):
            return t
    for k in range(1, len(toks)):                                   # 'the Picture House', 'the museum': a trailing part of the name
        suffix = " ".join(toks[k:])
        if re.search(r"\bthe\s+" + re.escape(suffix) + r"\b", ev, re.I) and not any(o_.endswith(suffix.lower()) for o_ in others):
            return "the " + suffix
    return None


DETERMINERS = r"(?:the|a|an|its|their|this|that|these|those|our|his|her)"
PRONOUN_OBJECTS = {"it", "them", "him", "her", "us", "this", "that", "these", "those", "there", "here", "one", "ones"}


def _sentence_object(r, ent, entities):
    """The object the sentence itself states for a funding/support/provision verb, when it is not this entity (None when the
    sentence states none). 'also supports the programme' -> 'programme'. Deliberately limited to verbs whose object is a different
    thing from the page's subject; 'runs'/'hosts'/'manages' sentences are about the thing the page is about and are left to the
    licence tiers. Passive voice ('supported by X') has no object after the verb and is not read."""
    ev = r.get("evidence") or ""
    label = (r.get("label") or r["predicate"] or "")
    words = [w for w in re.findall(r"[A-Za-z]+", re.sub(r"(?<=[a-z])(?=[A-Z])", " ", label).lower()) if w.startswith(("support", "sponsor", "fund", "suppl", "provid", "employ"))]
    names = [ent["label"]] + list(ent["aliases"])
    otoks = {t.lower() for t in ent["label"].split()}
    for w in words[:1]:
        stem = w[:max(4, len(w) - 2)]
        m = re.search(r"\b" + re.escape(stem) + r"\w*\s+(?!by\b)(?:" + DETERMINERS + r"\s+)?([A-Za-z][\w'-]*(?:\s+(?!and\b|or\b|at\b|on\b|in\b|for\b|with\b|who\b|which\b|that\b|after\b|to\b)[A-Za-z][\w'-]*){0,2})", ev, re.I)
        if not m:
            continue
        cand = m.group(1).strip()
        first = cand.split()[0].lower()
        if first in PRONOUN_OBJECTS or first in ("in", "on", "at", "to", "for", "of", "from", "and", "or", "also", "by", "with"):
            continue
        pc = _phr(cand)
        if any(_phr(n_).strip() and (_phr(n_) in pc or pc.strip() in _phr(n_)) for n_ in names if n_):
            return None
        if cand.split()[-1].lower() in otoks or _short_form(ent, cand, entities):
            return None                     # 'the Trust', 'the museum': the object under a short name or its type noun
        return cand
    return None


def _unit_of(text, ev):
    """The paragraph, table row or list item that holds the quote (the text is built one such unit per block)."""
    if not ev:
        return ""
    nev = " ".join(ev.lower().split()).rstrip(".!? ")
    for blk in re.split(r"\n\s*\n|\n", text or ""):
        if nev[:80] in " ".join(blk.lower().split()):
            return blk.strip()
    return ""


def _named(ent, txt, entities):
    """How the entity is named in this text: 'quote' (full name or alias), a short form, or None."""
    p = _phr(txt)
    if any(_phr(n_) in p for n_ in [ent["label"]] + list(ent["aliases"]) if n_):
        return "quote"
    sf = _short_form(ent, txt, entities)
    return f"a short form ('{sf}')" if sf else None


def _licence(o, r, page, entities, site_org):
    """Where on the page the object could have come from when neither the quote nor its paragraph names it. None = nowhere."""
    ent = entities[o]
    phr = [_phr(n_) for n_ in [ent["label"]] + list(ent["aliases"]) if n_]
    text, title = page.get("text") or "", page.get("title") or ""
    ev = r.get("evidence") or ""
    if any(p_ in _phr(title) for p_ in phr):
        return "page title"
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if any(ln.lstrip().startswith("#") and any(p_ in _phr(ln) for p_ in phr) for ln in lines):
        return "page heading"
    if any(" | " in ln and any(p_ in _phr(ln) for p_ in phr) for ln in lines) and " | " in ev:
        return "a table on the page"
    at = text.find(ev[:60]) if ev else -1
    if at > 0 and _named(ent, text[max(0, at - 450):at], entities):
        return "an adjacent block"
    if _named(ent, text, entities):
        return "elsewhere on the page"
    return None


def group_of(t):
    if t == "WebPage":
        return "page"
    anc = vocab.ancestors(t) if t in vocab.TYPES else {t}
    for g, key in (("person", "Person"), ("event", "Event"), ("product", "Product"), ("service", "Service"),
                   ("org", "Organization"), ("place", "Place")):
        if key in anc:
            return g
    return "thing"


def compatible(g1, g2):
    # 'thing' is a type the vocabulary does not know (for example a misspelt @type): it can still be the same entity
    return g1 == g2 or {g1, g2} == {"org", "place"} or "thing" in (g1, g2)


def norm_value(prop, v):
    v = str(v).strip().lower()
    if prop == "price":
        m = re.search(r"\d[\d,]*(\.\d+)?", v)
        return str(float(m.group().replace(",", ""))) if m else v
    if prop == "telephone":
        return re.sub(r"\D", "", v)
    if prop == "email":
        return v.replace("mailto:", "")
    v = v.replace("–", "-").replace("—", "-").replace(" to ", "-").replace("–", "-")
    return re.sub(r"[^a-z0-9:\-]", "", v)


def band(passed, total):
    r = passed / total if total else 0
    return "high" if passed == total and total else "medium" if r >= 0.6 else "low"


def conf(checks):
    p = sum(1 for c in checks if c.passed)
    return Confidence(band=band(p, len(checks)), passed=p, total=len(checks), checks=checks)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "x"


def short(*parts):
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:8]


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def f(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def resolve(mentions, relations, pages, decisions=()):
    """mentions: [{id,page_id,url,rid,kind,method,type,name,jsonld_id,props,prop_kind,prop_evidence,aliases,
                   evidence,evidence_verified}]
       relations: [{id,page_id,url,rid,kind,method,support,subject,predicate,object,evidence,evidence_verified}]
       Returns dict(nodes, edges, conflicts, ambiguities, mention_to_entity)."""
    n = len(mentions)
    uf = UF(n)
    by_id, by_nk, idclash = {}, defaultdict(list), []
    for i, m in enumerate(mentions):
        m["group"] = group_of(m["type"] or "")
        m["nk"] = norm_name(m["name"]) if m["group"] != "page" else (m["jsonld_id"] or m["name"])
        if m["jsonld_id"]:
            if m["jsonld_id"] in by_id:
                j = by_id[m["jsonld_id"]]
                if _same_name(m["nk"], mentions[j]["nk"], m, mentions[j]) or m["group"] == "page":
                    uf.u(i, j)
                else:
                    idclash.append((i, j))        # one @id on two different names: a markup fault or a real merge; a person decides
            else:
                by_id[m["jsonld_id"]] = i
        by_nk[m["nk"]].append(i)
    sep = set()
    ack = {d_["cid"]: d_ for d_ in decisions if d_.get("kind") == "conflict"}
    for dcs in decisions:                                 # a reviewer's explicit calls on earlier ambiguities
        if dcs.get("kind") == "conflict":
            continue
        if dcs["decision"] == "merge":
            for i in by_nk.get(dcs["a"], []):
                for j in by_nk.get(dcs["b"], []):
                    uf.u(i, j)
        else:
            sep.add(frozenset((dcs["a"], dcs["b"])))
    for nk, idxs in by_nk.items():                       # same normalised name + compatible type -> same entity
        for a, b in itertools.combinations(idxs, 2):
            ga, gb = mentions[a]["group"], mentions[b]["group"]
            if compatible(ga, gb) or (ga != "page" and gb != "page"):      # one name = one entity; its type is decided once, below
                uf.u(a, b)
    # A name that is a leading or trailing part of exactly ONE other name of the same kind is that entity under its short name
    # ('Trust' for 'Tarrowmere Heritage Trust', 'Open Roastery Day' for 'Open Roastery Day 2026'). Merged automatically, shown on the
    # node, and undoable with a reviewer's 'keep separate'. Two possible long forms means it is genuinely ambiguous and is left alone.
    auto_short = set()
    nks = [k for k in by_nk if mentions[by_nk[k][0]]["group"] != "page"]
    for a in nks:
        ta = a.split()
        cands = []
        for b in nks:
            tb = b.split()
            if b == a or len(tb) <= len(ta) or not (tb[:len(ta)] == ta or tb[-len(ta):] == ta):
                continue
            suffix = tb[-len(ta):] == ta
            if not (len(ta) >= 2 or (suffix and len(a) >= 4) or (not suffix and len(a) >= 6)):
                continue
            ga_, gb_ = mentions[by_nk[a][0]]["group"], mentions[by_nk[b][0]]["group"]
            if not (ga_ == gb_ or "thing" in (ga_, gb_)):          # strictly the same kind: a town is not the organisation named after it
                continue
            cands.append(b)
        if len(cands) == 1 and frozenset((a, cands[0])) not in sep:
            ids_a = {mentions[i]["jsonld_id"] for i in by_nk[a] if mentions[i]["jsonld_id"]}
            ids_b = {mentions[i]["jsonld_id"] for i in by_nk[cands[0]] if mentions[i]["jsonld_id"]}
            if ids_a and ids_b and not (ids_a & ids_b):
                continue                                   # two different identifiers: the site itself says they are different things
            for i in by_nk[a]:
                uf.u(i, by_nk[cands[0]][0])
            auto_short.add(a)
    for i, m in enumerate(mentions):                      # declared aliases (alternateName) merge deterministically
        for al in m.get("aliases", []):
            for j in by_nk.get(norm_name(al), []):
                if compatible(m["group"], mentions[j]["group"]):
                    uf.u(i, j)

    clusters = defaultdict(list)
    for i in range(n):
        clusters[uf.f(i)].append(i)

    entities, m2e = {}, {}
    for root, idxs in clusters.items():
        ms = [mentions[i] for i in idxs]
        ext = [m for m in ms if m["kind"] == "extracted"]
        pool = ext or ms
        label = Counter(m["name"] for m in pool).most_common(1)[0][0]
        # the richest extracted mention decides the type (an id and properties outweigh a bare nested reference)
        wt = Counter()
        for m in pool:
            if m["type"]:
                wt[m["type"]] += 1 + len(m["props"]) + (3 if m.get("jsonld_id") else 0)
        etype = wt.most_common(1)[0][0] if wt else "Thing"
        type_note = ""
        if etype not in vocab.TYPES and etype != "WebPage":
            best = get_close_matches(etype, list(vocab.TYPES), n=1, cutoff=0.7)
            if best:
                type_note, etype = f"'{etype}' is not a Schema.org type; read as '{best[0]}'", best[0]
            else:
                type_note = f"'{etype}' is not a Schema.org type and has no close match"
        g = group_of(etype)
        eid = f"{slug(label)}-{short(g if g != 'place' else 'org', ms[0]['nk'])}"
        while eid in entities:
            eid += "x"
        kinds = {m["kind"] for m in ms}
        entities[eid] = {"id": eid, "label": label, "type": etype, "group": g, "mentions": ms,
                         "origin": "both" if len(kinds) == 2 else kinds.pop(),
                         "auto_merged": sorted({m["name"] for m in ms if m["nk"] in auto_short}), "type_note": type_note,
                         "pages": sorted({m["page_id"] for m in ms}),
                         "aliases": sorted({m["name"] for m in ms if m["name"] != label} | {a for m in ms for a in m.get("aliases", [])})}
        for m in ms:
            m2e[m["id"]] = eid

    # ---- ambiguity candidates: similar but NOT identical, so never auto-merged --------------------
    ents = [e for e in entities.values() if e["group"] != "page"]
    amb, seen_pairs = [], set()
    for a, b in itertools.combinations(ents, 2):
        na, nb = norm_name(a["label"]), norm_name(b["label"])
        reason = None
        if na == nb and not compatible(a["group"], b["group"]):
            reason = f"Same name '{a['label']}' is typed {a['type']} in one place and {b['type']} in another."
        elif compatible(a["group"], b["group"]) and na != nb:
            ta, tb = na.split(), nb.split()
            if a["group"] == "person" and ta and tb and ta[-1] == tb[-1] and (
                    (len(ta[0]) == 1 and tb[0].startswith(ta[0])) or (len(tb[0]) == 1 and ta[0].startswith(tb[0])) or
                    len(ta) != len(tb) or ta[0] == tb[0]):
                reason = f"'{a['label']}' and '{b['label']}' share a surname and may be the same person."
            elif SequenceMatcher(None, na, nb).ratio() >= 0.86:
                reason = f"'{a['label']}' and '{b['label']}' are near-identical names and may be the same {a['type'].lower()}."
            else:
                short_t, long_t = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
                if len(short_t) >= 2 and set(short_t) <= set(long_t):
                    reason = f"'{a['label']}' appears to be a shortened form of '{b['label']}' (or the reverse)."
                elif len(short_t) == 1 and len(long_t) >= 2 and short_t[0] == long_t[-1] and a["group"] in ("org", "place"):
                    reason = f"'{a['label']}' and '{b['label']}' may be the same {a['type'].lower()}: one is the other's closing word on its own."
        if reason:
            key = tuple(sorted((a["id"], b["id"])))
            if key not in seen_pairs:
                seen_pairs.add(key)
                ka, kb = norm_name(a["label"]), norm_name(b["label"])
                amb.append(Ambiguity(id="amb-" + short(*key), entity_ids=list(key), labels=[a["label"], b["label"]], reason=reason,
                                     keys=[ka, kb], status="kept_separate" if frozenset((ka, kb)) in sep else "needs_review"))
    for i, j in idclash:
        ea, eb = entities.get(m2e.get(mentions[i]["id"])), entities.get(m2e.get(mentions[j]["id"]))
        if not ea or not eb or ea["id"] == eb["id"]:
            continue
        key = tuple(sorted((ea["id"], eb["id"])))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        ka, kb = norm_name(ea["label"]), norm_name(eb["label"])
        amb.append(Ambiguity(id="amb-" + short(*key), entity_ids=list(key), labels=[ea["label"], eb["label"]], keys=[ka, kb],
                             reason=f"The markup gives '{ea['label']}' and '{eb['label']}' the same @id ({mentions[i]['jsonld_id']}) but they carry different names. They were not merged.",
                             status="kept_separate" if frozenset((ka, kb)) in sep else "needs_review"))
    # a page that SAYS one thing was renamed or is also known by another name: flag the pair even when the names look nothing alike
    CUE = re.compile(r"\b(formerly|previously|renamed|now called|now known as|also known as|also called|known as|used to be|rebranded|reopened as|became|replaced by|originally)\b", re.I)
    phrase = lambda s_: " " + " ".join(re.findall(r"\w+", s_.lower())) + " "
    for pid_, pg in pages.items():
        for sent in re.split(r"(?<=[.!?])\s+|\n+", pg.get("text") or ""):
            if not CUE.search(sent):
                continue
            ps = phrase(sent)
            cue_at = ps.find(" " + CUE.search(sent).group(0).lower().split()[0] + " ")
            if cue_at < 0:
                cue_at = ps.lower().find(CUE.search(sent).group(0).lower().split()[0])
            before, after = [], []
            for e in ents:
                for nm_ in [e["label"]] + list(e["aliases"]):
                    at = ps.find(phrase(nm_))
                    if at >= 0:
                        (before if at < cue_at else after).append((abs(at - cue_at), at, e))
                        break
            before.sort(key=lambda x: x[0])
            after.sort(key=lambda x: x[0])
            here = [before[0][2], after[0][2]] if before and after and before[0][2]["id"] != after[0][2]["id"] else []
            for a, b in itertools.combinations(here, 2):
                key = tuple(sorted((a["id"], b["id"])))
                reason = f'A page says one may be the other: "{sent.strip()[:170]}"'
                if key in seen_pairs:
                    for x in amb:
                        if tuple(sorted(x.entity_ids)) == key and "A page says" not in x.reason:
                            x.reason += " " + reason
                    continue
                seen_pairs.add(key)
                ka, kb = norm_name(a["label"]), norm_name(b["label"])
                amb.append(Ambiguity(id="amb-" + short(*key), entity_ids=list(key), labels=[a["label"], b["label"]], reason=reason,
                                     keys=[ka, kb], status="kept_separate" if frozenset((ka, kb)) in sep else "needs_review"))
    amb_of = defaultdict(list)
    for x in amb:
        if x.status != "needs_review":
            continue
        for e in x.entity_ids:
            amb_of[e].append(x)

    # ---- relationships ----------------------------------------------------------------------------
    name_to_eid = {}
    for e in entities.values():
        for m in e["mentions"]:
            name_to_eid.setdefault((m["nk"]), e["id"])
    # An organisation that RUNS a venue is the employer, sponsor-recipient and owner of departments; the venue is the place.
    cand_ops = defaultdict(set)
    BY_RE = re.compile(r"\b(?:run|operated|managed|governed|controlled)\s+by\b", re.I)    # an OWNER (landlord) is not the operator
    for r_ in relations:
        sx, ox = name_to_eid.get(norm_name(r_["subject"])), name_to_eid.get(norm_name(r_["object"]))
        if not sx or not ox or sx == ox:
            continue
        if r_["kind"] == "suggested":      # a prose claim about who runs what must name both ends in its own sentence
            evp = _phr(r_.get("evidence") or "")
            if not all(any(_phr(n_) in evp for n_ in [entities[x_]["label"]] + list(entities[x_]["aliases"]) if n_) for x_ in (sx, ox)):
                continue
        lab = (r_.get("label") or "").lower()
        if r_["predicate"] == "parentOrganization":
            cand_ops[sx].add(ox)
        elif r_["predicate"] == "subOrganization":
            cand_ops[ox].add(sx)
        elif r_["predicate"] == "otherRelation":
            if BY_RE.search(lab):
                cand_ops[sx].add(ox)               # 'X is run by Y'
            elif lab.startswith(("operat", "run", "manag", "govern")):
                cand_ops[ox].add(sx)               # 'Y runs X'
    def _is_venue(e_):
        return e_["type"] in vocab.TYPES and "Place" in vocab.ancestors(e_["type"])
    def _is_operator(e_):
        return e_["group"] == "org" and not ("Place" in vocab.ancestors(e_["type"]) and e_["type"] != "Organization") and e_["type"] in vocab.TYPES
    # a venue with exactly one candidate operator that is itself an organisation (not another place); several candidates = unknown, so no migration
    operator_of = {v_: next(iter(ops)) for v_, ops in cand_ops.items() if len(ops) == 1 and _is_venue(entities[v_]) and _is_operator(entities[next(iter(ops))])}
    EMPLOY = {"worksFor", "employee", "department", "subOrganization", "sponsor", "founder", "memberOf"}
    site_org = _site_org(entities)
    sep_sents = [sn for pg_ in pages.values() for sn in re.split(r"(?<=[.!?])\s+|\n+", pg_.get("text") or "") if SEPARATION.search(sn)]
    sep_pairs = {}                       # frozenset({a, b}) -> the sentence: the entity before the cue and the one after it are what the sentence separates
    for sn in sep_sents:
        m_ = SEPARATION.search(sn)
        before, after = [], []
        for e2 in entities.values():
            if e2["group"] == "page":
                continue
            at = _pos(e2, sn, entities)
            if at >= 0:
                (before if at < m_.start() else after).append((abs(at - m_.start()), e2["id"]))
        if before and after:
            sep_pairs[frozenset((min(before)[1], min(after)[1]))] = sn
    sub_units = defaultdict(set)         # parts of an organisation, by its own department / subOrganization / parentOrganization relations
    for r_ in relations:
        sx_, ox_ = name_to_eid.get(norm_name(r_["subject"])), name_to_eid.get(norm_name(r_["object"]))
        if sx_ and ox_:
            if r_["predicate"] in ("department", "subOrganization"):
                sub_units[sx_].add(ox_)
            elif r_["predicate"] in ("parentOrganization", "isPartOf"):
                sub_units[ox_].add(sx_)
    merged, dropped_edges, dropped_detail = {}, 0, []
    for r in relations:
        if r["predicate"] == "otherRelation":
            from .infer import _role_label
            if _role_label((r.get("label") or "").strip()):        # a job title is never the name of a relationship, on whichever path the edge arrived
                r = {**r, "predicate": "worksFor", "label": ""}
        s = r.get("subject_eid") or name_to_eid.get(norm_name(r["subject"]))
        o = r.get("object_eid") or name_to_eid.get(norm_name(r["object"]))
        if r.get("subject_url"):
            s = name_to_eid.get(r["subject_url"], s)
        if r.get("object_url"):
            o = name_to_eid.get(r["object_url"], o)
        if not s or not o or s == o:
            continue
        redir_from = None
        if r["kind"] == "suggested" and operator_of:
            ev_ = _phr(r.get("evidence") or "")
            LOCATIONAL = {"location", "containedInPlace", "containsPlace", "isPartOf", "hasPart", "areaServed", "organizer", "performer"}
            for side in ("s", "o"):
                v_ = s if side == "s" else o
                if v_ not in operator_of:
                    continue
                op_named = _phr(entities[operator_of[v_]]["label"]) in ev_ or bool(_short_form(entities[operator_of[v_]], r.get("evidence") or "", entities))
                venue_named = _phr(entities[v_]["label"]) in ev_
                # a venue is a place: employment, funding and ownership statements go to the body that runs it unless the
                # sentence names the venue itself; any other prose statement that names the operator but not the venue is the operator's too
                if (r["predicate"] in EMPLOY and not venue_named) or (r["predicate"] not in LOCATIONAL and op_named and not venue_named):
                    if side == "s":
                        s = operator_of[v_]
                    else:
                        redir_from = v_
                        o = operator_of[v_]
        if s == o:
            continue
        pm_ = vocab.PROPS.get(r["predicate"])
        if pm_ and r["kind"] == "suggested" and entities[s]["group"] != "page":
            fits = lambda a, b: bool(set(pm_["dom"]) & vocab.ancestors(entities[a]["type"])) and (
                bool(set(pm_["rng"]) & vocab.ancestors(entities[b]["type"])) or "Thing" in pm_["rng"])
            if not fits(s, o) and fits(o, s):
                s, o = o, s                      # the model stated it backwards; Schema.org fixes the direction
                redir_from = None
        wrapped = False
        if r["kind"] == "suggested" and r["predicate"] != "otherRelation" and vocab.PROPS.get(r["predicate"]):
            # validity gate: the property must be defined for the subject's type AND accept the object's type (supertypes walked).
            # A failing property is repaired to its Schema.org equivalent where one exists, else kept as a named relationship
            # that does not claim the property. It is never emitted as an invalid property.
            ok, wrapped = vocab.edge_valid(r["predicate"], entities[s]["type"], entities[o]["type"])
            if not ok:
                r = dict(r)
                ps_, po_ = "Place" in vocab.ancestors(entities[s]["type"]), "Place" in vocab.ancestors(entities[o]["type"])
                gs_, go_ = entities[s]["group"], entities[o]["group"]
                if r["predicate"] in ("location", "isPartOf") and ps_ and po_:
                    r["predicate"] = "containedInPlace"
                elif r["predicate"] == "hasPart" and ps_ and po_:
                    r["predicate"], s, o = "containedInPlace", o, s
                elif r["predicate"] == "isPartOf" and gs_ == "org" and go_ == "org":
                    r["predicate"] = "parentOrganization"
                elif r["predicate"] == "hasPart" and gs_ == "org" and go_ == "org":
                    r["predicate"] = "subOrganization"
                elif vocab.edge_valid(r["predicate"], entities[o]["type"], entities[s]["type"])[0]:
                    s, o = o, s                                  # valid the other way round (for example brand)
                else:
                    r["label"] = r.get("label") or re.sub(r"(?<!^)(?=[A-Z])", " ", r["predicate"]).lower()
                    r["predicate"] = "otherRelation"
                ok2, wrapped = vocab.edge_valid(r["predicate"], entities[s]["type"], entities[o]["type"]) if r["predicate"] != "otherRelation" else (True, False)
                if not ok2:
                    r["label"] = r.get("label") or re.sub(r"(?<!^)(?=[A-Z])", " ", r["predicate"]).lower()
                    r["predicate"] = "otherRelation"
                    wrapped = False
        if r["kind"] == "suggested":
            # any page of the site separates the two endpoints ('The Friends scheme is separate from the Trust'): the edge is contradicted
            structural = r["predicate"] in STRUCTURAL_PREDICATES or (r["predicate"] == "otherRelation" and re.search(r"part of|\brun|operat|\bown|manag|govern|belong", (r.get("label") or "").lower()))
            for sent in ([sep_pairs[frozenset((s, o))]] if structural and frozenset((s, o)) in sep_pairs else []):    # funding is compatible with 'separate from'; membership, ownership and running are not
                if True:
                    dropped_edges += 1
                    dropped_detail.append({"subject": entities[s]["label"], "predicate": r["predicate"], "label": r.get("label", ""), "object": entities[o]["label"],
                                           "evidence": r.get("evidence"), "source_url": r["url"], "guard": "separation", "denying_sentence": sent.strip()[:300],
                                           "reason": f"the page says they are separate: \"{sent.strip()[:120]}\""})
                    s = None
                    break
            if s is None:
                continue
        named, source, evidence_out = True, "quote", None
        if r["kind"] == "suggested":
            # Export-eligible when the object is named in the evidence the reviewer actually reads: the quote (full name or a short form),
            # its paragraph/row/list item, or 'our' on the site's own organisation. Otherwise, if the page itself licenses the object
            # (title, heading, table, adjacent block, elsewhere), the edge stays in the explorer at the low band, labelled with where
            # the object came from. If nothing on the page licenses it, it is dropped and counted.
            pg_ = pages.get(r["page_id"]) or {}
            how = _named(entities[o], r.get("evidence") or "", entities)
            if how is None:
                other = _sentence_object(r, entities[o], entities)
                if other:      # the sentence answers 'what?' itself: that is the object. The page may not supply a different one.
                    dropped_edges += 1
                    dropped_detail.append({"subject": entities[s]["label"], "predicate": r["predicate"], "label": r.get("label", ""), "object": entities[o]["label"],
                                           "evidence": r.get("evidence"), "source_url": r["url"], "guard": "sentence_object", "reason": f"the sentence's own object is '{other}', not {entities[o]['label']}"})
                    continue
            unit = _unit_of(pg_.get("text"), r.get("evidence") or "")
            if how is None and unit:
                h2 = _named(entities[o], unit, entities)
                if h2:
                    how, evidence_out = "the same paragraph, row or list item" + ("" if h2 == "quote" else f" ({h2})"), unit[:420]
            if how is None and o == site_org and re.search(r"\b(?:our|we|us|ours)\b", (unit or r.get("evidence") or ""), re.I):
                others_org = [e2 for e2 in entities.values() if e2["group"] == "org" and e2["id"] not in (o, s) and _named(e2, unit or r.get("evidence") or "", entities)]
                if not others_org:
                    how = "'our' (the site's own organisation)"
            if how is not None:
                source = how
            else:
                src = _licence(o, r, pg_, entities, site_org)
                # if the sentence itself names another entity of the object's kind (that is not part of the object), the page may not
                # supply a different object: use what the sentence offers or drop the edge
                qtxt = r.get("evidence") or ""
                competing = [e2 for e2 in entities.values() if e2["id"] not in (s, o) and e2["id"] not in sub_units.get(o, set())
                             and e2["group"] == entities[o]["group"] and e2["group"] != "page"
                             and any(m["kind"] == "extracted" and m.get("jsonld_id") for m in e2["mentions"])      # a standalone body the site itself defines, not a team named in prose
                             and _named(e2, qtxt, entities)]
                if competing:
                    src = None
                    redir_from = None
                if src is None and redir_from:
                    vsrc = _licence(redir_from, r, pg_, entities, site_org) or ("quote" if _named(entities[redir_from], r.get("evidence") or "", entities) else None)
                    if vsrc:
                        src = f"the operator of {entities[redir_from]['label']} (which the {vsrc} supplies)"
                if src is None:
                    dropped_edges += 1
                    dropped_detail.append({"subject": entities[s]["label"], "predicate": r["predicate"], "label": r.get("label", ""), "object": entities[o]["label"],
                                           "evidence": r.get("evidence"), "source_url": r["url"], "guard": "competing_object" if competing else "object_not_on_page",
                                           "reason": (f"the sentence names another body ({', '.join(e2['label'] for e2 in competing[:3])}), so the page may not supply a different object" if competing else "the object is named nowhere on the page")})
                    continue
                named, source = False, src
        key = (s, r["predicate"] if r["predicate"] != "otherRelation" else "otherRelation:" + (r.get("label") or "").lower(), o)
        prov = Provenance(source_url=r["url"], resource_id=r["rid"], kind=r["kind"], method=r["method"],
                          evidence=evidence_out or r.get("evidence"), evidence_verified=bool(r.get("evidence_verified")))
        if key not in merged:
            merged[key] = {"s": s, "p": r["predicate"], "label": r.get("label") or "", "o": o, "provs": [prov], "support": r["support"], "kind": r["kind"],
                           "rids": {r["page_id"]}, "named": named, "source": source, "wrapped": wrapped}
        else:
            merged[key]["provs"].append(prov)
            merged[key]["rids"].add(r["page_id"])
            if named and not merged[key]["named"]:
                merged[key]["named"], merged[key]["source"] = True, "quote"
            if r["kind"] == "extracted":
                merged[key]["kind"] = "extracted"
                if merged[key]["support"] == "prose":
                    merged[key]["support"] = r["support"]
    edges = []
    for (s, p_key, o), d in merged.items():
        p = d["p"]
        provs = sorted(d["provs"], key=lambda x: (x.kind != "extracted", not x.evidence_verified))
        es, eo = entities[s], entities[o]
        pm = vocab.PROPS.get(p)
        plaus = True
        if pm and es["group"] != "page":
            plaus = bool(set(pm["dom"]) & vocab.ancestors(es["type"])) and (
                not (set(pm["rng"]) - vocab.DATATYPES) or bool(set(pm["rng"]) & vocab.ancestors(eo["type"])) or "Thing" in pm["rng"])
        checks = [Check(name="Predicate is a Schema.org property", passed=pm is not None,
                        detail="" if pm is not None else "A real relationship the vocabulary has no property for."),
                  Check(name="Types fit the property's domain and range", passed=plaus),
                  Check(name="Neither end is an unresolved ambiguity", passed=not (amb_of.get(s) or amb_of.get(o)))]
        if d["kind"] == "extracted":
            checks.append(Check(name="Read from existing page structure", passed=True))
        else:
            checks.append(Check(name="Evidence quote found verbatim on the page", passed=provs[0].evidence_verified))
            ev = norm_name(provs[0].evidence or "")
            both = all(any(norm_name(x) and norm_name(x) in ev for x in [lbl] + es_["aliases"]) for lbl, es_ in
                       ((es["label"], es), (eo["label"], eo)))
            checks.append(Check(name="The quoted sentence names both ends", passed=both,
                                detail="" if both else "One end is implied by context, not named in the sentence."))
            checks.append(Check(name="Stated on more than one page", passed=len(d["rids"]) > 1))
        edges.append(Edge(id="e-" + short(s, p_key, o), source=s, target=o, predicate=p,
                          label=d["label"] or re.sub(r"(?<!^)(?=[A-Z])", " ", p).lower(), in_schema_org=pm is not None, origin=d["kind"], support=d["support"],
                          provenance=provs[0], corroboration=provs[1:], confidence=conf(checks),
                          object_in_quote=d.get("named", True), object_source=d.get("source", "quote"),
                          wrapped_in="Offer" if d.get("wrapped") else ""))
        if not d.get("named", True):
            edges[-1].confidence.checks.append(Check(name="The quote names the object", passed=False, detail=f"The object comes from the {d['source']}, not from the sentence."))
            edges[-1].confidence.total += 1
            edges[-1].confidence.band = "low"

    # ---- conflicts: same entity, same property, different normalised value ----------------------------
    conflicts = []
    for e in ents:
        if e["group"] == "page":
            continue
        for prop in COMPARE:
            vals = []
            for m in e["mentions"]:
                if prop in m["props"] and m["props"][prop] != "":
                    vals.append({"value": m["props"][prop], "norm": norm_value(prop, m["props"][prop]), "page_id": m["page_id"],
                                 "url": m["url"], "kind": (m.get("prop_kind") or {}).get(prop, m["kind"]),
                                 "evidence": (m.get("prop_evidence") or {}).get(prop)})
            clash = compare.conflict_set(prop, [v["value"] for v in vals], [(v.get("evidence") or "") for v in vals])
            if clash:
                dedup, seen = [], set()
                for v in vals:
                    k = (v["norm"], v["page_id"])
                    if k not in seen:
                        seen.add(k)
                        dedup.append({k2: v[k2] for k2 in ("value", "page_id", "url", "kind", "evidence")})
                note = "The same fact is stated differently in more than one place. Neither value is treated as correct."
                if any(v["kind"] == "suggested" for v in dedup):
                    note += " At least one value was read from page prose by a model; check it against the page."
                cid = "cf-" + short(e["id"], prop)
                conflicts.append(Conflict(id=cid, entity_id=e["id"], entity_label=e["label"], property=prop, values=dedup, note=note,
                                          acknowledged=cid in ack, reviewer_note=(ack.get(cid) or {}).get("note", "")))
    cf_of = defaultdict(list)
    for c in conflicts:
        cf_of[c.entity_id].append(c.id)

    # ---- nodes -------------------------------------------------------------------------------------------
    nodes = []
    for e in entities.values():
        ms = e["mentions"]
        props = {}
        for m in sorted(ms, key=lambda m: m["kind"] != "extracted"):
            for k, v in m["props"].items():
                props.setdefault(k, v)
        provs = []
        for m in ms[:6]:
            provs.append(Provenance(source_url=m["url"], resource_id=m["rid"], kind=m["kind"], method=m["method"],
                                    evidence=m.get("evidence"), evidence_verified=bool(m.get("evidence_verified"))))
        types = {m["type"] for m in ms if m["type"]}
        groups = {group_of(t) for t in types}
        if {"org", "place"} <= groups:
            groups.discard("place")
        checks = [Check(name="Name present on the page", passed=True),
                  Check(name="Type is a Schema.org type", passed=e["type"] in vocab.TYPES or e["type"] == "WebPage"),
                  Check(name="One consistent type across pages", passed=len(groups) <= 1),
                  Check(name="Not an unresolved ambiguity", passed=not amb_of.get(e["id"]))]
        if e["origin"] != "extracted":
            checks.append(Check(name="Evidence quote found verbatim on the page", passed=any(m.get("evidence_verified") for m in ms if m["kind"] == "suggested")))
            checks.append(Check(name="Seen on more than one page or in markup", passed=len(e["pages"]) > 1 or e["origin"] == "both"))
        pgs = [{"page_id": p, "url": pages[p]["url"]} for p in e["pages"] if p in pages]
        nodes.append(Node(id=e["id"], label=e["label"], type=e["type"], origin=e["origin"], pages=pgs, properties=props,
                          aliases=e["aliases"], provenance=provs, confidence=conf(checks),
                          auto_merged=e.get("auto_merged", []), type_note=e.get("type_note", ""),
                          ambiguous_with=sorted({x for a in amb_of.get(e["id"], []) for x in a.entity_ids if x != e["id"]}),
                          conflict_ids=cf_of.get(e["id"], [])))
    return {"dropped_edges": dropped_edges, "dropped_detail": dropped_detail[:300], "nodes": nodes, "edges": edges, "conflicts": conflicts, "ambiguities": amb, "m2e": m2e, "entities": entities}
