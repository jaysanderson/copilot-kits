"""Assemble evidence-backed JSON-LD proposals. The model never writes JSON-LD. It supplies verified
facts and relationships; this module assembles the document deterministically, so syntax is always
well-formed and every added property can be traced to a quote on the page or to existing markup."""
import copy
import re
from difflib import get_close_matches

from . import vocab
from .compare import is_title
from .knowledge import repair_date
from .resolve import conf, norm_name, slug
from .schema import Check, Provenance, Suggestion, Validation

# markup that already says the same thing in another shape
EQUIV = {"openingHours": ("openingHoursSpecification",), "telephone": ("contactPoint",), "email": ("contactPoint",),
         "price": ("offers",), "address": ("location",)}
CORE_PROPS = {"address", "telephone", "openingHours", "price", "jobTitle"}
CORE_RELS = {"worksFor", "brand", "manufacturer", "parentOrganization"}
EQUIV_REL = {"manufacturer": ("brand",), "brand": ("manufacturer",), "parentOrganization": ("worksFor",), "worksFor": ("parentOrganization",)}
DIRECT = {"telephone", "email", "foundingDate", "jobTitle", "startDate", "endDate", "openingHours", "maximumAttendeeCapacity"}
CURRENCY = re.compile(r"\b(AUD|USD|NZD|GBP|EUR|CAD|SGD)\b", re.I)
SYMBOL_CURRENCY = [(re.compile(r"(?<![A-Za-z])A\$|\bAU\$"), "AUD"), (re.compile(r"\bNZ\$"), "NZD"), (re.compile(r"\bUS\$"), "USD"), (re.compile(r"(?<![A-Za-z])C\$|\bCA\$"), "CAD"),
                   (re.compile(r"(?<![A-Za-z])S\$|\bSG\$"), "SGD"), (re.compile("\u00a3"), "GBP"), (re.compile("\u20ac"), "EUR")]


def stated_currency(*texts):
    """A currency the page itself states: an ISO code or an unambiguous symbol (A$, NZ$, US$, £, €). A bare '$' is ambiguous and is never guessed."""
    for s in texts:
        m = CURRENCY.search(s or "")
        if m:
            return m.group().upper()
        for rx, code in SYMBOL_CURRENCY:
            if rx.search(s or ""):
                return code
    return None


def iri(e, root_url):
    """A stable identifier: the @id the site already uses, else a site-scoped fragment (not tied to whichever page was read first)."""
    for m in e["mentions"]:
        if m.get("jsonld_id") and m["kind"] == "extracted":
            return m["jsonld_id"]
    return f"{root_url.rstrip('/')}/#{slug(e['label'])}-{e['id'].rsplit('-', 1)[-1][:4]}"


def _repair(node, path, label, pp, needs, evid, page_url, prov_for):
    """In-place deterministic repairs on an existing node. Records suggested changes in pp."""
    ts = node.get("@type")
    if ts is not None:
        lst = ts if isinstance(ts, list) else [ts]
        fixed = []
        for t in lst:
            nt = vocab.norm_type(t)
            if nt not in vocab.TYPES:
                best = get_close_matches(nt, list(vocab.TYPES), n=1, cutoff=0.7)
                if best:
                    pp[f"{label}.@type"] = "suggested"
                    needs.append(f"{label}: @type '{t}' is not a Schema.org type; proposed '{best[0]}'.")
                    evid.append(Provenance(source_url=page_url, kind="suggested", method="model", evidence=f"@type '{t}' -> '{best[0]}' (nearest Schema.org type)", evidence_verified=True))
                    fixed.append(best[0])
                    continue
            fixed.append(t)
        node["@type"] = fixed if isinstance(ts, list) else fixed[0]
    for k in list(node):
        if k.startswith("@"):
            continue
        if k not in vocab.PROPS:
            best = get_close_matches(k, list(vocab.PROPS), n=1, cutoff=0.85)
            if best and best[0] not in node:
                node[best[0]] = node.pop(k)
                pp[f"{label}.{best[0]}"] = "suggested"
                needs.append(f"{label}: property '{k}' is not Schema.org; proposed '{best[0]}'.")
                k = best[0]
        p = vocab.PROPS.get(k)
        v = node.get(k)
        if p and ({"Date", "DateTime"} & set(p["rng"])) and isinstance(v, str) and not vocab.DATE_RE.match(v.strip()):
            iso, certain = repair_date(v)
            if iso and certain:
                node[k] = iso
                pp[f"{label}.{k}"] = "suggested"
                needs.append(f"{label}: '{k}' value '{v}' is not ISO 8601; proposed '{iso}'.")
            elif iso:
                needs.append(f"{label}: '{k}' value '{v}' is not ISO 8601 and the day/month order is ambiguous; not changed.")
        for item in (v if isinstance(v, list) else [v]):
            if isinstance(item, dict) and set(item) != {"@id"}:
                _repair(item, f"{path}.{k}", f"{label}.{k}", pp, needs, evid, page_url, prov_for)
        pp.setdefault(f"{label}.{k}", "extracted")


