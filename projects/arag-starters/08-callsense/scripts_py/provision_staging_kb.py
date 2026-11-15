"""
Provision the staging KB for the call-analysis voice-cast reseed (DAM work
b74205b5). Sanctioned account only (hard rule 14): 86d1adc8-64ef-499b-86d6-
72e9fd684ab0 ("progress-jay-geo"), NUA key + zone read from the factory root
.env, zonal host per hard rule 14. Writes coordinates to
apps/call-analysis/.env.staging (gitignored, never applied to the live app -
the lead applies the cutover only after the GM's review decision).

The live KB stays completely untouched - this creates a brand new KB.
"""
import json
import time
from pathlib import Path

import requests

FACTORY_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = Path(__file__).resolve().parents[1]
ENV_OUT = APP_ROOT / ".env.staging"


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
    assert account == "86d1adc8-64ef-499b-86d6-72e9fd684ab0", "wrong account - hard rule 14"

    zbase = f"https://{zone}.rag.progress.cloud/api/v1"
    title = "Call Analysis - Voice Cast Staging"
    slug = "call-analysis-voicecast-staging"

    print(f"Provisioning KB '{title}' in account {account} zone {zone}...")
    r = requests.post(f"{zbase}/account/{account}/kbs", headers={"Authorization": f"Bearer {nua}"},
                       json={"title": title, "slug": slug, "zone": zone}, timeout=30)
    if r.status_code not in (200, 201):
        raise SystemExit(f"KB creation failed ({r.status_code}): {r.text[:400]}")
    kb_id = r.json().get("id") or r.json().get("uuid")
    print(f"  KB created: {kb_id}")

    print("Minting SOWNER service-account token...")
    sa = requests.post(f"{zbase}/account/{account}/kb/{kb_id}/service_accounts",
                        headers={"Authorization": f"Bearer {nua}"},
                        json={"title": "call-analysis-staging-owner", "role": "SOWNER"}, timeout=30)
    if sa.status_code not in (200, 201):
        raise SystemExit(f"service account creation failed ({sa.status_code}): {sa.text[:400]}")
    sa_id = sa.json()["id"]
    expires = int(time.time()) + 365 * 24 * 60 * 60
    k = requests.post(f"{zbase}/account/{account}/kb/{kb_id}/service_account/{sa_id}/keys",
                       headers={"Authorization": f"Bearer {nua}"},
                       json={"expires": expires}, timeout=30)
    if k.status_code not in (200, 201):
        raise SystemExit(f"key mint failed ({k.status_code}): {k.text[:400]}")
    token = k.json().get("token") or k.json().get("key")
    if not token:
        raise SystemExit(f"no token in response: {k.text[:400]}")

    ENV_OUT.write_text(
        "# Staging KB for the ElevenLabs voice-cast reseed (DAM b74205b5) - NOT applied to the live app.\n"
        f"ARAG_BASE={zbase}\n"
        f"ARAG_KB_ID={kb_id}\n"
        f"ARAG_API_KEY={token}\n"
        f"ARAG_GENERATIVE_MODEL=chatgpt-azure-4o-mini\n"
        f"ARAG_ZONE={zone}\n"
    )
    print(f"  Service account token minted, written to {ENV_OUT}")
    print(f"\nDone. STAGING_KB_ID={kb_id}")


if __name__ == "__main__":
    main()
