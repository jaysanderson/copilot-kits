// ─────────────────────────────────────────────────────────────────────────────
// Domain REST API - the app's own system of record (fleet, work orders, parts,
// faults, service history, inspections). This is what the UI calls directly,
// and what /mcp calls in-process on ARAG's behalf. See domain-handlers.mjs for
// the shared logic + RBAC.
// ─────────────────────────────────────────────────────────────────────────────

import { Router } from 'express';
import { requireAuth, signToken } from './auth.mjs';
import * as data from './domain-data.mjs';
import * as handlers from './domain-handlers.mjs';
import { HandlerError } from './domain-handlers.mjs';

export const router = Router();

function wrap(fn) {
  return (req, res) => {
    try {
      const result = fn(req.user, req.query.unitId ? req.query : { ...req.query, ...req.body });
      res.json(result);
    } catch (err) {
      const status = err instanceof HandlerError ? err.status : 500;
      res.status(status).json({ error: err.message });
    }
  };
}

/** POST /api/login {username, password} → { token, user } - demo-only auth. */
router.post('/api/login', (req, res) => {
  const { username, password } = req.body || {};
  const record = data.DEMO_USERS[String(username || '').toLowerCase()];
  if (!record || record.password !== password) {
    return res.status(401).json({ error: 'Invalid demo login.' });
  }
  const claims = { userId: record.userId, name: record.name, role: record.role, site: record.site };
  const token = signToken(claims);
  res.json({ token, user: claims });
});

/** GET /api/me - who the current bearer token belongs to (for the UI header). */
router.get('/api/me', requireAuth, (req, res) => res.json({ user: req.user }));

/** GET /api/demo-logins - the demo's own login roster, so the UI can offer a switcher. */
router.get('/api/demo-logins', (_req, res) => {
  res.json({
    logins: Object.entries(data.DEMO_USERS).map(([username, u]) => ({
      username, name: u.name, role: u.role, site: u.site,
    })),
  });
});

router.get('/api/fleet/units-due', requireAuth, wrap(handlers.listUnitsDueForService));
router.get('/api/fleet/units/:unitId/parts-required', requireAuth, (req, res, next) => {
  req.query.unitId = req.params.unitId; next();
}, wrap(handlers.getPartsRequiredForUnit));
router.get('/api/fleet/parts/:partNumber', requireAuth, (req, res, next) => {
  req.query.partNumber = req.params.partNumber; next();
}, wrap(handlers.checkPartsInventory));
router.get('/api/fleet/work-orders/mine', requireAuth, wrap(handlers.listMyWorkOrders));
router.get('/api/fleet/work-orders/:id', requireAuth, (req, res, next) => {
  req.query.workOrderId = req.params.id; next();
}, wrap(handlers.getWorkOrder));
router.get('/api/fleet/units/by-supplier', requireAuth, wrap(handlers.getUnitsByComponentSupplier));
router.get('/api/fleet/units/:unitId/faults', requireAuth, (req, res, next) => {
  req.query.unitId = req.params.unitId; next();
}, wrap(handlers.getFaultHistory));
router.get('/api/fleet/units/:unitId/service-history', requireAuth, (req, res, next) => {
  req.query.unitId = req.params.unitId; next();
}, wrap(handlers.getServiceHistory));
router.get('/api/fleet/units/:unitId/inspection', requireAuth, (req, res, next) => {
  req.query.unitId = req.params.unitId; next();
}, wrap(handlers.getInspectionStatus));
router.get('/api/fleet/inspection-summary', requireAuth, wrap(handlers.listFleetInspectionStatus));

/** GET /api/fleet/units - full roster (site-scoped for technicians), for the UI shell. */
router.get('/api/fleet/units', requireAuth, (req, res) => {
  const units = data.UNITS
    .filter((u) => req.user.role === 'manager' || u.site === req.user.site)
    .map((u) => ({
      id: u.id, label: u.label, platform: u.platform, site: u.site,
      serviceDueInDays: u.serviceDueInDays, serviceType: u.serviceType,
    }));
  res.json({ units });
});
