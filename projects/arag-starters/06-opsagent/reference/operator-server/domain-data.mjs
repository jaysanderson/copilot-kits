// ─────────────────────────────────────────────────────────────────────────────
// Operator Fleet & Plant Maintenance - the app's OWN domain data.
//
// This is deliberately NOT in the Knowledge Box. The KB holds the unstructured,
// citable half of the demo (manuals, technician notes, bulletins). This file is
// the live, structured half - fleet roster, work orders, parts inventory, fault
// log, service history, inspection status - reachable only through this app's
// own REST API and, from there, its own /mcp server. That split is what proves
// the ARAG Retrieval Agent is calling a real application, not reading a KB twice.
//
// `serviceDueInDays` is relative to "now" at read time (not a stored date) so a
// redeploy or a demo run next week never shows a stale service-planner result.
// ─────────────────────────────────────────────────────────────────────────────

const DAY = 24 * 60 * 60 * 1000;
const today = () => new Date();
const plusDays = (n) => new Date(today().getTime() + n * DAY);
const minusDays = (n) => new Date(today().getTime() - n * DAY);
const iso = (d) => d.toISOString().slice(0, 10);

// ── sites & technicians ──────────────────────────────────────────────────────
export const SITES = ['Pinjarra Quarry', 'Blacktown Depot', 'Curramulka Site', 'Wollert Yard', 'Toowong Corridor'];

export const TECHNICIANS = [
  { id: 'tech-priya', name: 'Priya Nair', site: 'Pinjarra Quarry' },
  { id: 'tech-dale', name: 'Dale Whitfield', site: 'Blacktown Depot' },
  { id: 'tech-renee', name: 'Renee Okafor', site: 'Curramulka Site' },
  { id: 'tech-josh', name: 'Josh Tamati', site: 'Wollert Yard' },
  { id: 'tech-callum', name: 'Callum Reyes', site: 'Curramulka Site' },
  { id: 'tech-sione', name: 'Sione Fifita', site: 'Curramulka Site' },
  { id: 'tech-amber', name: 'Amber Kowalski', site: 'Blacktown Depot' },
];

// ── demo logins (server-side only; JWT minted at /api/login) ────────────────
export const DEMO_USERS = {
  'dale.whitfield': { userId: 'tech-dale', name: 'Dale Whitfield', role: 'technician', site: 'Blacktown Depot', password: 'operator' },
  'priya.nair': { userId: 'tech-priya', name: 'Priya Nair', role: 'technician', site: 'Pinjarra Quarry', password: 'operator' },
  'grace.sutherland': { userId: 'mgr-grace', name: 'Grace Sutherland', role: 'manager', site: null, password: 'operator' },
};

// ── components & suppliers (mirrors the KB corpus so the graph + live data agree)
export const COMPONENTS = {
  'hydraulic-pump-seal': { name: 'Hydraulic pump seal', partNumber: 'RH-4420', supplier: 'Ridgeback Hydraulics' },
  'brake-caliper': { name: 'Rear brake caliper assembly', partNumber: 'BF-2210', supplier: 'BrakeForce Components' },
  'steering-ram-seal': { name: 'Steering ram rod-end seal', partNumber: 'PH-1180', supplier: 'Pinnacle Hose & Seal' },
  'intercooler-service-kit': { name: 'Intercooler service kit', partNumber: 'CW-7712', supplier: 'Ferrotech Castings' },
  'fuel-injector': { name: 'Fuel injector', partNumber: 'CD-9040', supplier: 'Coastal Diesel Co.' },
};

// ── parts inventory (deliberately short on RH-4420 to give the Service Planner
// something real to surface) ─────────────────────────────────────────────────
export const PARTS_INVENTORY = {
  'RH-4420': { name: 'Hydraulic pump seal cartridge', supplier: 'Ridgeback Hydraulics', qtyOnHand: 2, reorderThreshold: 3, leadTimeDays: 6 },
  'BF-2210': { name: 'Rear brake caliper assembly', supplier: 'BrakeForce Components', qtyOnHand: 6, reorderThreshold: 2, leadTimeDays: 4 },
  'PH-1180': { name: 'Steering ram rod-end seal', supplier: 'Pinnacle Hose & Seal', qtyOnHand: 5, reorderThreshold: 2, leadTimeDays: 10 },
  'CW-7712': { name: 'Intercooler service kit', supplier: 'Ferrotech Castings', qtyOnHand: 4, reorderThreshold: 2, leadTimeDays: 5 },
  'CD-9040': { name: 'Fuel injector', supplier: 'Coastal Diesel Co.', qtyOnHand: 8, reorderThreshold: 2, leadTimeDays: 7 },
};

