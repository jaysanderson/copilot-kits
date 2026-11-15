"""Cyrillic -> Hebrew phonetic transliteration and fuzzy name matching.

This is a thin, deterministic server-side utility (not an ARAG call) - the
brief calls for "name transliteration" as part of the app's own orchestration
layer, alongside PDF splitting and stamp detection. The mapping is a practical
phonetic approximation (the kind an admissions clerk would eyeball), not a
formally standardised transliteration scheme - good enough to catch an
honest name mismatch in a demo, not a linguistic authority.
"""
import re

# Ordered longest-match-first so multi-letter Cyrillic sequences (e.g. "shch")
# are handled before their single-letter components.
_MULTI = [
    ("щ", "שץ'"), ("Щ", "שץ'"),
    ("ш", "ש"), ("Ш", "ש"),
    ("ч", "צ'"), ("Ч", "צ'"),
    ("ж", "ז'"), ("Ж", "ז'"),
    ("ц", "צ"), ("Ц", "צ"),
    ("х", "ח"), ("Х", "ח"),
    ("ё", "יו"), ("Ё", "יו"),
    ("ю", "יו"), ("Ю", "יו"),
    ("я", "יה"), ("Я", "יה"),
    ("й", "י"), ("Й", "י"),
    ("ь", ""), ("Ь", ""),
    ("ъ", ""), ("Ъ", ""),
]

_SINGLE = {
    "а": "א", "б": "ב", "в": "ו", "г": "ג", "д": "ד", "е": "ה",
    "з": "ז", "и": "י", "і": "י", "к": "ק", "л": "ל", "м": "מ",
    "н": "נ", "о": "ו", "п": "פ", "р": "ר", "с": "ס", "т": "ט",
    "у": "ו", "ф": "פ", "ы": "י", "э": "ה", "є": "ה", "ї": "י", "ґ": "ג",
}
for _k, _v in list(_SINGLE.items()):
    _SINGLE[_k.upper()] = _v


def detect_script(text: str) -> str:
    if not text:
        return "unknown"
    counts = {"cyrillic": 0, "hebrew": 0, "latin": 0}
    for ch in text:
        code = ord(ch)
        if 0x0400 <= code <= 0x04FF:
            counts["cyrillic"] += 1
        elif 0x0590 <= code <= 0x05FF:
            counts["hebrew"] += 1
        elif ch.isalpha():
            counts["latin"] += 1
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else "unknown"


def transliterate_cyrillic_to_hebrew(text: str) -> str:
    """Best-effort phonetic transliteration of a Cyrillic name into Hebrew script."""
    if not text:
        return ""
    out = text
    for src, dst in _MULTI:
        out = out.replace(src, dst)
    out = "".join(_SINGLE.get(ch, ch) for ch in out)
    return out


def _normalise(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s)
    return s


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def similarity(a: str, b: str) -> float:
    """0..1 similarity score, 1.0 = identical after normalisation."""
    na, nb = _normalise(a), _normalise(b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    dist = _levenshtein(na, nb)
    return max(0.0, 1.0 - dist / max(len(na), len(nb)))


def _part_match(declared_token: str, extracted_token: str) -> dict:
    score = similarity(declared_token, extracted_token)
    return {"status": "MATCH" if score >= 0.72 else "MISMATCH", "score": round(score, 2)}


def match_name(declared_name: str, declared_script: str, extracted_name: str, extracted_script: str) -> dict:
    """Compare a declared applicant name against a name extracted from a document.

    Transliterates Cyrillic -> Hebrew when the scripts differ so the comparison
    is apples-to-apples in the target script (Hebrew, per the Israel use case).

    Also returns first_name_match / last_name_match: a POSITIONAL token
    comparison (first whitespace-separated token vs first token, last vs
    last) - not a linguistically-aware first/last-name detector. This is a
    deliberate, disclosed simplification: Slavic names are conventionally
    written surname-first while Hebrew/English names are typically
    given-name-first, and reliably detecting which convention a given name
    string uses (without an explicit field for it) is not something this
    build attempts. Both sides come from the SAME declared/extracted pair a
    real admissions clerk would look at, so a positional mismatch is still a
    genuine, actionable signal even without solving name-order detection -
    see README "Known gaps". Returns None for a side when there aren't at
    least two tokens to compare (never fabricates a part-match on a
    single-word name).
    """
    if not extracted_name:
        return {
            "status": "NOT_FOUND", "score": 0.0, "compared_as": None, "transliterated": None,
            "first_name_match": None, "last_name_match": None,
        }

    compare_declared = declared_name
    compare_extracted = extracted_name
    transliterated = None

    if extracted_script == "cyrillic" and declared_script == "hebrew":
        transliterated = transliterate_cyrillic_to_hebrew(extracted_name)
        compare_extracted = transliterated
    elif extracted_script == declared_script:
        pass

    score = similarity(compare_declared, compare_extracted)
    status = "MATCH" if score >= 0.72 else "MISMATCH"

    declared_tokens = compare_declared.split()
    extracted_tokens = compare_extracted.split()
    first_name_match = None
    last_name_match = None
    if len(declared_tokens) >= 2 and len(extracted_tokens) >= 2:
        first_name_match = _part_match(declared_tokens[0], extracted_tokens[0])
        last_name_match = _part_match(declared_tokens[-1], extracted_tokens[-1])

    return {
        "status": status,
        "score": round(score, 2),
        "compared_as": {"declared": compare_declared, "extracted": compare_extracted},
        "transliterated": transliterated,
        "first_name_match": first_name_match,
        "last_name_match": last_name_match,
    }
