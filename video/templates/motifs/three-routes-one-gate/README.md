# Motif: three routes, one gate (`m-tr`)

Five phases over ONE unmoving layout: the three product objects hold position throughout,
which is what makes the act read as a single argument rather than five diagrams. Performs
the tenancy argument: a request for one tenant touches another, each of the three products
answers it by a different route, and all three routes put the gate in the ISV's code.

**When to use:** any tenancy or multi-tenant isolation beat. It is the longest motif in
the library and it is deliberately so - this is the thing an architect gets asked.

## Phases

| Phase | Window | What it performs |
|---|---|---|
| `/ask` | 0.00-7.14 | one estate, two tenant compartments, a request for A that CONTINUES past the wall into B and lifts one of B's documents |
| `/arag` | 7.14-20.23 | a filter gate that works, then whose stroke is simply NOT THERE, and the whole corpus flows through it into an answer carrying BOTH tenant letters |
| `/domo` | 20.23-25.81 | an embed token passing THROUGH the ISV's own amber block, which stamps it |
| `/openedge` | 25.81-32.05 | a lettered token replaced at the boundary by an unlettered badge, the letter dropping away, and the filtering reappearing as an amber gate inside the ISV's own band |
| `/verdict` | 31.03-34.77 | all three gates turning amber at the same instant, the only lit things on the stage |
| `/stronger` | 34.77-50.00 | the one estate drawn whole, then three GREEN platform-enforced boundaries landing one per spoken name, then the estate SPLITTING into three shards |

## `/stronger` is the scope, and without it `/verdict` is false

`primer.md:43` now reads "On the routes an ISV would actually use to run many customers on
one estate, all three put tenant enforcement in your code". It was unscoped, and unscoped
it is false, because **each product does have an option where the platform enforces the
boundary**: a knowledge base per tenant, a Domo environment per customer, OpenEdge
multi-tenant tables.

So `/stronger` exists to stop `/verdict` reading as "nothing can enforce it". **Its three
boundaries are GREEN - the only green gates in the whole act** - because the platform
really does enforce them, and the grammar's rule 3 would be lying if they were amber.

**What they cost is DRAWN, not said:** the single estate underneath them is shown whole,
then splits into three shards that drift apart and never settle. No price appears, because
we do not have one and the primer says so.

A host whose narration carries only the scoped verdict and not the options can run
`/ask` through `/verdict` and stop. A host that states the absolute must run `/stronger`
too, or it ships the unscoped claim.

## Three things in here are the argument, not decoration

**The `/arag` break is SILENT.** Nothing turns red and nothing stops. The gate's middle
segment goes to `autoAlpha: 0` and the corpus keeps flowing, because a red error state
would misrepresent the behaviour: a malformed filter does not refuse, it behaves as no
filter at all. **Never restyle this as an error.**

**Both tenant letters land in one answer card.** Every document carries its own tenant
letter, so the disclosure is shown rather than named. If you re-time this phase, keep the
`Tenant A` and `Tenant B` chips both visible.

**The dropped letter in `/openedge` is the shot.** A lettered token is replaced by an
unlettered badge at the application-server boundary and the letter it carried falls away.
Nobody has to be told the platform cannot tell the callers apart.

## Grammar

Uses rule 3 (green is the platform's, amber is the ISV's own code) and rule 4 (a gate is a
gap in a boundary with a token through it; an open gate has a visibly BROKEN stroke). The
`/verdict` phase is the pay-off of rule 3 and the reason amber is reserved from the first
shot of a film. Full grammar: `videos/_motifs/GRAMMAR.md`.

