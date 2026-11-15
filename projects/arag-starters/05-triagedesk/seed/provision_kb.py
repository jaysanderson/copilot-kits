#!/usr/bin/env python3
"""One-off KB provisioning for gov-degree-triage. Mirrors apps/marty-vdr/scripts/create-kb.mjs.

Run once: .venv/bin/python apps/gov-degree-triage/seed/provision_kb.py
Writes ARAG_KB_ID / ARAG_KB_URL / ARAG_ZONE / ARAG_SERVICEACCOUNT into apps/gov-degree-triage/.env
"""
import json
import os
import time
import sys
import requests

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(APP_DIR))
ROOT_ENV = os.path.join(ROOT, ".env")
APP_ENV = os.path.join(APP_DIR, ".env")


def read_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.split("#")[0].strip()
        env[k.strip()] = v
    return env


def write_env_vars(path, updates):
    lines = []
    if os.path.exists(path):
        lines = open(path).read().splitlines()
    keys_set = set()
    for i, line in enumerate(lines):
        if "=" not in line or line.strip().startswith("#"):
            continue
        k = line.split("=", 1)[0].strip()
        if k in updates:
            lines[i] = f"{k}={updates[k]}"
            keys_set.add(k)
    for k, v in updates.items():
        if k not in keys_set:
            lines.append(f"{k}={v}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    root_env = read_env(ROOT_ENV)
    account = root_env.get("ARAG_ACCOUNT")
    token = root_env.get("ARAG_NUA_KEY")
    zone = root_env.get("ARAG_ZONE", "<zone>")
    if not account or not token:
        print("Missing ARAG_ACCOUNT / ARAG_NUA_KEY in root .env", file=sys.stderr)
        sys.exit(1)

    zbase = f"https://{zone}.rag.progress.cloud/api/v1"
    title = "Gov Degree Equivalency Triage"
    slug = "gov-degree-triage"

    print(f"Provisioning KB in account {account} (zone {zone})...")
    r = requests.post(
        f"{zbase}/account/{account}/kbs",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"title": title, "slug": slug, "zone": zone},
        timeout=30,
    )
    if not r.ok:
        print(f"KB creation failed ({r.status_code}): {r.text[:400]}", file=sys.stderr)
        sys.exit(1)
    kb = r.json()
    kb_id = kb.get("id") or kb.get("uuid")
    if not kb_id:
        print(f"KB created but no id in response: {kb}", file=sys.stderr)
        sys.exit(1)
    kb_url = f"{zbase}/kb/{kb_id}"
    print(f"KB created: {kb_id}")

    write_env_vars(
        APP_ENV,
        {
            "ARAG_ACCOUNT": account,
            "ARAG_NUA_KEY": token,
            "ARAG_ZONE": zone,
            "ARAG_KB_ID": kb_id,
            "ARAG_KB_URL": kb_url,
        },
    )

    # Mint SOWNER service-account token
    sa = requests.post(
        f"{zbase}/account/{account}/kb/{kb_id}/service_accounts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"title": f"factory-{slug}", "role": "SOWNER"},
        timeout=30,
    )
    if not sa.ok:
        print(f"service_account creation failed ({sa.status_code}): {sa.text[:400]}", file=sys.stderr)
        sys.exit(1)
    sa_id = sa.json().get("id")
    if not sa_id:
        print(f"No service account id in response: {sa.json()}", file=sys.stderr)
        sys.exit(1)

    expires = int(time.time()) + 1080 * 24 * 60 * 60
    k = requests.post(
        f"{zbase}/account/{account}/kb/{kb_id}/service_account/{sa_id}/keys",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"expires": expires},
        timeout=30,
    )
    if not k.ok:
        print(f"key mint failed ({k.status_code}): {k.text[:400]}", file=sys.stderr)
        sys.exit(1)
    sa_token = k.json().get("token") or k.json().get("key")
    if not sa_token:
        print(f"No token in key response: {k.json()}", file=sys.stderr)
        sys.exit(1)

    write_env_vars(APP_ENV, {"ARAG_SERVICEACCOUNT": sa_token})
    print("Service-account token minted and written to .env")
    print(f"KB_ID={kb_id}")
    print(f"KB_URL={kb_url}")


if __name__ == "__main__":
    main()
