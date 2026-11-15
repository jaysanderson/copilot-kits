"""Provision the Clinic demo Knowledge Box and ingest the crawled corpus.

Hard rule 14: sanctioned account only (progress-jay-geo,
86d1adc8-64ef-499b-86d6-72e9fd684ab0), every call to the ZONAL host.
Hard rule 15: no Data-Augmentation or graph-extraction task is registered here -
every classification axis is intrinsic and set deterministically at ingest, at
zero LLM cost.
"""
import json, re, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import requests

APP = Path(__file__).resolve().parent.parent
FACTORY = APP.parent.parent
ACCOUNT = "86d1adc8-64ef-499b-86d6-72e9fd684ab0"


def read_env(path):
    e = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


# ---------------------------------------------------------------- taxonomy
PRODUCTS = [
    ("Remplir", [r"remplir"]),
    ("Striate+", [r"striate"]),
    ("OrthoACI", [r"orthoaci"]),
    ("OrthoATI", [r"orthoati"]),
    ("SMRTGRAFT", [r"smrtgraft"]),
]

DOCTYPES = [
    ("Instructions for use", [r"/instructions-for-use", r"eifu", r"instructions for use"]),
    ("Surgical technique", [r"surgical-technique"]),
    ("Clinical evidence", [r"summary-of-clinical-evidence", r"clinical evidence"]),
    ("Patient information", [r"patient-information", r"/patients/"]),
    ("Practitioner resource", [r"/practitioners/", r"webinar", r"symposium"]),
    ("Patient story", [r"-story/"]),
    ("Corporate", [r"/about/", r"/team/", r"/contact/", r"/invest/", r"/solutions/", r"^https://clinic.com/$"]),
]


def classify(url, title):
    u = url.lower()
    t = (title or "").lower()
    prods = [p for p, pats in PRODUCTS if any(re.search(x, u) or re.search(x, t) for x in pats)]
    if not prods:
        prods = ["Company-wide"]

    dtype = None
    for name, pats in DOCTYPES:
        if any(re.search(p, u) for p in pats):
            dtype = name
            break
    if dtype is None:
        dtype = "Announcement"  # everything under the news post sitemap

    if "/practitioners/" in u:
        aud = "Practitioner"
    elif "/patients/" in u or dtype == "Patient story":
        aud = "Patient"
    elif dtype == "Announcement" or "/invest" in u:
        aud = "Investor and media"
    else:
        aud = "Corporate"

    region = "Global"
    if "/au/" in u:
        region = "Australia"
    elif "/uk/" in u:
        region = "United Kingdom"
    elif "/ca/" in u:
        region = "Canada"
    return prods, dtype, aud, region


def main():
    env = read_env(FACTORY / ".env")
    zone, nua = env["ARAG_ZONE"], env["ARAG_NUA_KEY"]
    assert env["ARAG_ACCOUNT"] == ACCOUNT, "wrong account - hard rule 14"
    zbase = f"https://{zone}.rag.progress.cloud/api/v1"

    # hard rule 14 scoping check, zonal host
    r = requests.get(f"{zbase}/account/{ACCOUNT}/kbs", headers={"Authorization": f"Bearer {nua}"}, timeout=30)
    print(f"account scoping check: {r.status_code} ({len(r.json()) if r.status_code == 200 else r.text[:120]} kbs)")
    if r.status_code != 200:
        raise SystemExit("scoping check failed")

    envfile = APP / ".env"
    if envfile.exists() and "KB_ID=" in envfile.read_text():
        cfg = read_env(envfile)
        kb_id, token = cfg["KB_ID"], cfg["KB_TOKEN"]
        print(f"reusing KB {kb_id}")
    else:
        r = requests.post(f"{zbase}/account/{ACCOUNT}/kbs", headers={"Authorization": f"Bearer {nua}"},
                          json={"title": "Clinic Knowledge Desk (demo)", "slug": "clinic-demo", "zone": zone}, timeout=60)
        if r.status_code not in (200, 201):
            raise SystemExit(f"KB create failed {r.status_code}: {r.text[:400]}")
        kb_id = r.json().get("id") or r.json().get("uuid")
        print("KB", kb_id)
        sa = requests.post(f"{zbase}/account/{ACCOUNT}/kb/{kb_id}/service_accounts",
                           headers={"Authorization": f"Bearer {nua}"},
                           json={"title": "clinic-demo-owner", "role": "SOWNER"}, timeout=30)
        sa_id = sa.json()["id"]
        k = requests.post(f"{zbase}/account/{ACCOUNT}/kb/{kb_id}/service_account/{sa_id}/keys",
                          headers={"Authorization": f"Bearer {nua}"},
                          json={"expires": int(time.time()) + 365 * 24 * 3600}, timeout=30)
        token = k.json().get("token") or k.json().get("key")
        envfile.write_text(
            f"ARAG_HOST={zbase}\nKB_ID={kb_id}\nKB_TOKEN={token}\nARAG_ZONE={zone}\n")
        print("service-account token written to apps/clinic/.env")

    kburl = f"{zbase}/kb/{kb_id}"
    H = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {token}", "Content-Type": "application/json"}

    docs = json.loads((APP / "corpus" / "docs.json").read_text())
    index = []

    def push(d):
        prods, dtype, aud, region = classify(d["url"], d["title"])
        # the title and the URL context are written INTO the body - a name that
        # lives only in a title never grounds an answer.
        body = f"{d['title']}\nClinic published page: {d['url']}\n\n{d['text']}"
        cls = [{"labelset": "Product", "label": p} for p in prods]
        cls += [{"labelset": "Document type", "label": dtype},
                {"labelset": "Audience", "label": aud},
                {"labelset": "Region", "label": region}]
        payload = {
            "title": d["title"],
            "slug": re.sub(r"[^a-z0-9]+", "-", d["url"].replace("https://clinic.com/", "").lower()).strip("-")[:60] or "home",
            "origin": {"url": d["url"]},
            "usermetadata": {"classifications": cls},
            "texts": {"body": {"body": body, "format": "PLAIN"}},
        }
        rr = requests.post(f"{kburl}/resources", headers=H, json=payload, timeout=90)
        if rr.status_code not in (200, 201):
            return ("FAIL", d["url"], rr.status_code, rr.text[:160])
        rid = rr.json()["uuid"]
        index.append({"rid": rid, "url": d["url"], "title": d["title"], "products": prods,
                      "doctype": dtype, "audience": aud, "region": region,
                      "chars": len(d["text"]), "excerpt": d["text"][:260]})
        return ("OK", d["url"], rid, "")

    fails = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, res in enumerate(ex.map(push, docs)):
            if res[0] != "OK":
                fails.append(res)
            if i % 25 == 0:
                print(f"  ingested {i}/{len(docs)}", flush=True)
    print(f"ingested {len(index)} resources, {len(fails)} failures")
    for f in fails[:10]:
        print("  ", f)
    (APP / "corpus" / "index.json").write_text(json.dumps(index, indent=1))


if __name__ == "__main__":
    main()
