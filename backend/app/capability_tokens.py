"""HMAC-signed capability tokens — fine-grained scopes bound to policy digest."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.config import settings


def _secret() -> bytes:
    return settings.token_secret.encode("utf-8")


def issue_capability(
    *,
    request_id: str,
    scopes: list[str],
    policy_digest: str,
    ttl_seconds: int = 300,
) -> str:
    now = int(time.time())
    payload = {
        "v": 1,
        "jti": request_id,
        "iat": now,
        "exp": now + ttl_seconds,
        "scopes": scopes,
        "pd": policy_digest,
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(_secret(), body, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(body + b"." + sig).decode("ascii").rstrip("=")
    return token


def verify_capability(token: str) -> dict[str, Any] | None:
    try:
        pad = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(token + pad)
        body, sig = raw.rsplit(b".", 1)
        expect = hmac.new(_secret(), body, hashlib.sha256).digest()
        if not hmac.compare_digest(expect, sig):
            return None
        payload = json.loads(body.decode("utf-8"))
        if int(time.time()) > int(payload.get("exp", 0)):
            return None
        return payload
    except Exception:
        return None


def scope_allows(payload: dict[str, Any], required: str) -> bool:
    scopes = payload.get("scopes") or []
    if "*" in scopes or required in scopes:
        return True
    prefix = required.split(":", 1)[0]
    return any(s.startswith(prefix + ":") for s in scopes)
