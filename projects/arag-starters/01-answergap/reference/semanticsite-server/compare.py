"""Compare two values of the same property and decide whether they genuinely disagree.

Different formatting is not a conflict ('Mo-Fr 07:00-15:00' and 'Monday to Friday 7:00am to 3:00pm' say
the same thing), and a value that cannot be parsed is not evidence of disagreement either (it is a markup
problem and is reported as one). Returns True only when two values parse and differ."""
import re

DAYS = ["mo", "tu", "we", "th", "fr", "sa", "su"]
DAY_WORD = r"(?:mon(?:day)?s?|tue(?:s(?:day)?)?s?|wed(?:nesday)?s?|thu(?:r(?:s(?:day)?)?)?s?|fri(?:day)?s?|sat(?:urday)?s?|sun(?:day)?s?|mo|tu|we|th|fr|sa|su|daily|every ?day|weekdays?|weekends?)"
MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _day_set(a, b=None):
    a = a.lower().replace(" ", "")
    if a in ("daily", "everyday"):
        return set(range(7))
    if a.startswith("weekday"):
        return set(range(5))
    if a.startswith("weekend"):
        return {5, 6}
    ia = DAYS.index(a[:2])
    if b is None:
        return {ia}
    ib = DAYS.index(b.lower()[:2])
    return set(range(ia, ib + 1)) if ib >= ia else set(range(ia, 7)) | set(range(0, ib + 1))


def _t(s):
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", s.strip().lower())
    if not m:
        return None
    h, mi, ap = int(m[1]), int(m[2] or 0), m[3]
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return h * 60 + mi


def parse_hours(text):
    """-> {day_index: (open, close) | 'closed'} for the days the text mentions, or None if nothing parsed."""
    s = text.lower().replace("–", "-").replace("—", "-").replace("/", " and ")
    out = {}
    pat = re.compile(rf"(?P<d1>{DAY_WORD})(?:\s*(?:-|to|until|through)\s*(?P<d2>{DAY_WORD}))?(?P<more>(?:\s*(?:,|and|&)\s*{DAY_WORD}(?:\s*(?:-|to)\s*{DAY_WORD})?)*)")
    time_re = re.compile(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:-|to|until)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)")
    pos = 0
    for m in pat.finditer(s):
        if m.start() < pos:
            continue
        days = _day_set(m["d1"], m["d2"])
        for extra in re.finditer(rf"({DAY_WORD})(?:\s*(?:-|to)\s*({DAY_WORD}))?", m["more"] or ""):
            days |= _day_set(extra[1], extra[2])
        rest = s[m.end():m.end() + 40]
        before = s[max(0, m.start() - 8):m.start()]
        tm = time_re.search(rest)
        if "closed" in before or re.match(r"\s*:?\s*closed", rest):
            for d in days:
                out[d] = "closed"
            pos = m.end()
        elif tm and tm.start() < 25:
            o, c = _t(tm[1]), _t(tm[2])
            if o is not None and c is not None:
                if c <= 12 * 60 and c < o and not re.search(r"am|pm", tm[2]):
                    c += 12 * 60
                for d in days:
                    out[d] = (o, c)
            pos = m.end() + tm.end()
    return out or None


QUAL = re.compile(r"\b(summer|winter|spring|autumn|fall|season\w*|holidays?|valid|until|from \d|from (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|between (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|"
                  r"(?:jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\w*\s+(?:to|-|until)\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|reopen\w*|temporar\w*|school terms?)\b", re.I)


def qualifier(text):
    return frozenset(m.group(0).lower() for m in QUAL.finditer(text or ""))


def hours_conflict(a, b):
    pa, pb = parse_hours(a), parse_hours(b)
    if not pa or not pb:
        return False
    return any(pa[d] != pb[d] for d in set(pa) & set(pb))


def parse_date(s):
    """-> ISO-like prefix 'YYYY[-MM[-DD]]' plus optional 'THH:MM', or None."""
    s = s.strip().lower()
    m = re.match(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?:[t ](\d{2}):(\d{2}))?", s)
    if m:
        d = m[1] + (f"-{m[2]}" if m[2] else "") + (f"-{m[3]}" if m[3] else "")
        return d, (f"{m[4]}:{m[5]}" if m[4] else None)
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]{3})[a-z]*\.?,?\s+(\d{4})", s)
    if m and m[2][:3] in MONTHS:
        d = f"{m[3]}-{MONTHS[m[2][:3]]:02d}-{int(m[1]):02d}"
    else:
        m = re.search(r"([a-z]{3})[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", s)
        if m and m[1][:3] in MONTHS:
            d = f"{m[3]}-{MONTHS[m[1][:3]]:02d}-{int(m[2]):02d}"
        else:
            m = re.search(r"\b(\d{4})\b", s)
            if not m:
                return None
            d = m[1]
    tm = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", s)
    t = None
    if tm:
        mins = _t(tm[0])
        t = f"{mins // 60:02d}:{mins % 60:02d}"
    return d, t


