#!/usr/bin/env python3
"""Generate the synthetic Coppermill Motor Group corpus for the Ignition DMS demo.

Fictional dealer group, fictional stock, fictional people. Real automotive DMS
document types and realistic domain language (B5 research discipline applied to
the vertical rather than a named company). Every document is disclosed synthetic
in the app footer, not in the corpus itself (the corpus should read like real
dealer records). No em dashes (hard rule 2) - use " - ".
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "corpus")
os.makedirs(OUT, exist_ok=True)

SITES = ["Riverside", "Northgate"]

STOCK = [
    dict(no="CM-5102", year=2023, make="Toyota", model="RAV4 GXL", body="SUV", site="Riverside",
         colour="Silver Sky", odo=4200),
    dict(no="CM-5118", year=2022, make="Ford", model="Ranger XLT", body="Ute", site="Northgate",
         colour="Meteor Grey", odo=18900),
    dict(no="CM-5124", year=2023, make="Mazda", model="CX-5 Touring", body="SUV", site="Riverside",
         colour="Soul Red Crystal", odo=6100),
    dict(no="CM-5137", year=2021, make="Hyundai", model="i30 Active", body="Hatch", site="Northgate",
         colour="Phantom Black", odo=31200),
    dict(no="CM-5145", year=2023, make="Isuzu", model="D-Max SX", body="Ute", site="Riverside",
         colour="Splash White", odo=9800),
    dict(no="CM-5150", year=2022, make="Kia", model="Sportage SX", body="SUV", site="Northgate",
         colour="Gravity Blue", odo=22400),
    dict(no="CM-5163", year=2023, make="Yamaha", model="MT-07", body="Motorcycle", site="Riverside",
         colour="Icon Blue", odo=1400),
    dict(no="CM-5171", year=2021, make="Subaru", model="Outback Sport", body="Wagon", site="Northgate",
         colour="Autumn Green", odo=28700),
    dict(no="CM-5184", year=2023, make="Toyota", model="HiLux SR5", body="Ute", site="Riverside",
         colour="Feverish Red", odo=5300),
    dict(no="CM-5192", year=2022, make="Honda", model="CR-V VTi-L", body="SUV", site="Northgate",
         colour="Platinum White", odo=17600),
    dict(no="CM-5205", year=2023, make="Suzuki", model="Swift GL+", body="Hatch", site="Riverside",
         colour="Speedy Blue", odo=2100),
    dict(no="CM-5213", year=2021, make="Ford", model="Everest Trend", body="SUV", site="Northgate",
         colour="Arctic White", odo=33900),
    dict(no="CM-5226", year=2023, make="Kawasaki", model="Ninja 650", body="Motorcycle", site="Riverside",
         colour="Lime Green", odo=800),
    dict(no="CM-5234", year=2022, make="Mitsubishi", model="Triton GLS", body="Ute", site="Northgate",
         colour="Graphite Grey", odo=20100),
]

CONSULTANTS = [
    ("Marcus Deng", "Recon Consultant"),
    ("Aroha Ngata", "Recon Consultant"),
    ("Liam Fitzgerald", "Recon Consultant"),
    ("Priya Balan", "Dealer Principal"),
    ("Josh Carrow", "Sales Consultant"),
    ("Renee Okafor", "Sales Consultant"),
]

def write(name, body):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write(body.strip() + "\n")
    return path

docs = []  # (filename, title, doc_type, tags)

# ---------------------------------------------------------------- recon manuals
RECON_MANUALS = [
    ("recon-manual-full-detail-paint-correction.md",
     "Recon Manual - Full Detail and Paint Correction Standard",
     """# Recon Manual - Full Detail and Paint Correction Standard

Applies to every retail-bound vehicle at Coppermill Motor Group, both sites.

## Scope
Full detail and paint correction is mandatory before a vehicle is listed for retail
sale, regardless of trade-in condition. It is a separate sign-off from the
Pre-Delivery Inspection (PDI) and must be logged on its own line in the recon
history.

## Standard procedure
1. Pre-wash and decontamination wash (iron fallout remover, clay bar where
   surface contamination is felt after the first wash).
2. Paint inspection under raking light - log every panel with visible swirl
   marks, RIDS (random isolated deep scratches), or clear-coat fade.
3. Machine polish, two-stage minimum on any panel scoring below 7/10 on the
   recon consultant's visual grade; single-stage on panels scoring 7 or above.
4. Sealant or ceramic top coat (site manager's call based on retail price
   point - vehicles listed above $35,000 get the ceramic top coat as standard).
5. Interior detail - steam clean carpets and seats, full trim wipe-down,
   odour treatment if the vehicle carried a smoking or pet disclosure at
   trade-in.
6. Engine bay detail and a final photography pass for the online listing.