**Variables:** `trTenantA`, `trTenantB` (compartment labels, defaults Tenant A / Tenant B),
`trLabel0..trLabel2` (product names, defaults OpenEdge / Progress Agentic RAG / Domo),
`trFilter` (default "filter expression"), `trNoFilter` (default "no filter at all"),
`trServer` (default "Your server"), `trAssertion` (default "Your assertion"),
`trToolLayer` (default "Your tool layer"), `trServiceAcct` (default "Service account"),
`trVerdict` (default "Three routes"), `trStrong0..trStrong2` (the three
platform-enforced options, defaults "Knowledge base per tenant" / "Domo environment
per customer" / "OpenEdge multi-tenant tables"), `trOneEstate` (default "One estate").

**On `trStrong0`:** the product's own container term is on the sa-use-cases
must-not-appear list, so the default says "knowledge base". The beat's point is
one-per-tenant, not what the container is called. A host with a different vocabulary
policy can bind it.

**Timing:** internal timeline 50.4s. Event constants at the top of the script: `AT_ASK`
0.50, `AT_CUST_A` 4.88, `AT_CUST_B` 6.08, `AT_SCOPE` 7.77, `AT_MALFORM` 12.00, `AT_NOFILT`
15.62, `AT_EVERY` 17.01, `AT_DOMO` 19.09, `AT_SIGNS` 21.22, `AT_ASSERT` 23.49, `AT_OE`
24.77, `AT_SVCACCT` 26.23, `AT_TOOLLYR` 29.81, `AT_ROUTES` 31.03, `AT_YOURS` 33.28, `AT_STRONGER` 34.77,
`AT_ENFORCES` 37.52, `AT_KB` 39.58, `AT_DOMOENV` 41.94, `AT_OEMT` 45.03, `AT_ESTATE`
48.08. These are the `sa-use-cases` b3 word events rebased to motif zero, re-derived
9 Oct 2026 after that line was re-recorded to carry the scope. **Re-derive from the host's
own narration alignment when reusing** - each route must land on its own spoken product
name.

A host may run any contiguous subset of phases; the ids are stable.

Host slot id `m-tr`. Fonts: expects `ProgDisplay` / `ProgText` in the host.

**Gated by:** the `sa-use-cases` render (shots B3, B3b, B3c, B3d, B3e, B3f). All six phases are
rendered there (shot B3f runs `/stronger`).

## Phases

<!-- PHASES:BEGIN (generated by gen_phase_tables.py - do not hand-edit) -->

| Phase | Window | Notes |
|---|---|---|
| `/ask` | 0.00-7.14 | the question: a request for A touches B |
| `/arag` | 7.14-20.23 | a malformed filter behaves as no filter at all |
| `/domo` | 20.23-25.81 | your own server signs the filter |
| `/openedge` | 25.81-32.05 | a service account carries the call |
| `/verdict` | 31.03-34.77 | three routes, one owner |
| `/stronger` | 34.77-50.00 | the platform-enforced option, and what it costs |

Internal timeline **50.4s**. The last phase may end before the declared duration; a host plays the window it needs.

Event constants, read from the composition:

- `AT_ASK` 0.5  -  "Tenancy is the one you will be asked about"
- `AT_CUST_A` 4.63  -  "customer A"
- `AT_CUST_B` 5.67  -  "touches customer B"
- `AT_SCOPE` 7.21  -  "Scope Progress Agentic RAG"
- `AT_MALFORM` 12.0  -  "malformed filter"
- `AT_NOFILT` 15.51  -  "no filter at all"
- `AT_EVERY` 16.73  -  "Every document comes back"
- `AT_DOMO` 19.42  -  "Domo signs the filter on your own server"
- `AT_OE` 22.15  -  "OpenEdge carries the call"
- `AT_SVCACCT` 24.07  -  "service account"
- `AT_ROUTES` 25.11  -  "Three routes"
- `AT_YOURS` 27.18  -  "at scale the gate is yours"
- `AT_STRONGER` 28.56  -  "Each product has a stronger option"
- `AT_ENFORCES` 31.6  -  "where the platform enforces it"
- `AT_KB` 33.74  -  "a knowledge base per tenant"
- `AT_DOMOENV` 35.62  -  "a Domo environment per customer"
- `AT_OEMT` 38.47  -  "OpenEdge multi-tenant tables"
- `AT_ESTATE` 41.76  -  "costs you the single estate you wanted"

*Generated from the composition's own phase comments and `AT_` constants. A README that describes timings drifts on the next re-time; this one cannot.*

<!-- PHASES:END -->
