// ─────────────────────────────────────────────────────────────────────────────
// Domain handlers - the single source of business logic for the fleet system.
//
// Both the app's own REST API (domain-api.mjs, called by the React UI with the
// signed-in user's JWT) AND the /mcp server (mcp.mjs, called by ARAG's own
// Retrieval Agent with the SAME caller's JWT forwarded) dispatch through these
// exact functions. That is what makes the RBAC pattern real: there is only one
// code path that enforces "a technician only sees their own site's work", and
// both the UI and the live agent go through it - the agent gets no privilege
// the signed-in user doesn't already have.
// ─────────────────────────────────────────────────────────────────────────────

import * as data from './domain-data.mjs';

class HandlerError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

function requireUser(user) {
  if (!user) throw new HandlerError(401, 'Authentication required.');
  return user;
}

function scopeUnits(units, user) {
  if (user.role === 'manager') return units;
  return units.filter((u) => u.site === user.site);
}

// ── 1. list_units_due_for_service ────────────────────────────────────────────
export function listUnitsDueForService(user, { withinDays = 14 } = {}) {
  requireUser(user);
  const site = user.role === 'technician' ? user.site : undefined;
  return {
    withinDays,
    scope: user.role === 'technician' ? `technician (${user.site} only)` : 'manager (fleet-wide)',
    units: data.unitsDueForService(withinDays, { site }),
  };
}

// ── 2. get_parts_required_for_unit ───────────────────────────────────────────
export function getPartsRequiredForUnit(user, { unitId } = {}) {
  requireUser(user);
  const unit = data.unitById(unitId);
  if (!unit) throw new HandlerError(404, `No unit ${unitId}.`);
  if (user.role === 'technician' && unit.site !== user.site) {
    throw new HandlerError(403, `${user.name} is scoped to ${user.site} and cannot view unit ${unitId} at ${unit.site}.`);
  }
  const parts = unit.partsNeeded.map((pn) => data.partInventory(pn)).filter(Boolean);
  return { unitId, label: unit.label, serviceType: unit.serviceType, dueInDays: unit.serviceDueInDays, parts };
}

// ── 3. check_parts_inventory ─────────────────────────────────────────────────
export function checkPartsInventory(user, { partNumber } = {}) {
  requireUser(user);
  const part = data.partInventory(partNumber);
  if (!part) throw new HandlerError(404, `No part ${partNumber} on file.`);
  return part;
}

// ── 4. list_my_work_orders ───────────────────────────────────────────────────
export function listMyWorkOrders(user) {
  requireUser(user);
  const orders = user.role === 'manager' ? data.allWorkOrders() : data.workOrdersForTechnician(user.userId);
  return { scope: user.role === 'manager' ? 'fleet-wide' : `assigned to ${user.name}`, workOrders: orders };
}

// ── 5. get_work_order ────────────────────────────────────────────────────────
export function getWorkOrder(user, { workOrderId } = {}) {
  requireUser(user);
  const wo = data.workOrderById(workOrderId);
  if (!wo) throw new HandlerError(404, `No work order ${workOrderId}.`);
  if (user.role === 'technician' && wo.assignedTechnician !== user.userId) {
    throw new HandlerError(403, `${user.name} is not assigned to ${workOrderId}.`);
  }
  return wo;
}

// ── 6. get_units_by_component_supplier ───────────────────────────────────────
export function getUnitsByComponentSupplier(user, { supplier } = {}) {
  requireUser(user);
  if (!supplier) throw new HandlerError(400, 'supplier is required.');
  const units = scopeUnits(data.unitsByComponentSupplier(supplier), user);
  return { supplier, units };
}

// ── 7. get_fault_history ─────────────────────────────────────────────────────
export function getFaultHistory(user, { unitId } = {}) {
  requireUser(user);
  const unit = data.unitById(unitId);
  if (!unit) throw new HandlerError(404, `No unit ${unitId}.`);
  if (user.role === 'technician' && unit.site !== user.site) {
    throw new HandlerError(403, `${user.name} is scoped to ${user.site} and cannot view unit ${unitId} at ${unit.site}.`);
  }
  return { unitId, label: unit.label, faults: data.faultHistory(unitId) };
}

// ── 8. get_service_history ───────────────────────────────────────────────────
export function getServiceHistory(user, { unitId } = {}) {
  requireUser(user);
  const unit = data.unitById(unitId);
  if (!unit) throw new HandlerError(404, `No unit ${unitId}.`);
  if (user.role === 'technician' && unit.site !== user.site) {
    throw new HandlerError(403, `${user.name} is scoped to ${user.site} and cannot view unit ${unitId} at ${unit.site}.`);
  }
  return { unitId, label: unit.label, history: data.serviceHistory(unitId) };
}

// ── 9. get_inspection_status ─────────────────────────────────────────────────
export function getInspectionStatus(user, { unitId } = {}) {
  requireUser(user);
  const status = data.inspectionStatus(unitId);
  if (!status) throw new HandlerError(404, `No unit ${unitId}.`);
  return status;
}

// ── 10. list_fleet_inspection_status ─────────────────────────────────────────
// Deliberately returns a SUMMARY, never a single "roadworthy: true/false" verdict
// for the whole fleet - the honest gate depends on this tool being unable to
// hand the agent a fleet-wide yes/no to just repeat.
export function listFleetInspectionStatus(user) {
  requireUser(user);
  return data.fleetInspectionSummary();
}

export const TOOLS = {
  list_units_due_for_service: listUnitsDueForService,
  get_parts_required_for_unit: getPartsRequiredForUnit,
  check_parts_inventory: checkPartsInventory,
  list_my_work_orders: listMyWorkOrders,
  get_work_order: getWorkOrder,
  get_units_by_component_supplier: getUnitsByComponentSupplier,
  get_fault_history: getFaultHistory,
  get_service_history: getServiceHistory,
  get_inspection_status: getInspectionStatus,
  list_fleet_inspection_status: listFleetInspectionStatus,
};

export { HandlerError };
