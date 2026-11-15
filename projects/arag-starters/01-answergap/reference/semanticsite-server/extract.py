"""Deterministic, zero-model extraction from one HTML page: readable text, existing JSON-LD,
breadcrumbs and navigation hierarchy, links. Anything derived here is 'extracted', never 'suggested'."""
import re
from urllib.parse import urldefrag, urljoin

from bs4 import BeautifulSoup

BLOCK = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "dt", "dd", "blockquote", "address", "figcaption",
         "tr", "summary", "pre"]
BLOCKS_ALL = {"p", "li", "dt", "dd", "blockquote", "address", "figcaption", "summary", "pre", "h1", "h2", "h3", "h4", "h5", "h6",
              "div", "section", "article", "main", "td", "th", "tr", "body", "caption", "label"}
STRIP = ["script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg", "template", "iframe"]


def _ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def parse_page(html, url):
    soup = BeautifulSoup(html, "lxml")
    out = {"url": url, "title": None, "description": None, "canonical": None, "robots": "", "lang": None}
    out["title"] = _ws(soup.title.string) if soup.title and soup.title.string else None
    for m in soup.find_all("meta"):
        n = (m.get("name") or m.get("property") or "").lower()
        if n == "description":
            out["description"] = _ws(m.get("content"))
        elif n == "robots":
            out["robots"] = (m.get("content") or "").lower()
    c = soup.find("link", rel="canonical")
    out["canonical"] = c.get("href") if c else None
    out["lang"] = soup.html.get("lang") if soup.html else None

    # existing structured data (raw blocks, parsed later by vocab.parse)
    out["jsonld_raw"] = [s.string or s.get_text() for s in soup.find_all("script", type=lambda t: t and "ld+json" in t.lower())]
    out["microdata_present"] = bool(soup.find(attrs={"itemscope": True}))

    # links and navigation, taken before boilerplate is stripped
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        links.append((urldefrag(urljoin(url, href))[0], _ws(a.get_text(" "))))
    out["links"] = links
    out["breadcrumb_html"] = _breadcrumb_html(soup, url)
    out["nav_tree"] = _nav_tree(soup, url)

    # main readable text with boilerplate stripped
    for t in soup.find_all(STRIP):
        t.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    # Text is grouped by its nearest block-level ancestor, so content held in plain <div>/<span> markup (very common)
    # is read as well as content in <p>/<li>/<h*>. A table row is one line.
    from bs4 import Comment, NavigableString
    groups, order = {}, []
    for t in root.find_all(string=True):
        if isinstance(t, Comment) or not t.strip():
            continue
        el = t.parent
        while el is not None and el is not root and el.name not in BLOCKS_ALL:
            el = el.parent
        if el is None:
            el = root
        if el.name in ("td", "th"):
            up = el.find_parent("tr")
            el = up or el
        k = id(el)
        if k not in groups:
            groups[k] = (el, [])
            order.append(k)
        groups[k][1].append(t.strip())
    lines, seen = [], set()
    h1 = root.find("h1")
    for k in order:
        el, parts = groups[k]
        txt = _ws(" | ".join(parts) if el.name == "tr" else " ".join(parts))
        if not txt or txt in seen:
            continue
        seen.add(txt)
        if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            txt = "#" * min(int(el.name[1]), 3) + " " + txt
        lines.append(txt)
    if not out["title"] and h1:
        out["title"] = _ws(h1.get_text())
    out["text"] = "\n\n".join(lines)
    return out


def _breadcrumb_html(soup, base):
    el = soup.find(attrs={"aria-label": re.compile("breadcrumb", re.I)}) or \
        soup.find(class_=re.compile("breadcrumb", re.I))
    if not el:
        return []
    crumbs = []
    for a in el.find_all(["a", "li", "span"]):
        if a.name == "a" and a.get("href"):
            crumbs.append({"name": _ws(a.get_text(" ")), "url": urldefrag(urljoin(base, a["href"]))[0]})
        elif a.name == "li" and not a.find("a"):
            crumbs.append({"name": _ws(a.get_text(" ")), "url": base})
    out = []
    for c in crumbs:
        if c["name"] and not (out and out[-1]["name"].lower() == c["name"].lower()):     # the current page is often listed twice (a link and a plain item)
            out.append(c)
    return out


def _nav_tree(soup, base):
    """Parent->child link pairs from nested lists inside <nav> (a menu hierarchy is a structural fact)."""
    pairs = []
    for nav in soup.find_all("nav"):
        if nav.get("aria-label") and re.search("breadcrumb", nav["aria-label"], re.I):
            continue
        for li in nav.find_all("li"):
            a = li.find("a", href=True, recursive=False) or (li.find("a", href=True) if not li.find("ul") else None)
            sub = li.find(["ul", "ol"], recursive=False)
            if not a or not sub:
                continue
            for child in sub.find_all("li", recursive=False):
                ca = child.find("a", href=True)
                if ca:
                    pairs.append({"parent": {"name": _ws(a.get_text(" ")), "url": urldefrag(urljoin(base, a["href"]))[0]},
                                  "child": {"name": _ws(ca.get_text(" ")), "url": urldefrag(urljoin(base, ca["href"]))[0]}})
    return pairs
