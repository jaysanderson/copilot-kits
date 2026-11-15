"""Model-assisted extraction of what is stated in page PROSE and in no markup.

One structured /ask per page, scoped to that page's own resource and given the whole resource, with
the cheapest capable model pinned. The model proposes; deterministic code decides what survives:
every proposal must carry a verbatim evidence quote that exists in the ingested page text, otherwise
it is discarded (and counted) rather than shown as a fact. Provenance is bound structurally: the
record's page and resource come from the call we made, never from model output."""
import re

from . import arag
from .compare import VERB_START, is_title

TYPES = ["Person", "Organization", "Product", "Service", "Place", "Event"]
PREDICATES = ["worksFor", "employee", "memberOf", "founder", "department", "subOrganization", "parentOrganization",
              "location", "containedInPlace", "containsPlace", "brand", "manufacturer", "provider", "makesOffer",
              "areaServed", "organizer", "performer", "sponsor", "author", "isRelatedTo", "isSimilarTo",
              "isAccessoryOrSparePartFor", "alumniOf", "hasPart", "isPartOf", "instructor", "otherRelation"]
FACT_PROPS = ["price", "openingHours", "telephone", "email", "address", "foundingDate", "jobTitle", "startDate", "endDate", "maximumAttendeeCapacity", "memberCount"]
INVERSE = {"employee": "worksFor", "parentOrganization": "subOrganization", "containsPlace": "containedInPlace"}

PREDICATE_HELP = (
    "worksFor: Person works for Organization. employee: Organization employs Person. memberOf: Person/Organization is "
    "a member of Organization. founder: Organization founded by Person. department: Organization has department "
    "Organization. subOrganization/parentOrganization: Organization hierarchy. location: Organization/Event is at a "
    "Place. containedInPlace/containsPlace: Place within Place. brand/manufacturer: Product made or branded by "
    "Organization. provider: Service provided by Organization or Person. makesOffer: Organization sells Product or "
    "Service. areaServed: Service/Organization serves Place. organizer/performer/sponsor: Event roles. author: "
    "Person wrote the work. isRelatedTo/isSimilarTo: Product relationships. isAccessoryOrSparePartFor: Product fits "
    "Product. alumniOf: Person studied at Organization.")


def build_schema(rid):
    src = {"type": "string", "enum": [rid]}
    return {
        "name": "page_knowledge",
        "description": "Entities, relationships and facts that this page's text itself states.",
        "type": "object",
        "properties": {
            "primary_entity": {"type": "string", "description": "Name of the one entity this page is mainly about, or empty."},
            "entities": {"type": "array", "items": {"type": "object", "properties": {
                "name": {"type": "string"}, "type": {"type": "string", "enum": TYPES},
                "source": src, "evidence": {"type": "string", "description": "A sentence copied word for word from the page."}},
                "required": ["name", "type", "source", "evidence"]}},
            "relations": {"type": "array", "items": {"type": "object", "properties": {
                "subject": {"type": "string"}, "predicate": {"type": "string", "enum": PREDICATES},
                "object": {"type": "string"}, "source": src,
                "label": {"type": "string", "description": "One or two words naming the relationship, such as 'roasts' or 'leads'. Required for otherRelation."},
                "evidence": {"type": "string", "description": "The sentence from the page that states this relationship, copied word for word."}},
                "required": ["subject", "predicate", "object", "source", "evidence"]}},
            "facts": {"type": "array", "items": {"type": "object", "properties": {
                "entity": {"type": "string"}, "property": {"type": "string", "enum": FACT_PROPS},
                "value": {"type": "string"}, "source": src,
                "evidence": {"type": "string", "description": "The text copied word for word that states the value."}},
                "required": ["entity", "property", "value", "source", "evidence"]}},
        },
        "required": ["entities", "relations", "facts"],
    }


