"""Shared answer shaping for every surface that calls the knowledge base's ask endpoint.

One module, imported by chat.py, app.py, pagemode.py and wander.py, so a fix to the voice of an answer
(no "based on the provided context" preamble, Australian English, one spelling of the university's name,
proper names left alone) cannot be applied to one surface and missed on three.

Usage:
  prompt  - append STYLE to the surface's own system prompt:  {"system": own_prompt + " " + STYLE}
  prose   - text = clean_prose(text, lang) on the FINAL answer text, after any citation markers are inserted
            (stripping a preamble shifts character offsets, so never run it before offset maths).
"""
import re

STYLE = ("Never refer to 'the context', 'the provided context', 'the sources' or 'the text provided'. "
          "Use Australian English spelling and vocabulary (specialised, organised, enquiries, centre, enrol). "
          "Copy phone numbers exactly as they appear in the sources, Latin digits in the same left-to-right order (for example +61 8 9360 6063), even when answering in Arabic. "
          "Always write the university's name in the form given for the answer language: English 'The university', "
          "Arabic 'جامعة مردوخ', Simplified Chinese '大学', Indonesian 'Universitas University'.")
# Belt and braces: prompts do not hold every time. A leading "Based on the provided context," style preamble is removed.
PREAMBLE = re.compile(
    r"^\s*(?:based on|according to|from|using)\s+(?:the\s+)?(?:provided|given|available|supplied)?\s*(?:context|information|sources?|text|documents?)[^.:\n]{0,80}?[:,.]\s*"
    r"|^\s*(?:بناءً|بناء)\s+على\s+(?:المعلومات|السياق|النص)[^.:\n،]{0,80}[:،.]\s*"
    r"|^\s*根据[^，。：:\n]{0,20}(?:上下文|信息|资料|来源)[^，。：:\n]{0,20}[，。：:]\s*"
    r"|^\s*Berdasarkan\s+(?:konteks|informasi|sumber)[^.:,\n]{0,80}[.:,]\s*", re.I)
# Australian spellings for the American forms models drift to. Whole words only, case kept.
AUS = [("specialized", "specialised"), ("specialize", "specialise"), ("organized", "organised"), ("organize", "organise"),
       ("organization", "organisation"), ("inquiries", "enquiries"), ("inquiry", "enquiry"), ("recognized", "recognised"),
       ("prioritize", "prioritise"), ("center", "centre"), ("enrollment", "enrolment"), ("behavior", "behaviour")]


def _aus(m, b):
    """Respell a word unless it sits inside a proper name ("World Health Organization", "Center for Disease
    Control", "Organization of American States"). A capitalised word that follows another capitalised word
    mid-run, or leads an "of/for <Capital>" name, is left alone; a title-case HEADING that merely starts with
    the word ("Specialized Support Teams") is still corrected."""
    t, w = m.string, m.group(0)
    if w[0].isupper():
        before = re.search(r"(\w+)[ \t]+$", t[:m.start()])
        if before and before.group(1)[0].isupper() and not re.search(r"(?:^|[.:!?\n⟧*#-])\s*\**\w+[ \t]+$", t[:m.start()]):
            return w
        if re.match(r"\s+(?:of|for)\s+[A-Z]", t[m.end():m.end() + 12]):
            return w
    return b.capitalize() if w[0].isupper() else b


def clean_prose(text: str, lang: str) -> str:
    text = text.replace("ميردوك", "مردوخ")  # one Arabic spelling of the name (the form Arabic Wikipedia uses)
    text = PREAMBLE.sub("", text, count=1)
    text = text[:1].upper() + text[1:] if text[:1].islower() else text
    if lang == "en":
        for a, b in AUS:
            if a != b:
                text = re.sub(r"\b" + a + r"\b", lambda m, b=b: _aus(m, b), text, flags=re.I)
    return text

# The conversational assistants (chat.py) use the style rules plus the role line.
SYSTEM = "You are the The university assistant, answering a prospective student. Open with the answer itself. " + STYLE


# ---- phone numbers: a wrong number is a wrong fact -------------------------------------------------------
# The model sometimes emits a phone number's digits in the wrong order in Arabic answers ("6063 9360 8 61+"). That is a
# generation fault, not a rendering one, so nothing downstream can fix it and nothing here may "repair" it: an answer whose
# numbers are not found in its sources is retried once by the caller, then withheld.
import unicodedata

PHONE_RUN = re.compile(r"\+?[\d٠-٩۰-۹][\d٠-٩۰-۹ \t().\-]{6,}[\d٠-٩۰-۹]\+?")
MIN_DIGITS = 9   # shorter runs (years, ranges, prices, postcodes) are not phone numbers


def _digits(s):
    return "".join(str(unicodedata.digit(c)) for c in s if c.isdigit())


def phone_runs(text):
    """Phone-like digit runs in text, each as its digit string (Arabic-Indic digits folded to 0-9)."""
    out = []
    for m in PHONE_RUN.finditer(text or ""):
        d = _digits(m.group(0))
        if len(d) >= MIN_DIGITS:
            out.append(d)
    return out


def _key(d):
    # Last 8 digits: equal for "+61 8 9360 6063" and "(08) 9360 6063", different for any reordering.
    return d[-8:]


def phone_guard(answer, source_texts):
    """(ok, bad_runs). ok is True when the answer holds no phone-like run, or every one appears in a source.
    Pure: no network, no mutation. A source text may also carry the number only inside a tel: link."""
    runs = phone_runs(answer)
    if not runs:
        return True, []
    have = set()
    for t in source_texts:
        for d in phone_runs(t):
            have.add(_key(d))
        # tel:+61893606063 style links have no separators at all
        for m in re.finditer(r"tel:\+?(\d{9,15})", t or ""):
            have.add(_key(m.group(1)))
    bad = [d for d in runs if _key(d) not in have]
    return (not bad), bad


def ask_sources(d):
    """Paragraph texts of the CITED resources in an ask response (all retrieved paragraphs if nothing is cited)."""
    rr = (d.get("retrieval_results") or {}).get("resources") or {}
    cited = {k.split("/")[0] for k in (d.get("citations") or {})}
    out = []
    for rid, res in rr.items():
        if cited and rid not in cited:
            continue
        for f in (res.get("fields") or {}).values():
            for p in (f.get("paragraphs") or {}).values():
                out.append(p.get("text") or "")
    return out


def ask_numbers_ok(d):
    """Convenience for the ask-shaped surfaces: are the phone numbers in d['answer'] present in its cited sources?"""
    return phone_guard(d.get("answer") or "", ask_sources(d))


def mask_phone_runs(text):
    """For a streamed DRAFT only: the sources are not yet known, so a phone number is not shown until it is checked."""
    return PHONE_RUN.sub(lambda m: "…" if len(_digits(m.group(0))) >= MIN_DIGITS else m.group(0), text)
