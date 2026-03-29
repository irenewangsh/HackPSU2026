"""Persistence: prefs with decay, authority timeline, reversible ops, user profile."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Mapping
from pathlib import Path

import aiosqlite

from app.config import settings
from app.native_policy import hash_chain_digest, move_replace, unlink_path, write_file


def _decay(weight: float, last_ts: float, now: float) -> float:
    if weight <= 0:
        return 0.0
    hours = (now - last_ts) / 3600.0
    hl = settings.trust_decay_half_life_hours
    factor = math.pow(0.5, hours / hl) if hl > 0 else 0.0
    return weight * factor


class PreferenceMemory:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or settings.database_path

    async def init(self) -> None:
        Path(settings.sandbox_root).mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS prefs (
                    category TEXT PRIMARY KEY,
                    accept_weight REAL NOT NULL,
                    reject_weight REAL NOT NULL,
                    last_ts REAL NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    action_type TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    composite_risk REAL NOT NULL,
                    summary TEXT NOT NULL,
                    chain_digest TEXT
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS authority_timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    request_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    composite_risk REAL NOT NULL,
                    envelope REAL NOT NULL,
                    summary TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS reversible_ops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    kind TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    inverse_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'committed',
                    request_id TEXT
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value REAL NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS scenario_prefs (
                    key TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    allow_count INTEGER NOT NULL DEFAULT 0,
                    deny_count INTEGER NOT NULL DEFAULT 0,
                    ask_count INTEGER NOT NULL DEFAULT 0,
                    last_ts REAL NOT NULL
                )
                """
            )
            await db.commit()
        await self._migrate_schema()
        await self._ensure_profile_defaults()
        await self.apply_forgetting_if_due()

    async def _migrate_schema(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            try:
                await db.execute("ALTER TABLE audit ADD COLUMN chain_digest TEXT")
            except aiosqlite.OperationalError:
                pass
            await db.commit()

    async def _ensure_profile_defaults(self) -> None:
        defaults = {
            "risk_aversion": 0.45,
            "forgetting_lambda_per_hour": settings.forgetting_lambda_per_hour,
            "last_forget_wallclock": time.time(),
        }
        async with aiosqlite.connect(self.path) as db:
            for k, v in defaults.items():
                await db.execute(
                    """
                    INSERT INTO user_profile(key, value) VALUES(?, ?)
                    ON CONFLICT(key) DO NOTHING
                    """,
                    (k, float(v)),
                )
            await db.commit()

    async def profile_value(self, key: str, default: float = 0.0) -> float:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT value FROM user_profile WHERE key = ?", (key,)
            )
            row = await cur.fetchone()
        return float(row[0]) if row else default

    async def set_profile_value(self, key: str, value: float) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO user_profile(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            await db.commit()

    async def apply_forgetting_if_due(self) -> None:
        """Exponential decay on stored preference weights — models human forgetting."""
        now = time.time()
        lam = await self.profile_value(
            "forgetting_lambda_per_hour", settings.forgetting_lambda_per_hour
        )
        last = await self.profile_value("last_forget_wallclock", now)
        dt_h = max(0.0, (now - last) / 3600.0)
        if dt_h < 0.02:  # ~72s minimum between passes
            return
        factor = math.exp(-lam * dt_h)
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT category, accept_weight, reject_weight, last_ts FROM prefs"
            )
            rows = await cur.fetchall()
            for cat, aw, rw, lts in rows:
                aw = aw * factor
                rw = rw * factor
                await db.execute(
                    "UPDATE prefs SET accept_weight = ?, reject_weight = ?, last_ts = ? WHERE category = ?",
                    (aw, rw, now, cat),
                )
            await db.execute(
                "INSERT INTO user_profile(key, value) VALUES('last_forget_wallclock', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (now,),
            )
            await db.commit()

    async def trust_bias(self, category: str) -> float:
        now = time.time()
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT accept_weight, reject_weight, last_ts FROM prefs WHERE category = ?",
                (category,),
            )
            row = await cur.fetchone()
        if not row:
            return 0.0
        aw, rw, last_ts = row
        aw = _decay(aw, last_ts, now)
        rw = _decay(rw, last_ts, now)
        total = aw + rw + 1e-6
        ra = await self.profile_value("risk_aversion", 0.45)
        raw = (aw - rw) / total
        return max(-1.0, min(1.0, raw * (1.0 - 0.25 * ra)))

    async def record_feedback(
        self,
        *,
        category: str,
        accepted: bool,
        high_risk: bool,
    ) -> None:
        now = time.time()
        if high_risk and category in (
            "financial",
            "authentication",
            "payment",
            "identity_or_finance",
        ):
            delta_accept = 0.05 if accepted else 0.0
            delta_reject = 0.05 if not accepted else 0.0
        else:
            delta_accept = 0.25 if accepted else 0.0
            delta_reject = 0.25 if not accepted else 0.0

        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT accept_weight, reject_weight, last_ts FROM prefs WHERE category = ?",
                (category,),
            )
            row = await cur.fetchone()
            if row:
                aw, rw, last_ts = row
                aw = _decay(aw, last_ts, now) + delta_accept
                rw = _decay(rw, last_ts, now) + delta_reject
            else:
                aw, rw = delta_accept, delta_reject
            await db.execute(
                """
                INSERT INTO prefs(category, accept_weight, reject_weight, last_ts)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(category) DO UPDATE SET
                accept_weight = excluded.accept_weight,
                reject_weight = excluded.reject_weight,
                last_ts = excluded.last_ts
                """,
                (category, aw, rw, now),
            )
            await db.commit()

    async def reset(self, category: str | None = None) -> None:
        async with aiosqlite.connect(self.path) as db:
            if category:
                await db.execute("DELETE FROM prefs WHERE category = ?", (category,))
            else:
                await db.execute("DELETE FROM prefs")
                await db.execute("DELETE FROM scenario_prefs")
            await db.commit()

    async def scenario_bias(
        self, *, task_type: str, action_type: str, sensitivity: str
    ) -> float:
        key = f"{task_type}|{action_type}|{sensitivity}"
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """
                SELECT allow_count, deny_count, ask_count
                FROM scenario_prefs WHERE key = ?
                """,
                (key,),
            )
            row = await cur.fetchone()
        if not row:
            return 0.0
        allow_count, deny_count, ask_count = [int(x) for x in row]
        total = max(1, allow_count + deny_count + ask_count)
        # Ask votes are neutral; confidence tempers the pull.
        raw = (allow_count - deny_count) / total
        confidence = min(1.0, total / 8.0)
        if action_type in ("delete_file", "make_payment", "submit_form"):
            raw = max(-0.3, min(0.15, raw))
        return raw * confidence

    async def record_scenario_feedback(
        self,
        *,
        task_type: str,
        action_type: str,
        sensitivity: str,
        outcome: str,  # allow | deny | ask
    ) -> None:
        key = f"{task_type}|{action_type}|{sensitivity}"
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """
                SELECT allow_count, deny_count, ask_count
                FROM scenario_prefs WHERE key = ?
                """,
                (key,),
            )
            row = await cur.fetchone()
            allow_count, deny_count, ask_count = (0, 0, 0)
            if row:
                allow_count, deny_count, ask_count = [int(x) for x in row]
            if outcome == "allow":
                allow_count = min(50, allow_count + 1)
            elif outcome == "deny":
                deny_count = min(50, deny_count + 1)
            else:
                ask_count = min(50, ask_count + 1)
            await db.execute(
                """
                INSERT INTO scenario_prefs(
                    key, task_type, action_type, sensitivity,
                    allow_count, deny_count, ask_count, last_ts
                )
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(key) DO UPDATE SET
                    allow_count = excluded.allow_count,
                    deny_count = excluded.deny_count,
                    ask_count = excluded.ask_count,
                    last_ts = excluded.last_ts
                """,
                (
                    key,
                    task_type,
                    action_type,
                    sensitivity,
                    allow_count,
                    deny_count,
                    ask_count,
                    time.time(),
                ),
            )
            await db.commit()

    async def scenario_profile(
        self, *, task_type: str, action_type: str, sensitivity: str
    ) -> dict[str, object]:
        key = f"{task_type}|{action_type}|{sensitivity}"
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """
                SELECT allow_count, deny_count, ask_count
                FROM scenario_prefs WHERE key = ?
                """,
                (key,),
            )
            row = await cur.fetchone()
        allow_count, deny_count, ask_count = (0, 0, 0)
        if row:
            allow_count, deny_count, ask_count = [int(x) for x in row]
        total = allow_count + deny_count + ask_count
        confidence = round(min(1.0, total / 8.0), 3)
        bias = round(await self.scenario_bias(task_type=task_type, action_type=action_type, sensitivity=sensitivity), 3)
        return {
            "key": key,
            "task_type": task_type,
            "action_type": action_type,
            "sensitivity": sensitivity,
            "allow_count": allow_count,
            "deny_count": deny_count,
            "ask_count": ask_count,
            "confidence": confidence,
            "bias": bias,
        }

    async def list_scenario_profiles(self, limit: int = 80) -> list[dict[str, object]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT key, task_type, action_type, sensitivity,
                       allow_count, deny_count, ask_count, last_ts
                FROM scenario_prefs ORDER BY last_ts DESC LIMIT ?
                """,
                (limit,),
            )
            rows = await cur.fetchall()
        out: list[dict[str, object]] = []
        for r in rows:
            total = int(r["allow_count"]) + int(r["deny_count"]) + int(r["ask_count"])
            confidence = round(min(1.0, total / 8.0), 3)
            raw = (int(r["allow_count"]) - int(r["deny_count"])) / max(1, total)
            bias = round(raw * confidence, 3)
            out.append(
                {
                    "key": r["key"],
                    "task_type": r["task_type"],
                    "action_type": r["action_type"],
                    "sensitivity": r["sensitivity"],
                    "allow_count": int(r["allow_count"]),
                    "deny_count": int(r["deny_count"]),
                    "ask_count": int(r["ask_count"]),
                    "confidence": confidence,
                    "bias": bias,
                }
            )
        return out

    async def append_audit(
        self,
        *,
        action_type: str,
        decision: str,
        composite_risk: float,
        summary: str,
    ) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur_prev = await db.execute(
                "SELECT chain_digest FROM audit ORDER BY id DESC LIMIT 1"
            )
            prev = await cur_prev.fetchone()
            prev_digest = str(prev[0]) if prev and prev[0] else "0000000000000000"
            entry = (
                f"{action_type}|{decision}|{composite_risk:.6f}|{summary}|{time.time():.6f}"
            )
            chain_digest = hash_chain_digest(prev_digest, entry)
            cur = await db.execute(
                "INSERT INTO audit(ts, action_type, decision, composite_risk, summary, chain_digest) VALUES(?,?,?,?,?,?)",
                (
                    time.time(),
                    action_type,
                    decision,
                    composite_risk,
                    summary,
                    chain_digest,
                ),
            )
            await db.commit()
            return int(cur.lastrowid)

    async def append_authority_event(
        self,
        *,
        request_id: str,
        action_type: str,
        decision: str,
        composite_risk: float,
        envelope: float,
        summary: str,
    ) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO authority_timeline(ts, request_id, action_type, decision, composite_risk, envelope, summary)
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    time.time(),
                    request_id,
                    action_type,
                    decision,
                    composite_risk,
                    envelope,
                    summary,
                ),
            )
            await db.commit()

    async def append_reversible_op(
        self,
        *,
        kind: str,
        detail: dict,
        inverse: dict,
        request_id: str | None = None,
    ) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """
                INSERT INTO reversible_ops(ts, kind, detail_json, inverse_json, status, request_id)
                VALUES(?,?,?,?, 'committed', ?)
                """,
                (
                    time.time(),
                    kind,
                    json.dumps(detail),
                    json.dumps(inverse),
                    request_id,
                ),
            )
            await db.commit()
            return int(cur.lastrowid)

    async def list_reversible_ops(self, limit: int = 40) -> list[Mapping[str, object]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT id, ts, kind, detail_json, inverse_json, status, request_id
                FROM reversible_ops ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            )
            rows = await cur.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["detail"] = json.loads(str(d.pop("detail_json")))
            d["inverse"] = json.loads(str(d.pop("inverse_json")))
            out.append(d)
        return out

    async def rollback_operation(self, op_id: int) -> dict[str, object]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, inverse_json, status FROM reversible_ops WHERE id = ?",
                (op_id,),
            )
            row = await cur.fetchone()
        if not row:
            return {"ok": False, "error": "operation not found"}
        if row["status"] != "committed":
            return {"ok": False, "error": "already rolled back or invalid"}
        inv = json.loads(row["inverse_json"])
        kind = inv.get("kind")
        try:
            if kind == "move":
                src, dst = inv["from"], inv["to"]
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(src):
                    ok, err = move_replace(src, dst)
                    if not ok:
                        return {"ok": False, "error": err}
            elif kind == "unlink":
                path = inv["path"]
                if os.path.lexists(path):
                    ok, err = unlink_path(path)
                    if not ok:
                        return {"ok": False, "error": err}
            elif kind == "write_restore":
                path = inv["path"]
                prev = inv.get("previous_content_b64")
                if prev is None:
                    if os.path.exists(path):
                        ok, err = unlink_path(path)
                        if not ok:
                            return {"ok": False, "error": err}
                else:
                    import base64

                    raw = base64.b64decode(prev.encode("ascii"))
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    ok, err = write_file(path, raw)
                    if not ok:
                        return {"ok": False, "error": err}
            else:
                return {"ok": False, "error": f"unknown inverse kind {kind}"}
        except OSError as e:
            return {"ok": False, "error": str(e)}

        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE reversible_ops SET status = 'rolled_back' WHERE id = ?",
                (op_id,),
            )
            await db.commit()
        return {"ok": True, "applied_inverse": inv}

    async def list_audit(self, limit: int = 50) -> list[Mapping[str, object]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, ts, action_type, decision, composite_risk, summary, chain_digest FROM audit ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_authority_timeline(self, limit: int = 80) -> list[Mapping[str, object]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT id, ts, request_id, action_type, decision, composite_risk, envelope, summary
                FROM authority_timeline ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            )
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def heatmap_buckets(self) -> list[dict[str, object]]:
        """Risk × action buckets for last records (UI heatmap)."""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT action_type, composite_risk, envelope FROM authority_timeline
                ORDER BY id DESC LIMIT 400
                """
            )
            rows = await cur.fetchall()
        cells: dict[tuple[str, int], list[float]] = {}
        for r in rows:
            at = str(r["action_type"])
            risk = float(r["composite_risk"])
            bucket = min(3, int(risk * 4))
            key = (at, bucket)
            cells.setdefault(key, []).append(risk)
        out: list[dict[str, object]] = []
        for (at, b), vals in cells.items():
            out.append(
                {
                    "action_type": at,
                    "risk_bucket": b,
                    "count": len(vals),
                    "avg_risk": sum(vals) / len(vals),
                }
            )
        out.sort(key=lambda x: (-int(x["count"]), str(x["action_type"])))
        return out
