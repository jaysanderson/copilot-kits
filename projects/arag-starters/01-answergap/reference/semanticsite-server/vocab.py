"""JSON-LD validation against the official Schema.org vocabulary (bundled, compiled by
scripts/build_vocab.py). Checks syntax, context, type, property-for-type, value type, dates, URLs,
and a recommended-minimum property table. Schema.org validity does not guarantee rich-result
eligibility (PRD s13) and this module never claims it does."""
import json
import re
from functools import lru_cache

from .config import SERVER
from .schema import Issue, Validation

_V = json.loads((SERVER / "data" / "schemaorg.min.json").read_text())
TYPES, PROPS = _V["types"], _V["props"]
DATATYPES = {"Text", "URL", "Number", "Integer", "Float", "Boolean", "Date", "DateTime", "Time", "CssSelectorType",
             "XPathType", "PronounceableText"}

REQUIRED = {  # recommended minimum, so a record is useful, not merely legal
    "Organization": ["name"], "LocalBusiness": ["name", "address"], "Person": ["name"],
    "Product": ["name"], "Offer": ["price", "priceCurrency"], "Event": ["name", "startDate", "location"],
    "Article": ["headline", "author", "datePublished"], "BreadcrumbList": ["itemListElement"],
    "FAQPage": ["mainEntity"], "Place": ["name"], "Service": ["name"], "ListItem": ["position"],
    "JobPosting": ["title", "datePosted", "hiringOrganization"],
}
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$|^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
URL_RE = re.compile(r"^(https?://|/|#|mailto:|tel:)\S+$", re.I)
NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


@lru_cache(maxsize=None)
def ancestors(t):
    seen, stack = set(), [t]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack.extend(TYPES.get(x, {}).get("sub", []))
    return frozenset(seen)


def norm_type(t):
    return t.split("/")[-1].split(":")[-1] if isinstance(t, str) else str(t)


def types_of(node):
    t = node.get("@type")
    if t is None:
        return []
    return [norm_type(x) for x in (t if isinstance(t, list) else [t])]


def _iter_nodes(doc):
    """Yield every top-level node of a document (handles @graph and lists)."""
    if isinstance(doc, list):
        for d in doc:
            yield from _iter_nodes(d)
    elif isinstance(doc, dict):
        if "@graph" in doc:
            ctx = doc.get("@context")
            for d in doc["@graph"] if isinstance(doc["@graph"], list) else [doc["@graph"]]:
                if isinstance(d, dict) and ctx and "@context" not in d:
                    d = {**d, "@context": ctx}
                yield from _iter_nodes(d)
        else:
            yield doc


def validate_doc(doc):
    """Validate a parsed JSON-LD document. Returns Validation."""
    issues = []

    def add(sev, code, msg, path=""):
        issues.append(Issue(severity=sev, code=code, message=msg, path=path))

    nodes = list(_iter_nodes(doc))
    if not nodes:
        add("error", "empty", "The JSON-LD block contains no objects.")
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            add("error", "not_object", "Top-level JSON-LD value is not an object.", f"[{i}]")
            continue
        ctx = n.get("@context")
        if ctx is None:
            add("error", "no_context", "Missing @context; Schema.org terms are undefined without it.", f"[{i}]")
        elif "schema.org" not in json.dumps(ctx):
            add("warning", "context_not_schema", "@context does not reference schema.org.", f"[{i}]")
        _node(n, f"[{i}]" if len(nodes) > 1 else "", add, top=True)
    return Validation(valid=not any(x.severity == "error" for x in issues), issues=issues)