// ── fleet roster ──────────────────────────────────────────────────────────────
// serviceDueInDays: negative = overdue, small positive = due soon (drives the
// Service Planner's "next 14 days" pattern). tiltSensorCleared mirrors the KB's
// inspection checklist doc exactly, so the Roadworthy pattern's live data and
// the KB's cited doc agree (and both correctly withhold a fleet-wide claim).
const unit = (o) => ({ faults: [], serviceHistory: [], components: [], ...o });

export const UNITS = [
  unit({ id: 'unit-03', label: 'Unit 03', platform: 'Vantage Tipper', site: 'Blacktown Depot', hours: null, km: 118400, unsealedRoadPct: 65, serviceDueInDays: 9, serviceType: 'Brake caliper inspection', partsNeeded: ['BF-2210'], components: ['brake-caliper'], assignedTechnician: 'tech-dale', tiltSensorApplicable: false }),
  unit({ id: 'unit-05', label: 'Unit 05', platform: 'Vantage Tipper', site: 'Blacktown Depot', hours: null, km: 96200, unsealedRoadPct: 58, serviceDueInDays: 41, serviceType: 'Standard service', partsNeeded: [], components: ['brake-caliper'], assignedTechnician: 'tech-dale', tiltSensorApplicable: false }),
  unit({ id: 'unit-07', label: 'Unit 07', platform: 'Ridgeline Excavator', site: 'Pinjarra Quarry', hours: 2148, km: null, unsealedRoadPct: null, serviceDueInDays: 3, serviceType: 'Hydraulic system check + brake caliper (chassis)', partsNeeded: ['RH-4420', 'BF-2210'], components: ['hydraulic-pump-seal', 'brake-caliper'], assignedTechnician: 'tech-priya', tiltSensorApplicable: true, tiltSensorCleared: true, tiltSensorInspectedOn: '2026-05-14' }),
  unit({ id: 'unit-09', label: 'Unit 09', platform: 'Vantage Tipper', site: 'Blacktown Depot', hours: null, km: 101500, unsealedRoadPct: 38, serviceDueInDays: 52, serviceType: 'Standard service', partsNeeded: [], components: ['brake-caliper'], assignedTechnician: 'tech-amber', tiltSensorApplicable: false }),
  unit({ id: 'unit-11', label: 'Unit 11', platform: 'Vantage Tipper', site: 'Blacktown Depot', hours: null, km: 87300, unsealedRoadPct: 44, serviceDueInDays: 28, serviceType: 'Standard service', partsNeeded: [], components: ['brake-caliper'], assignedTechnician: 'tech-dale', tiltSensorApplicable: false }),
  unit({ id: 'unit-13', label: 'Unit 13', platform: 'Vantage Tipper', site: 'Blacktown Depot', hours: null, km: 73900, unsealedRoadPct: 22, serviceDueInDays: 60, serviceType: 'Standard service', partsNeeded: [], components: ['brake-caliper'], assignedTechnician: 'tech-amber', tiltSensorApplicable: false }),
  unit({ id: 'unit-14', label: 'Unit 14', platform: 'Ridgeline Excavator', site: 'Curramulka Site', hours: 1780, km: null, unsealedRoadPct: null, serviceDueInDays: 1, serviceType: 'URGENT - hydraulic pump seal replacement + thermal survey', partsNeeded: ['RH-4420'], components: ['hydraulic-pump-seal'], assignedTechnician: 'tech-renee', tiltSensorApplicable: true, tiltSensorCleared: true, tiltSensorInspectedOn: '2026-05-20' }),
  unit({ id: 'unit-16', label: 'Unit 16', platform: 'Ridgeline Excavator', site: 'Pinjarra Quarry', hours: 340, km: null, unsealedRoadPct: null, serviceDueInDays: 210, serviceType: 'Standard service', partsNeeded: [], components: ['hydraulic-pump-seal'], assignedTechnician: 'tech-priya', tiltSensorApplicable: true, tiltSensorCleared: true, tiltSensorInspectedOn: '2026-05-22' }),
  unit({ id: 'unit-18', label: 'Unit 18', platform: 'Ridgeline Excavator', site: 'Pinjarra Quarry', hours: 1870, km: null, unsealedRoadPct: null, serviceDueInDays: 6, serviceType: 'Hydraulic pump seal replacement (early, per fleet pattern)', partsNeeded: ['RH-4420'], components: ['hydraulic-pump-seal'], assignedTechnician: 'tech-priya', tiltSensorApplicable: true, tiltSensorCleared: false, tiltSensorInspectedOn: null }),
  unit({ id: 'unit-20', label: 'Unit 20', platform: 'Ridgeline Excavator', site: 'Pinjarra Quarry', hours: 620, km: null, unsealedRoadPct: null, serviceDueInDays: 95, serviceType: 'Standard service', partsNeeded: [], components: ['hydraulic-pump-seal'], assignedTechnician: 'tech-priya', tiltSensorApplicable: true, tiltSensorCleared: false, tiltSensorInspectedOn: null }),
  unit({ id: 'unit-21', label: 'Unit 21', platform: 'Talon Loader', site: 'Wollert Yard', hours: 990, km: null, unsealedRoadPct: null, serviceDueInDays: 34, serviceType: 'Standard service', partsNeeded: [], components: ['steering-ram-seal'], assignedTechnician: 'tech-josh', tiltSensorApplicable: true, tiltSensorCleared: true, tiltSensorInspectedOn: '2026-05-16' }),
  unit({ id: 'unit-22', label: 'Unit 22', platform: 'Talon Loader', site: 'Wollert Yard', hours: 860, km: null, unsealedRoadPct: null, serviceDueInDays: 30, serviceType: 'Standard service', partsNeeded: [], components: ['steering-ram-seal'], assignedTechnician: 'tech-josh', tiltSensorApplicable: true, tiltSensorCleared: true, tiltSensorInspectedOn: '2026-05-16' }),
  unit({ id: 'unit-23', label: 'Unit 23', platform: 'Talon Loader', site: 'Wollert Yard', hours: 410, km: null, unsealedRoadPct: null, serviceDueInDays: 120, serviceType: 'Standard service', partsNeeded: [], components: ['steering-ram-seal'], assignedTechnician: 'tech-josh', tiltSensorApplicable: true, tiltSensorCleared: false, tiltSensorInspectedOn: null }),
  unit({ id: 'unit-24', label: 'Unit 24', platform: 'Crestway Grader', site: 'Curramulka Site', hours: 540, km: null, unsealedRoadPct: null, serviceDueInDays: 12, serviceType: 'Intercooler service + forced-regen schedule change', partsNeeded: ['CW-7712'], components: ['intercooler-service-kit'], assignedTechnician: 'tech-callum', tiltSensorApplicable: false }),
  unit({ id: 'unit-25', label: 'Unit 25', platform: 'Crestway Grader', site: 'Curramulka Site', hours: 505, km: null, unsealedRoadPct: null, serviceDueInDays: 47, serviceType: 'Standard service', partsNeeded: [], components: ['intercooler-service-kit'], assignedTechnician: 'tech-callum', tiltSensorApplicable: false }),
  unit({ id: 'unit-26', label: 'Unit 26', platform: 'Ridgeline Water Cart', site: 'Toowong Corridor', hours: 260, km: null, unsealedRoadPct: null, serviceDueInDays: 75, serviceType: 'Standard service', partsNeeded: [], components: ['fuel-injector'], assignedTechnician: 'tech-sione', tiltSensorApplicable: false }),
  unit({ id: 'unit-27', label: 'Unit 27', platform: 'Vantage Roller', site: 'Toowong Corridor', hours: 190, km: null, unsealedRoadPct: null, serviceDueInDays: 88, serviceType: 'Standard service', partsNeeded: [], components: ['fuel-injector'], assignedTechnician: 'tech-sione', tiltSensorApplicable: false }),
  unit({ id: 'unit-28', label: 'Unit 28', platform: 'Vantage Roller', site: 'Toowong Corridor', hours: 205, km: null, unsealedRoadPct: null, serviceDueInDays: 63, serviceType: 'Standard service', partsNeeded: [], components: ['fuel-injector'], assignedTechnician: 'tech-sione', tiltSensorApplicable: false }),
];

