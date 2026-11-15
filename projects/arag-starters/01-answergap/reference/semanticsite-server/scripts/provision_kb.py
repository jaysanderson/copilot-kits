"""Provision the SemanticSite knowledge box (Phase 1 of the composable-stack
MACH demo). Sanctioned account only (hard rule 14):
account id 86d1adc8-64ef-499b-86d6-72e9fd684ab0 ("progress-jay-geo"), read from the
factory root .env. Verifies account scoping BEFORE provisioning.

Mints a LONG-LIVED (2-year) SOWNER service-account token - hard rule 15b: the
30-day de-risk throwaway token killed two prior live demos.

Writes coordinates to apps/bank-co/.env (gitignored - proven separately with
`git check-ignore -v`). Never prints the token or NUA key value.
"""
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent.parent
FACTORY_ROOT = ROOT.parent.parent
ENV_OUT = ROOT / ".env"

ACCOUNT_ID = "86d1adc8-64ef-499b-86d6-72e9fd684ab0"


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
    assert account == ACCOUNT_ID, f"wrong account - hard rule 14 (got {account})"

    zbase = f"https://{zone}.rag.progress.cloud/api/v1"

    print(f"Verifying account scoping: GET {zbase}/account/{account}/kbs")
    v = requests.get(f"{zbase}/account/{account}/kbs", headers={"Authorization": f"Bearer {nua}"}, timeout=30)
    if v.status_code != 200:
        raise SystemExit(f"Account scoping check FAILED ({v.status_code}): {v.text[:400]}")
    existing = v.json()
    print(f"  OK - 200, {len(existing)} existing KBs visible on this account/zone.")

    title = "SemanticSite"
    slug = "semanticsite"

    print(f"Provisioning KB '{title}' (slug={slug}) in account {account} zone {zone}...")
    r = requests.post(f"{zbase}/account/{account}/kbs", headers={"Authorization": f"Bearer {nua}"},
                      json={"title": title, "slug": slug, "zone": zone}, timeout=30)
    if r.status_code not in (200, 201):
        raise SystemExit(f"KB creation failed ({r.status_code}): {r.text[:400]}")
    kb_id = r.json().get("id") or r.json().get("uuid")
    print(f"  KB created: {kb_id}")

    print("Minting SOWNER service-account token (2-year expiry)...")
    sa = requests.post(f"{zbase}/account/{account}/kb/{kb_id}/service_accounts",
                       headers={"Authorization": f"Bearer {nua}"},
                       json={"title": "semanticsite-owner", "role": "SOWNER"}, timeout=30)
    if sa.status_code not in (200, 201):
        raise SystemExit(f"service account creation failed ({sa.status_code}): {sa.text[:400]}")
    sa_id = sa.json()["id"]
    expires = int(time.time()) + 730 * 24 * 60 * 60  # 2 years - hard rule 15b
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
        f"ARAG_ZONE={zone}\n"
        f"ARAG_HOST={zbase}\n"
        f"ARAG_ACCOUNT={account}\n"
        f"KB_ID={kb_id}\n"
        f"KB_URL={kb_url}\n"
        f"KB_TOKEN={token}\n"
        f"KB_TOKEN_EXPIRES={expires}\n"
    )
    print(f"  Service account token minted (expires epoch {expires}), written to {ENV_OUT}")
    print(f"\nDone. KB_ID={kb_id}")


if __name__ == "__main__":
    main()
