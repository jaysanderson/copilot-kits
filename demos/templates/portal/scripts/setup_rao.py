#!/usr/bin/env python3
# setup_rao.py - stand up the Progress Agentic RAG Retrieval Agent (RAO) for the
# Publisher Claims Copilot, per the rao-workflow skill. Creates a mode:"agent" KB,
# wires an MCP context node -> a Smart Agent -> a Summarize node, all via the PAT
# on the dp host, and writes ARAG_AGENT_KB_ID back to .env.
#
# Direct port of the proven sibling support-co-support/scripts/setup_rao.py, with
# Publisher's own MCP url, tools and claims-desk grounding prompt. The PAT
# (ARAG_AGENT_KEY) is the same account-level credential Support-co's working agent
# uses, so registration succeeds the same way.
#
# Reads .env: ARAG_AGENT_KEY (PAT), NUCLIA_NUA_KEY, NUCLIA_ACCOUNT, NUCLIA_ZONE.
#   python3 scripts/setup_rao.py
import re, json, os, sys, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(__file__), "..")
ENV = os.path.join(ROOT, ".env")
MCP_URL = "https://your-app.fly.dev/mcp"
# Standard B26 (GM review, 18 Aug 2026): search_claim_documents is the
# UNSTRUCTURED knowledge-box retrieval source the agent blends with the three
# structured live-data tools - so one answer grounds on live systems AND the
# policy/claim documents, and the UI shows both.
TOOLS = ["get_policy_status", "get_claimant_history", "get_claim", "search_claim_documents"]