## Fail conditions - do not proceed to listing
- Any panel with exposed primer or bare metal after polishing (escalate to
  the site's approved panel shop, not resolvable by detailing alone).
- Persistent odour after two treatment passes - escalate to the site manager
  for a trim replacement quote before listing.
- Paint depth reading below 80 microns on any panel (log with a paint
  thickness gauge reading; a reading below this threshold indicates prior
  repaint history that must be disclosed to the buyer under the consumer
  guarantee policy).

## Sign-off
The recon consultant who performs the detail logs their name, the date, and
the paint grade (1-10) achieved. A second consultant must countersign any
vehicle listed above $40,000 before it proceeds to PDI.
"""),
    ("recon-manual-windscreen-adas-calibration.md",
     "Recon Manual - Windscreen Replacement and ADAS Calibration Requirement",
     """# Recon Manual - Windscreen Replacement and ADAS Calibration Requirement

Applies to any vehicle fitted with a forward-facing driver-assist camera
(lane-keep assist, adaptive cruise, forward collision warning) that requires a
windscreen replacement or repair during recon.

## Why this matters
On every model in the Coppermill range built from 2019 onward, the
forward-facing ADAS camera is mounted directly to the windscreen glass. Any
windscreen replacement on these models invalidates the camera's calibration,
even when the physical mounting point looks identical to the original part.
A vehicle sold with an uncalibrated ADAS camera can misjudge following
distance or lane position, and this is a compliance issue as well as a
safety one.

## Required sequence
1. Confirm the vehicle's ADAS camera mounting position against the model's
   parts diagram (see the relevant Parts Cross-Reference sheet) before
   ordering the glass - the wrong part number will not accept the camera
   bracket.
2. Replace the windscreen using an OEM-equivalent part rated for ADAS
   mounting (WS-series part numbers only - see Parts Cross-Reference
   WS-4410).
3. Perform static or dynamic recalibration per the manufacturer's
   procedure (static calibration requires a level bay and a calibration
   target board; dynamic calibration requires a documented road test at
   the specified speed range).
4. Log the calibration result (pass/fail, calibration method used,
   technician name) in the recon history before the vehicle proceeds to
   PDI. A vehicle with a pending or failed calibration cannot pass PDI
   regardless of any other sign-off.

## Common failure points
- Aftermarket glass without the correct camera bracket geometry - this is
  the single most common cause of a failed static calibration on the
  Coppermill fleet and is why WS-4410 exists as a locked part reference.
- Attempting dynamic calibration in wet weather or low light - the target
  detection algorithm needs consistent lane markings and will not complete.
- Skipping calibration when the glass "looks fine" - the camera's
  calibration state is not visually inspectable; it must be verified through
  the diagnostic tool every time the glass is disturbed.
"""),
    ("recon-manual-brake-pad-rotor-service.md",
     "Recon Manual - Brake Pad and Rotor Service Standard",
     """# Recon Manual - Brake Pad and Rotor Service Standard

Applies to any vehicle where recon inspection finds pad material below 3mm,
rotor scoring visible to touch, or a consultant note flagging brake noise,
pulsation, or extended stopping distance.

## Inspection standard
Every vehicle receives a brake inspection as part of intake recon, regardless
of odometer reading. Measure pad thickness on all four corners with calipers,
not by eye - a worn inner pad can look fine from the wheel's outer face.

## Replacement thresholds
- Pad thickness below 3mm: replace before PDI, no exceptions.
- Pad thickness 3-5mm: consultant's discretion based on retail hold time; if
  the vehicle is expected to sit in stock more than 30 days, replace now
  rather than risk a second inspection cycle.
- Rotor scoring deeper than 0.5mm or thickness below the manufacturer's
  minimum stamped on the rotor hat: replace the rotor, do not resurface.
  Resurfacing below minimum thickness is a safety fail and is not an
  approved procedure at Coppermill Motor Group.

## Parts sourcing
Use Meridian Brake Components pad and rotor sets as the default supplier
(see Supplier Reliability Record - Meridian Brake Components) unless a
specific model's warranty terms require OEM parts, in which case order
through the franchise parts channel.

## Sign-off
Record pad thickness (all four corners), rotor condition, and the parts used
in the recon history. A brake service performed during recon must be
re-verified during PDI with a road test before the vehicle is cleared for
delivery.
"""),
    ("recon-manual-pdi-standard.md",
     "Recon Manual - Pre-Delivery Inspection (PDI) Standard",
     """# Recon Manual - Pre-Delivery Inspection (PDI) Standard

The PDI is the final gate before a vehicle is cleared for customer delivery.
It is performed after all recon work (detail, mechanical, glass, tyres) is
complete and signed off individually.

## PDI checklist (all items mandatory)
1. Road test - minimum 10km covering city and highway-equivalent speed, no
   warning lights, no unusual noise or vibration.
2. All fluid levels checked and topped: engine oil, coolant, brake fluid,
   washer fluid, power steering fluid where applicable.
3. Tyre pressures set to placard spec (not "close enough" - use the gauge and
   the placard on the driver's door jamb, not the tyre's own sidewall max).
4. All lights, indicators, and horn function-tested.
5. ADAS calibration status verified if the windscreen or any camera-adjacent
   panel was touched during recon (see Recon Manual - Windscreen Replacement
   and ADAS Calibration Requirement).
6. Spare wheel or repair kit present and correctly stowed.
7. Service history and owner's manual present in the glovebox (or a
   Coppermill-issued replacement pack if the original is missing).
8. Fuel level minimum quarter tank at delivery.

## Fail and hold
Any failed item places the vehicle in PDI Hold status. A vehicle in PDI Hold
cannot be scheduled for delivery, listed as "ready for delivery" in the
dealer management system, or included in a lot-wide compliance sign-off,
even if every other item passed. The hold is cleared only when the failing
item is re-tested and passes.

## Sign-off
The PDI technician logs their name, the date, odometer reading at PDI, and
either a full pass or the specific item(s) on hold. A second signature from
the site's service manager is required before a vehicle can be marked
delivery-ready.
"""),
    ("recon-manual-tyre-wheel-alignment.md",
     "Recon Manual - Tyre and Wheel Alignment Standard",
     """# Recon Manual - Tyre and Wheel Alignment Standard

Applies to every vehicle during intake recon and again at PDI if any
suspension or steering component was disturbed.

## Tread depth thresholds
- Below 1.5mm: replace immediately, not roadworthy for retail delivery.
- 1.5mm - 3mm: replace before listing if the tyre is on a steer axle;
  discretionary on a non-steer axle only if the retail hold time is
  expected to be short.
- Uneven wear across the tread width (inner or outer edge wearing faster
  than the centre): do not just replace the tyre - this is usually a sign of
  a misaligned or worn suspension component and must be investigated before
  a new tyre is fitted, or the new tyre will wear the same way.

## Load and speed rating
Replacement tyres must match or exceed the original equipment load index and
speed rating stamped on the vehicle's tyre placard. This applies even when a
cheaper tyre in the same physical size is available - a lower load rating is
a compliance and safety issue on a ute or SUV carrying a factory-rated load.

## Wheel alignment
A four-wheel alignment check is standard at intake recon on every vehicle,
and mandatory (not discretionary) whenever a tyre is replaced due to uneven
wear, or after any suspension component service. Log the before and after
toe, camber, and caster readings in the recon history.

