"""HMAC-signed capability tokens — fine-grained scopes bound to policy digest."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.config import settings
from app.native_policy import capability_guard, hmac_sha256_native


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
    sig = hmac_sha256_native(_secret(), body)
    if sig is None:
        sig = hmac.new(_secret(), body, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(body + b"." + sig).decode("ascii").rstrip("=")
    return token


def verify_capability(token: str) -> dict[str, Any] | None:
    try:
        pad = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(token + pad)
        body, sig = raw.rsplit(b".", 1)
        expect = hmac_sha256_native(_secret(), body)
        if expect is None:
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
    scopes_csv = ",".join(str(s) for s in scopes)
    now_epoch = int(time.time())
    exp_epoch = int(payload.get("exp", 0))
    return capability_guard(
        now_epoch=now_epoch,
        exp_epoch=exp_epoch,
        scopes_csv=scopes_csv,
        required_scope=required,
    )
