"""Derive the University cross-site knowledge graph deterministically and write it to the KB.

No model call anywhere: every edge comes from a regex over text already stored in the KB, or from
the page's own URL path. Relations are written with PATCH usermetadata.relations (zero LLM cost).

  build_graph.py            derive from the KB, write graph/graph_edges.json, print counts (dry run)
  build_graph.py --apply    also PATCH the relations onto every resource
  build_graph.py --purge    clear this script's relations from every resource
"""
import collections, json, re, sys
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0, str(Path(__file__).parent))
from gk import KB_URL, c

OUT = Path(__file__).parent.parent / "graph" / "graph_edges.json"

# ---- the schema: the only relation labels and node groups this graph may contain ----
LABELS = {
    "parent-of":       ("CHILD", "page", "page"),      # structural: URL path parent to child
    "covers-topic":    ("ABOUT", "page", "TOPIC"),     # cross-cutting: page to topic concept
    "addresses":       ("ABOUT", "page", "AUDIENCE"),  # cross-cutting: page to audience
    "located-at":      ("ABOUT", "page", "CAMPUS"),    # cross-cutting: page to campus / mode
    "names":           ("ENTITY", "page", "NAMED"),    # cross-cutting: page to rare proper name
}

# facet -> label; (id, display name, regex)
VOCAB = {
 "TOPIC": ("covers-topic", [
  ("english-language-requirement", "English language requirement", r"\bIELTS\b|\bTOEFL\b|\bPTE Academic\b|English language (?:requirement|proficiency|competency|test)s?|English proficiency|English (?:and|or) academic requirements"),
  ("student-visa", "Student visa and OSHC", r"student visa|\bOSHC\b|overseas student health cover|confirmation of enrolment|\bCoE\b|\bvisa\b"),
  ("scholarships", "Scholarships", r"scholarship|bursar"),
  ("fees-and-loans", "Fees and student loans", r"tuition fee|\bFEE-HELP\b|\bHECS\b|Commonwealth supported|student contribution|\bCSP\b|\bHELP loan"),
  ("how-to-apply", "How to apply", r"how to apply|\bapplication (?:form|process|deadline|fee)s?|\bTISC\b|\bapply (?:now|online|directly|through|via)|closing date"),
  ("credit-for-prior-learning", "Credit for prior learning", r"credit for prior|recognition of prior|advanced standing|\bRPL\b|credit transfer"),
  ("pathways-and-enabling", "Pathways and enabling programs", r"enabling (?:program|course|pathway)|pathway (?:program|course)s?|foundation studies|University College|preparation course|\bOpen Universities\b|diploma pathway"),
  ("accommodation", "Accommodation", r"accommodation|student village|on-campus living|residential college|housing"),
  ("student-support", "Student support and wellbeing", r"counselling|wellbeing|AccessAbility|disability (?:support|service)|academic skills|student support|support services|student care"),
  ("work-integrated-learning", "Placements and work-integrated learning", r"work[- ]integrated|placement|internship|industry experience|clinical rotation|work experience"),
  ("careers-employability", "Careers and employability", r"employability|career(?:s)? (?:service|development|advice|centre)|graduate outcomes|job[- ]ready|career ready"),
  ("veterinary-and-animal-health", "Veterinary and animal health", r"veterinar|animal health|animal welfare|wildlife|small animal|equine"),
  ("environment-and-sustainability", "Environment and sustainability", r"sustainab|conservation|climate|biodiversity|environmental (?:science|management|research)"),
  ("agriculture-and-food", "Agriculture and food", r"agricultur|food security|farming|livestock|\bfood science|aquaculture"),
  ("health-and-medicine", "Health and medicine", r"nursing|health science|medical science|public health|paramedic|physiotherap|clinical (?:skills|training)"),
  ("engineering-and-it", "Engineering and technology", r"engineering|information technology|cyber ?security|data science|computer science|artificial intelligence"),
  ("research-ethics-and-integrity", "Research ethics and integrity", r"research ethics|research integrity|ethics committee|animal ethics|human research ethics|research misconduct|responsible conduct"),
  ("indigenous-engagement", "Aboriginal and Torres Strait Islander engagement", r"Aboriginal|Torres Strait|Indigenous|Kulbardi|First Nations|Noongar"),
  ("industry-partnership", "Industry partnerships", r"industry partner|industry engagement|industry collaboration|work with (?:industry|us)|business partner"),
  ("study-online", "Study online and flexible attendance", r"study online|online (?:study|learning|course|unit)|flexible study|attendance mode|external mode"),
 ]),
 "AUDIENCE": ("addresses", [
  ("international-students", "International students", r"international students?|overseas students?|students? from overseas|study abroad"),
  ("school-leavers", "School leavers", r"school leavers?|Year 12|\bATAR\b|\bTEE\b|secondary school"),
  ("postgraduate-coursework", "Postgraduate coursework students", r"postgraduate coursework|master(?:'s| of)|graduate certificate|graduate diploma|coursework master"),
  ("research-candidates", "Research degree candidates", r"higher degree by research|\bHDR\b|\bPhD\b|doctoral|research candidate|research training program"),
  ("regional-and-remote", "Regional and remote students", r"regional (?:and|or) remote|regional student|rural and remote|remote student"),
  ("mature-age", "Mature age and returning students", r"mature[- ]age|returning to study|non-school leaver|adult learner"),
  ("employers-and-industry", "Employers and industry", r"employers?\b|industry partners?|business owners?|organisations? looking"),
  ("staff-and-prospective-staff", "Staff and prospective staff", r"work at University|join our team|academic staff|prospective staff|career opportunities at University"),
  ("alumni", "Alumni", r"\balumni\b|\bgraduates? of University"),
 ]),
 "CAMPUS": ("located-at", [
  ("perth-campus", "Perth campus", r"Perth campus|South Street|University campus|Boola Katitjin"),
  ("rockingham-campus", "Rockingham campus", r"Rockingham"),
  ("peel-campus", "Peel and Mandurah campus", r"Mandurah|Peel (?:campus|region)"),
 ]),
}
COMPILED = {g: (lab, [(i, n, re.compile(rx, re.I if g != "CAMPUS" else 0)) for i, n, rx in items]) for g, (lab, items) in VOCAB.items()}

