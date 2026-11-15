"""Print the provenance block for a site's APPROVED export, by script, with the source it read named in the same block.

    SS_ACCESS_KEY=... python server/scripts/provenance_block.py --api https://your-app.fly.dev --site <id>

Population: the approved export only (records the reviewer approved), not every proposal. Rows are compared with the property occurrences
counted in the exported JSON-LD itself, at every depth, excluding @context. Exits non-zero if rows and occurrences differ or any row is not_recorded.
"""
import argparse, collections, hashlib, json, os, sys, time
import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--api", default="https://your-app.fly.dev")
ap.add_argument("--site", required=True)
a = ap.parse_args()
c = httpx.Client(timeout=120, headers={"X-SemanticSite-Key": os.environ.get("SS_ACCESS_KEY", "")})
st = c.get(f"{a.api}/api/sites/{a.site}").json()
ex_raw = c.get(f"{a.api}/api/sites/{a.site}/export").content
pv_raw = c.get(f"{a.api}/api/sites/{a.site}/export/provenance").content
ex, pv = json.loads(ex_raw), json.loads(pv_raw)


def occ(x):
    n = 0
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "@context":
                continue
            n += 1
            for it in (v if isinstance(v, list) else [v]):
                if isinstance(it, dict) and set(it) != {"@id"}:
                    n += occ(it)
    return n


occurrences = 0
for rec in ex["records"]:
    d = rec["jsonld"]
    occurrences += sum(occ(n) for n in (d.get("@graph", [d]) if isinstance(d, dict) else d))
rows = [r for r in pv["rows"] if r["provenance"] != "removed by reviewer"]
kinds = collections.Counter(r["provenance"] for r in rows)
print("SOURCE  site", a.site, st["root_url"], "| run finished", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st["finished_at"])))
print("        export sha256", hashlib.sha256(ex_raw).hexdigest()[:16], "| provenance sha256", hashlib.sha256(pv_raw).hexdigest()[:16])
print(f"POPULATION  approved export, {ex['record_count']} pages ({len(ex['excluded'])} excluded at export)")
print(f"RESULT  {len(rows)} provenance rows for {occurrences} property occurrences in the exported JSON-LD (rows are per occurrence, at every depth)")
print("SPLIT   " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + f"  | inherited from a parent property: {sum(1 for r in rows if r['inherited_from_parent'])}")
print("DEFINITION  an occurrence is one key in the JSON-LD at any depth, excluding @context. A bare reference value {\"@id\": ...} is NOT counted as its own occurrence:")
print("            it is covered by the row of the property that holds it. A record with N references therefore has N more JSON keys than rows if references were counted.")
print("NOTE    not a comparison with any figure computed over every proposal; that is a different population")
bad = []
if len(rows) != occurrences:
    bad.append(f"rows {len(rows)} != occurrences {occurrences}")
if kinds.get("not_recorded"):
    bad.append(f"{kinds['not_recorded']} rows are not_recorded")
if not ex["record_count"]:
    bad.append("no approved records: zero of zero is not a pass")
print("VERDICT", "FAIL: " + "; ".join(bad) if bad else "PASS")
sys.exit(1 if bad else 0)