QUERY = (
    "Read this whole web page and list what its text states. "
    "ENTITIES: named people, organisations, products, services, places and events (use the exact name as written). "
    "RELATIONS: only relationships the text explicitly states between two listed entities. Allowed predicates: "
    + PREDICATE_HELP +
    " FACTS: a price, opening hours, telephone, email, address, founding date, job title, start or end date, seating or attendance capacity (maximumAttendeeCapacity) or number of members (memberCount) that the text "
    "states for a listed entity, with the value exactly as written. "
    "Entities must be proper names (for example 'Marrow Creek' or 'Odette Ransome'), never generic words or topics such as 'coffee', "
    "'training' or 'the team'. "
    "Named departments, programmes, courses and events count as entities. Be exhaustive: if one sentence lists several items, "
    "return one relation per item. "
    "A venue (museum, gallery, cafe, shop, hall) is a place. When a page says an organisation runs, owns or operates a venue, "
    "staff, sponsors and departments belong to that organisation, not to the building: use the organisation as the subject or object. "
    "Never state a relationship the sentence denies. "
    "For every item, copy a supporting sentence word for word into evidence. Do not infer, guess or add anything the "
    "text does not say. If the page states nothing for a section, return an empty list for it.")


def norm_text(s):
    s = (s or "").lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def in_text(needle, haystack_norm):
    n = norm_text(needle).strip(" .\"'")
    return len(n) >= 3 and n in haystack_norm


RECALL_QUERY = (
    "These entities were already found on this page: {ents}. These relationships were already found: {rels}. "
    "Read the whole page again, sentence by sentence, and list every OTHER relationship the text explicitly states "
    "between two of the entities above (use their exact names). A sentence that lists several items gives one relation per "
    "item. A sentence that says who does something to what (for example 'X roasts Y', 'X is led by Y', 'X is taught by Y', "
    "'collect from X') is a relationship. Use the same predicates as before; use otherRelation with a label when none fits. "
    "Return no entities and no facts. Copy a supporting sentence word for word into evidence for each relation.")


def run_page(meter, rid, page_text, passes=2):
    """Returns (verified, dropped). Pass 1 extracts entities, relations and facts. Pass 2 (optional) re-reads the
    page with pass 1's findings in hand and adds only the relationships pass 1 missed; it is reported separately
    so its cost and its yield are both visible."""
    data, _ = arag.extract(meter, rid, QUERY, build_schema(rid))
    out, dropped = _verify(data or {}, page_text)
    out["pass2_added"] = 0
    if passes >= 2 and len(out["entities"]) >= 2:
        names = ", ".join(e["name"] for e in out["entities"])
        have = "; ".join(f"{r['subject']} {r['label'] or r['predicate']} {r['object']}" for r in out["relations"]) or "none"
        d2, _ = arag.extract(meter, rid, RECALL_QUERY.format(ents=names, rels=have), build_schema(rid), kind="structured_extraction_recall")
        o2, dr2 = _verify(d2 or {}, page_text, [e['name'] for e in out['entities']])
        known = {norm_text(e["name"]) for e in out["entities"]}
        seen = {(norm_text(r["subject"]), r["predicate"], norm_text(r["object"])) for r in out["relations"]}
        for r in o2["relations"]:
            k = (norm_text(r["subject"]), r["predicate"], norm_text(r["object"]))
            if k not in seen and norm_text(r["subject"]) in known and norm_text(r["object"]) in known:
                out["relations"].append(r)
                seen.add(k)
                out["pass2_added"] += 1
        for kk, v in dr2.items():
            dropped[kk] = dropped.get(kk, 0) + v
        out["dropped_examples"] += o2["dropped_examples"]
    return out, dropped


_ROLES = r"(?:manager|director|curator|coordinator|officer|roaster|guide|chair|chairperson|president|secretary|treasurer|trustee|administrator|technician|barista|executive|conservator|librarian|archivist|programmer|engineer|assistant)"
ROLE_FIRST = {"head", "chief", "deputy", "senior", "junior", "assistant", "general", "technical", "volunteer", "executive", "acting", "associate", "principal", "vice"}