// ── fault log (live, structured - distinct from the KB's technician notes,
// which narrate the SAME events in prose for grounding/citation) ────────────
export const FAULT_LOG = [
  { unitId: 'unit-07', faultCode: 'F-114', description: 'Hydraulic pressure loss, boom sluggish', loggedAt: iso(minusDays(75)), resolved: true, resolvedAction: 'RH-4420 seal replaced' },
  { unitId: 'unit-14', faultCode: 'F-441', description: 'Boost underspeed', loggedAt: iso(minusDays(140)), resolved: true, resolvedAction: 'Intercooler cleaned' },
  { unitId: 'unit-14', faultCode: 'F-441', description: 'Boost underspeed (recurrence within 250-hour window)', loggedAt: iso(minusDays(78)), resolved: true, resolvedAction: 'Intercooler cleaned; wastegate actuator inspection flagged, not yet completed' },
  { unitId: 'unit-14', faultCode: 'F-512', description: 'Transmission slip under sustained load', loggedAt: iso(minusDays(35)), resolved: false, resolvedAction: null },
  { unitId: 'unit-16', faultCode: 'F-114', description: 'Early hydraulic seal lip wear found on inspection', loggedAt: iso(minusDays(55)), resolved: true, resolvedAction: 'RH-4420 seal replaced ahead of schedule' },
  { unitId: 'unit-21', faultCode: 'F-147', description: 'Steering ram drift, weeping at rod end', loggedAt: iso(minusDays(70)), resolved: true, resolvedAction: 'PH-1180 seal replaced' },
  { unitId: 'unit-22', faultCode: 'F-147', description: 'Steering ram seal early weeping (same supplier batch as Unit 21)', loggedAt: iso(minusDays(95)), resolved: true, resolvedAction: 'PH-1180 seal replaced' },
  { unitId: 'unit-24', faultCode: 'F-256', description: 'DPF regen failure after two failed passive cycles', loggedAt: iso(minusDays(72)), resolved: true, resolvedAction: 'Manual forced regen; moved to weekly forced-regen schedule' },
  { unitId: 'unit-03', faultCode: 'F-208', description: 'Brake pad wear sensor, metallic scrape on descent', loggedAt: iso(minusDays(92)), resolved: true, resolvedAction: 'Pads + caliper pin boots replaced' },
];

