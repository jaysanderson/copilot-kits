"""Deterministic knowledge extraction from existing JSON-LD and page structure. Zero model cost.
Everything produced here has kind='extracted': it was read off markup that already exists."""
import re
from urllib.parse import urljoin

from . import vocab

NAME_KEYS = ("name", "headline", "legalName", "title")
FOLD = {"Offer", "AggregateOffer", "PostalAddress", "OpeningHoursSpecification", "ContactPoint", "GeoCoordinates",
        "ListItem", "Rating", "AggregateRating", "QuantitativeValue", "PriceSpecification", "MonetaryAmount"}
SKIP_TOP = {"BreadcrumbList", "WebSite", "SearchAction", "ImageObject"}
# a page about a thing is not the thing: documents (web pages, articles, lists) are not entities
DOC_TYPES = {"WebPage", "Article", "WebSite", "ItemList", "FAQPage", "CollectionPage", "SiteNavigationElement", "WPHeader", "WPFooter"}
INTEREST_PROPS = {"price", "priceCurrency", "openingHours", "telephone", "email", "address", "foundingDate", "maximumAttendeeCapacity", "numberOfEmployees",
                  "jobTitle", "startDate", "endDate", "url", "description"}


def _scalar(v):
    if isinstance(v, (str, int, float)):
        return str(v)
    return None