## Sign-off
Record tread depth (all four positions), tyre brand and size fitted, and the
alignment result. A vehicle with tyres below the replacement threshold cannot
be cleared through PDI regardless of any other sign-off.
"""),
]

for fname, title, body in RECON_MANUALS:
    write(fname, body)
    docs.append(dict(file=fname, title=title, doc_type="recon-manual", tags=["recon", "manual"]))

# ---------------------------------------------------------------- recall/service bulletins
BULLETINS = [
    ("bulletin-toyota-fuel-pump-control-module.md",
     "Recall Bulletin - Toyota RAV4 and HiLux - Fuel Pump Control Module",
     "recall", "high",
     """# Recall Bulletin - Toyota RAV4 and HiLux - Fuel Pump Control Module

**Affected models:** RAV4 (2022-2023 build), HiLux (2022-2023 build)
**Issue class:** Recall - safety
**Status:** Open, remedy available

## Description
A fault in the fuel pump control module's internal capacitor can cause the
fuel pump to lose power intermittently under high engine load, resulting in
a momentary loss of drive power. The fault does not set a permanent
diagnostic trouble code in every case, so a scan alone is not sufficient to
clear a vehicle - the control module must be physically inspected or
replaced per the remedy procedure.

## Affected stock at Coppermill Motor Group
Any RAV4 or HiLux built in the affected window must have the fuel pump
control module checked against the manufacturer's VIN lookup before
delivery, even if the vehicle shows no reported symptoms. Do not rely on the
customer or previous owner's account of "no issues" - this fault can be
present with zero prior symptoms.

## Remedy procedure
1. Look up the VIN against the manufacturer's recall register.
2. If affected and not already remedied, replace the fuel pump control
   module with the updated part (revised capacitor spec).
3. Road test minimum 15km including at least one full-throttle acceleration
   event to confirm the fault does not recur.
4. Log the remedy in the vehicle's recon history and update PDI status - a
   vehicle affected by this recall cannot pass PDI until the remedy is
   confirmed complete.

## Compliance note
A vehicle affected by an open safety recall must not be advertised, listed,
or delivered until the remedy is complete, regardless of retail demand or
days-in-stock pressure. This is a hard PDI blocker, not a discretionary
item.
"""),
    ("bulletin-ford-rear-differential-seal.md",
     "Recall Bulletin - Ford Ranger and Everest - Rear Differential Seal",
     "recall", "high",
     """# Recall Bulletin - Ford Ranger and Everest - Rear Differential Seal

**Affected models:** Ranger (2021-2022 build), Everest (2021-2022 build)
**Issue class:** Recall - safety
**Status:** Open, remedy available

## Description
The rear differential output seal on affected build-window vehicles can
degrade prematurely, leading to a slow oil leak that, if left unaddressed,
causes the differential to run low and eventually seize under load - most
commonly reported during towing or fully-loaded highway driving.

## Affected stock at Coppermill Motor Group
Every Ranger and Everest in the affected build window needs a visual
inspection of the differential housing for oil residue, plus a fluid level
check, before delivery. A dry housing with correct fluid level does not
guarantee the seal hasn't started to weep - schedule a follow-up inspection
note in the vehicle's file for 90 days post-delivery regardless of the
initial inspection result.

## Remedy procedure
1. Inspect the differential housing and driveshaft area for oil residue.
2. Check differential fluid level against spec.
3. If any residue or low fluid is found, replace the output seal and
   top up fluid to spec, then re-inspect after a 10km test drive under
   moderate load (a loaded ute tray, if available, is the closest proxy to
   towing load available at the dealership).
4. If no residue is found, the seal replacement is still recommended as a
   preventative measure on vehicles intended for towing use, and mandatory
   as a preventative measure on any demonstrator vehicle used for customer
   test-tow experiences.

## Compliance note
Log the inspection result and any remedy performed in the recon history.
This recall does not block PDI on its own unless active leakage or low
fluid is found - a clean inspection with no remedy needed can proceed to
PDI with the inspection logged.
"""),
    ("bulletin-mazda-infotainment-update.md",
     "Service Bulletin - Mazda CX-5 - Infotainment Software Update",
     "service-bulletin", "low",
     """# Service Bulletin - Mazda CX-5 - Infotainment Software Update

**Affected models:** CX-5 (2022-2023 build, pre-update software)
**Issue class:** Service bulletin - non-safety
**Status:** Update available

## Description
Early production CX-5 units shipped with an infotainment software version
that occasionally fails to reconnect a previously paired phone via Bluetooth
after the vehicle has been left off for more than 48 hours - the unit then
requires the phone to be manually re-paired. This is a customer-experience
issue, not a safety or compliance issue.

## Recommended action
Check the infotainment software version during recon (Settings > System >
Software Version). If the version is below the documented current release,
apply the update via USB before delivery. This takes approximately 20
minutes and should be logged as a recon line item so the customer isn't the
one discovering and troubleshooting a stale software version.

## Notes for consultants
This is a good item to mention proactively during delivery handover - a
customer who experiences the reconnection issue in their first week of
ownership and then finds out it was a known, already-fixed issue reads very
differently to a customer who was told about it up front.
"""),
    ("bulletin-hyundai-timing-chain-tensioner.md",
     "Service Bulletin - Hyundai i30 - Timing Chain Tensioner Noise",
     "service-bulletin", "medium",
     """# Service Bulletin - Hyundai i30 - Timing Chain Tensioner Noise

**Affected models:** i30 (2020-2021 build, 2.0L petrol)
**Issue class:** Service bulletin - non-safety
**Status:** Inspection and remedy available

## Description
A subset of 2.0L petrol i30 units built in this window can develop an
audible rattle from the timing chain tensioner on cold start, most
noticeable in the first 5-10 seconds after starting and typically fading as
oil pressure builds. In isolation this is a known, low-severity noise issue
rather than a sign of imminent failure, but it should still be checked and
logged rather than dismissed, since a genuinely worn tensioner left
unaddressed can eventually affect timing accuracy.

