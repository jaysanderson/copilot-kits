"""Polite crawler. Crawling is outbound behaviour, so politeness is a shipping gate:
- fetches only the host the user named (and its sitemaps), never other hosts
- obeys robots.txt (Disallow and Crawl-delay) for the SemanticSiteBot token and for *
- waits at least MIN_DELAY_S between requests to a host (more if robots asks)
- identifies itself honestly in the User-Agent, with a URL describing the bot
- honours noindex (meta robots and X-Robots-Tag): such pages are reported as gaps, not ingested
- no JavaScript execution, no authentication, size and time limits
"""
import fnmatch
import gzip
import ipaddress
import socket
import time
from .robots import Robots
from urllib.parse import urldefrag, urlparse, urlunparse

import httpx
from lxml import etree

from . import config


BLOCKED_SUFFIXES = (".internal", ".local", ".localhost", ".localdomain", ".lan", ".home.arpa")


def _is_public(ip):
    ip = ipaddress.ip_address(ip)
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
                or ip.is_unspecified or not ip.is_global)


def resolve_public(host):
    """Resolve once and return a PUBLIC address to connect to, or None when any answer is non-public (deny by default)."""
    h = host.strip("[]").lower().rstrip(".")
    if h == "localhost" or h.endswith(BLOCKED_SUFFIXES):
        return None
    try:
        infos = socket.getaddrinfo(h, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return "unresolvable"
    ips = [i[4][0] for i in infos]
    if not ips or not all(_is_public(i) for i in ips):
        return None
    return ips[0]


def private_address(host):
    """True when the host must not be fetched (non-public, or an internal-style name)."""
    return resolve_public(host) is None


def norm(url):
    u = urldefrag(url.strip())[0]
    p = urlparse(u)
    path = p.path or "/"
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", p.query, ""))


class Fetch:
    def __init__(self, url, status=None, body=None, ctype="", final=None, error=None, headers=None):
        self.url, self.status, self.body, self.ctype = url, status, body, ctype
        self.final, self.error, self.headers = final or url, error, headers or {}


class Crawler:
    def __init__(self, origin):
        p = urlparse(origin)
        self.scheme, self.host = p.scheme, p.netloc.lower()
        self.base = f"{self.scheme}://{self.host}"
        self.client = httpx.Client(headers={"User-Agent": config.USER_AGENT, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.1"},
                                   timeout=config.FETCH_TIMEOUT_S, follow_redirects=False)
        self.rp = Robots(allow_all=True)
        self.robots = {"found": False, "sitemaps": [], "crawl_delay": None, "disallow_rules": 0, "status": None}
        self._last = 0.0
        self.delay = config.MIN_DELAY_S
        self.requests = 0
        self.load_robots()

    def same_site(self, netloc):
        """example.com and www.example.com are one site: a user typing the bare name must not be refused at the redirect."""
        strip = lambda h: h.lower().removeprefix("www.")
        return strip(netloc) == strip(self.host)

    def close(self):
        self.client.close()

    # --- robots -------------------------------------------------------------------------------
    def load_robots(self):
        r = self._get(f"{self.base}/robots.txt", check_robots=False)
        self.robots["status"] = r.status
        if r.status == 200 and r.body is not None:
            text = r.body.decode("utf-8", "replace")
            self.rp = Robots(text, agent=config.BOT_TOKEN)
            self.robots["found"] = True
            self.robots["sitemaps"] = list(self.rp.sitemaps)
            self.robots["disallow_rules"] = self.rp.disallow_count
            if self.rp.delay:
                self.robots["crawl_delay"] = float(self.rp.delay)
                self.delay = max(self.delay, float(self.rp.delay))
        elif r.status in (401, 403):
            # access control on robots.txt itself: treat as disallow-all, the conservative reading
            self.rp = Robots(disallow_all=True)
            self.robots["found"] = True
            self.robots["note"] = "robots.txt returned an access error; treating the site as disallowed"
        else:
            self.rp = Robots(allow_all=True)

    def allowed(self, url):
        return self.rp.can_fetch(url)

    # --- fetch --------------------------------------------------------------------------------
    def _get(self, url, check_robots=True, hops=3):
        cur = url
        for _ in range(hops + 1):
            if check_robots and not self.allowed(cur):
                return Fetch(url, error="blocked_by_robots")
            if not self.same_site(urlparse(cur).netloc):
                return Fetch(url, error="off_host", final=cur)
            pu = urlparse(cur)
            if pu.scheme not in ("http", "https"):
                return Fetch(url, error="private_address", final=cur, headers={"_err": "scheme not allowed"})
            req_url, req_headers, ext = cur, {}, {}
            if not config.ALLOW_PRIVATE_HOSTS:
                ip = resolve_public(pu.hostname or "")
                if ip is None:
                    return Fetch(url, error="private_address", final=cur)
                if ip != "unresolvable":                  # connect to the address we validated, never re-resolve the name
                    host_ip = f"[{ip}]" if ":" in ip else ip
                    port = f":{pu.port}" if pu.port else ""
                    req_url = cur.replace(f"//{pu.netloc}", f"//{host_ip}{port}", 1)
                    req_headers = {"Host": pu.netloc}
                    if pu.scheme == "https":
                        ext = {"sni_hostname": pu.hostname}
            wait = self.delay - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            self.requests += 1
            try:
                with self.client.stream("GET", req_url, headers=req_headers, extensions=ext) as r:
                    if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                        nxt = httpx.URL(cur).join(r.headers["location"])
                        cur = str(nxt)
                        continue
                    chunks, size = [], 0
                    for c in r.iter_bytes():
                        size += len(c)
                        if size > config.MAX_BYTES:
                            return Fetch(url, status=r.status_code, error="too_large", final=cur)
                        chunks.append(c)
                    return Fetch(url, status=r.status_code, body=b"".join(chunks),
                                 ctype=r.headers.get("content-type", ""), final=cur, headers=dict(r.headers))
            except (httpx.TimeoutException, httpx.TransportError) as e:
                return Fetch(url, error="fetch_failed", final=cur, headers={"_err": e.__class__.__name__})
        return Fetch(url, error="fetch_failed", final=cur, headers={"_err": "too many redirects"})

    def fetch(self, url):
        return self._get(url)

    # --- sitemaps -----------------------------------------------------------------------------
    def sitemap_urls(self, sitemap_url, depth=0, seen=None):
        """Returns (urls, notes). Handles sitemap indexes (depth<=3), gzip, and sitemaps that 404."""
        seen = seen if seen is not None else set()
        notes, urls = [], []
        if sitemap_url in seen or depth > 3:
            return urls, notes
        seen.add(sitemap_url)
        r = self._get(sitemap_url)
        if r.error or r.status != 200 or not r.body:
            notes.append({"url": sitemap_url, "problem": r.error or f"HTTP {r.status}"})
            return urls, notes
        body = r.body
        if body[:2] == b"\x1f\x8b":
            try:
                body = gzip.decompress(body)
            except OSError:
                notes.append({"url": sitemap_url, "problem": "bad gzip"})
                return urls, notes
        try:
            root = etree.fromstring(body, etree.XMLParser(resolve_entities=False, no_network=True, recover=False))
        except etree.XMLSyntaxError as e:
            notes.append({"url": sitemap_url, "problem": f"invalid XML: {e}"})
            return urls, notes
        tag = etree.QName(root).localname
        locs = [(e.text or "").strip() for e in root.iter() if isinstance(e.tag, str) and etree.QName(e).localname == "loc"]
        if tag == "sitemapindex":
            for loc in locs:
                u, n = self.sitemap_urls(loc, depth + 1, seen)
                urls += u
                notes += n
        else:
            urls = [norm(l) for l in locs if l]
        return urls, notes


def matches(url, patterns):
    path = urlparse(url).path + (("?" + urlparse(url).query) if urlparse(url).query else "")
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(url, p) for p in patterns)