// ── service history (live, structured) ───────────────────────────────────────
export const SERVICE_HISTORY = [
  { unitId: 'unit-07', date: iso(minusDays(75)), type: 'Hydraulic pump seal replacement', technician: 'Priya Nair', notes: 'RH-4420 replaced at 2,140 hrs, past the 2,000-hr ceiling' },
  { unitId: 'unit-14', date: iso(minusDays(140)), type: 'Intercooler clean', technician: 'Renee Okafor', notes: 'First boost underspeed event' },
  { unitId: 'unit-14', date: iso(minusDays(78)), type: 'Intercooler clean (recurrence)', technician: 'Renee Okafor', notes: 'Second event within 9 weeks; wastegate inspection flagged' },
  { unitId: 'unit-14', date: iso(minusDays(35)), type: 'Thermal check', technician: 'Sione Fifita', notes: 'Transmission slip; elevated hydraulic circuit temperature found' },
  { unitId: 'unit-16', date: iso(minusDays(55)), type: 'Hydraulic pump seal replacement (early)', technician: 'Priya Nair', notes: 'Replaced at 1,960 hrs ahead of ceiling' },
  { unitId: 'unit-21', date: iso(minusDays(70)), type: 'Steering ram seal replacement', technician: 'Josh Tamati', notes: 'PH-1180 seal, February supplier batch' },
  { unitId: 'unit-22', date: iso(minusDays(95)), type: 'Steering ram seal replacement', technician: 'Josh Tamati', notes: 'PH-1180 seal, same February batch as Unit 21' },
  { unitId: 'unit-03', date: iso(minusDays(92)), type: 'Brake caliper service', technician: 'Dale Whitfield', notes: 'Pads + caliper pin boots replaced' },
  { unitId: 'unit-05', date: iso(minusDays(85)), type: 'Pre-emptive brake caliper check', technician: 'Dale Whitfield', notes: 'Early uneven wear found, pads replaced' },
  { unitId: 'unit-09', date: iso(minusDays(20)), type: 'Scheduled brake inspection', technician: 'Amber Kowalski', notes: 'Within spec, no action' },
  { unitId: 'unit-24', date: iso(minusDays(72)), type: 'DPF forced regeneration', technician: 'Callum Reyes', notes: 'Moved to weekly forced-regen schedule' },
];