## Recommended action
During recon, perform two cold starts (engine must sit for at least 4 hours
between starts to be a valid test) and listen specifically for the
tensioner rattle pattern described above. If present, replace the
tensioner per the documented procedure. If absent, no action is required
and this can be noted as "inspected, no fault found" in the recon history.

## Consultant note
Because this fault is intermittent and cold-start-dependent, a single warm
test drive during a walk-around will not reliably surface it either way.
The two-cold-start protocol above is the only reliable check.
"""),
    ("bulletin-kia-airbag-control-unit.md",
     "Recall Bulletin - Kia Sportage - Airbag Control Unit",
     "recall", "high",
     """# Recall Bulletin - Kia Sportage - Airbag Control Unit

**Affected models:** Sportage (2021-2022 build)
**Issue class:** Recall - safety
**Status:** Open, remedy available

## Description
The airbag control unit on affected Sportage units can, in rare cases,
misread a moderate-severity frontal impact as below the deployment
threshold, delaying or preventing airbag deployment. The manufacturer has
issued a firmware remedy that recalibrates the impact-severity algorithm.

## Affected stock at Coppermill Motor Group
Every Sportage in the affected build window must have the airbag control
unit firmware checked against the current release before delivery. This is
a firmware flash, not a physical part replacement, and takes approximately
30 minutes with the correct diagnostic tool.

## Remedy procedure
1. Connect the diagnostic tool and read the current airbag control unit
   firmware version.
2. If below the current released version, apply the firmware update.
3. Perform the tool's built-in self-test sequence to confirm the airbag
   system reports no faults post-update.
4. Log the firmware version before and after, plus the self-test result, in
   the recon history.

## Compliance note
As with any open safety recall, a Sportage affected by this bulletin cannot
be advertised, listed, or delivered until the firmware remedy is confirmed
applied and logged. This is a hard PDI blocker.
"""),
    ("bulletin-isuzu-dpf-regeneration.md",
     "Service Bulletin - Isuzu D-Max - DPF Regeneration Cycle Advisory",
     "service-bulletin", "medium",
     """# Service Bulletin - Isuzu D-Max - DPF Regeneration Cycle Advisory

**Affected models:** D-Max (all diesel variants)
**Issue class:** Service bulletin - non-safety, customer education
**Status:** Advisory, no parts remedy

## Description
D-Max units used predominantly for short, low-speed trips (common on
demonstrator vehicles and trade-ins from customers who used the vehicle
mainly around town) can accumulate soot in the diesel particulate filter
(DPF) faster than the passive regeneration cycle can clear it, eventually
triggering an active regeneration warning light. This is expected diesel
behaviour, not a fault, but it is one of the most common reasons a
demonstrator or low-mileage trade-in D-Max returns with a dashboard warning
shortly after a customer takes delivery.

## Recommended action
During recon, run a diagnostic check of DPF soot load percentage. If above
the advisory threshold, perform a forced regeneration cycle (requires a
minimum 20-minute sustained highway-speed drive or a workshop forced
regeneration using the diagnostic tool) before delivery, and log the
resulting soot load percentage.

## Consultant note for delivery handover
This is a strong candidate for proactive customer education at handover -
explain that sustained highway driving periodically is part of normal
diesel ownership, not a sign the vehicle is faulty. A customer who
understands this before the warning light first appears is far less likely
to present as an unhappy comeback.
"""),
]

for fname, title, doc_type, urgency, body in BULLETINS:
    write(fname, body)
    docs.append(dict(file=fname, title=title, doc_type=doc_type, urgency=urgency,
                      tags=["compliance", doc_type]))

# ---------------------------------------------------------------- compliance
COMPLIANCE = [
    ("compliance-fi-disclosure.md",
     "Compliance Policy - Finance and Insurance Disclosure Requirements",
     """# Compliance Policy - Finance and Insurance Disclosure Requirements

Applies to every finance or insurance product offered alongside a vehicle
sale at either Coppermill Motor Group site.

## Mandatory disclosures
1. Comparison rate for any finance product, displayed with equal prominence
   to the advertised interest rate, not in smaller print.
2. Total amount payable over the life of the loan, including all fees.
3. Commission or benefit the dealership or consultant receives from
   recommending a specific finance or insurance product - this must be
   disclosed verbally and in writing before the customer signs.
4. The customer's right to seek finance independently and that finance
   approval is not a condition of the vehicle purchase unless explicitly
   stated in the contract of sale.
5. For any add-on insurance product (gap insurance, tyre and rim insurance,
   extended warranty), a clear statement of what is and is not covered, and
   the cooling-off period available.

## Prohibited practices
- Bundling finance approval with vehicle price in a way that obscures the
  true cash price of the vehicle.
- Pressuring a customer to decide on a finance or insurance product within
  the same visit without disclosing their right to take documentation away
  and consider it.
- Any verbal representation of a finance rate or term that differs from
  what is documented in the written contract.

## Consultant responsibility
Every consultant who discusses finance or insurance with a customer must
complete the disclosure checklist and have the customer countersign it as
part of the sale file, independently of the vehicle sale contract itself.
"""),
    ("compliance-pdi-signoff.md",
     "Compliance Standard - Pre-Delivery Inspection Sign-Off Requirements",
     """# Compliance Standard - Pre-Delivery Inspection Sign-Off Requirements

This standard governs who may sign off a PDI and under what conditions a
vehicle may be marked delivery-ready in the dealer management system.

## Sign-off authority
A PDI may be performed by any qualified recon technician or consultant, but
the final sign-off marking a vehicle as delivery-ready requires a second
signature from the site's service manager or dealer principal. A single
signature is not sufficient regardless of the technician's seniority.

## Hold conditions that cannot be overridden
The following conditions place a vehicle in PDI Hold and cannot be
overridden by any signature, including the dealer principal's:
- An open safety recall with no remedy applied.
- A failed or pending ADAS calibration on a vehicle where the windscreen or
  a camera-adjacent panel was replaced.
