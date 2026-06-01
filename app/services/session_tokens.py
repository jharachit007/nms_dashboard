import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import Settings
from app.core.constants import UserRole
from app.services.auth_service import AuthenticatedUser

_PROCESS_SECRET = secrets.token_bytes(32)


class SessionTokenError(Exception):
    pass


def create_session_token(user: AuthenticatedUser, settings: Settings) -> str:
    payload = {
        "sub": user.username,
        "roles": [role.value for role in user.roles],
        "exp": int(time.time()) + settings.session_token_ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
    signature = _sign(payload_part, settings)
    return f"{payload_part}.{signature}"


def parse_session_token(token: str, settings: Settings) -> AuthenticatedUser:
    try:
        payload_part, signature = token.split(".", 1)
    except ValueError as exc:
        raise SessionTokenError("invalid session token") from exc

    expected_signature = _sign(payload_part, settings)
    if not hmac.compare_digest(signature, expected_signature):
        raise SessionTokenError("invalid session token signature")

    payload_bytes = _urlsafe_b64decode(payload_part)
    payload = json.loads(payload_bytes)
    if int(payload.get("exp", 0)) < int(time.time()):
        raise SessionTokenError("session token expired")

    roles = []
    for role in payload.get("roles", []):
        try:
            roles.append(UserRole(role))
        except ValueError as exc:
            raise SessionTokenError(f"unsupported role: {role}") from exc

    username = payload.get("sub")
    if not username:
        raise SessionTokenError("session token missing subject")

    return AuthenticatedUser(username=username, roles=roles or [UserRole.NOC_VIEWER])


def _sign(payload_part: str, settings: Settings) -> str:
    secret = settings.session_token_secret.encode("utf-8") if settings.session_token_secret else _PROCESS_SECRET
    digest = hmac.new(secret, payload_part.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
