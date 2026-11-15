"""Drive real questions through the real /api/answer so they land in the insights log.
Rows are flagged 'team' via the driver key (INSIGHTS_DRIVER_KEY in .env / env). Usage:
  INSIGHTS_DRIVER_KEY=... python drive.py [base_url]"""
import os, sys, httpx
BASE = sys.argv[1] if len(sys.argv) > 1 else "https://your-app.fly.dev"
from dotenv import dotenv_values
H = {"X-Insights-Source": dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))["INSIGHTS_DRIVER_KEY"]}
QS = [
 ("How do I apply to study at University?", "en"),
 ("What scholarships are available for international students?", "en"),
 ("Can I visit the campus before I apply?", "en"),
 ("What courses can I study in veterinary science?", "en"),
 ("Is there on-campus accommodation?", "en"),
 ("What is the parking fee for students?", "en"),
 ("Does University have a childcare centre on campus?", "en"),
 ("Can I get credit for my TAFE diploma?", "en"),
 ("What is the bus timetable from University station to campus?", "en"),
 ("Does the university have a gym membership discount for students?", "en"),
 ("\u7533\u8bf7\u9700\u8981\u4ec0\u4e48\u82f1\u8bed\u6210\u7ee9\uff1f", "zh"),
 ("\u5982\u4f55\u7533\u8bf7\u5956\u5b66\u91d1\uff1f", "zh"),
 ("\u0645\u0627 \u0647\u064a \u0634\u0631\u0648\u0637 \u0627\u0644\u0642\u0628\u0648\u0644 \u0644\u0644\u0637\u0644\u0627\u0628 \u0627\u0644\u062f\u0648\u0644\u064a\u064a\u0646\u061f", "ar"),
 ("Bagaimana cara mendaftar sebagai mahasiswa internasional?", "id"),
 ("Apakah ada asrama untuk mahasiswa internasional?", "id"),
]
START = int(sys.argv[2]) if len(sys.argv) > 2 else 0
for q, l in QS[START:]:
    try:
        r = httpx.post(BASE + "/api/answer", json={"q": q, "lang": l}, headers=H, timeout=70)
        d = r.json()
    except Exception as e:
        print("ERROR", type(e).__name__, q, flush=True)
        continue
    print(r.status_code,flush=True) if False else print(r.status_code, "DECLINED" if d.get("declined") else f"answered/{len(d.get('sources', []))}", q)
