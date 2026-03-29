"""Real hooks: file / URL / exec go through mediation + C path policy + sandboxed execution."""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.models.schemas import ActionType, AgentActionRequest, DecisionType
from app.native_policy import (
    canonicalize_path,
    lstat_info,
    native_status,
    policy_digest,
    sandbox_exec,
    within_sandbox,
)
from app.services.mediator import MediatorService

router = APIRouter(prefix="/api/v1/hooks", tags=["hooks"])

_mediator: MediatorService | None = None


def bind_mediator(m: MediatorService) -> None:
    global _mediator
    _mediator = m


def _root() -> str:
    return str(Path(settings.sandbox_root).resolve())


def _resolve_under_sandbox(user_path: str) -> str:
    root = Path(settings.sandbox_root)
    root.mkdir(parents=True, exist_ok=True)
    p = Path(user_path)
    if not p.is_absolute():
        p = (root / p).resolve()
    else:
        p = p.resolve()
    ok, canon = canonicalize_path(str(p))
    if not ok or not canon:
        raise HTTPException(status_code=400, detail="invalid path")
    if not within_sandbox(canon, str(root.resolve())):
        raise HTTPException(
            status_code=403,
            detail="path outside sandbox — place assets under sandbox_workspace/",
        )
    return canon


class FileHookRequest(BaseModel):
    action_type: Literal["read_file", "write_file", "move_file"]
    source_path: str = Field(..., description="Path under sandbox_workspace")
    dest_path: str | None = None
    content_b64: str | None = None
    mime_type: str | None = "application/octet-stream"
    dry_run: bool = True
    session_id: str = "hook-demo"
    environment_hint: str | None = "home"


@router.post("/file")
async def hook_file(body: FileHookRequest):
    assert _mediator is not None
    src_resolved = _resolve_under_sandbox(body.source_path)
    dest_resolved = (
        _resolve_under_sandbox(body.dest_path) if body.dest_path else None
    )

    req = AgentActionRequest(
        action_type=ActionType(body.action_type),
        target_path=src_resolved,
        mime_type=body.mime_type,
        payload_preview=None,
        session_id=body.session_id,
        environment_hint=body.environment_hint,
        overwrite=bool(body.dest_path and body.action_type == "move_file"),
    )
    mediation = await _mediator.mediate(req)

    out: dict = {"mediation": mediation.model_dump(), "executed": False}
    ls_ok, st_mode, is_sym = lstat_info(src_resolved)
    if ls_ok:
        out["c_fs"] = {
            "st_mode_oct": oct(st_mode),
            "is_symlink": is_sym,
        }

    if body.dry_run or mediation.decision.decision in (
        DecisionType.DENY,
        DecisionType.PROMPT_USER,
    ):
        return out

    if mediation.decision.decision not in (DecisionType.ALLOW, DecisionType.TRANSFORM):
        return out

    try:
        if body.action_type == "read_file":
            data = Path(src_resolved).read_bytes()
            out["executed"] = True
            out["read_bytes"] = len(data)
            out["preview_b64"] = base64.b64encode(data[:4096]).decode("ascii")
        elif body.action_type == "write_file":
            if not body.content_b64:
                raise HTTPException(400, "content_b64 required for write")
            raw = base64.b64decode(body.content_b64)
            prev = None
            if Path(src_resolved).exists():
                prev = base64.b64encode(Path(src_resolved).read_bytes()).decode("ascii")
            Path(src_resolved).parent.mkdir(parents=True, exist_ok=True)
            Path(src_resolved).write_bytes(raw)
            op_id = await _mediator.memory.append_reversible_op(
                kind="write",
                detail={"path": src_resolved, "bytes": len(raw)},
                inverse={
                    "kind": "write_restore",
                    "path": src_resolved,
                    "previous_content_b64": prev,
                },
                request_id=mediation.request_id,
            )
            out["executed"] = True
            out["reversible_op_id"] = op_id
        elif body.action_type == "move_file":
            if not dest_resolved:
                raise HTTPException(400, "dest_path required for move")
            shutil.move(src_resolved, dest_resolved)
            op_id = await _mediator.memory.append_reversible_op(
                kind="move",
                detail={"from": src_resolved, "to": dest_resolved},
                inverse={
                    "kind": "move",
                    "from": dest_resolved,
                    "to": src_resolved,
                },
                request_id=mediation.request_id,
            )
            out["executed"] = True
            out["reversible_op_id"] = op_id
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return out


class BrowserHookRequest(BaseModel):
    target_url: str
    session_id: str = "hook-demo"
    environment_hint: str | None = "home"


@router.post("/browser")
async def hook_browser(body: BrowserHookRequest):
    assert _mediator is not None
    req = AgentActionRequest(
        action_type=ActionType.OPEN_URL,
        target_url=body.target_url,
        session_id=body.session_id,
        environment_hint=body.environment_hint,
    )
    mediation = await _mediator.mediate(req)
    digest = policy_digest(["browser", body.target_url, mediation.decision.decision.value])
    return {
        "mediation": mediation.model_dump(),
        "note": "Browser surface is mediated; integrate with extension/Playwright using this policy digest.",
        "policy_digest": digest,
        "native": native_status(),
    }


class ExecHookRequest(BaseModel):
    argv: list[str] = Field(..., min_length=1)
    session_id: str = "hook-demo"
    environment_hint: str | None = "public_wifi"


@router.post("/exec")
async def hook_exec(body: ExecHookRequest):
    assert _mediator is not None
    preview = " ".join(body.argv)[:800]
    req = AgentActionRequest(
        action_type=ActionType.SHELL,
        payload_preview=preview,
        session_id=body.session_id,
        environment_hint=body.environment_hint,
    )
    mediation = await _mediator.mediate(req)
    out: dict = {"mediation": mediation.model_dump(), "executed": False}

    if mediation.decision.decision in (DecisionType.DENY, DecisionType.PROMPT_USER):
        return out
    if mediation.decision.decision not in (DecisionType.ALLOW, DecisionType.TRANSFORM):
        return out

    root = _root()
    tmp = os.path.join(root, ".tmp")
    os.makedirs(tmp, exist_ok=True)

    ok_c, code, so, se, cerr = sandbox_exec(
        body.argv,
        root,
        timeout_sec=settings.exec_timeout_sec,
    )
    if ok_c and cerr is None:
        out["executed"] = True
        out["returncode"] = code
        out["stdout"] = so[:12000]
        out["stderr"] = se[:8000]
        out["engine"] = "c_fork_pipe_execve"
        return out

    out["c_exec_note"] = cerr or "c_exec_failed"
    try:
        proc = subprocess.run(
            body.argv,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=settings.exec_timeout_sec,
            env={
                "SENTINEL_SANDBOX": "1",
                "HOME": root,
                "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
                "TMPDIR": tmp,
            },
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="sandbox exec timeout") from None
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    out["executed"] = True
    out["returncode"] = proc.returncode
    out["stdout"] = proc.stdout[:12000]
    out["stderr"] = proc.stderr[:8000]
    out["engine"] = "python_subprocess_fallback"
    return out


@router.get("/native")
async def native_info():
    return native_status()
