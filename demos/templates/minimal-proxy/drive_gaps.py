"""Drive real questions through the real /api/answer so they land in the insights log.
Rows are flagged 'team' via the driver key (INSIGHTS_DRIVER_KEY in .env / env). Usage:
  INSIGHTS_DRIVER_KEY=... python drive.py [base_url]"""
import os, sys, httpx
BASE = sys.argv[1] if len(sys.argv) > 1 else "https://your-app.fly.dev"
from dotenv import dotenv_values
H = {"X-Insights-Source": dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))["INSIGHTS_DRIVER_KEY"]}
QS = [
 ("What is the ATAR cut-off for the Bachelor of Nursing?", "en"),
 ("Can I defer my offer for two years?", "en"),
 ("How much does a parking permit cost per semester?", "en"),
 ("Is my Indian Bachelor of Commerce recognised for postgraduate entry?", "en"),
 ("What is the weekly rent for on-campus accommodation?", "en"),
 ("Are there any part-time jobs on campus for international students?", "en"),
 ("What are the class contact hours per week for engineering?", "en"),
 ("\u5b66\u8d39\u662f\u591a\u5c11\uff1f\u6709\u5206\u671f\u4ed8\u6b3e\u5417\uff1f", "zh"),
 ("\u6211\u7684\u4e2d\u56fd\u9ad8\u8003\u6210\u7ee9\u53ef\u4ee5\u76f4\u63a5\u7533\u8bf7\u672c\u79d1\u5417\uff1f", "zh"),
 ("\u0643\u0645 \u062a\u0643\u0644\u0641\u0629 \u0627\u0644\u0625\u0642\u0627\u0645\u0629 \u0641\u064a \u0627\u0644\u062d\u0631\u0645 \u0627\u0644\u062c\u0627\u0645\u0639\u064a\u061f", "ar"),
 ("\u0647\u0644 \u064a\u0645\u0643\u0646\u0646\u064a \u0625\u062d\u0636\u0627\u0631 \u0639\u0627\u0626\u0644\u062a\u064a \u0645\u0639\u064a \u0623\u062b\u0646\u0627\u0621 \u0627\u0644\u062f\u0631\u0627\u0633\u0629\u061f", "ar"),
 ("Berapa biaya hidup per bulan di Perth untuk mahasiswa?", "id"),
 ("Apakah ijazah S1 dari Indonesia diakui untuk program magister?", "id"),
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
