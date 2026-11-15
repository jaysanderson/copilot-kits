"""robots.txt per RFC 9309: user-agent groups, Allow/Disallow with `*` wildcards and `$` end anchors, longest-match
precedence (Allow wins a tie), Crawl-delay and Sitemap lines. Python's stdlib parser is first-match and has no wildcards,
so a disallowed URL could be fetched; this replaces it."""
import re
from urllib.parse import unquote, urlparse


class Robots:
    def __init__(self, text="", agent="semanticsitebot", allow_all=False, disallow_all=False):
        self.agent = agent.lower()
        self.allow_all, self.disallow_all = allow_all, disallow_all
        self.rules, self.delay, self.sitemaps, self.disallow_count = [], None, [], 0
        if text:
            self._parse(text)

    def _parse(self, text):
        groups, cur, last_was_ua = [], None, False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            k, v = (x.strip() for x in line.split(":", 1))
            k = k.lower()
            if k == "sitemap":
                self.sitemaps.append(v)
                continue
            if k == "user-agent":
                if not last_was_ua or cur is None:
                    cur = {"agents": [], "rules": [], "delay": None}
                    groups.append(cur)
                cur["agents"].append(v.lower())
                last_was_ua = True
                continue
            last_was_ua = False
            if cur is None:
                continue
            if k in ("allow", "disallow"):
                cur["rules"].append((k == "allow", v))
            elif k == "crawl-delay":
                try:
                    cur["delay"] = float(v)
                except ValueError:
                    pass
        # the most specific agent token that matches us wins; "*" is the fallback; matching groups with the same token merge
        best, best_len = [], -1
        for g in groups:
            for a in g["agents"]:
                if a != "*" and a in self.agent and len(a) > best_len:
                    best_len = len(a)
        chosen = [g for g in groups if any(a != "*" and a in self.agent and len(a) == best_len for a in g["agents"])] if best_len >= 0 \
            else [g for g in groups if "*" in g["agents"]]
        for g in chosen:
            self.rules += g["rules"]
            if g["delay"] is not None:
                self.delay = g["delay"]
        self.disallow_count = sum(1 for allow, p in self.rules if not allow and p)
        self._compiled = [(allow, unquote(p), self._rx(unquote(p))) for allow, p in self.rules if p]   # empty Disallow = allow everything

    @staticmethod
    def _rx(pattern):
        anchored = pattern.endswith("$")
        body = pattern[:-1] if anchored else pattern
        rx = "".join(".*" if ch == "*" else re.escape(ch) for ch in body)
        return re.compile("^" + rx + ("$" if anchored else ""))

    def can_fetch(self, url):
        if self.allow_all:
            return True
        if self.disallow_all:
            return False
        u = urlparse(url)
        path = unquote(u.path or "/") + (("?" + u.query) if u.query else "")
        if path == "/robots.txt":
            return True
        best_len, verdict = -1, True
        for allow, pat, rx in getattr(self, "_compiled", []):
            if rx.match(path):
                n = len(pat)
                if n > best_len or (n == best_len and allow):
                    best_len, verdict = n, allow
        return verdict
