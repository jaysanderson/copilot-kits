# Corpus provenance

`data/corpus/*.md` is a direct export of the live, reconciled Knowledge Box
(21 resources — see the build report for the reconciliation history: an
earlier generator script produced a different, contradictory version of the
same documents during a same-session duplicate-agent collision on 17 Aug
2026, which was caught, root-caused as a within-session artifact rather than
a genuine external actor, and reconciled by treating the live KB as
canonical and pulling it back to disk).

To regenerate this export after any live KB edit:

```
node -e "<pull-to-disk script — see build report / git history commit
'Reconcile local corpus with the live, internally-consistent KB'>"
```

Do not hand-edit `data/corpus/*.md` without also updating the live KB (or
vice versa) — the two must stay in lockstep, since `scripts/provision.mjs
--purge` followed by re-ingest treats this directory as the source of truth.
