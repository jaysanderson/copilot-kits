# Recon Manual - Windscreen Replacement and ADAS Calibration Requirement

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
