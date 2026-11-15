"""Offline controls for answers.phone_guard. Every case declares FIRE (guard must reject) or QUIET (must accept) up front,
and every plant proves it changed its input. Exit non-zero on any miss. Run: .venv/bin/python tests/phone_guard_check.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import answers as A

SRC = ["## Have a question? Talk to us\n\n[+61 8 9360 6063](tel:+61893606063 )\n\nOpen Monday to Friday, 8:30am - 5:30pm."]
OK = "International students can call +61 8 9360 6063 (Monday to Friday)."
cases = [  # (name, answer, sources, expect_ok)
    ("correct number passes", OK, SRC, True),
    ("local form of the same number passes", "Call (08) 9360 6063.", SRC, True),
    ("no digits is untouched", "Contact the international team online.", SRC, True),
    ("years and ranges are not phone numbers", "Applications run 2026-2027, from 1 September 2026 - 6 March 2027, fee $12,000.", SRC, True),
    ("number only in a tel: link passes", "Call +61 8 9360 6063.", ["[call](tel:+61893606063)"], True),
    ("Arabic-Indic digits of the correct number pass", "اتصل على +٦١ ٨ ٩٣٦٠ ٦٠٦٣", SRC, True),
    ("REVERSED number fires (the measured defect)", "6063 9360 8 61+", SRC, False),
    ("reversed inside Arabic prose fires", "يمكنك الاتصال على 6063 9360 8 61+ من الاثنين إلى الجمعة", SRC, False),
    ("a number that is in no source fires", "Call +61 8 9999 1234.", SRC, False),
    ("one good and one bad fires", OK + " Or +61 8 1111 2222.", SRC, False),
]
fails = 0
for name, ans, src, expect in cases:
    ok, bad = A.phone_guard(ans, src)
    good = (ok == expect)
    fails += not good
    print(("PASS" if good else "FAIL"), ("QUIET" if expect else "FIRE "), name, ("" if ok else f"bad={bad}"))
# plant proof: the reversed plant really differs from the correct text, and mutating the source flips the verdict
rev = "6063 9360 8 61+"
assert rev != "+61 8 9360 6063", "inert plant"
ok1, _ = A.phone_guard("Call +61 8 9360 6063.", SRC); ok2, _ = A.phone_guard("Call +61 8 9360 6063.", [s.replace("9360", "9361") for s in SRC])
assert ok1 and not ok2, "source mutation did not flip the verdict"
print("PASS plant mutates input: same answer, source digits changed -> verdict flips")
# draft mask
m = A.mask_phone_runs("Call +61 8 9360 6063 now, fee $12,000, 2026-2027.")
good = "9360" not in m and "12,000" in m and "2026-2027" in m
fails += not good; print(("PASS" if good else "FAIL"), "draft mask hides phone runs only:", m)
# ask-shaped convenience
d = {"answer": "Call +61 8 9360 6063", "citations": {"r1/u/x/1-2": [[0, 5]]}, "retrieval_results": {"resources": {"r1": {"fields": {"f": {"paragraphs": {"p": {"text": SRC[0]}}}}}, "r2": {"fields": {"f": {"paragraphs": {"p": {"text": "+61 8 1111 2222"}}}}}}}}
ok, _ = A.ask_numbers_ok(d); d2 = dict(d, answer="Call +61 8 1111 2222")  # present only in the UNCITED resource r2
ok2, _ = A.ask_numbers_ok(d2)
good = ok and not ok2; fails += not good; print(("PASS" if good else "FAIL"), "ask_numbers_ok checks CITED resources only")
print("FAILS", fails); sys.exit(1 if fails else 0)
