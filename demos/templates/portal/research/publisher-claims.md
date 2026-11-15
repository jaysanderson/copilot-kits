# Vertical research - general insurance claims handling (Publisher Mutual Claims Desk)

Pre-build research (arag-demo-app Standard B5/B17) for the Publisher Mutual Claims Desk
demo. Publisher Mutual is a fictional Australian general insurer writing home, motor and
small commercial property. The vehicle is a claims handler's workbench; the product being
sold is Progress Agentic RAG.

## Real terminology (used verbatim in the seeded corpus)
- **FNOL (First Notice of Loss)** - the claim form a policyholder lodges: date of loss,
  description, estimate, supporting evidence.
- **PDS / policy wording** - the Product Disclosure Statement setting covered perils,
  exclusions, sub-limits and conditions.
- **Policy schedule** - the per-policyholder record of what cover, sums insured, excess,
  endorsements and options were actually selected. Where the wording and schedule differ,
  the schedule prevails.
- **Peril** - the insured event (fire, storm, flood, water damage, collision, theft,
  burglary, windscreen, impact).
- **Excess** - the policyholder's contribution per claim, deducted before payment.
- **Sub-limit** - a cap on a category of loss regardless of the overall sum insured
  (unspecified single-item contents limit; business-interruption sub-limit).
- **Endorsement** - a variation to standard cover (e.g. a Glass Excess Waiver = nil
  windscreen excess).
- **Exclusion** - a loss the policy does not cover (flood where flood cover not selected;
  gradual deterioration; lack of maintenance).
- **Duty of disclosure**, **subrogation**, **indemnity vs replacement**, **cash settlement**,
  **loss adjuster / assessor** - standard general-insurance mechanics.

## The real claims workflow
Lodgement (FNOL) -> triage (identify policy, record peril, route) -> assessment (gather the
schedule, the wording, third-party reports, photos) -> coverage determination (peril
covered? exclusion? within sums insured and sub-limits? conditions met?) -> decision /
settlement (payable / not payable / needs-more-info; settle by repair, replacement or cash).
Timeframes are aligned to a General Insurance Code of Practice style: acknowledge within one
business day, decide within four months, update at least every twenty business days.

## Document types (the seeded corpus mirrors these)
Product Disclosure Statement / wording; policy schedule; FNOL claim form; adjuster / assessor
report; coverage decision letter; claims handling manual; claims integrity-indicators
reference. Plus third-party evidence referenced in reports (plumber, repairer, police event
reference, fire brigade report, building inspector, hydrology note).

## Roles
Claims Adjuster, Senior Claims Adjuster, Motor Claims Assessor, Property Claims Adjuster,
Claims Team Lead. Policyholders (personal and commercial). Handlers are shown name + role;
claimants name + "Policyholder" (Standard B14).

## Edge cases seeded (each grounds a use case)
- **Flood not selected** - riverine flood, optional flood cover not on the schedule -> not
  payable (the coverage-decision teaching case).
- **Gradual vs sudden water damage** - a slow leak found in a renovation is gradual
  (excluded) vs a burst flexible hose which is sudden and accidental (covered).
- **Premium in arrears at date of loss** - motor theft where the policy was in arrears ->
  cover may be reduced or refused (an integrity exception).
- **Date-of-loss mismatch** - FNOL date vs police report date differ -> integrity exception.
- **Over sub-limit specified item** - an unlisted diamond ring capped at the $2,500
  unspecified single-item sub-limit -> partial payment.
- **Glass Excess Waiver** - nil windscreen excess where the endorsement is held.

## The six use cases (genuinely diverse, one flagship each)
1. Claim intake - document extraction of a submitted claim into structured fields
   (generative UI via query-time `answer_json_schema`).
2. Coverage Q&A - grounded, cited answer from the policy wording; the citation navigates to
   the source document.
3. Coverage decision - payable / not payable / needs-more-info with cited reasons + a REMi
   trust score.
4. Exception / integrity check - inconsistencies across the claim and policy, each cited.
5. Claims portfolio dashboard - volumes, cycle time, status mix and peril breakdown as
   charts.
6. Claims Copilot - ARAG's own Retrieval Agent over the app's live policy / claimant-history /
   claim-record tools via MCP.

**Voice deliberately out of scope** (Standard B16/B17): a claims desk is a document- and
decision-heavy workflow, not a call centre. A voice use case would be a thin add here; the
six above are the genuinely high-value set for this vertical. (A call-analysis demo is the
right home for the voice/call flagship, not a claims workbench.)