- Tyre tread depth below the replacement threshold on any position.
- Brake pad thickness below 3mm on any position.

A vehicle in PDI Hold for any of these reasons must not be represented as
delivery-ready in any system, report, or customer-facing communication
until the hold is cleared and re-verified.

## Audit trail
Every PDI sign-off, hold, and hold-clearance must be logged with a
timestamp, the technician or consultant's name, and (for hold clearances)
the specific remedy applied. This audit trail is what a compliance review
checks first when a delivery dispute arises.
"""),
    ("compliance-adr-modification-disclosure.md",
     "Compliance Note - Australian Design Rule (ADR) Modification Disclosure",
     """# Compliance Note - Australian Design Rule (ADR) Modification Disclosure

Applies to any vehicle in stock that has an aftermarket modification
affecting ride height, tyre size outside the original equipment range, tow
bar rating, or any electrical accessory drawing significant continuous
current (auxiliary lighting, driving lights, dual-battery systems).

## Disclosure requirement
Any such modification must be disclosed to the buyer in writing before
sale, including whether the modification complies with the relevant
Australian Design Rule and, where applicable, whether a compliance
engineer's certificate is held on file. A modification without a
compliance certificate on file must be disclosed as "certification not
held" rather than silently omitted.

## Common items requiring disclosure at Coppermill Motor Group
- Aftermarket suspension lift kits on ute trade-ins.
- Non-standard tyre and wheel combinations outside the placard load and
  speed rating.
- Aftermarket tow bars without a compliance plate or matching capacity
  documentation.
- Auxiliary driving lights or light bars wired into the vehicle's
  electrical system.

## Consultant responsibility
Identify any such modification during intake recon (not at the point of
sale) so the disclosure can be prepared and included in the vehicle's
listing and sale file from the outset, rather than surfacing it under time
pressure at the point of sale.
"""),
    ("compliance-consumer-guarantee-cooling-off.md",
     "Compliance Policy - Consumer Guarantee and Cooling-Off Disclosure",
     """# Compliance Policy - Consumer Guarantee and Cooling-Off Disclosure

Applies to every retail vehicle sale at Coppermill Motor Group.

## Consumer guarantee disclosure
Every vehicle sale must include a written disclosure of the buyer's
consumer guarantee rights under Australian Consumer Law, independent of any
dealer or manufacturer warranty offered. This disclosure must not be
presented in a way that suggests the consumer guarantee is optional or can
be waived - it cannot be, regardless of any "as-is" language elsewhere in
the sale documentation.

## Cooling-off period
Where a cooling-off period applies (state-dependent; check the site's
current jurisdiction rules), the specific number of business days and the
process for exercising it must be disclosed in writing at the point of
sale, not only referenced generically as "standard cooling-off applies."

## Prior repaint and structural history disclosure
If a vehicle's recon history includes a paint depth reading below the
threshold defined in the Full Detail and Paint Correction Standard
(indicating a prior repaint), or any structural repair history is known
from the trade-in inspection or a vehicle history report, this must be
disclosed to the buyer in writing before sale. This is a consumer guarantee
matter, not a discretionary sales disclosure.

## Consultant responsibility
The disclosure checklist for consumer guarantee and cooling-off rights is a
mandatory part of the sale file and must be countersigned by the buyer
separately from the vehicle purchase contract.
"""),
]

for fname, title, body in COMPLIANCE:
    write(fname, body)
    docs.append(dict(file=fname, title=title, doc_type="compliance", tags=["compliance"]))

# ---------------------------------------------------------------- supplier reliability
SUPPLIERS = [
    ("supplier-radiant-auto-glass.md",
     "Supplier Reliability Record - Radiant Auto Glass",
     """# Supplier Reliability Record - Radiant Auto Glass

**Category:** Windscreens and ADAS-compatible glass
**Sites supplied:** Riverside, Northgate
**Relationship since:** 2021

## Performance summary
Radiant Auto Glass is Coppermill Motor Group's primary windscreen supplier
for ADAS-equipped models, supplying the WS-4410 part range referenced in
the Windscreen Replacement and ADAS Calibration Requirement manual. Over the
last 12 months, static calibration first-pass success on Radiant-supplied
glass has run consistently above 95%, materially better than the
aftermarket alternative previously used, which required a second
calibration attempt on close to one in five jobs due to bracket alignment
tolerance.

## Known issues
A small batch of WS-4410 units received in Q1 shipped with a slightly
recessed camera bracket mount, requiring a shim kit (now stocked
separately) to achieve correct camera alignment. Radiant Auto Glass
acknowledged the batch issue and has since tightened incoming quality
control on that specific bracket tooling.

## Lead time and stock
Standard lead time is 3 business days for in-range part numbers, 7-10 days
for a special order. Coppermill Motor Group holds a small buffer stock of
WS-4410 at the Riverside site only, given it handles the higher volume of
ADAS-equipped recon work.
"""),
    ("supplier-trackgrip-tyres.md",
     "Supplier Reliability Record - TrackGrip Tyres",
     """# Supplier Reliability Record - TrackGrip Tyres

**Category:** Replacement tyres, all fitments
**Sites supplied:** Riverside, Northgate
**Relationship since:** 2019

## Performance summary
TrackGrip Tyres is the default supplier for tyre replacements under the
Tyre and Wheel Alignment Standard, covering the full range of load and
speed ratings used across the Coppermill fleet from hatchbacks through to
heavy-duty ute fitments. Order accuracy against the load and speed rating
specified has been consistently reliable, with no compliance-relevant
mis-ships recorded in the last 12 months.

## Known issues
Ute-fitment tyre sizes used on the D-Max and Triton ranges occasionally run
a 5-7 business day lead time during peak seasonal demand (typically over
the summer trade-in period), longer than the standard 2-3 day lead time on
passenger and SUV sizes. This has occasionally been the limiting factor on
PDI turnaround for affected ute stock.

