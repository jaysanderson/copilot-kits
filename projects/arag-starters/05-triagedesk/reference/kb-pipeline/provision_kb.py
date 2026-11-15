"""Provision the Studycity Knowledge Box.

Sanctioned account only (hard rule 14): account id 86d1adc8-64ef-499b-86d6-72e9fd684ab0
("progress-jay-geo"), read from the factory root .env. Verifies account membership on the
ZONAL host (a 401 there means wrong host, only a 403 says anything about scoping - never
call the global nuclia.cloud host for this check).

Mints a KB + SOWNER service-account token, same pattern as
content/ci-demo/derisk/scripts/provision_kb.py. Writes coordinates to
apps/studycity/.env (gitignored via the root **/.env rule - never committed, never
printed to the console, never put in the README or the DAM).
"""
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent  # apps/studycity
FACTORY_ROOT = ROOT.parent.parent
ENV_OUT = ROOT / ".env"
EXPECTED_ACCOUNT = "86d1adc8-64ef-499b-86d6-72e9fd684ab0"


def read_env(path):
    e = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


def main():
    env = read_env(FACTORY_ROOT / ".env")
    account = env["ARAG_ACCOUNT"]
    zone = env["ARAG_ZONE"]
    nua = env["ARAG_NUA_KEY"]
    assert account == EXPECTED_ACCOUNT, "wrong account - hard rule 14"

    zbase = f"https://{zone}.rag.progress.cloud/api/v1"

    print(f"Verifying account scoping on zonal host ({zone})...")
    chk = requests.get(f"{zbase}/account/{account}/kbs",
                        headers={"Authorization": f"Bearer {nua}"}, timeout=30)
    if chk.status_code != 200:
        raise SystemExit(f"account check failed ({chk.status_code}): {chk.text[:300]}")
    print(f"  OK - {len(chk.json())} existing KBs visible on this account")

    title = "Studycity - International Student Concierge"
    slug = "studycity-concierge"

    print(f"Provisioning KB '{title}' (slug {slug}) in zone {zone}...")
    r = requests.post(f"{zbase}/account/{account}/kbs",
                       headers={"Authorization": f"Bearer {nua}"},
                       json={"title": title, "slug": slug, "zone": zone}, timeout=30)
    if r.status_code not in (200, 201):
        raise SystemExit(f"KB creation failed ({r.status_code}): {r.text[:400]}")
    kb_id = r.json().get("id") or r.json().get("uuid")
    print(f"  KB created: {kb_id}")

    print("Minting SOWNER service-account token...")
    sa = requests.post(f"{zbase}/account/{account}/kb/{kb_id}/service_accounts",
                        headers={"Authorization": f"Bearer {nua}"},
                        json={"title": "studycity-owner", "role": "SOWNER"}, timeout=30)
    if sa.status_code not in (200, 201):
        raise SystemExit(f"service account creation failed ({sa.status_code}): {sa.text[:400]}")
    sa_id = sa.json()["id"]
    expires = int(time.time()) + 365 * 24 * 60 * 60  # 1 year - long-lived demo KB
    k = requests.post(f"{zbase}/account/{account}/kb/{kb_id}/service_account/{sa_id}/keys",
                       headers={"Authorization": f"Bearer {nua}"},
                       json={"expires": expires}, timeout=30)
    if k.status_code not in (200, 201):
        raise SystemExit(f"key mint failed ({k.status_code}): {k.text[:400]}")
    token = k.json().get("token") or k.json().get("key")
    if not token:
        raise SystemExit(f"no token in response: {k.text[:400]}")

    kb_url = f"{zbase}/kb/{kb_id}"
    ENV_OUT.write_text(
        f"ARAG_HOST={zbase}\n"
        f"ARAG_ACCOUNT={account}\n"
        f"ARAG_ZONE={zone}\n"
        f"KB_ID={kb_id}\n"
        f"KB_SLUG={slug}\n"
        f"KB_URL={kb_url}\n"
        f"KB_TOKEN={token}\n"
    )
    print(f"  Service account token minted, written to {ENV_OUT} (not printed)")
    print(f"\nDone. KB_ID={kb_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
