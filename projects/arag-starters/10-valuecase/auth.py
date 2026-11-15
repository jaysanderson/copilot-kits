"""Single shared-passphrase gate (team-lead directive, required change #1,
22 Sep 2026): unlike a demo KB, a case here holds a real account name and a
buyer's real numbers, so it cannot sit on an unauthenticated public URL even
behind an unguessable slug. One passphrase, no user accounts, checked
server-side on every API route - a signed, httpOnly cookie so there is no
server-side session table to manage.
"""
import os

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

COOKIE_NAME = "roi_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

SECRET_KEY = os.environ.get("ROI_SECRET_KEY", "dev-only-insecure-secret-change-in-fly-secrets")
PASSPHRASE = os.environ.get("ROI_PASSPHRASE", "")  # set as a Fly secret before real use

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="roi-case-tool-session")


def check_passphrase(candidate: str) -> bool:
    if not PASSPHRASE:
        return False
    return candidate.strip() == PASSPHRASE


def make_session_cookie_value() -> str:
    return _serializer.dumps({"ok": True})


def verify_session_cookie(value: str) -> bool:
    if not value:
        return False
    try:
        _serializer.loads(value, max_age=COOKIE_MAX_AGE)
        return True
    except (BadSignature, SignatureExpired):
        return False
