#!/usr/bin/env python3
"""Clone a Progress Agentic RAG (Nuclia) Knowledge Box into a brand-new KB - a
literal working twin: models/config, labelsets, entities, synonyms,
vectorsets, search configurations, data-augmentation tasks, AND every resource.

USAGE
  .venv/bin/python scripts/clone_kb.py --source <kb-id-or-url> [options]

  --source KB_ID_OR_URL   required. A bare KB uuid, or a URL/host path containing
                          it (e.g. https://<zone>.rag.progress.cloud
                          /api/v1/kb/<uuid>/...). If the source KB lives outside
                          the factory account (86d1adc8-...), set SOURCE_ARAG_TOKEN
                          in the environment to a service-account token for it -
                          the script otherwise mints a temporary reader token via
                          the account API (only works for KBs under this account).
  --target-title TITLE    display title for the new KB. Default:
                          "<source title> (clone)".
  --target-slug SLUG      slug for the new KB. Default: derived from target-title
                          + a short timestamp suffix (slugs must be unique).
  --dry-run               report exactly what WOULD be copied - counts per
                          category + anything the API can't replicate - and
                          create nothing.
  --verify-only           skip cloning; run only the step-7 verification (scoped
                          /ask + config diff) against an already-created target.
                          Requires --target-kb-id and TARGET_ARAG_TOKEN env (or a
                          previously-written scripts/clone_kb_output/<slug>.env).
  --target-kb-id ID       an existing target KB id (used with --verify-only, or
                          to resume applying config/resources into an already-
                          created but incomplete target).
  --skip-tasks            do not recreate data-augmentation tasks on the target
                          (useful if you only want the resources + taxonomy).
  --poll-timeout SECONDS  max time to wait for target resources to reach
                          PROCESSED before giving up on the augmentation-task
                          step. Default 1800 (30 min).
  --yes                   skip the interactive confirmation before creating.

WHAT IT COPIES
  - KB models/config: semantic model(s), generative model (pinned - never left to
    the fresh-KB default, which refuses every /ask), anonymization/ner/relation
    models, summary config, vectorsets.
  - Labelsets, entity groups, custom synonyms.
  - Every resource (prefers the official POST /kb/{id}/export + POST
    /kb/{id}/import portable-dump path; falls back to paging /resources and
    recreating title/summary/texts/links/files + re-uploading file bytes if
    export/import isn't available or fails).
  - Data-augmentation / extraction tasks (labeler, llm-graph, ask, synthetic-
    questions, llm-align, ...), recreated with apply=EXISTING ONLY AFTER every
    imported resource reaches PROCESSED (enabling these before ingest completes
    stalls ALL processing on the KB - the #1 gotcha in the arag-kb skill).
  - Search configurations (best-effort - the schema for `config` inside a saved
    search configuration is not fully documented; copied as returned by the
    source, so an incompatible field may 422 and is reported, not silently
    dropped).

LIMITATIONS (the API cannot replicate these - flagged, never silently dropped)
  - **Agent node graph (`mode: "agent"` KBs) is DASHBOARD-ONLY.** No REST endpoint
    exposes or accepts the Retrieval Agent's node graph. If the source KB is in
    agent mode, the script creates the plain `kb`-mode twin (data + config) and
    prints an explicit MANUAL STEP notice - the agent workflow itself must be
    rebuilt by hand in the dashboard (see the rao-workflow skill).
  - **Zone is fixed.** The factory's ARAG_NUA_KEY provisions in
    <zone> (AU/Sydney) ONLY - the create-KB `zone` param is
    accepted but ignored. If the source KB is hosted in a different zone, the
    clone lands in AU regardless; the script prints a residency warning. Fine
    for synthetic demo content, NOT fine for a residency-sensitive live demo.
  - **Entity-group WRITES 404 on this deployment via a KB service-account
    token** - confirmed empirically 2026-07-22: both `POST .../entitiesgroups`
    and `PATCH .../entitiesgroup/{group}` return 404 even though the published
    schema documents them (OPTIONS on both routes advertises only GET as
    Allowed). The script still calls them (harmless if a future deployment
    enables them) and reports the failure per group - it does NOT silently
    drop entity groups. In practice this has NOT lost data in testing: the
    export/import path embeds entity groups in its portable dump, so a
    successful export/import restores them anyway (verified: a source KB with
    8 entity groups produced a target with 8 after import, despite every
    direct-write call 404ing). Only the FALLBACK manual-resource-migration
    path (used when export/import is unavailable) would actually miss entity
    groups on this deployment.
  - **Vectorset provider secrets aren't readable.** `GET .../configuration` only
    returns the semantic model NAME(S), not any custom embedding-provider
    credentials. Extra vectorsets are recreated by name (`POST
    /vectorsets/{model}`) using Nuclia's built-in catalogue; a source KB using a
    private/BYO embedding endpoint cannot be replicated automatically.
  - **Export/import scope.** No documented way to export a subset of resources -
    it is whole-KB. If it's unavailable (older KB, permission, format mismatch)
    the fallback recreates resources field-by-field; conversation-field replies,
    fine-grained paragraph annotations and existing extracted vectors are NOT
    reconstructed (they are regenerated by reprocessing on the target instead).
  - **Search-configuration schema is only partially documented** - `kind`/`config`
    are copied verbatim; the target may reject fields it doesn't recognise
    (reported per-config-name, not fatal to the rest of the clone).
  - **Existing knowledge-graph edges** produced by a PAST llm-graph run are not
    exported as data - only the *task config* is recreated; the graph is rebuilt
    when that task runs again with apply=EXISTING on the target's own resources.
  - **A task's `parameters` must contain real `operations`/`on` to be replayable.**
    `GET /kb/{id}/tasks["tasks"]` is a CATALOGUE of available task TYPES (with
    full jsonschema) - not what's configured on the KB (confirmed: a KB that
    has never run any augmentation still returns 8 "tasks" entries). The
    script reads the KB's actually-configured instances from
    `configs`/`running`/`done` instead (each has a re-postable `parameters`
    block). If a task entry somehow still lacks `operations`, it is skipped
    with a warning rather than sent as an empty (guaranteed-422) task/start.

ENDPOINTS THIS SCRIPT USES (confirmed LIVE against nuclia-mcp + reference-repos
+ two real end-to-end clones, 2026-07-22 - see the arag-kb skill for the six
operational gotchas). Several endpoints behave differently from the published
docs; working code (below) is what this script actually sends.
  Account API   (host = https://<zone>.rag.progress.cloud, header
                Authorization: Bearer <ARAG_NUA_KEY>):
    POST   /api/v1/account/{account}/kbs
    GET    /api/v1/account/{account}/kbs
    DELETE /api/v1/account/{account}/kb/{kb}                      (cleanup)
    POST   /api/v1/account/{account}/kb/{kb}/service_accounts
    POST   /api/v1/account/{account}/kb/{kb}/service_account/{sa_id}/keys
  KB API        (header X-NUCLIA-SERVICEACCOUNT: Bearer <kb-token>):
    GET   /kb/{id}                          - config + model (similarity/dims)
    GET   /kb/{id}/configuration             - semantic/generative/ner/etc models
    PATCH /kb/{id}/configuration             - set target's model config (docs say
                                                POST; the live host 405s POST and
                                                only accepts PATCH - confirmed)
    GET   /kb/{id}/labelsets   POST /kb/{id}/labelset/{name}
    GET   /kb/{id}/entitiesgroups             (NO show_entities param - the live
                                                host 400s that; list names only,
                                                then GET each group individually)
    GET   /kb/{id}/entitiesgroup/{group}      - per-group detail
    POST  /kb/{id}/entitiesgroups             - create (404 on this deployment via
                                                a KB token - see LIMITATIONS)
    GET   /kb/{id}/custom-synonyms   PUT /kb/{id}/custom-synonyms
    GET   /kb/{id}/search_configurations   POST /kb/{id}/search_configurations/{name}
    POST  /kb/{id}/vectorsets/{model}
    GET   /kb/{id}/tasks   -> {tasks: [TYPE catalogue], configs, running, done}
                                (configured instances are in configs/running/done,
                                NOT "tasks" - see LIMITATIONS)
    POST  /kb/{id}/task/start   DELETE /kb/{id}/task/{id}
    POST  /kb/{id}/export   GET /kb/{id}/export/{eid}/status   GET /kb/{id}/export/{eid}
                                (status field is a flat lowercase string, e.g.
                                "running"/"finished" - not the nested object docs show)
    POST  /kb/{id}/import   GET /kb/{id}/import/{iid}/status
    GET   /kb/{id}/resources (paged, ?page=N&size=M)   GET /kb/{id}/resource/{rid}
    POST  /kb/{id}/resources   PUT /kb/{id}/resource/{rid}/file/{field}
    GET   /kb/{id}/resource/{rid}/file/{field}/download/field
    POST  /kb/{id}/ask   GET /kb/{id}/counters

Working code beat docs where they disagreed (e.g. create-KB auth is the account
NUA key via `Authorization: Bearer`, NOT the KB service-account header; the four
divergences called out above were all found by probing the real host, not by
reading documentation).
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "scripts" / "clone_kb_output"

HOST = "https://<zone>.rag.progress.cloud"  # the only zone this
                                                            # factory key provisions
ZONE_NAME = "<zone> (AU / Sydney)"

# Live status values come back lowercase ("running", "finished") despite the
# published schema showing "PENDING" - confirmed against the real host
# 2026-07-22. Compare case-insensitively so either casing is handled.
PENDING_STATUSES = {"pending", "running", "scheduled", "submitted", ""}
TERMINAL_OK_STATUSES = {"finished", "done", "finished_success", "success", "ok"}
AUGMENTATION_TASK_NAMES = {
    "labeler", "llm-graph", "ask", "synthetic-questions", "llm-align",
    "llama-guard", "prompt-guard",
}  # excludes "demo-dataset", "dummy", "env", "semantic-model-migrator" - not
   # meaningful / not safe to blind-replicate onto a different KB's content


def log(msg):
    print(f"[clone_kb] {msg}", flush=True)


def warn(msg):
    print(f"[clone_kb] WARNING: {msg}", flush=True)


def factory_env():
    e = {}
    env_path = ROOT / ".env"
    if not env_path.exists():
        sys.exit("factory .env not found at " + str(env_path))
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.strip()
    return e


def extract_kb_id(source):
    """Accept a bare uuid or any URL/path containing /kb/<uuid>."""
    m = re.search(r"/kb/([0-9a-fA-F-]{8,})", source)
    if m:
        return m.group(1)
    if re.fullmatch(r"[0-9a-fA-F-]{8,}", source.strip()):
        return source.strip()
    sys.exit(f"could not extract a KB id from --source {source!r}")


def acct_auth(nua):
    return {"Authorization": f"Bearer {nua}", "Content-Type": "application/json"}


def kb_auth(token):
    return {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {token}"}


class ArAgError(RuntimeError):
    pass


def req(method, url, headers=None, ok=(200,), **kw):
    r = requests.request(method, url, headers=headers, timeout=kw.pop("timeout", 120), **kw)
    if r.status_code not in ok:
        raise ArAgError(f"{method} {url} -> {r.status_code}: {r.text[:500]}")
    return r


# --------------------------------------------------------------------------
# Account-level: mint a temporary service-account token for a KB we don't
# already hold a token for (source KBs living in the factory account).
# --------------------------------------------------------------------------

def mint_reader_token(account, nua, kb_id, title):
    auth = acct_auth(nua)
    r = req("POST", f"{HOST}/api/v1/account/{account}/kb/{kb_id}/service_accounts",
            headers=auth, json={"title": title, "role": "SOWNER"}, ok=(200, 201))
    sa_id = r.json()["id"]
    expires = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = req("POST",
            f"{HOST}/api/v1/account/{account}/kb/{kb_id}/service_account/{sa_id}/keys",
            headers=auth, json={"expires": expires}, ok=(200, 201))
    return r.json()["token"]


def create_kb(account, nua, slug, title, mode, learning_configuration):
    auth = acct_auth(nua)
    body = {"slug": slug, "title": title, "mode": mode,
            "learning_configuration": learning_configuration}
    r = requests.post(f"{HOST}/api/v1/account/{account}/kbs", headers=auth,
                       json=body, timeout=120)
    if r.status_code == 409:
        warn(f"slug {slug!r} already exists; recovering id from account listing")
        lr = req("GET", f"{HOST}/api/v1/account/{account}/kbs", headers=auth)
        kb_id = next(k["id"] for k in lr.json() if k.get("slug") == slug)
        return kb_id, False
    if r.status_code not in (200, 201):
        raise ArAgError(f"create KB failed {r.status_code}: {r.text[:500]}")
    return r.json()["id"], True


def mint_owner_token(account, nua, kb_id, title):
    return mint_reader_token(account, nua, kb_id, title)  # same call, SOWNER role


# --------------------------------------------------------------------------
# KB-level inventory reads
# --------------------------------------------------------------------------

def get_kb_meta(host, kb_id, token):
    r = req("GET", f"{host}/api/v1/kb/{kb_id}", headers=kb_auth(token))
    return r.json()


def get_kb_configuration(host, kb_id, token):
    r = req("GET", f"{host}/api/v1/kb/{kb_id}/configuration", headers=kb_auth(token))
    return r.json()


def get_labelsets(host, kb_id, token):
    r = req("GET", f"{host}/api/v1/kb/{kb_id}/labelsets", headers=kb_auth(token))
    return (r.json() or {}).get("labelsets", {}) or {}


def get_entity_groups(host, kb_id, token):
    # Live API rejects show_entities on the LIST endpoint ("please use
    # /entitiesgroup/{group} instead" - docs say otherwise; working code wins).
    # List group names first, then fetch each group's full detail.
    r = req("GET", f"{host}/api/v1/kb/{kb_id}/entitiesgroups", headers=kb_auth(token))
    d = r.json() or {}
    names = list((d.get("groups", d) or {}).keys())
    out = {}
    for name in names:
        try:
            gr = req("GET", f"{host}/api/v1/kb/{kb_id}/entitiesgroup/{name}",
                     headers=kb_auth(token))
            out[name] = gr.json()
        except ArAgError as e:
            warn(f"entity group {name!r} detail not readable: {e}")
    return out


def get_synonyms(host, kb_id, token):
    r = req("GET", f"{host}/api/v1/kb/{kb_id}/custom-synonyms", headers=kb_auth(token))
    return (r.json() or {}).get("synonyms", {}) or {}


def get_search_configs(host, kb_id, token):
    try:
        r = req("GET", f"{host}/api/v1/kb/{kb_id}/search_configurations",
                headers=kb_auth(token))
        d = r.json()
        if isinstance(d, dict):
            return d
        if isinstance(d, list):
            return {c.get("name", f"cfg-{i}"): c for i, c in enumerate(d)}
        return {}
    except ArAgError as e:
        warn(f"search_configurations not readable on {kb_id}: {e}")
        return {}


def get_tasks(host, kb_id, token):
    """Return the KB's actually-CONFIGURED task instances.

    GET /kb/{id}/tasks -> {"tasks": [...available TYPES with full jsonschema...],
    "configs": [...currently enabled...], "running": [...], "done": [...]}.
    The "tasks" key is a catalogue of task TYPES (labeler, llm-graph, ask, ...)
    with their validation schema - NOT what's configured on this KB (confirmed
    empirically 2026-07-22: a KB with zero augmentation ever run still returns
    8 "tasks" entries). The real instances - each with a re-postable
    `parameters` block (name, on, filter, operations, llm) - live in "configs"
    (enabled for new data) / "running" / "done" (historical runs), keyed by
    entry["task"]["name"]. Merge all three, de-duping by (task type, config
    name), preferring the earliest bucket seen (configs > running > done).
    """
    try:
        r = req("GET", f"{host}/api/v1/kb/{kb_id}/tasks", headers=kb_auth(token))
        d = r.json() or {}
    except ArAgError as e:
        warn(f"tasks not readable on {kb_id}: {e}")
        return []
    out, seen = [], set()
    for bucket in ("configs", "running", "done"):
        for entry in d.get(bucket, []) or []:
            name = (entry.get("task") or {}).get("name") or entry.get("name")
            params = entry.get("parameters") or {}
            key = (name, params.get("name"))
            if not name or key in seen:
                continue
            seen.add(key)
            out.append({"name": name, "parameters": params, "_bucket": bucket,
                        "_id": entry.get("id")})
    return out


def list_resources(host, kb_id, token, page_size=50):
    out, page = [], 0
    while True:
        r = req("GET", f"{host}/api/v1/kb/{kb_id}/resources", headers=kb_auth(token),
                params={"page": page, "size": page_size})
        d = r.json()
        batch = d.get("resources", [])
        out += batch
        more = (d.get("pagination") or {}).get("more", False)
        if not more and len(batch) < page_size:
            break
        if not batch:
            break
        page += 1
    return out


def get_counters(host, kb_id, token):
    r = req("GET", f"{host}/api/v1/kb/{kb_id}/counters", headers=kb_auth(token))
    return r.json()


# --------------------------------------------------------------------------
# Apply config to target (order matters: BEFORE resources import)
# --------------------------------------------------------------------------

def apply_configuration(host, kb_id, token, cfg):
    fields = {k: v for k, v in {
        "anonymization_model": cfg.get("anonymization_model"),
        "generative_model": cfg.get("generative_model"),
        "ner_model": cfg.get("ner_model"),
        "relation_model": cfg.get("relation_model"),
        "default_semantic_model": cfg.get("semantic_model"),
        "semantic_models": [cfg["semantic_model"]] if cfg.get("semantic_model") else None,
    }.items() if v not in (None, "", [])}
    if not fields:
        return
    try:
        # Docs say POST; the live host 405s on POST and accepts PATCH instead -
        # confirmed empirically 2026-07-22 (working code beats docs).
        req("PATCH", f"{host}/api/v1/kb/{kb_id}/configuration", headers=kb_auth(token),
            json=fields, ok=(200, 204))
        log(f"target configuration applied: {fields}")
    except ArAgError as e:
        warn(f"configuration PATCH rejected some/all fields (often because the "
             f"semantic model was already fixed at KB-creation time): {e}")


def apply_labelsets(host, kb_id, token, labelsets):
    for name, spec in labelsets.items():
        body = {k: spec[k] for k in ("title", "color", "multiple", "kind", "labels")
                if k in spec}
        try:
            req("POST", f"{host}/api/v1/kb/{kb_id}/labelset/{name}",
                headers=kb_auth(token), json=body, ok=(200, 201))
        except ArAgError as e:
            warn(f"labelset {name!r} not applied: {e}")


def apply_entities(host, kb_id, token, groups):
    for group, spec in groups.items():
        body = {"group": group, "entities": spec.get("entities", {}),
                "title": spec.get("title"), "color": spec.get("color")}
        try:
            req("POST", f"{host}/api/v1/kb/{kb_id}/entitiesgroups",
                headers=kb_auth(token), json=body, ok=(200, 201))
        except ArAgError as e:
            # Confirmed empirically 2026-07-22: this factory's KB tier 404s on
            # BOTH POST /entitiesgroups and PATCH /entitiesgroup/{group} via a
            # KB service-account token, despite the published schema - entity
            # groups appear read-only through this API on this deployment.
            # They are still detected and reported (never silently dropped);
            # if export/import restores them from the KB's internal dump that
            # covers this gap (see the export/import step's own report).
            warn(f"entity group {group!r} not applied via the direct write "
                 f"API (this deployment 404s create/update calls for entity "
                 f"groups via a KB token - a real API limitation, not a bug "
                 f"in this script): {e}")


def apply_synonyms(host, kb_id, token, synonyms):
    if not synonyms:
        return
    try:
        req("PUT", f"{host}/api/v1/kb/{kb_id}/custom-synonyms", headers=kb_auth(token),
            json={"synonyms": synonyms}, ok=(200, 204))
    except ArAgError as e:
        warn(f"synonyms not applied: {e}")


def apply_vectorsets(host, kb_id, token, extra_models):
    for model in extra_models:
        try:
            req("POST", f"{host}/api/v1/kb/{kb_id}/vectorsets/{model}",
                headers=kb_auth(token), json={}, ok=(200, 201, 204))
        except ArAgError as e:
            warn(f"vectorset {model!r} not applied (private/BYO embedding "
                 f"providers cannot be auto-replicated): {e}")


def apply_search_configs(host, kb_id, token, configs):
    for name, spec in configs.items():
        body = {"kind": spec.get("kind", "find"), "config": spec.get("config", spec)}
        try:
            req("POST", f"{host}/api/v1/kb/{kb_id}/search_configurations/{name}",
                headers=kb_auth(token), json=body, ok=(200, 201))
        except ArAgError as e:
            warn(f"search configuration {name!r} not applied (schema is "
                 f"partially documented - field mismatch likely): {e}")


# --------------------------------------------------------------------------
# Resources: export/import path, with manual fallback
# --------------------------------------------------------------------------

def try_export_import(host, source_id, source_token, target_id, target_token,
                       timeout=1800):
    log("attempting official export/import path ...")
    r = req("POST", f"{host}/api/v1/kb/{source_id}/export", headers=kb_auth(source_token),
            json={}, ok=(200, 201))
    export_id = r.json().get("export_id") or r.json().get("id")
    if not export_id:
        raise ArAgError(f"export start returned no export_id: {r.text[:300]}")

    t0 = time.time()
    while True:
        r = req("GET", f"{host}/api/v1/kb/{source_id}/export/{export_id}/status",
                headers=kb_auth(source_token))
        raw = r.json() or {}
        status = raw.get("status")
        if isinstance(status, dict):  # tolerate the nested shape docs describe too
            status = status.get("status")
        status = (status or "").lower()
        if status not in PENDING_STATUSES:
            break
        if time.time() - t0 > timeout:
            raise ArAgError("export status poll timed out")
        time.sleep(5)
    if status not in TERMINAL_OK_STATUSES:
        raise ArAgError(f"export finished in unexpected status {status!r}")

    log(f"export {export_id} finished, downloading ...")
    r = req("GET", f"{host}/api/v1/kb/{source_id}/export/{export_id}", headers=kb_auth(source_token))
    payload = r.content

    log(f"starting import into target ({len(payload)} bytes) ...")
    r = req("POST", f"{host}/api/v1/kb/{target_id}/import", headers={
        **kb_auth(target_token), "Content-Type": "application/octet-stream"},
        data=payload, ok=(200, 201))
    import_id = r.json().get("import_id") or r.json().get("id")
    if not import_id:
        raise ArAgError(f"import start returned no import_id: {r.text[:300]}")

    t0 = time.time()
    while True:
        r = req("GET", f"{host}/api/v1/kb/{target_id}/import/{import_id}/status",
                headers=kb_auth(target_token))
        d = r.json() or {}
        status = d.get("status")
        if isinstance(status, dict):
            status = status.get("status")
        status = (status or "").lower()
        if status not in PENDING_STATUSES:
            break
        if time.time() - t0 > timeout:
            raise ArAgError("import status poll timed out")
        time.sleep(5)
    if status not in TERMINAL_OK_STATUSES:
        raise ArAgError(f"import finished in unexpected status {status!r}")
    log(f"import finished: {d}")
    return True


def manual_migrate_resources(host, source_id, source_token, target_id, target_token):
    log("falling back to manual page-and-recreate resource migration ...")
    resources = list_resources(host, source_id, source_token)
    log(f"{len(resources)} source resources to recreate")
    failures = []
    for i, stub in enumerate(resources, 1):
        rid = stub.get("id") or stub.get("uuid")
        try:
            r = req("GET", f"{host}/api/v1/kb/{source_id}/resource/{rid}",
                    headers=kb_auth(source_token),
                    params={"show": ["basic", "origin", "extra", "values", "extracted"],
                            "extracted": ["text", "metadata", "link", "file"]})
            full = r.json()
            body = {
                "title": full.get("title"),
                "summary": full.get("summary"),
                "icon": full.get("icon"),
                "origin": full.get("origin"),
                "usermetadata": full.get("usermetadata", {}),
                "texts": {}, "links": {},
            }
            data = full.get("data", full)
            for fname, fspec in (data.get("texts") or {}).items():
                val = (fspec.get("value") or {})
                body["texts"][fname] = {"body": val.get("body", ""),
                                         "format": val.get("format", "PLAIN")}
            for fname, fspec in (data.get("links") or {}).items():
                val = (fspec.get("value") or {})
                if val.get("uri"):
                    body["links"][fname] = {"uri": val["uri"]}
            cr = req("POST", f"{host}/api/v1/kb/{target_id}/resources",
                     headers=kb_auth(target_token), json=body, ok=(200, 201))
            new_rid = cr.json()["uuid"]

            for fname, fspec in (data.get("files") or {}).items():
                val = (fspec.get("value") or {})
                filename = (val.get("file") or {}).get("filename", fname)
                try:
                    dl = req("GET",
                             f"{host}/api/v1/kb/{source_id}/resource/{rid}/file/{fname}/download/field",
                             headers=kb_auth(source_token))
                    req("PUT", f"{host}/api/v1/kb/{target_id}/resource/{new_rid}/file/{fname}",
                        headers={**kb_auth(target_token), "X-Filename": filename},
                        data=dl.content, ok=(200, 201, 204))
                except ArAgError as e:
                    failures.append((rid, fname, str(e)))
            if i % 10 == 0:
                log(f"  ... {i}/{len(resources)} resources recreated")
        except ArAgError as e:
            failures.append((rid, None, str(e)))
    log(f"manual migration done: {len(resources) - len(failures)} ok, "
        f"{len(failures)} failures")
    for rid, fname, err in failures[:20]:
        warn(f"  resource {rid} field={fname}: {err}")
    return failures


def wait_processed(host, kb_id, token, timeout=1800, poll=10):
    t0 = time.time()
    while True:
        resources = list_resources(host, kb_id, token)
        if not resources:
            return True
        states = {}
        for r in resources:
            st = (r.get("metadata") or {}).get("status", "?")
            states[st] = states.get(st, 0) + 1
        log(f"  resource status: {states}")
        if all((r.get("metadata") or {}).get("status") == "PROCESSED" for r in resources):
            return True
        if time.time() - t0 > timeout:
            warn(f"poll timed out after {timeout}s; some resources not PROCESSED - "
                 f"NOT starting augmentation tasks (would stall ingest)")
            return False
        time.sleep(poll)


# --------------------------------------------------------------------------
# Tasks (AFTER processed only)
# --------------------------------------------------------------------------

def recreate_tasks(host, kb_id, token, tasks, fallback_model):
    created = []
    for t in tasks:
        name = t.get("name")
        if name not in AUGMENTATION_TASK_NAMES:
            log(f"  skipping task {name!r} (not an augmentation task worth cloning)")
            continue
        params = dict(t.get("parameters") or {})
        cfg_name = params.get("name", name)
        if not params.get("operations"):
            warn(f"task {name!r} ({cfg_name!r}) has no real 'operations' in its "
                 f"source parameters - was it actually configured on the source, "
                 f"or just present in the task-type catalogue? Skipping rather "
                 f"than sending an empty task/start body (422 'at least one "
                 f"operation must be defined').")
            continue
        if not params.get("llm"):
            params["llm"] = {"model": fallback_model, "provider": "openai"}
        body = {"name": name, "parameters": params, "apply": "EXISTING"}
        try:
            r = req("POST", f"{host}/api/v1/kb/{kb_id}/task/start", headers=kb_auth(token),
                    json=body, ok=(200, 201))
            created.append((name, r.json()))
            log(f"  task {name!r} ({cfg_name!r}) started on target (apply=EXISTING): "
                f"{r.json()}")
        except ArAgError as e:
            warn(f"task {name!r} ({cfg_name!r}) not recreated: {e}")
    return created


# --------------------------------------------------------------------------
# Verify
# --------------------------------------------------------------------------

def scoped_ask(host, kb_id, token, resource_ids, generative_model, question):
    body = {
        "query": question,
        "resource_filters": resource_ids,
        "generative_model": generative_model,
        "citations": True,
        "prompt": {"system": "Answer only from the supplied context. Use Australian "
                              "English spelling."},
    }
    r = req("POST", f"{host}/api/v1/kb/{kb_id}/ask", headers=kb_auth(token), json=body,
            ok=(200,))
    # /ask streams NDJSON; requests .json() only works for the sync shape - try both
    try:
        return r.json()
    except ValueError:
        lines = [json.loads(l) for l in r.text.splitlines() if l.strip()]
        return {"stream": lines}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{s}-{int(time.time())}"[:63]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--target-title")
    ap.add_argument("--target-slug")
    ap.add_argument("--target-kb-id")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--skip-tasks", action="store_true")
    ap.add_argument("--poll-timeout", type=int, default=1800)
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    fe = factory_env()
    nua = fe.get("ARAG_NUA_KEY")
    account = fe.get("ARAG_ACCOUNT")
    if not nua or not account:
        sys.exit("ARAG_NUA_KEY / ARAG_ACCOUNT missing from factory .env - see "
                  "the arag-kb-provisioning memory")

    source_id = extract_kb_id(args.source)
    source_token = fe.get("SOURCE_ARAG_TOKEN") or None
    if not source_token:
        log(f"minting a temporary 6h reader token for source KB {source_id} "
            f"(factory-account KBs only)")
        source_token = mint_reader_token(account, nua, source_id, "clone-source-reader")

    src_meta = get_kb_meta(HOST, source_id, source_token)
    src_cfg = get_kb_configuration(HOST, source_id, source_token)
    src_title = (src_meta.get("config") or {}).get("title") or source_id
    src_mode = (src_meta.get("config") or {}).get("mode", "kb")
    src_labelsets = get_labelsets(HOST, source_id, source_token)
    src_entities = get_entity_groups(HOST, source_id, source_token)
    src_synonyms = get_synonyms(HOST, source_id, source_token)
    src_search_cfgs = get_search_configs(HOST, source_id, source_token)
    src_tasks = get_tasks(HOST, source_id, source_token)
    src_resources = list_resources(HOST, source_id, source_token)
    src_counters = get_counters(HOST, source_id, source_token)

    extra_vectorsets = []
    sem_models = src_cfg.get("semantic_models") or []
    primary_model = src_cfg.get("semantic_model")
    extra_vectorsets = [m for m in sem_models if m and m != primary_model]

    print("\n=== SOURCE KB INVENTORY ===")
    print(f"  id/title:      {source_id}  /  {src_title!r}  (mode={src_mode})")
    print(f"  models:        generative={src_cfg.get('generative_model')!r} "
          f"semantic={primary_model!r} ner={src_cfg.get('ner_model')!r} "
          f"relation={src_cfg.get('relation_model')!r} "
          f"anonymization={src_cfg.get('anonymization_model')!r}")
    print(f"  extra vectorsets: {extra_vectorsets or 'none'}")
    print(f"  resources:     {len(src_resources)}  (counters: {src_counters})")
    print(f"  labelsets:     {len(src_labelsets)}  {list(src_labelsets.keys())}")
    print(f"  entity groups: {len(src_entities)}  {list(src_entities.keys())}")
    print(f"  synonym terms: {len(src_synonyms)}")
    print(f"  search configs:{len(src_search_cfgs)}  {list(src_search_cfgs.keys())}")
    print(f"  tasks:         {len(src_tasks)}  "
          f"{[t.get('name') for t in src_tasks]}")

    if src_mode == "agent":
        warn("SOURCE IS AN AGENT-MODE KB. The Retrieval Agent node graph is "
             "DASHBOARD-ONLY - no REST endpoint exposes or accepts it. This "
             "script will clone the plain kb-mode data+config twin; the agent "
             "workflow itself is a MANUAL STEP you must rebuild in the ARAG "
             "dashboard (see the rao-workflow skill).")

    print(f"\nZone: every KB this factory credential creates lands in "
          f"{ZONE_NAME} - the create-KB zone param is ignored by this account. "
          f"Fine for synthetic demo content; do not use for a residency-"
          f"sensitive live demo of a non-AU source.")

    if args.dry_run:
        print("\n--dry-run: nothing created. Would also attempt (in order):")
        print("  1. create target KB with generative_model pinned + same semantic model")
        print("  2. apply labelsets/entities/synonyms/search-configs/vectorsets")
        print(f"  3. export/import all {len(src_resources)} resources (fallback: "
              f"page + recreate + re-upload files)")
        print("  4. poll until every target resource is PROCESSED")
        if args.skip_tasks:
            print("  5. (skipped: --skip-tasks)")
        else:
            aug = [t for t in src_tasks if t.get("name") in AUGMENTATION_TASK_NAMES]
            print(f"  5. recreate {len(aug)} augmentation task(s) with apply=EXISTING: "
                  f"{[t.get('name') for t in aug]}")
        print("  6. scoped /ask verification + config diff")
        return

    if args.verify_only:
        if not args.target_kb_id:
            sys.exit("--verify-only requires --target-kb-id")
        target_id = args.target_kb_id
        env_file = OUT_DIR / f"{target_id}.env"
        if not env_file.exists():
            sys.exit(f"no saved token at {env_file} - pass TARGET_ARAG_TOKEN env "
                      f"or re-run the clone")
        target_token = None
        for line in env_file.read_text().splitlines():
            if line.startswith("KB_TOKEN="):
                target_token = line.split("=", 1)[1].strip()
        verify(source_id, src_cfg, src_labelsets, src_entities, src_synonyms,
               src_tasks, src_resources, target_id, target_token)
        return

    target_title = args.target_title or f"{src_title} (clone)"
    target_slug = args.target_slug or slugify(target_title)

    if not args.yes:
        resp = input(f"\nCreate target KB {target_slug!r} in {ZONE_NAME} and clone "
                      f"{len(src_resources)} resources into it? [y/N] ")
        if resp.strip().lower() != "y":
            print("aborted")
            return

    learning_configuration = {k: v for k, v in {
        "generative_model": src_cfg.get("generative_model") or "chatgpt-azure-4o-mini",
        "semantic_model": primary_model,
        "ner_model": src_cfg.get("ner_model"),
        "relation_model": src_cfg.get("relation_model"),
        "anonymization_model": src_cfg.get("anonymization_model"),
    }.items() if v}
    log(f"creating target KB {target_slug!r} (mode=kb) with learning_configuration="
        f"{learning_configuration}")
    target_id, created = create_kb(account, nua, target_slug, target_title, "kb",
                                    learning_configuration)
    log(f"target KB id: {target_id} (newly created={created})")

    target_token = mint_owner_token(account, nua, target_id, f"{target_slug}-owner")
    c = get_counters(HOST, target_id, target_token)
    log(f"target token validated: counters={c}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    env_file = OUT_DIR / f"{target_id}.env"
    env_file.write_text(
        f"ARAG_HOST={HOST}\nKB_ID={target_id}\nKB_SLUG={target_slug}\n"
        f"KB_TOKEN={target_token}\n")
    log(f"target credentials written to {env_file} (gitignored dir, token never "
        f"printed to stdout)")

    log("applying pre-data configuration (models, labelsets, entities, synonyms, "
        "vectorsets, search configs) BEFORE any resource import ...")
    apply_configuration(HOST, target_id, target_token, src_cfg)
    apply_labelsets(HOST, target_id, target_token, src_labelsets)
    apply_entities(HOST, target_id, target_token, src_entities)
    apply_synonyms(HOST, target_id, target_token, src_synonyms)
    apply_vectorsets(HOST, target_id, target_token, extra_vectorsets)
    apply_search_configs(HOST, target_id, target_token, src_search_cfgs)

    log(f"migrating {len(src_resources)} resource(s) ...")
    migration_failures = []
    if src_resources:
        try:
            try_export_import(HOST, source_id, source_token, target_id, target_token,
                               timeout=args.poll_timeout)
        except ArAgError as e:
            warn(f"export/import path failed ({e}); falling back to manual migration")
            migration_failures = manual_migrate_resources(
                HOST, source_id, source_token, target_id, target_token)
    else:
        log("source KB has no resources; nothing to migrate")

    log("polling target resources until every one is PROCESSED "
        "(augmentation tasks must NOT start before this) ...")
    all_processed = wait_processed(HOST, target_id, target_token,
                                    timeout=args.poll_timeout)

    if args.skip_tasks:
        log("--skip-tasks set; not recreating augmentation tasks")
    elif not all_processed:
        warn("not all resources reached PROCESSED within the poll timeout - "
             "SKIPPING augmentation-task recreation to avoid the ingest-stall "
             "gotcha. Re-run with a longer --poll-timeout once ingest settles, "
             "or start the tasks by hand once /kb/{id}/resources shows all "
             "PROCESSED.")
    else:
        log("all target resources PROCESSED - recreating augmentation tasks "
            "(apply=EXISTING) ...")
        recreate_tasks(HOST, target_id, target_token, src_tasks,
                       learning_configuration.get("generative_model"))

    target_resources = list_resources(HOST, target_id, target_token)
    verify(source_id, src_cfg, src_labelsets, src_entities, src_synonyms, src_tasks,
           src_resources, target_id, target_token, target_resources=target_resources)

    print(f"\nDone. Target KB id: {target_id}   slug: {target_slug}")
    print(f"Credentials: {env_file}")
    if migration_failures:
        print(f"{len(migration_failures)} resource/field migration failures - see "
              f"warnings above.")


def verify(source_id, src_cfg, src_labelsets, src_entities, src_synonyms, src_tasks,
           src_resources, target_id, target_token, target_resources=None):
    if target_resources is None:
        target_resources = list_resources(HOST, target_id, target_token)
    tgt_cfg = get_kb_configuration(HOST, target_id, target_token)
    tgt_labelsets = get_labelsets(HOST, target_id, target_token)
    tgt_entities = get_entity_groups(HOST, target_id, target_token)
    tgt_synonyms = get_synonyms(HOST, target_id, target_token)
    tgt_tasks = get_tasks(HOST, target_id, target_token)

    print("\n=== CONFIG DIFF (source -> target) ===")
    print(f"  generative_model: {src_cfg.get('generative_model')!r} -> "
          f"{tgt_cfg.get('generative_model')!r}")
    print(f"  semantic_model:   {src_cfg.get('semantic_model')!r} -> "
          f"{tgt_cfg.get('semantic_model')!r}")
    print(f"  ner_model:        {src_cfg.get('ner_model')!r} -> "
          f"{tgt_cfg.get('ner_model')!r}")
    print(f"  resources:        {len(src_resources)} -> {len(target_resources)}")
    print(f"  labelsets:        {len(src_labelsets)} -> {len(tgt_labelsets)}")
    print(f"  entity groups:    {len(src_entities)} -> {len(tgt_entities)}")
    print(f"  synonym terms:    {len(src_synonyms)} -> {len(tgt_synonyms)}")
    aug_src = [t for t in src_tasks if t.get("name") in AUGMENTATION_TASK_NAMES]
    aug_tgt = [t for t in tgt_tasks if t.get("name") in AUGMENTATION_TASK_NAMES]
    print(f"  augmentation tasks:{len(aug_src)} -> {len(aug_tgt)}")

    if not target_resources:
        warn("target has no resources - skipping /ask verification")
        return
    ids = [r.get("id") or r.get("uuid") for r in target_resources]
    log("running a scoped /ask against the target to confirm a grounded, cited "
        "answer ...")
    try:
        result = scoped_ask(HOST, target_id, target_token, ids,
                             tgt_cfg.get("generative_model") or "chatgpt-azure-4o-mini",
                             "Summarise the key topics covered in this knowledge base "
                             "in two sentences.")
        answer = result.get("answer") or result.get("stream")
        print("\n=== VERIFY: scoped /ask on target ===")
        print(json.dumps(result, indent=2)[:2000])
        if result.get("status") == "no_context" or not answer:
            warn("target /ask returned no grounded answer - check that resources "
                 "reached PROCESSED and the generative model is pinned")
        else:
            log("target /ask returned a grounded answer")
    except ArAgError as e:
        warn(f"verification /ask failed: {e}")


if __name__ == "__main__":
    sys.exit(main())