def _role_label(label):
    """Does a relationship label read as a job title rather than a verb? ('Head of Programming', 'Technical Manager', 'Head of')"""
    toks = re.findall(r"[A-Za-z&'-]+", label.lower())
    if not toks or toks[0] in VERB_START:
        return False
    return toks[0] in ROLE_FIRST or bool(re.search(r"\b" + _ROLES + r"$", label.strip(), re.I))


ROLE_NAME = re.compile(r"^(?:(?:head|chief|senior|junior|assistant|deputy|technical|volunteer|general|acting|lead|principal|executive)\s+(?:of\s+[\w&' -]{1,30}|(?:\w+\s+){0,2}" + _ROLES + r")|" + _ROLES + r"s?)$", re.I)
NEGATION = re.compile(r"\b(not|no|never|neither|nor|isn't|aren't|wasn't|weren't|doesn't|don't|didn't|unrelated|no longer|without)\b", re.I)
SUCCESSION = re.compile(r"\b(succeed(?:ed|s|ing)?|successor|predecessor|replac(?:ed|es|ing)|took over|takes over|handed over|stepped down|retire[ds]?|follow(?:ed|s) (?:\w+ ){0,2}as)\b", re.I)
TITLE_FRAGMENT = re.compile(r"\b(led|run|managed|headed|chaired|overseen|directed|supervised|founded|owned)\s+by\b|^by\b", re.I)
PERSON_PREDICATES_OK = {"otherRelation"}