## Lead time and stock
Standard passenger and SUV tyre sizes: 2-3 business days. Ute and heavy
fitment sizes: 3-7 business days depending on season. No buffer stock held
on-site; all fitments ordered against a specific stock number.
"""),
    ("supplier-meridian-brake-components.md",
     "Supplier Reliability Record - Meridian Brake Components",
     """# Supplier Reliability Record - Meridian Brake Components

**Category:** Brake pads and rotors, non-warranty replacement
**Sites supplied:** Riverside, Northgate
**Relationship since:** 2020

## Performance summary
Meridian Brake Components is the default supplier under the Brake Pad and
Rotor Service Standard for any vehicle outside its manufacturer warranty
period. Pad and rotor sets have performed reliably against the
specification, with no comeback related to premature wear or noise
reported on Meridian-fitted parts in the last 12 months.

## Known issues
None currently open. A minor packaging labelling issue in early 2025 (two
similar part numbers sharing a near-identical box design) was resolved
after Meridian updated their labelling; no parts were mis-fitted as a
result, but consultants were advised at the time to double-check the part
number against the Parts Cross-Reference sheet before fitment regardless of
box labelling.

## Lead time and stock
Standard lead time 2 business days for common passenger and SUV fitments.
A working stock of the most common pad and rotor combinations is held at
both sites.
"""),
    ("supplier-solstice-paint-coatings.md",
     "Supplier Reliability Record - Solstice Paint and Coatings",
     """# Supplier Reliability Record - Solstice Paint and Coatings

**Category:** Ceramic top coat and paint correction consumables
**Sites supplied:** Riverside, Northgate
**Relationship since:** 2022

## Performance summary
Solstice supplies the ceramic top coat product used under the Full Detail
and Paint Correction Standard for vehicles listed above the $35,000
threshold. Durability has met expectations, with no customer comebacks
related to coating failure or water-spotting on Solstice-coated vehicles
delivered in the last 12 months.

## Known issues
Cure time is longer than the previous supplier's product (recommended
minimum 4 hours indoor cure before the vehicle can be moved outdoors),
which has occasionally been a scheduling friction point on high-turnover
days at the Riverside site. This is a process consideration, not a product
defect.

## Lead time and stock
Consumables are ordered in bulk quarterly; day-to-day availability has not
been a constraint at either site.
"""),
]

for fname, title, body in SUPPLIERS:
    write(fname, body)
    docs.append(dict(file=fname, title=title, doc_type="supplier-record", tags=["supplier"]))

# ---------------------------------------------------------------- parts cross-reference
PARTS = [
    ("parts-ws4410-windscreen-adas.md",
     "Parts Cross-Reference - WS-4410 Windscreen and ADAS Calibration Requirement",
     """# Parts Cross-Reference - WS-4410 Windscreen and ADAS Calibration Requirement

**Part range:** WS-4410 series
**Applies to:** All ADAS-equipped models in the Coppermill fleet (Toyota
RAV4, Toyota HiLux, Mazda CX-5, Ford Ranger, Ford Everest, Kia Sportage,
Honda CR-V built 2019 onward)

## Compatibility notes
The WS-4410 series is the only approved windscreen part range for
ADAS-equipped models at Coppermill Motor Group, sourced through Radiant
Auto Glass. Each model variant requires a specific bracket geometry within
the WS-4410 range - always confirm the exact sub-part number against the
vehicle's build plate before ordering, as the RAV4 and HiLux share a
similar but not identical bracket mount.

## Required companion procedure
Any WS-4410 fitment must be followed by static or dynamic ADAS calibration
per the Windscreen Replacement and ADAS Calibration Requirement manual. A
WS-4410 windscreen fitted without a logged calibration result is a PDI
blocker.

## Known fitment issue
A Q1 batch shipped with a slightly recessed camera bracket mount (see
Supplier Reliability Record - Radiant Auto Glass); affected units require
the shim kit stocked alongside WS-4410 stock at the Riverside site.
"""),
    ("parts-br2210-brake-pad-compatibility.md",
     "Parts Cross-Reference - BR-2210 Brake Pad Set Compatibility",
     """# Parts Cross-Reference - BR-2210 Brake Pad Set Compatibility

**Part range:** BR-2210 series
**Applies to:** Passenger and SUV models in the Coppermill fleet outside
manufacturer warranty (Toyota RAV4, Mazda CX-5, Hyundai i30, Kia Sportage,
Honda CR-V, Suzuki Swift, Subaru Outback)

## Compatibility notes
BR-2210 series pads are sourced through Meridian Brake Components and
cover the front and rear fitments for the passenger and SUV range. Ute and
heavy-duty fitments (Ranger, HiLux, D-Max, Triton, Everest) use the
separate BR-3300 heavy-duty range, not BR-2210 - fitting a BR-2210 pad set
to a heavy-duty fitment is a compatibility error even where the physical
dimensions appear similar.

## Required companion procedure
Follow the Brake Pad and Rotor Service Standard for measurement thresholds
and sign-off requirements. Log the exact part number fitted (not just
"BR-2210 series") in the recon history, since sub-variants within the range
differ by pad compound for higher-performance variants.
"""),
    ("parts-tr1180-tyre-compatibility.md",
     "Parts Cross-Reference - TR-1180 Tyre Compatibility and Load Rating",
     """# Parts Cross-Reference - TR-1180 Tyre Compatibility and Load Rating

**Part range:** TR-1180 series
**Applies to:** All models in the Coppermill fleet

## Compatibility notes
The TR-1180 series is a load and speed rating cross-reference, not a single
tyre size - it maps each model's placard load index and speed rating to the
approved TrackGrip Tyres product line for that fitment. Ute and heavy SUV
fitments (Ranger, HiLux, D-Max, Triton, Everest) require the higher load
index band within TR-1180; fitting a passenger-band tyre to these models
even in the correct physical size is a load rating compliance issue under
the Tyre and Wheel Alignment Standard.