def _fmt_address(a):
    parts = [a.get(k) for k in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry")]
    return ", ".join(str(p) for p in parts if p and isinstance(p, (str, int)))


def _fmt_hours(o):
    days = o.get("dayOfWeek")
    days = days if isinstance(days, list) else [days] if days else []
    days = [str(d).split("/")[-1] for d in days]
    when = " (valid " + " to ".join(str(o[k]) for k in ("validFrom", "validThrough") if o.get(k)) + ")" if (o.get("validFrom") or o.get("validThrough")) else ""
    return f"{'/'.join(days)} {o.get('opens', '')}-{o.get('closes', '')}{when}".strip()


def mentions_from_jsonld(doc, page_url):
    """Return (mentions, edges, refs). mention = {key, type, name, jsonld_id, props{}, path}.
    edges = [{subject_key, predicate, object_key|object_ref}], refs = referenced @ids."""
    mentions, edges, refs = [], [], []
    counter = [0]

    def walk(node, path, parent=None, pred=None):
        ts = vocab.types_of(node)
        main = next((t for t in ts if t in vocab.TYPES), ts[0] if ts else None)
        nid = node.get("@id")
        nid = urljoin(page_url, nid) if isinstance(nid, str) else None
        name = next((str(node[k]) for k in NAME_KEYS if isinstance(node.get(k), (str, int))), None)
        if main == "ListItem":                       # a list entry wraps the real entity in `item`
            it = node.get("item")
            if isinstance(it, dict) and set(it) != {"@id"}:
                walk(it, f"{path}.item", None, None)
            return None
        if main == "ItemList":                       # a container, not an entity: walk its entries
            els = node.get("itemListElement", [])
            for el in els if isinstance(els, list) else [els]:
                if isinstance(el, dict):
                    walk(el, f"{path}.itemListElement", None, None)
            return None
        if main in FOLD or (parent is not None and name is None and main):
            if parent is not None:
                _fold(parent, pred, main, node)
            return None
        if main in SKIP_TOP and parent is None:
            return None
        if main and main in vocab.TYPES and vocab.ancestors(main) & DOC_TYPES and parent is None:
            for k2, v2 in node.items():                   # still read what the document says ABOUT things (author, publisher, about)
                for item in (v2 if isinstance(v2, list) else [v2]):
                    if isinstance(item, dict) and set(item) != {"@id"} and k2 in ("about", "mainEntity", "author", "publisher", "mentions"):
                        walk(item, f"{path}.{k2}", None, None)
            return None
        if not main or not name:
            return None
        counter[0] += 1
        m = {"key": f"{page_url}#m{counter[0]}", "type": main, "name": name.strip(), "jsonld_id": nid, "props": {},
             "aliases": [], "path": path}
        mentions.append(m)
        for k, v in node.items():
            if k.startswith("@") or k in NAME_KEYS:
                continue
            for item in (v if isinstance(v, list) else [v]):
                if isinstance(item, dict):
                    if set(item) == {"@id"}:
                        refs.append(item["@id"])
                        edges.append({"subject_key": m["key"], "predicate": k, "object_ref": urljoin(page_url, item["@id"])})
                    else:
                        child = walk(item, f"{path}.{k}", m, k)
                        if child:
                            edges.append({"subject_key": m["key"], "predicate": k, "object_key": child["key"]})
                elif k == "alternateName":
                    m["aliases"].extend([str(x) for x in (v if isinstance(v, list) else [v])])
                    break
                elif k == "sameAs":
                    m["props"].setdefault("sameAs", []).append(str(item))
                elif k in INTEREST_PROPS and _scalar(item) is not None:
                    m["props"].setdefault(k, str(item))
        return m

    def _fold(parent_m, pred, ftype, node):
        # folding writes into the named parent mention
        target = parent_m
        if target is None:
            return
        if ftype in ("Offer", "AggregateOffer", "PriceSpecification"):
            for k in ("price", "priceCurrency", "lowPrice"):
                if _scalar(node.get(k)) is not None:
                    target["props"].setdefault("price" if k == "lowPrice" else k, str(node[k]))
        elif ftype == "PostalAddress":
            a = _fmt_address(node)
            if a:
                target["props"].setdefault("address", a)
        elif ftype == "OpeningHoursSpecification":
            target["props"]["openingHours"] = (target["props"].get("openingHours", "") + "; " + _fmt_hours(node)).strip("; ")
        elif ftype == "ContactPoint":
            for k in ("telephone", "email"):
                if _scalar(node.get(k)):
                    target["props"].setdefault(k, str(node[k]))

    for n in vocab._iter_nodes(doc):
        if isinstance(n, dict):
            walk(n, "", None, None)
    return mentions, edges, refs


def breadcrumb_edges(doc, html_crumbs, nav_pairs, page_url):
    """Navigation facts: 'X is part of Y' from breadcrumbs, 'Y has part X' from nested nav menus.
    Returns list of {child:{name,url}, parent:{name,url}, method}."""
    out = []
    crumbs = []
    for n in vocab._iter_nodes(doc) if doc else []:
        if isinstance(n, dict) and "BreadcrumbList" in vocab.types_of(n):
            items = n.get("itemListElement", [])
            items = items if isinstance(items, list) else [items]
            items = sorted([i for i in items if isinstance(i, dict)], key=lambda i: int(str(i.get("position", 0)) if str(i.get("position", 0)).isdigit() else 0))
            for i in items:
                it = i.get("item")
                nm = i.get("name") or (it.get("name") if isinstance(it, dict) else None)
                u = (it.get("@id") if isinstance(it, dict) else it) if it else page_url
                if nm:
                    crumbs.append({"name": str(nm), "url": urljoin(page_url, str(u)) if isinstance(u, str) else page_url})
    method = "json-ld"
    if not crumbs and html_crumbs:
        crumbs, method = html_crumbs, "breadcrumb"
    for a, b in zip(crumbs, crumbs[1:]):
        out.append({"child": b, "parent": a, "predicate": "isPartOf", "method": "breadcrumb" if method == "breadcrumb" else "json-ld"})
    for p in nav_pairs:
        out.append({"child": p["child"], "parent": p["parent"], "predicate": "isPartOf", "method": "navigation"})
    return out


_DATE_FORMATS = ["%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]


def repair_date(s):
    """Return (iso, certain) for a malformed date string; certain=False when day/month order is ambiguous."""
    from datetime import datetime
    s = str(s).strip()
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m:
        a, b, y = int(m[1]), int(m[2]), int(m[3])
        if a > 12 and b <= 12:
            return f"{y:04d}-{b:02d}-{a:02d}", True
        if b > 12 and a <= 12:
            return f"{y:04d}-{a:02d}-{b:02d}", True
        if a <= 12 and b <= 12:
            return (f"{y:04d}-{b:02d}-{a:02d}", False) if a != b else (f"{y:04d}-{a:02d}-{b:02d}", True)
    for f in _DATE_FORMATS:
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%d"), True
        except ValueError:
            continue
    return None, False