def _node(n, path, add, top=False):
    ts = types_of(n)
    if not ts:
        if not (top and set(n) <= {"@context", "@id"}):
            add("warning", "no_type", "Object has no @type.", path)
        ts = []
    known = []
    for t in ts:
        if t in TYPES:
            known.append(t)
        else:
            add("error", "unknown_type", f"'{t}' is not a Schema.org type.", f"{path}.@type")
    allowed = set()
    for t in known:
        allowed |= ancestors(t)
    for t in known:
        for req in REQUIRED.get(t, []):
            if t == "Offer" and "itemOffered" in n:
                continue                         # a catalogue offer wrapping an item carries no price of its own
            if req not in n:
                add("warning", "missing_property", f"{t} is missing recommended property '{req}'.", path)
    if "Offer" in known and n.get("price") not in (None, "") and not n.get("priceCurrency") and "itemOffered" not in n:
        add("error", "price_without_currency", "An Offer states a price with no priceCurrency; a bare number is not a price a search engine can use.", f"{path}.price")
    for k, v in n.items():
        if k.startswith("@"):
            continue
        p = PROPS.get(k)
        if p is None:
            add("error", "unknown_property", f"'{k}' is not a Schema.org property.", f"{path}.{k}")
            continue
        if known and not (set(p["dom"]) & allowed):
            add("warning", "property_not_for_type",
                f"'{k}' is not defined for {'/'.join(known)} (expected on {', '.join(p['dom'][:3])}).", f"{path}.{k}")
        for item in (v if isinstance(v, list) else [v]):
            _value(k, p, item, f"{path}.{k}", add)


def _value(k, p, item, path, add):
    rng = set(p["rng"])
    if isinstance(item, dict):
        if set(item) == {"@id"}:
            return                                  # reference; resolved at site level
        its = types_of(item)
        if its and all(t in TYPES for t in its):
            ok = any(ancestors(t) & rng for t in its) or ("Thing" in rng)
            if not ok and not (rng & DATATYPES and not rng - DATATYPES - {"Text"}):
                add("warning", "range_mismatch",
                    f"'{k}' expects {', '.join(sorted(rng)[:4])}, got {'/'.join(its)}.", path)
        _node(item, path, add)
        return
    if "Date" in rng or "DateTime" in rng:
        if not isinstance(item, str) or not DATE_RE.match(item.strip()):
            add("error", "invalid_date", f"'{k}' value {json.dumps(item)} is not an ISO 8601 date/datetime.", path)
    elif rng and rng <= {"URL"} or (k in ("url", "sameAs", "image", "logo") and isinstance(item, str)):
        if isinstance(item, str) and not URL_RE.match(item.strip()):
            add("warning", "invalid_url", f"'{k}' value {json.dumps(item)} is not a URL.", path)
    elif k in ("price", "lowPrice", "highPrice") or (rng and rng <= {"Number", "Integer", "Float"}):
        if not NUM_RE.match(str(item).strip()):
            add("error", "invalid_number", f"'{k}' value {json.dumps(item)} is not numeric.", path)


def defined_ids(doc):
    """All @id values DEFINED (object with more than the reference) inside a document, plus all referenced."""
    defined, referenced = set(), set()

    def walk(x):
        if isinstance(x, dict):
            if "@id" in x:
                (referenced if set(x) == {"@id"} else defined).add(x["@id"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(doc)
    return defined, referenced


def parse(raw):
    """Parse a raw <script> body. Returns (doc, Validation) - syntax errors become an error issue."""
    try:
        doc = json.loads(raw)
    except Exception as e:  # noqa: BLE001 - any parse failure is a finding
        return None, Validation(valid=False, issues=[Issue(severity="error", code="syntax",
                                                           message=f"Invalid JSON: {e}")])
    return doc, validate_doc(doc)


def edge_valid(pred, subj_type, obj_type):
    """Is this Schema.org property valid between these node types? Checks the property's domain against the subject's type and its
    range against the object's type, walking each type's supertypes (never comparing names). Returns (valid, wrapped_in_offer).
    makesOffer/offers have range Offer: a Product or Service target is valid when emitted inside an Offer's itemOffered."""
    p = PROPS.get(pred)
    if not p:
        return False, False
    if not (set(p["dom"]) & ancestors(subj_type)):
        return False, False
    rng = set(p["rng"]) - DATATYPES
    oa = ancestors(obj_type)
    if not rng or "Thing" in rng or (rng & oa):
        return True, False
    if "Offer" in rng and ({"Product", "Service"} & oa):
        return True, True
    return False, False
