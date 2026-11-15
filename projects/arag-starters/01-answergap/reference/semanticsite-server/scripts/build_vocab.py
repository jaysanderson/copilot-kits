"""Compile the official Schema.org vocabulary (schemaorg-current-https.jsonld) into a
compact lookup used by the validator. Run once; commit the output, not the 1.5MB source.

    python server/scripts/build_vocab.py path/to/schemaorg-current-https.jsonld
"""
import json
import sys
from pathlib import Path

src = json.loads(Path(sys.argv[1]).read_text())
OUT = Path(__file__).resolve().parent.parent / "data" / "schemaorg.min.json"


def short(i):
    return i.replace("schema:", "") if isinstance(i, str) and i.startswith("schema:") else None


def ids(v):
    if v is None:
        return []
    v = v if isinstance(v, list) else [v]
    return [short(x.get("@id")) for x in v if isinstance(x, dict) and short(x.get("@id"))]


types, props = {}, {}
for n in src["@graph"]:
    t = n.get("@type")
    t = t if isinstance(t, list) else [t]
    nid = short(n.get("@id"))
    if not nid:
        continue
    if "rdfs:Class" in t:
        types[nid] = {"sub": ids(n.get("rdfs:subClassOf"))}
    elif "rdf:Property" in t:
        props[nid] = {"dom": ids(n.get("schema:domainIncludes")), "rng": ids(n.get("schema:rangeIncludes"))}
OUT.write_text(json.dumps({"source": "schema.org schemaorg-current-https.jsonld", "types": types, "props": props},
                          separators=(",", ":")))
print(len(types), "types", len(props), "properties ->", OUT, OUT.stat().st_size, "bytes")