def date_conflict(a, b):
    pa, pb = parse_date(a), parse_date(b)
    if not pa or not pb:
        return False
    da, db = pa[0], pb[0]
    if not (da.startswith(db) or db.startswith(da)):
        return True
    return bool(pa[1] and pb[1] and pa[1] != pb[1])


def _tokens(s):
    return set(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def price_value(s):
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(s))
    return float(m.group().replace(",", "")) if m else None


NUMERIC_PROPS = {"maximumAttendeeCapacity", "memberCount", "numberOfEmployees"}


def number_value(s):
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(s))
    return float(m.group().replace(",", "")) if m else None


def conflicts(prop, a, b):
    """True when two values for the same property genuinely disagree."""
    a, b = str(a), str(b)
    if prop in NUMERIC_PROPS:
        na, nb = number_value(a), number_value(b)
        return na is not None and nb is not None and na != nb
    if prop == "openingHours":
        return hours_conflict(a, b)
    if prop in ("startDate", "endDate", "foundingDate"):
        return date_conflict(a, b)
    if prop == "price":
        pa, pb = price_value(a), price_value(b)
        return pa is not None and pb is not None and abs(pa - pb) > 1e-9
    if prop == "telephone":
        da, db = re.sub(r"\D", "", a), re.sub(r"\D", "", b)
        return bool(da and db) and not (da.endswith(db) or db.endswith(da))
    if prop == "email":
        return a.lower().replace("mailto:", "").strip() != b.lower().replace("mailto:", "").strip()
    ta, tb = _tokens(a), _tokens(b)           # jobTitle, address: compatible when one says no more than the other
    return bool(ta and tb) and not (ta <= tb or tb <= ta)


def conflict_set(prop, vals, ctxs=None):
    """Set-level decision. For free-text properties a short value covered by a longer one is not a disagreement
    ('founder' and 'managing director' are both parts of 'Founder and Managing Director'): only values that no
    other value covers can disagree."""
    vals = [str(v) for v in vals]
    if prop == "jobTitle":
        vals = [v for v in vals if is_title(v)]          # a sentence fragment is never one side of a conflict
    if prop == "openingHours":
        # hours bounded by a season, a date range or a temporary change are different facts for different periods, not a
        # contradiction; only compare hours that carry the same period (or none) - the qualifier may sit in the quote, not the value
        ctxs = [str(x) for x in (ctxs or vals)]
        quals = [qualifier(v + " " + x) for v, x in zip(vals, ctxs)]
        return any(quals[i] == quals[j] and conflicts(prop, vals[i], vals[j]) for i in range(len(vals)) for j in range(i + 1, len(vals)))
    if prop in ("jobTitle", "address"):
        toks = [_tokens(v) for v in vals]
        maximal = [t for i, t in enumerate(toks) if t and not any(i != j and t < u or (t == u and i > j) for j, u in enumerate(toks))]
        return any(not (a <= b or b <= a) for i, a in enumerate(maximal) for b in maximal[i + 1:])
    return any(conflicts(prop, x, y) for i, x in enumerate(vals) for y in vals[i + 1:])


VERB_START = {"led", "lead", "leads", "leading", "run", "runs", "running", "managed", "manages", "managing", "headed", "heads", "chaired", "chairs",
              "overseen", "oversees", "directed", "directs", "supervised", "supervises", "founded", "owned", "staffed", "taught", "teaches",
              "curated", "curates", "looked", "looks", "works", "worked", "joined", "hosted", "hosts", "coordinated", "coordinates", "guides", "guided"}


def is_title(v):
    """A job title names a role ('Senior Curator'). A verb, a participle, or a phrase such as 'led by Dr Rao' is a sentence fragment."""
    t = re.sub(r"\s+", " ", str(v)).strip().lower()
    if not t or len(t.split()) > 8:
        return False
    first = t.split()[0]
    return first not in VERB_START and not re.search(r"\bby\b", t) and not t.endswith((" by", " for", " at", " of"))