// ── work orders ─────────────────────────────────────────────────────────────
export const WORK_ORDERS = UNITS.filter((u) => u.serviceDueInDays <= 60).map((u, i) => ({
  id: `wo-${String(i + 1).padStart(3, '0')}`,
  unitId: u.id,
  site: u.site,
  type: u.serviceType,
  status: u.serviceDueInDays <= 3 ? 'in-progress' : 'open',
  assignedTechnician: u.assignedTechnician,
  dueDate: iso(plusDays(u.serviceDueInDays)),
  partsNeeded: u.partsNeeded,
  priority: u.serviceDueInDays <= 3 ? 'urgent' : u.serviceDueInDays <= 14 ? 'high' : 'normal',
}));

// ── lookups ──────────────────────────────────────────────────────────────────
export function unitById(id) {
  return UNITS.find((u) => u.id === id) || null;
}

export function technicianById(id) {
  return TECHNICIANS.find((t) => t.id === id) || null;
}

export function unitsDueForService(withinDays, { site } = {}) {
  return UNITS
    .filter((u) => u.serviceDueInDays <= withinDays)
    .filter((u) => !site || u.site === site)
    .map((u) => ({
      id: u.id, label: u.label, platform: u.platform, site: u.site,
      dueDate: iso(plusDays(u.serviceDueInDays)), daysUntilDue: u.serviceDueInDays,
      serviceType: u.serviceType, partsNeeded: u.partsNeeded, assignedTechnician: u.assignedTechnician,
    }))
    .sort((a, b) => a.daysUntilDue - b.daysUntilDue);
}

export function unitsByComponentSupplier(supplier) {
  const norm = supplier.trim().toLowerCase();
  const componentKeys = Object.entries(COMPONENTS)
    .filter(([, c]) => c.supplier.toLowerCase().includes(norm))
    .map(([key]) => key);
  return UNITS
    .filter((u) => u.components.some((c) => componentKeys.includes(c)))
    .map((u) => ({
      id: u.id, label: u.label, platform: u.platform, site: u.site,
      components: u.components.filter((c) => componentKeys.includes(c)).map((c) => COMPONENTS[c].name),
      openFaultCount: FAULT_LOG.filter((f) => f.unitId === u.id && !f.resolved).length,
      pastFaultCount: FAULT_LOG.filter((f) => f.unitId === u.id).length,
    }));
}

export function faultHistory(unitId) {
  return FAULT_LOG.filter((f) => f.unitId === unitId);
}

export function serviceHistory(unitId) {
  return SERVICE_HISTORY.filter((s) => s.unitId === unitId);
}

export function inspectionStatus(unitId) {
  const u = unitById(unitId);
  if (!u) return null;
  return {
    id: u.id, label: u.label,
    tiltSensorApplicable: u.tiltSensorApplicable,
    tiltSensorCleared: u.tiltSensorApplicable ? !!u.tiltSensorCleared : null,
    tiltSensorInspectedOn: u.tiltSensorInspectedOn || null,
  };
}

export function fleetInspectionSummary() {
  const applicable = UNITS.filter((u) => u.tiltSensorApplicable);
  return {
    totalUnits: UNITS.length,
    tiltSensorApplicableUnits: applicable.length,
    cleared: applicable.filter((u) => u.tiltSensorCleared).map((u) => u.id),
    notYetInspected: applicable.filter((u) => !u.tiltSensorCleared).map((u) => u.id),
  };
}

export function partInventory(partNumber) {
  const p = PARTS_INVENTORY[partNumber];
  if (!p) return null;
  return { partNumber, ...p, belowReorderThreshold: p.qtyOnHand <= p.reorderThreshold };
}

export function workOrdersForTechnician(technicianId) {
  return WORK_ORDERS.filter((w) => w.assignedTechnician === technicianId);
}

export function allWorkOrders() {
  return WORK_ORDERS;
}

export function workOrderById(id) {
  return WORK_ORDERS.find((w) => w.id === id) || null;
}