def fetch_corpus():
    out, ids, p = [], [], 0
    with c() as s:
        while True:
            j = s.get(f"{KB_URL}/resources", params={"page": p, "size": 100}).json()
            ids += [x["id"] for x in j["resources"]]
            if j["pagination"]["last"]: break
            p += 1
        for i in ids:
            r = s.get(f"{KB_URL}/resource/{i}", params=[("show", "basic"), ("show", "origin"), ("show", "extracted"), ("extracted", "text")]).json()
            txt = ""
            for kind in ("links", "texts"):
                for f in (r.get("data", {}).get(kind) or {}).values():
                    txt += (((f.get("extracted") or {}).get("text") or {}).get("text") or "")
            out.append({"id": i, "title": r.get("title") or "", "url": (r.get("origin") or {}).get("url") or "", "text": txt})
    return out

def strip_boilerplate(docs):
    """Drop navigation: link-list lines, and any line repeated on 15+ pages."""
    lc = collections.Counter()
    for d in docs:
        d["lines"] = [l.strip() for l in d["text"].split("\n") if l.strip()]
        lc.update(set(d["lines"]))
    for d in docs:
        keep = [l for l in d["lines"] if lc[l] < 15 and not re.match(r"^[\*\-\+]\s*\[", l) and not re.match(r"^\[.*\]\(.*\)$", l)]
        d["body"] = "\n".join(keep)
        d["title_short"] = re.sub(r"\s*\|\s*The university\s*\.?$", "", d["title"]).strip()

def path_of(url):
    u = urlparse(url)
    return u.netloc, [s for s in u.path.split("/") if s]

def sentence_around(body, m):
    a = max(body.rfind(".", 0, m.start()), body.rfind("\n", 0, m.start())) + 1
    e = [x for x in (body.find(".", m.end()), body.find("\n", m.end())) if x != -1]
    b = (min(e) + 1) if e else len(body)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body[a:b])
    s = re.sub(r"^[#>\*\-\|\s]+", "", s.strip())          # heading / list markers
    s = re.sub(r"\*\*|__", "", s)                          # emphasis
    s = re.sub(r"\s+", " ", s).strip()
    return s[:280]

def good_snippet(t):
    """A sentence a reader can take as evidence: prose, not a title echo, a link stub or a heading."""
    return len(t) > 45 and not re.search(r"\|\s*The university|https?:|\]\(|\bImage\b|^\W*pdf", t) and t.count(" ") > 6

def is_graphed(url):
    """Aliases: short links on other hosts, and fragment/query variants of a page (the home page appears as /#mainContent)."""
    return path_of(url)[0] == "www.university.edu.au" and "#" not in url and "?" not in url