def env():
    d = {}
    for l in open(ENV):
        m = re.match(r'^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$', l.rstrip("\n"))
        if m: d[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return d

def write_env(k, v):
    t = open(ENV).read()
    if re.search(rf'^{k}=.*$', t, re.M): t = re.sub(rf'^{k}=.*$', f'{k}={v}', t, flags=re.M)
    else: t = t.rstrip("\n") + f"\n{k}={v}\n"
    open(ENV, "w").write(t)

e = env()
PAT = e.get("ARAG_AGENT_KEY", "")
NUA = e.get("NUCLIA_NUA_KEY", "")
ACC = e["NUCLIA_ACCOUNT"]; ZONE = e["NUCLIA_ZONE"]
if not PAT:
    print("No ARAG_AGENT_KEY (PAT) in .env - RAO stays in disclosed-gap mode."); sys.exit(2)
RAG = f"https://{ZONE}.rag.progress.cloud/api/v1"
DP = f"https://{ZONE}.dp.progress.cloud/api/v1"

def call(url, method="GET", body=None, bearer=PAT):
    req = urllib.request.Request(url, method=method,
        headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        txt = r.read().decode()
        try: return r.status, json.loads(txt)
        except: return r.status, txt
    except urllib.error.HTTPError as ex:
        b = ex.read().decode()
        try: return ex.code, json.loads(b)
        except: return ex.code, b

# 1) agent KB (reuse if already set)
agent_id = e.get("ARAG_AGENT_KB_ID", "")
if not agent_id:
    st, r = call(f"{RAG}/account/{ACC}/kbs", "POST",
        {"title": "Publisher Claims Agent", "slug": "publisher-claims-agent", "zone": ZONE, "mode": "agent"},
        bearer=NUA or PAT)
    if st >= 400 and "exists" not in str(r).lower():
        print("agent KB create failed:", st, str(r)[:300]); sys.exit(1)
    agent_id = (r.get("id") or r.get("uuid")) if isinstance(r, dict) else None
    if not agent_id:
        # maybe exists; list and find by slug
        st2, kbs = call(f"{RAG}/account/{ACC}/kbs", bearer=NUA or PAT)
        for kb in (kbs if isinstance(kbs, list) else []):
            if kb.get("slug") == "publisher-claims-agent": agent_id = kb.get("id")
    if not agent_id: print("no agent id"); sys.exit(1)
    print("agent KB:", agent_id)
    write_env("ARAG_AGENT_KB_ID", agent_id)
else:
    print("reusing agent KB:", agent_id)

A = f"{DP}/agent/{agent_id}"

# NOTE (18 Aug 2026): GET /agent/{id}/context/{node_id} (single-node by id) 500s on
# this deployment, so we source each node's FULL object from the LIST endpoint
# (GET .../context and .../generation both return 200) rather than a GET-by-id.
def get_node(kind, module):
    st, lst = call(f"{A}/{kind}")
    items = lst if isinstance(lst, list) else (lst.get("items") if isinstance(lst, dict) else [])
    return next((x for x in items if x.get("module") == module), None)

# 2) MCP driver. Shape confirmed from the working compliance-co/support-co agents: each
# driver from GET is wrapped as {config: {identifier, name, provider, config:{uri,...}}};
# POST needs identifier + name + provider + a nested config.
def driver_cfg(d):
    return d.get("config", d) if isinstance(d, dict) else {}
st, drivers = call(f"{A}/drivers")
dlist = drivers if isinstance(drivers, list) else []
drv = next((driver_cfg(d) for d in dlist if driver_cfg(d).get("provider") == "mcphttp" and (driver_cfg(d).get("config") or {}).get("uri") == MCP_URL), None)
if not drv:
    st, r = call(f"{A}/drivers", "POST", {
        "identifier": "publisher-mcp", "name": "publisher-mcp", "provider": "mcphttp",
        "config": {"uri": MCP_URL, "timeout": 30, "sse_read_timeout": 300, "scope": "user", "pkce": True},
    })
    print("create driver:", st, str(r)[:200])
    st, drivers = call(f"{A}/drivers")
    dlist = drivers if isinstance(drivers, list) else []
    drv = next((driver_cfg(d) for d in dlist if (driver_cfg(d).get("config") or {}).get("uri") == MCP_URL), None)
drv_ident = drv.get("identifier") if drv else None
print("driver identifier:", drv_ident)
if not drv_ident: print("no driver identifier"); sys.exit(1)

# 3) MCP context node
st, ctxs = call(f"{A}/context")
ctx_list = ctxs if isinstance(ctxs, list) else (ctxs.get("items") if isinstance(ctxs, dict) else [])
mcp_node = next((c for c in ctx_list if c.get("module") == "mcp"), None)
if not mcp_node:
    st, r = call(f"{A}/context", "POST", {"module": "mcp", "source": drv_ident})
    print("create mcp node:", st, str(r)[:200])
    mcp_id = r.get("id") if isinstance(r, dict) else None
else:
    mcp_id = mcp_node.get("id")
print("mcp node id:", mcp_id)
# Pull the full node object from the list (GET-by-id 500s here) and patch it with
# HTTP transport + forwarded auth + published functions.
mcp_full = get_node("context", "mcp")
if isinstance(mcp_full, dict):
    mcp_full["transport"] = "HTTP"
    mcp_full["valid_headers"] = ["authorization"]
    mcp_full["published_functions"] = TOOLS
    if not mcp_full.get("description"): mcp_full["description"] = "Publisher policy, claimant-history and claim record lookups over the insurer's live systems."
    st, r = call(f"{A}/context/{mcp_id}", "PATCH", mcp_full)
    print("patch mcp node:", st, str(r)[:120])

# 4) Smart Agent node (reuse or create) - re-list, the mcp create/patch may have changed state
st, ctxs = call(f"{A}/context")
ctx_list = ctxs if isinstance(ctxs, list) else (ctxs.get("items") if isinstance(ctxs, dict) else [])
smart = next((c for c in ctx_list if c.get("module") == "smart"), None)
if not smart:
    st, r = call(f"{A}/context", "POST", {"module": "smart", "planning_mode": "reactive", "max_iterations": 5})
    print("create smart:", st, str(r)[:200]); smart_id = r.get("id") if isinstance(r, dict) else None
else:
    smart_id = smart.get("id")
print("smart id:", smart_id)

# 5) register MCP node under Smart Agent (full nested object shape - the resolved fix)
mcp_obj = get_node("context", "mcp")
smart_full = get_node("context", "smart")
if isinstance(smart_full, dict) and isinstance(mcp_obj, dict):
    smart_full["registered_agents"] = [mcp_obj]
    smart_full["registered_agents_descriptions"] = {mcp_id: "queries live Publisher policy, claimant-history and claim records"}
    smart_full["registered_agents_exposed_functions"] = {mcp_id: TOOLS}
    st, r = call(f"{A}/context/{smart_id}", "PATCH", smart_full)
    print("register mcp under smart:", st, ("OK" if st < 400 else str(r)[:300]))

# 6) Summarize generation node
st, gens = call(f"{A}/generation")
gen_list = gens if isinstance(gens, list) else (gens.get("items") if isinstance(gens, dict) else [])
summ = next((g for g in gen_list if g.get("module") == "summarize"), None)
if not summ:
    st, r = call(f"{A}/generation", "POST", {"module": "summarize"})
    print("create summarize:", st, str(r)[:150]); summ_id = r.get("id") if isinstance(r, dict) else None
else:
    summ_id = summ.get("id")
if summ_id:
    sf = get_node("generation", "summarize")
    if isinstance(sf, dict):
        sf["system_prompt"] = (
            "You answer questions about SPECIFIC claims and policies for a Publisher Mutual claims handler, using ONLY the data the tools returned. "
            "A specific claim's or policy's outcome - payable, not payable, covered, excluded, in force, in arrears - may ONLY be stated when get_claim or "
            "get_policy_status UNIQUELY resolved that exact record by its identifier (found:true). Always cite the record by its claim or policy number. "
            "The document-search tool returns general policy WORDING only, never a specific claim's status; use it to quote the governing clause once a specific "
            "record is resolved, and never treat a wording passage as a particular claim's outcome. "
            "If the request does not name a specific claim or policy (e.g. 'the motor claim', 'a flood claim') and no record was uniquely resolved, do NOT state an "
            "outcome. Instead reply like a helpful claims handler who needs the identifier, for example: 'I can look that up - which claim do you mean? Give me the "
            "claim number (e.g. CLM-2026-0466) or the policyholder's name and I will check its status and the wording that applies.' Never reply with a bare "
            "'not enough data'. "
            "If a lookup returned an ambiguous result (found:false, ambiguous:true, with candidates), do NOT pick one - say the request matches several records, list "
            "the candidates by their identifiers, and ask which one is meant. "
            "If a lookup failed or returned nothing, say you could not determine it. "
            "Behave like a competent claims handler who never guesses which record was meant and never asserts a status not verified from a resolved record.")
        if not sf.get("description"): sf["description"] = "Compose a grounded answer from the claims-desk tool results."
        st, r = call(f"{A}/generation/{summ_id}", "PATCH", sf)
        print("patch summarize:", st, ("OK" if st < 400 else str(r)[:200]))

print("\nRAO setup complete. Verify with a live /session/ephemeral call.")
