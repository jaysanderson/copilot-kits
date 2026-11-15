// ─────────────────────────────────────────────────────────────────────────────
// Minimal HS256 JWT - demo logins only, zero external dependency.
//
// This is what makes the RBAC pattern real: a technician's and a manager's
// login mint a JWT carrying their role/site, the app's own REST API enforces
// it, and the SAME JWT is the one forwarded to ARAG's ephemeral agent session
// (per the rao-workflow skill's "authorization forward-header" trap) so the
// live Retrieval Agent's tool calls run under the caller's own RBAC, not a
// privileged service credential.
// ─────────────────────────────────────────────────────────────────────────────

import { createHmac, timingSafeEqual } from 'node:crypto';

const SECRET = process.env.APP_JWT_SECRET || 'operator-demo-secret-change-me';

const b64url = (buf) => Buffer.from(buf).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const fromB64url = (s) => Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64');

export function signToken(payload, { expiresInSec = 60 * 60 * 8 } = {}) {
  const header = { alg: 'HS256', typ: 'JWT' };
  const body = { ...payload, iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + expiresInSec };
  const encHeader = b64url(JSON.stringify(header));
  const encBody = b64url(JSON.stringify(body));
  const sig = createHmac('sha256', SECRET).update(`${encHeader}.${encBody}`).digest();
  return `${encHeader}.${encBody}.${b64url(sig)}`;
}

export function verifyToken(token) {
  if (!token || typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [encHeader, encBody, encSig] = parts;
  const expected = createHmac('sha256', SECRET).update(`${encHeader}.${encBody}`).digest();
  const given = fromB64url(encSig);
  if (given.length !== expected.length || !timingSafeEqual(given, expected)) return null;
  let payload;
  try { payload = JSON.parse(fromB64url(encBody).toString('utf8')); } catch { return null; }
  if (typeof payload.exp === 'number' && Date.now() / 1000 > payload.exp) return null;
  return payload;
}

/** Extracts + verifies the bearer token from an Authorization header. */
export function userFromAuthHeader(authHeader) {
  const m = /^Bearer\s+(.+)$/i.exec(authHeader || '');
  if (!m) return null;
  return verifyToken(m[1]);
}

/** Express middleware: requires a valid bearer JWT, attaches req.user. */
export function requireAuth(req, res, next) {
  const user = userFromAuthHeader(req.headers.authorization);
  if (!user) return res.status(401).json({ error: 'Sign in required.' });
  req.user = user;
  next();
}