def derive(docs):
    # goto.university.edu.au pages are short-link aliases of pages already in the corpus: graphing them
    # would only duplicate nodes, so the graph covers the www.university.edu.au pages.
    docs = [d for d in docs if is_graphed(d["url"])]
    edges = []
    # structural: nearest ancestor path that is itself a page in the corpus
    by_path = {}
    for d in docs:
        net, segs = path_of(d["url"])
        if net == "www.university.edu.au" and segs: by_path["/".join(segs)] = d
    for key, d in by_path.items():
        segs = key.split("/")
        for k in range(len(segs) - 1, 0, -1):
            par = by_path.get("/".join(segs[:k]))
            if par and par["id"] != d["id"]:
                edges.append({"label": "parent-of", "from": par["id"], "to": d["id"], "node": None, "why": "URL path: " + "/" + "/".join(segs[:k]) + " contains /" + key})
                break
    # cross-cutting: vocabulary concepts
    for d in docs:
        if len(d["body"]) < 300: continue
        # a page is "about" a concept when it is in the title/URL, or the body says it at least 3 times
        head = d["title_short"] + " " + d["url"]
        for g, (lab, items) in COMPILED.items():
            for cid, name, rx in items:
                ms = list(rx.finditer(d["body"]))
                in_head = bool(rx.search(head.replace("-", " ")))
                if len(ms) >= 3 or in_head:
                    hdr = d["body"].find("\n", d["body"].find("\n") + 1)  # skip the repeated title lines
                    first = next((m for m in ms if m.start() > hdr and good_snippet(sentence_around(d["body"], m))), None)
                    snippet = sentence_around(d["body"], first) if first else "In the page title: " + d["title_short"]
                    edges.append({"label": lab, "from": d["id"], "to": None, "node": {"value": name, "group": g, "id": cid}, "why": snippet, "count": len(ms)})
    # cross-cutting: rare proper names (2-4 capitalised words) that are on 2..8 pages
    NAMEPAT = re.compile(r"\b(?:Dr|Professor|Prof) [A-Z][a-z]+(?: [A-Z][a-z]+){1,2}\b|\b[A-Z][a-z]{2,}(?: [A-Z][a-z]{2,}){1,3}\b")
    STOP = re.compile(r"^(?:Image|Higher|Deputy|Chief|Vice|Our|Get|See|Spaces|Hire|High|Learn|Studying|Welcome|Connect|General|Business|Education|Law|Office|The|This|That|These|Our|Your|You|We|For|With|From|Find|Learn|Read|See|View|Apply|Contact|Study|The university|Western Australia|Perth Western|Skip|Image|Meet|Why|How|What|Who|Visit|Explore|Join|Get|Search|More|About|Home|All|Our)\b")
    GENERIC = {"Higher Education", "Vice Chancellor", "Clinical Psychology", "Forensic Science", "Cultural Studies", "Clinical Immunology", "Brighter Future", "University Alumni", "Clinical Exercise Physiology", "First Nations", "Veterinary Anatomy", "Western Australia", "The university", "University Uni", "Perth Western Australia", "South Street", "Student Services", "University Drive", "Frequently Asked"}
    pages_for = collections.defaultdict(set); sample = {}
    for d in docs:
        if len(d["body"]) < 300: continue
        seen = set()
        for m in NAMEPAT.finditer(d["body"]):
            nm = m.group(0)
            if STOP.match(nm) or nm in GENERIC or nm in seen: continue
            seen.add(nm); pages_for[nm].add(d["id"]); sn = sentence_around(d["body"], m)
            if good_snippet(sn) or (nm, d["id"]) not in sample: sample[(nm, d["id"])] = sn
    section = {d["id"]: (path_of(d["url"])[1][:1] or [""])[0] for d in docs}
    for nm, pids in pages_for.items():
        # cross-cutting only: the name must turn up in at least two different top-level sections
        if 2 <= len(pids) <= 8 and len({section[p] for p in pids}) >= 2:
            for pid in pids:
                edges.append({"label": "names", "from": pid, "to": None, "node": {"value": nm, "group": "NAMED", "id": "n:" + nm.lower().replace(" ", "-")}, "why": sample[(nm, pid)] if good_snippet(sample[(nm, pid)]) else "Named on this page.", "count": 1})
    return edges

def to_relation(e):
    rel, _, _ = LABELS[e["label"]]
    if e["label"] not in LABELS: raise ValueError(e["label"])
    frm = {"type": "resource", "value": e["from"]}
    to = {"type": "resource", "value": e["to"]} if e["to"] else {"type": "entity", "value": e["node"]["value"], "group": e["node"]["group"]}
    return {"relation": rel, "label": e["label"], "from": frm, "to": to}

def main():
    docs = fetch_corpus(); strip_boilerplate(docs)
    edges = derive(docs)
    for e in edges: assert e["label"] in LABELS, e
    ids = {d["id"] for d in docs}
    pages = {d["id"]: {"title": d["title_short"], "url": d["url"], "chars": len(d["body"]), "alias": not is_graphed(d["url"])} for d in docs}
    OUT.write_text(json.dumps({"pages": pages, "edges": edges}, indent=0))
    cnt = collections.Counter(e["label"] for e in edges)
    print("pages", len(docs), "edges", len(edges)); print(dict(cnt))
    nodes = collections.Counter((e["node"]["group"], e["node"]["value"]) for e in edges if e["node"])
    print("concept nodes", len(nodes), "; pages per node, top:", nodes.most_common(12))
    if "--apply" in sys.argv or "--purge" in sys.argv:
        per = collections.defaultdict(list)
        if "--apply" in sys.argv:
            for e in edges: per[e["from"]].append(to_relation(e))
        with c() as s:
            for i in ids:
                r = s.patch(f"{KB_URL}/resource/{i}", json={"usermetadata": {"relations": per.get(i, [])}})
                if r.status_code != 200: print("FAIL", i, r.status_code, r.text[:120]); sys.exit(1)
        print("patched", len(ids))

if __name__ == "__main__":
    main()