def _verify(data, page_text, extra_known=()):
    hay = norm_text(page_text)
    first_line = norm_text(page_text.split("\n", 1)[0])
    out = {"entities": [], "relations": [], "facts": [], "primary": (data.get("primary_entity") or "").strip()}
    dropped = {"no_evidence_on_page": 0, "name_not_on_page": 0, "bad_shape": 0}
    names = set()
    ex = out["dropped_examples"] = []
    for e in data.get("entities") or []:
        if not isinstance(e, dict) or not e.get("name") or e.get("type") not in TYPES:
            dropped["bad_shape"] += 1
            continue
        if ROLE_NAME.match(e["name"].strip()):
            dropped["role_not_entity"] = dropped.get("role_not_entity", 0) + 1            # a job title or team-column value is not a thing in the world
            ex.append(f"role, not an entity: {e['name']}")
            continue
        if re.match(r"^\d+[a-z]?\s+\w+.*\b(street|st|road|rd|lane|ln|avenue|ave|drive|dr|row|court|place|terrace|parade|way|crescent)\b", e["name"].strip(), re.I):
            dropped["address_not_entity"] = dropped.get("address_not_entity", 0) + 1       # an address is a property of a place, not a place
            ex.append(f"address, not an entity: {e['name']}")
            continue
        if not in_text(e["name"], hay):
            dropped["name_not_on_page"] += 1
            ex.append(f"entity name not on page: {e['name']}")
            continue
        ev_ok = in_text(e.get("evidence", ""), hay)
        out["entities"].append({"name": e["name"].strip(), "type": e["type"], "evidence": (e.get("evidence") or "").strip(),
                                "evidence_verified": ev_ok})
        names.add(norm_text(e["name"]))
    for r in data.get("relations") or []:
        if not isinstance(r, dict) or r.get("predicate") not in PREDICATES or not r.get("subject") or not r.get("object"):
            dropped["bad_shape"] += 1
            continue
        if not in_text(r.get("evidence", ""), hay):
            dropped["no_evidence_on_page"] += 1       # an unsupported relationship is never presented as a fact
            ex.append(f"relation evidence not on page: {r['subject']} {r['predicate']} {r['object']} :: {r.get('evidence','')[:80]}")
            continue
        if not (in_text(r["subject"], hay) and in_text(r["object"], hay)):
            dropped["name_not_on_page"] += 1
            ex.append(f"relation endpoint not on page: {r['subject']} {r['predicate']} {r['object']}")
            continue
        s, p, o = r["subject"].strip(), r["predicate"], r["object"].strip()
        ev_ = r.get("evidence", "")
        if norm_text(ev_) and norm_text(ev_) in first_line:
            dropped["title_only"] = dropped.get("title_only", 0) + 1     # a page title or menu label is a label, not a sentence that states a relationship
            ex.append(f"title only: {s} {p} {o} :: {ev_[:60]}")
            continue
        if NEGATION.search(ev_) and (norm_text(s) in norm_text(ev_) or norm_text(o) in norm_text(ev_)):
            dropped["negated"] = dropped.get("negated", 0) + 1            # a sentence that denies a relationship never becomes an edge
            ex.append(f"negated: {s} {p} {o} :: {ev_[:80]}")
            continue
        if SUCCESSION.search(ev_) and p in ("otherRelation", "isRelatedTo", "colleague", "knows"):
            dropped["succession"] = dropped.get("succession", 0) + 1       # two people who held the same role in turn are not related by it
            ex.append(f"succession: {s} {p} {o} :: {ev_[:80]}")
            continue
        if norm_text(s) == norm_text(o):
            dropped["bad_shape"] += 1
            continue
        if p in INVERSE:
            s, o, p = o, s, INVERSE[p]
        lab_ = (r.get("label") or "").strip()
        if p == "otherRelation" and _role_label(lab_):
            # a job title is not a relationship name: 'Moss Hale - Volunteer Coordinator - the cinema' says Moss works for the cinema,
            # and the title is the person's jobTitle, which has its own evidence check below
            dropped["role_label"] = dropped.get("role_label", 0) + 1
            p = "worksFor"
            if is_title(lab_) and in_text(lab_, hay) and not lab_.lower().endswith((" of", " for", " at")):
                data.setdefault("facts", [])
                data["facts"] = list(data.get("facts") or []) + [{"entity": s, "property": "jobTitle", "value": lab_, "evidence": r["evidence"]}]
            r = {**r, "label": ""}
        out["relations"].append({"subject": s, "predicate": p, "object": o, "label": (r.get("label") or "").strip()[:40], "evidence": r["evidence"].strip(), "evidence_verified": True})
    for f in data.get("facts") or []:
        if not isinstance(f, dict) or f.get("property") not in FACT_PROPS or not f.get("entity") or not f.get("value"):
            dropped["bad_shape"] += 1
            continue
        if f["property"] == "jobTitle" and (TITLE_FRAGMENT.search(f["value"]) or not is_title(f["value"])):
            dropped["not_a_title"] = dropped.get("not_a_title", 0) + 1     # 'led by Dr X' is a sentence fragment, not a job title
            ex.append(f"jobTitle fragment: {f['value'][:60]}")
            continue
        if not in_text(f.get("evidence", ""), hay) or not in_text(f["value"], hay):
            dropped["no_evidence_on_page"] += 1
            ex.append(f"fact not verbatim: {f['entity']} {f['property']}={f['value']} :: {f.get('evidence','')[:60]}")
            continue
        out["facts"].append({"entity": f["entity"].strip(), "property": f["property"], "value": f["value"].strip(),
                             "evidence": f["evidence"].strip(), "evidence_verified": True})
    # a relationship whose endpoints are not listed entities has no typed node to attach to: discard it, counted
    known = {norm_text(e["name"]) for e in out["entities"]} | {norm_text(x) for x in extra_known}
    keep = []
    for r in out["relations"]:
        if norm_text(r["subject"]) in known and norm_text(r["object"]) in known:
            keep.append(r)
        else:
            dropped["unknown_endpoint"] = dropped.get("unknown_endpoint", 0) + 1
    out["relations"] = keep
    out["facts"] = [f for f in out["facts"] if norm_text(f["entity"]) in known or dropped.update(
        unknown_endpoint=dropped.get("unknown_endpoint", 0) + 1)]
    return out, dropped