## Required companion procedure
Cross-check the specific stock unit's placard (driver's door jamb) against
this reference before ordering - do not rely on the previous tyre's size
alone, since a prior owner's non-compliant fitment should not be repeated.
"""),
]

for fname, title, body in PARTS:
    write(fname, body)
    docs.append(dict(file=fname, title=title, doc_type="parts-reference", tags=["parts"]))

# ---------------------------------------------------------------- consultant field notes (per stock unit)
FINDINGS = {
    "CM-5102": ("Marcus Deng", "Recon Consultant",
        "Intake inspection on Stock CM-5102 (2023 Toyota RAV4 GXL) found the front left "
        "brake pad at 2.6mm and the front right at 2.8mm, both below the 3mm replacement "
        "threshold in the Brake Pad and Rotor Service Standard. Rotors show light scoring "
        "but measure within the manufacturer's minimum thickness. Recommend BR-2210 pad "
        "replacement, front axle only, rear pads measured at 6.1mm and 6.3mm, within "
        "tolerance. No other mechanical findings. Paint grade 8/10, minor door edge chip "
        "on the driver's door, within normal detail scope."),
    "CM-5118": ("Aroha Ngata", "Recon Consultant",
        "Stock CM-5118 (2022 Ford Ranger XLT) is within the affected build window for the "
        "rear differential seal recall bulletin. Visual inspection of the differential "
        "housing found light oil residue consistent with early seal weep, fluid level "
        "reads slightly below spec. Recommend seal replacement and fluid top-up before "
        "PDI, per the recall remedy procedure - do not clear PDI without this. Tyres "
        "measured 6mm across all four positions, well within tolerance. No other findings."),
    "CM-5124": ("Liam Fitzgerald", "Recon Consultant",
        "Stock CM-5124 (2023 Mazda CX-5 Touring) intake recon found the infotainment "
        "software version below the current release referenced in the Infotainment "
        "Software Update service bulletin - customer test showed Bluetooth reconnect "
        "failure after an overnight power-off, consistent with the known issue. "
        "Recommend applying the update before delivery. Brakes and tyres both within "
        "tolerance, no other findings. Paint grade 9/10, no correction required beyond "
        "standard detail."),
    "CM-5137": ("Marcus Deng", "Recon Consultant",
        "Stock CM-5137 (2021 Hyundai i30 Active) flagged for the timing chain tensioner "
        "noise advisory - performed the two-cold-start protocol and the characteristic "
        "rattle was present on both cold starts, fading after approximately 8 seconds "
        "each time. Recommend tensioner replacement per the service bulletin rather than "
        "noting as inspected-only, given the noise was clearly reproducible. Front tyres "
        "at 4mm, within the discretionary replacement band given expected retail hold "
        "time under 30 days - holding off on replacement for now."),
    "CM-5145": ("Aroha Ngata", "Recon Consultant",
        "Stock CM-5145 (2023 Isuzu D-Max SX) is a demonstrator vehicle returned with a "
        "DPF regeneration warning light active, consistent with the DPF Regeneration "
        "Cycle Advisory given its predominantly short-trip demonstrator use. Diagnostic "
        "scan showed soot load above the advisory threshold. Performed a forced "
        "regeneration cycle via the diagnostic tool, soot load now within normal range "
        "and warning light cleared. Recommend the delivery-handover education note be "
        "included in this vehicle's sale file given the demonstrator history."),
    "CM-5150": ("Liam Fitzgerald", "Recon Consultant",
        "Stock CM-5150 (2022 Kia Sportage SX) falls within the affected build window for "
        "the airbag control unit recall bulletin. Diagnostic tool read the current "
        "firmware version as below the released remedy version. Applied the firmware "
        "update and ran the built-in self-test sequence, which completed with no faults "
        "reported. Logged firmware version before and after per the compliance "
        "requirement. No other mechanical findings; paint grade 8/10."),
    "CM-5163": ("Josh Carrow", "Sales Consultant",
        "Stock CM-5163 (2023 Yamaha MT-07) intake note: extremely low odometer "
        "demonstrator unit, minor scuffing on the right-side fairing consistent with a "
        "low-speed stand drop rather than any road incident - cosmetic only, no frame or "
        "mechanical concern noted by the recon consultant who inspected it. Chain "
        "tension and brake fluid both within spec. Recommend standard detail only, no "
        "recon holds."),
    "CM-5171": ("Renee Okafor", "Sales Consultant",
        "Stock CM-5171 (2021 Subaru Outback Sport) trade-in intake note: customer "
        "disclosed a minor rear quarter panel repair from a low-speed carpark incident "
        "approximately 18 months ago. Paint depth reading on the rear left quarter panel "
        "came back at 74 microns, below the 80 micron threshold in the Full Detail "
        "standard, consistent with the disclosed repaint. Per the Consumer Guarantee "
        "policy this must be disclosed to the next buyer in writing. No mechanical "
        "concerns identified."),
    "CM-5184": ("Marcus Deng", "Recon Consultant",
        "Stock CM-5184 (2023 Toyota HiLux SR5) falls within the affected build window for "
        "the fuel pump control module recall bulletin. VIN lookup confirmed the vehicle "
        "has not yet had the remedy applied. Replaced the fuel pump control module and "
        "completed a 15km road test including a full-throttle acceleration event with no "
        "recurrence of power loss. Logged remedy completion. Windscreen and ADAS camera "
        "untouched during this recon, no calibration required."),
    "CM-5192": ("Aroha Ngata", "Recon Consultant",
        "Stock CM-5192 (2022 Honda CR-V VTi-L) windscreen required replacement due to a "
        "stone chip that had spread into a crack across the driver's line of sight during "
        "transport from the auction yard. Fitted WS-4410 series glass and performed "
        "static ADAS calibration - first attempt failed due to a bracket alignment issue "
        "matching the known Q1 batch shim requirement, second attempt with the shim kit "
        "passed cleanly. Calibration result logged before PDI."),
    "CM-5205": ("Renee Okafor", "Sales Consultant",
        "Stock CM-5205 (2023 Suzuki Swift GL+) is a near-new demonstrator with minimal "
        "recon required. Tyres and brakes both well within tolerance. Minor interior "
        "trim scuff on the driver's door card, resolved with standard interior detail. "
        "No compliance items identified. Ready for PDI pending standard full detail "
        "sign-off."),
    "CM-5213": ("Liam Fitzgerald", "Recon Consultant",
        "Stock CM-5213 (2021 Ford Everest Trend) falls within the affected build window "
        "for the rear differential seal recall bulletin. Inspection found the housing dry "
        "with no residue and fluid level within spec. Given the vehicle is being retailed "
        "as a family SUV rather than a towing-focused sale, performed the preventative "
        "seal replacement anyway per the bulletin's recommendation for demonstrator and "
        "tow-capable stock, and logged the clean initial inspection alongside the "
        "preventative remedy."),
    "CM-5226": ("Josh Carrow", "Sales Consultant",
        "Stock CM-5226 (2023 Kawasaki Ninja 650) is an extremely low-odometer unit, "
        "essentially showroom condition. No mechanical findings from the recon "
        "consultant's inspection. Chain, brakes and tyres all within spec. Recommend "
        "standard detail only."),
    "CM-5234": ("Marcus Deng", "Recon Consultant",
        "Stock CM-5234 (2022 Mitsubishi Triton GLS) intake recon found rear tyre tread "
        "at 2mm on both rear positions with visible uneven wear across the tread width, "
        "worse on the outer edge - consistent with a suspension alignment issue rather "
        "than simple wear-out. Four-wheel alignment check found the rear toe out of "
        "spec. Recommend correcting the alignment before fitting new heavy-duty TR-1180 "
        "band tyres, not simply replacing the tyres on the existing misalignment."),
}

for stock in STOCK:
    no = stock["no"]
    name, role, body = FINDINGS[no]
    fname = f"consultant-note-{no.lower()}.md"
    title = f"Consultant Field Note - Stock {no} ({stock['year']} {stock['make']} {stock['model']})"
    md = f"""# Consultant Field Note - Stock {no}