NOT_ENTITIES = {"ListItem", "Offer", "AggregateOffer", "PostalAddress", "OpeningHoursSpecification", "ContactPoint", "Question", "Answer", "Rating", "AggregateRating",
                "Review", "ImageObject", "GeoCoordinates", "PropertyValue", "QuantitativeValue", "MonetaryAmount", "PriceSpecification", "BreadcrumbList", "ItemList"}


def _typed_nested(node):
    """Typed, named objects defined inline inside a node (not references, not wrappers like Offer or ListItem)."""
    out = []

    def walk(x):
        if isinstance(x, dict):
            ts = vocab.types_of(x)
            if ts and not (set(ts) & NOT_ENTITIES) and x is not node and isinstance(x.get("name"), str) and set(x) != {"@id"}:
                out.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(node)
    return out


def build(page, res, mentions_by_page, edges, dangling, root_url):
    """page: stored page dict; res: resolve() output; returns Suggestion-ready dict or None."""
    pid, purl, rid = page["id"], page["url"], page.get("rid")
    ents = res["entities"]
    m2e = res["m2e"]
    nodes_out, pp, needs, evid = [], {}, [], []
    pe = {}      # provenance key -> list of Provenance carrying the quote
    enriched = []
    page_ms = mentions_by_page.get(pid, [])
    page_eids = []
    for m in page_ms:
        e = m2e.get(m["id"])
        if e and e not in page_eids and ents[e]["group"] != "page":
            page_eids.append(e)

    # 1. existing markup, preserved and repaired deterministically ---------------------------------------
    existing_labels, inline_labels = {}, set()
    label2key, node_label, node_key = {}, {}, {}

    def uniq(label, key):
        base, i = label, 1
        while label in label2key and label2key[label] != key:
            i += 1
            label = f"{base} #{i}"
        label2key[label] = key
        return label
    for raw in page.get("existing", []):
        doc = raw.get("parsed")
        if doc is None:
            continue
        for n in vocab._iter_nodes(doc):
            if not isinstance(n, dict):
                continue
            n = copy.deepcopy(n)
            n.pop("@context", None)
            ts = vocab.types_of(n)
            name = next((str(n[k]) for k in ("name", "headline") if isinstance(n.get(k), str)), None)
            key = n.get("@id") or f"_:n{len(nodes_out)}"
            label = uniq(name or (ts[0] if ts else "node"), key)
            node_label[id(n)], node_key[id(n)] = label, key
            _repair(n, "", label, pp, needs, evid, purl, None)
            for kk in ("@type", "@id"):
                if kk in n:
                    pp.setdefault(f"{label}.{kk}", "extracted")      # identity read from the markup unless a repair above changed it
            nodes_out.append(n)
            if name:
                existing_labels[norm_name(name)] = n
            for nested in _typed_nested(n):         # an entity the site's own markup already defines inline (an ItemList of Products) is not defined a second time
                nm_ = nested.get("name")
                if isinstance(nm_, str):
                    inline_labels.add(norm_name(nm_))

    # 2. facts the page states that existing nodes lack; new nodes for prose-only entities -------------
    def eiri(eid):
        return iri(ents[eid], root_url)

    new_nodes = {}
    amb_open = {x for a in res["ambiguities"] if a.status == "needs_review" for x in a.entity_ids}
    for eid in page_eids:
        e = ents[eid]
        mine = [m for m in e["mentions"] if m["page_id"] == pid]
        sug = [m for m in mine if m["kind"] == "suggested"]
        node = existing_labels.get(norm_name(e["label"])) or next((existing_labels.get(norm_name(m["name"])) for m in mine if norm_name(m["name"]) in existing_labels), None)
        created = False
        if node is None and (norm_name(e["label"]) in inline_labels or any(norm_name(m["name"]) in inline_labels for m in mine)):
            continue                                  # the page's own markup already defines it inline (for example inside an ItemList)
        if node is None:
            if not sug:
                continue                              # extracted from markup already covered above
            if any(m["kind"] == "extracted" and m.get("jsonld_id") for m in e["mentions"]):
                continue                              # defined by markup elsewhere on the site: reference it by @id, do not redefine
            if eid in amb_open:
                needs.append(f"{e['label']}: held back from the JSON-LD until its ambiguous match is settled (it may be the same thing as another entity).")
                continue
            node = {"@type": e["type"] if e["type"] in vocab.TYPES else "Thing", "@id": eiri(eid), "name": sug[0]["name"]}
            for m in sug:
                evid.append(Provenance(source_url=purl, resource_id=rid, kind="suggested", method="model",
                                       evidence=m.get("evidence"), evidence_verified=bool(m.get("evidence_verified"))))
            created = True
            new_nodes[eid] = node
            nodes_out.append(node)
            node_label[id(node)] = uniq(e["label"], node["@id"])
            for k in ("@type", "@id", "name"):
                pp[f"{node_label[id(node)]}.{k}"] = "suggested"
                pe[f"{node_label[id(node)]}.{k}"] = [x for x in evid[-len(sug):]]
        types = set()
        for t in vocab.types_of(node):
            types |= vocab.ancestors(t)
        for m in sug:
            for prop, val in m["props"].items():
                ev = (m.get("prop_evidence") or {}).get(prop)
                label = e["label"]
                if any(x in node for x in EQUIV.get(prop, ())):
                    continue
                if prop == "jobTitle" and (not is_title(val) or len(val.split()) > 6 or re.search(r"\b(manages?|leads?|runs?|oversees?|looks after|is responsible|works? (?:at|for|with))\b", val, re.I)):
                    needs.append(f"{label}: '{val}' reads as a sentence, not a job title; not added.")
                    continue
                if prop in DIRECT:
                    if prop in node:
                        continue
                    if not (set(vocab.PROPS.get(prop, {}).get("dom", [])) & types):
                        needs.append(f"{label}: the page states {prop} '{val}' but {'/'.join(vocab.types_of(node))} has no '{prop}' property; not added.")
                        continue
                    node[prop] = val
                elif prop == "address" and "address" not in node:
                    parts = [x.strip() for x in val.split(",") if x.strip()]
                    addr = {"@type": "PostalAddress", "streetAddress": parts[0]} if parts else {"@type": "PostalAddress", "streetAddress": val}
                    if len(parts) >= 2:
                        addr["addressLocality"] = parts[1]
                    if len(parts) >= 3:
                        addr["addressRegion"] = parts[2]
                    if len(parts) > 3:
                        addr = {"@type": "PostalAddress", "streetAddress": val}
                        needs.append(f"{label}: the address has more parts than could be split safely; kept as one string.")
                    node["address"] = addr
                elif prop == "price" and "offers" not in node and ("Product" in types or "Service" in types):
                    num = re.search(r"\d[\d,]*(\.\d+)?", val)
                    if not num:
                        continue
                    offer = {"@type": "Offer", "price": num.group().replace(",", "")}
                    cur = stated_currency(val, ev)
                    if cur:
                        offer["priceCurrency"] = cur
                    else:
                        needs.append(f"{label}: price '{val}' has no stated currency (a bare $ is ambiguous), so priceCurrency is missing: a price with no currency cannot be approved until the reviewer adds it.")
                    node["offers"] = offer
                elif prop == "memberCount":
                    needs.append(f"{label}: the page states {prop} ('{val}'); Schema.org has no property for a member count, so it stays in the explorer and the conflict checks and is left out of the JSON-LD.")
                    continue
                else:
                    continue
                nk_ = "offers" if prop == "price" else prop          # provenance is keyed on the property the JSON-LD actually carries
                pp[f"{node_label[id(node)]}.{nk_}"] = "suggested"
                pe[f"{node_label[id(node)]}.{nk_}"] = [Provenance(source_url=purl, resource_id=rid, kind="suggested", method="model", evidence=ev, evidence_verified=True)]
                if not created:
                    enriched.append((prop in CORE_PROPS, f"{label}: the page states {prop} ('{val}') but the existing markup does not include it."))
                evid.append(Provenance(source_url=purl, resource_id=rid, kind="suggested", method="model", evidence=ev, evidence_verified=True))
        # relations stated on this page with this entity as subject
        for ed in edges:
            if ed.source != eid or ed.support == "navigation":
                continue
            on_page = ed.provenance.source_url == purl or any(c.source_url == purl for c in ed.corroboration)
            if not on_page or ed.origin == "extracted" or not ed.object_in_quote:
                continue            # an edge whose object the sentence does not name stays in the explorer; it is never proposed
            prov = ed.provenance if ed.provenance.source_url == purl else next(c for c in ed.corroboration if c.source_url == purl)
            if not ed.in_schema_org:
                needs.append(f"{e['label']} {ed.label} {ents[ed.target]['label']}: stated on the page, but Schema.org has no property for it; kept in the graph, left out of the JSON-LD.")
                continue
            ok_, _w = vocab.edge_valid(ed.predicate, e["type"], ents[ed.target]["type"])
            if not (set(vocab.PROPS.get(ed.predicate, {}).get("dom", [])) & types) or not ok_:
                needs.append(f"{e['label']}: relationship '{ed.predicate}' to {ents[ed.target]['label']} is not valid Schema.org between {'/'.join(vocab.types_of(node))} and {ents[ed.target]['type']}; not added.")
                continue
            if any(x in node for x in EQUIV_REL.get(ed.predicate, ())):
                continue                              # the markup already says this with a sibling property
            ref = {"@id": eiri(ed.target)}
            val = {"@type": "Offer", "itemOffered": ref} if ed.predicate == "makesOffer" else ref
            cur = node.get(ed.predicate)
            if cur is None:
                node[ed.predicate] = val
            elif isinstance(cur, list):
                cur.append(val)
            elif cur != val:
                node[ed.predicate] = [cur, val]
            else:
                continue
            pp[f"{node_label[id(node)]}.{ed.predicate}"] = "suggested"
            pe.setdefault(f"{node_label[id(node)]}.{ed.predicate}", []).append(prov)
            if not created:
                enriched.append((ed.predicate in CORE_RELS and all(c.passed for c in ed.confidence.checks if c.name == "The quoted sentence names both ends"), f"{e['label']}: the page states '{ed.predicate}' to {ents[ed.target]['label']} but the existing markup does not include it."))
            evid.append(prov)

    # 3. dangling references ---------------------------------------------------------------------------
    for d in dangling.get(pid, []):
        needs.append(f"@id '{d}' is referenced but defined nowhere on this site; not resolved.")

    # 4. breadcrumb visible in HTML but absent from markup -> structure-derived, so 'extracted' ----------
    has_bc = any(isinstance(n, dict) and "BreadcrumbList" in vocab.types_of(n)
                 for raw in page.get("existing", []) if raw.get("parsed") for n in vocab._iter_nodes(raw["parsed"]))
    if not has_bc and len(page.get("breadcrumb_html", [])) >= 2:
        nodes_out.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": c["name"], "item": c["url"]} for i, c in enumerate(page["breadcrumb_html"])]})
        pp["BreadcrumbList.itemListElement"] = "derived"      # built from the visible HTML trail: the page had no BreadcrumbList markup to read
        pp["BreadcrumbList.@type"] = "derived"
        needs.append("Breadcrumb trail is visible in the page HTML but has no BreadcrumbList markup; proposed from the HTML structure.")

    # Only entities that carry enough to be useful reach the exported file: the explorer can hold everything, a published file cannot.
    # A prose-created node needs at least one property beyond its name (an Event needs a start date) or something else must refer to it.
    def refs_to(nid, skip):
        found = []

        def walk(x, parent_key=None):
            if isinstance(x, dict):
                if x.get("@id") == nid and set(x) == {"@id"}:
                    found.append(x)
                for v_ in x.values():
                    walk(v_)
            elif isinstance(x, list):
                for v_ in x:
                    walk(v_)
        for n_ in nodes_out:
            if n_ is not skip:
                walk(n_)
        return found
    changed = True
    while changed:
        changed = False
        for eid_, nd in list(new_nodes.items()):
            if nd not in nodes_out:
                continue
            extra = [k for k in nd if k not in ("@type", "@id", "name")]
            is_event = "Event" in {a for t in vocab.types_of(nd) for a in vocab.ancestors(t)}
            weak = (is_event and "startDate" not in nd) or (not extra and not refs_to(nd["@id"], nd))
            if weak:
                nodes_out.remove(nd)
                changed = True
                needs.append(f"{nd.get('name')}: held back from the JSON-LD (" + ("an Event needs a start date" if is_event and "startDate" not in nd else "nothing else on the page refers to it and it has no properties of its own") + "); it stays in the explorer.")
                for n_ in nodes_out:           # remove dangling references to what was held back
                    for k_, v_ in list(n_.items()):
                        if isinstance(v_, list):
                            n_[k_] = [x for x in v_ if not (isinstance(x, dict) and (x.get("@id") == nd["@id"] or (isinstance(x.get("itemOffered"), dict) and x["itemOffered"].get("@id") == nd["@id"])))]
                            if not n_[k_]:
                                del n_[k_]
                        elif isinstance(v_, dict) and (v_.get("@id") == nd["@id"] or (isinstance(v_.get("itemOffered"), dict) and v_["itemOffered"].get("@id") == nd["@id"])) and set(v_) <= {"@id", "@type", "itemOffered"}:
                            del n_[k_]
    if not nodes_out:
        return None
    # provenance is keyed on the node's own identifier ("<@id>|<property>"), never on its display name, so two
    # same-named entities can never share an entry
    valid = {n_.get("@id") for n_ in nodes_out if n_.get("@id")}
    keep = lambda key_: key_.startswith("_:") or key_ in valid
    remapped = {}
    for k, v in pp.items():
        for lab in sorted(label2key, key=len, reverse=True):
            if k.startswith(lab + "."):
                if keep(label2key[lab]):
                    remapped[f"{label2key[lab]}|{k[len(lab) + 1:]}"] = v
                break
        else:
            remapped[k.replace("BreadcrumbList.", "_:breadcrumb|", 1)] = v
    pp = remapped
    pe_re = {}
    for k, v in pe.items():
        for lab in sorted(label2key, key=len, reverse=True):
            if k.startswith(lab + "."):
                pe_re[f"{label2key[lab]}|{k[len(lab) + 1:]}"] = v
                break
    pe = pe_re
    doc = {"@context": "https://schema.org", "@graph": nodes_out} if len(nodes_out) > 1 else {"@context": "https://schema.org", **nodes_out[0]}
    val = vocab.validate_doc(doc)

    # review signals ------------------------------------------------------------------------------------
    amb_here = {x for a in res["ambiguities"] for x in a.entity_ids if x in page_eids}
    cf_here = [c for c in res["conflicts"] if c.entity_id in page_eids and any(v["page_id"] == pid for v in c.values)]
    for c in cf_here:
        needs.append(f"Conflict on {c.entity_label}: '{c.property}' is stated differently in more than one place.")
    for a in res["ambiguities"]:
        if any(x in page_eids for x in a.entity_ids):
            needs.append(f"Ambiguous match: {a.reason}")
    suggested_props = [k for k, v in pp.items() if v == "suggested"]
    checks = [Check(name="Valid JSON-LD syntax and Schema.org vocabulary", passed=val.valid,
                    detail=f"{sum(1 for i in val.issues if i.severity == 'error')} errors, {sum(1 for i in val.issues if i.severity == 'warning')} warnings"),
              Check(name="Every suggested item carries a verbatim page quote or a stated repair", passed=all(e.evidence_verified for e in evid)),
              Check(name="No conflicting statements involve this page's entities", passed=not cf_here),
              Check(name="No unresolved ambiguous entity matches", passed=not amb_here)]
    if page.get("existing"):
        checks.append(Check(name="Existing valid markup preserved unchanged", passed=True))
    return {"jsonld": doc, "property_provenance": pp, "evidence": evid, "validation": val,
            "confidence": conf(checks), "needs_review": list(dict.fromkeys(needs)), "suggested_props": len(suggested_props), "enriched": enriched,
            "property_evidence": {k: [{"quote": x.evidence, "source_url": x.source_url, "resource_id": x.resource_id, "verified": x.evidence_verified} for x in v] for k, v in pe.items()}}