**Stock number:** {no}
**Vehicle:** {stock['year']} {stock['make']} {stock['model']} ({stock['body']})
**Site:** {stock['site']}
**Colour:** {stock['colour']}
**Odometer at intake:** {stock['odo']:,} km
**Logged by:** {name}, {role}

## Finding
{body}
"""
    write(fname, md)
    docs.append(dict(file=fname, title=title, doc_type="consultant-note",
                      stock_no=no, site=stock["site"], make=stock["make"],
                      tags=["consultant-note", stock["site"].lower()]))

# ---------------------------------------------------------------- marketing spec sheets (subset)
SPEC_MODELS = STOCK[:10]
SPEC_COPY = {
    "RAV4 GXL": "a mid-size SUV built for daily family use, with Toyota's hybrid-ready "
                "platform available and a genuinely usable boot for weekend trips.",
    "Ranger XLT": "a capable mid-size ute with a strong tray payload and the towing "
                  "capacity buyers expect from the segment leader.",
    "CX-5 Touring": "Mazda's refined mid-size SUV, with a noticeably upmarket cabin feel "
                    "for the price point and confident highway manners.",
    "i30 Active": "a practical small hatch with class-competitive boot space and Hyundai's "
                  "long factory warranty as a strong buyer reassurance point.",
    "D-Max SX": "a workhorse ute with genuine off-road capability and one of the more "
                "comfortable ride qualities in the segment unladen.",
    "Sportage SX": "Kia's compact SUV with a distinctive cabin design and strong standard "
                   "safety equipment for the price point.",
    "MT-07": "a torquey middleweight naked bike, popular with riders moving up from a "
             "learner-approved machine who want more mid-range punch.",
    "Outback Sport": "Subaru's rugged wagon with standard all-wheel drive and genuine "
                     "light off-road ability most wagon buyers never fully use but "
                     "appreciate having.",
    "HiLux SR5": "Toyota's benchmark ute, with strong resale value and the dealer network "
                 "depth that matters to tradie and grey-nomad buyers alike.",
    "CR-V VTi-L": "Honda's practical mid-size SUV with one of the more spacious second "
                  "rows in the segment and a reputation for mechanical reliability.",
}

for stock in SPEC_MODELS:
    fname = f"spec-sheet-{stock['make'].lower()}-{stock['model'].lower().replace(' ', '-')}.md"
    title = f"Marketing Spec Sheet - {stock['make']} {stock['model']} ({stock['year']})"
    blurb = SPEC_COPY.get(stock["model"], "a well-equipped vehicle in its class.")
    md = f"""# Marketing Spec Sheet - {stock['make']} {stock['model']} ({stock['year']})

**Body type:** {stock['body']}
**Example stock at Coppermill Motor Group:** {stock['no']} ({stock['site']} site)

## Overview
The {stock['year']} {stock['make']} {stock['model']} is {blurb}

## Typical buyer profile
This model consistently attracts buyers prioritising running cost certainty
and dealer network support over outright performance, and is a reliable
recommendation for a customer whose brief is "something dependable that
won't surprise me."

## Consultant talking points
- Confirm current recon status and any open recall bulletin against this
  model line before quoting a delivery date to a customer.
- Reference the relevant Parts Cross-Reference sheet if a customer asks
  about tyre or brake replacement cost expectations for this model.
- This model has an established service history pattern at Coppermill
  Motor Group; use recent consultant field notes on same-model stock as a
  realistic guide to typical recon findings, not a guarantee of this unit's
  specific condition.
"""
    write(fname, md)
    docs.append(dict(file=fname, title=title, doc_type="spec-sheet",
                      tags=["marketing", stock["make"].lower()]))

# ---------------------------------------------------------------- manifest
manifest_path = os.path.join(OUT, "..", "corpus_manifest.json")
with open(manifest_path, "w") as f:
    json.dump({"stock": STOCK, "docs": docs}, f, indent=2)

print(f"Generated {len(docs)} documents + manifest with {len(STOCK)} stock units.")
