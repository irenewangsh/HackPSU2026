"""Real hooks: file / URL / exec go through mediation + C path policy + sandboxed execution."""

from __future__ import annotations

import base64
import os
import subprocess
import time
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.capability_tokens import scope_allows, verify_capability
from app.config import settings
from app.models.schemas import ActionType, AgentActionRequest, DecisionType
from app.native_policy import (
    canonicalize_path,
    lstat_info,
    move_replace,
    namespace_exec,
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


def _require_capability(token: str | None, required_scope: str) -> dict:
    if not token:
        raise HTTPException(
            status_code=401,
            detail="capability_token required for non-dry-run hook execution",
        )
    payload = verify_capability(token)
    if not payload:
        raise HTTPException(status_code=401, detail="invalid or expired capability token")
    if not scope_allows(payload, required_scope):
        raise HTTPException(
            status_code=403,
            detail=f"token missing required scope: {required_scope}",
        )
    return payload


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
    action_type: Literal["read_file", "classify_file", "move_file", "rename_file", "delete_file"]
    source_path: str = Field(..., description="Path under sandbox_workspace")
    dest_path: str | None = None
    content_b64: str | None = None
    mime_type: str | None = "application/octet-stream"
    dry_run: bool = True
    capability_token: str | None = None
    session_id: str = "hook-demo"
    environment_hint: str | None = "home"


@router.post("/file")
async def hook_file(body: FileHookRequest):
    assert _mediator is not None
    src_resolved = _resolve_under_sandbox(body.source_path)
    dest_resolved = (
        _resolve_under_sandbox(body.dest_path) if body.dest_path else None
    )

    action_for_mediation = body.action_type
    if body.action_type in ("rename_file", "delete_file"):
        # Reuse move semantics in existing mediation path until dedicated hook action is chosen.
        action_for_mediation = "move_file"

    req = AgentActionRequest(
        action_type=ActionType(action_for_mediation),
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
        DecisionType.CONFIRM,
    ):
        return out

    _require_capability(body.capability_token, "hook:execute")

    if mediation.decision.decision not in (DecisionType.ALLOW, DecisionType.LIMITED):
        return out

    try:
        if body.action_type == "read_file":
            data = Path(src_resolved).read_bytes()
            out["executed"] = True
            out["read_bytes"] = len(data)
            out["preview_b64"] = base64.b64encode(data[:4096]).decode("ascii")
        elif body.action_type == "classify_file":
            data = Path(src_resolved).read_bytes()
            out["executed"] = True
            out["read_bytes"] = len(data)
            out["classification"] = {
                "size_bytes": len(data),
                "extension": Path(src_resolved).suffix.lower(),
            }
        elif body.action_type == "move_file":
            if not dest_resolved:
                raise HTTPException(400, "dest_path required for move")
            ok, err = move_replace(src_resolved, dest_resolved)
            if not ok:
                raise HTTPException(500, f"native move failed: {err}")
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
        elif body.action_type == "rename_file":
            if not dest_resolved:
                raise HTTPException(400, "dest_path required for rename")
            ok, err = move_replace(src_resolved, dest_resolved)
            if not ok:
                raise HTTPException(500, f"native rename failed: {err}")
            op_id = await _mediator.memory.append_reversible_op(
                kind="rename",
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
        elif body.action_type == "delete_file":
            backup = src_resolved + ".sentinel_deleted_backup"
            if os.path.exists(src_resolved):
                ok, err = move_replace(src_resolved, backup)
                if not ok:
                    raise HTTPException(500, f"native delete backup move failed: {err}")
            op_id = await _mediator.memory.append_reversible_op(
                kind="delete",
                detail={"path": src_resolved},
                inverse={"kind": "move", "from": backup, "to": src_resolved},
                request_id=mediation.request_id,
            )
            out["executed"] = True
            out["reversible_op_id"] = op_id
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return out


class BrowserHookRequest(BaseModel):
    target_url: str
    capability_token: str | None = None
    automate: bool = False
    timeout_sec: int = 10
    steps: list[dict] = Field(
        default_factory=list,
        description="Optional Playwright steps, e.g. {type:'click', selector:'#submit'}",
    )
    session_id: str = "hook-demo"
    environment_hint: str | None = "home"


@router.post("/browser")
async def hook_browser(body: BrowserHookRequest):
    assert _mediator is not None
    req = AgentActionRequest(
        action_type=ActionType.OPEN_WEBSITE,
        target_url=body.target_url,
        session_id=body.session_id,
        environment_hint=body.environment_hint,
    )
    mediation = await _mediator.mediate(req)
    digest = policy_digest(["browser", body.target_url, mediation.decision.decision.value])
    browser_result: dict | None = None
    if body.automate and mediation.decision.decision in (
        DecisionType.ALLOW,
        DecisionType.LIMITED,
    ):
        _require_capability(body.capability_token, "hook:execute")
        browser_result = await _run_playwright(
            target_url=body.target_url,
            steps=body.steps,
            timeout_sec=body.timeout_sec,
        )
    return {
        "mediation": mediation.model_dump(),
        "note": "Browser surface is mediated; integrate with extension/Playwright using this policy digest.",
        "policy_digest": digest,
        "browser_automation": browser_result,
        "native": native_status(),
    }


class ExecHookRequest(BaseModel):
    argv: list[str] = Field(..., min_length=1)
    capability_token: str | None = None
    prefer_container: bool = True
    session_id: str = "hook-demo"
    environment_hint: str | None = "public_wifi"


@router.post("/exec")
async def hook_exec(body: ExecHookRequest):
    assert _mediator is not None
    preview = " ".join(body.argv)[:800]
    req = AgentActionRequest(
        action_type=ActionType.RUN_SHELL,
        payload_preview=preview,
        session_id=body.session_id,
        environment_hint=body.environment_hint,
    )
    mediation = await _mediator.mediate(req)
    out: dict = {"mediation": mediation.model_dump(), "executed": False}

    if mediation.decision.decision in (DecisionType.DENY, DecisionType.CONFIRM):
        return out
    if mediation.decision.decision not in (DecisionType.ALLOW, DecisionType.LIMITED):
        return out

    _require_capability(body.capability_token, "hook:execute")

    root = _root()
    tmp = os.path.join(root, ".tmp")
    os.makedirs(tmp, exist_ok=True)

    if body.prefer_container and settings.enable_container_exec:
        cont = _sandbox_exec_container(
            argv=body.argv,
            cwd=root,
            timeout_sec=settings.exec_timeout_sec,
        )
        if cont["ok"]:
            out.update(cont["payload"])
            return out
        out["container_note"] = cont["error"]

    if settings.enable_namespace_exec:
        ok_ns, code_ns, err_ns = namespace_exec(
            body.argv,
            root,
            timeout_sec=settings.exec_timeout_sec,
        )
        if ok_ns:
            out["executed"] = True
            out["engine"] = "c_linux_namespace_exec"
            out["returncode"] = code_ns
            out["stdout"] = ""
            out["stderr"] = ""
            return out
        out["namespace_note"] = err_ns

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


def _sandbox_exec_container(argv: list[str], cwd: str, timeout_sec: int) -> dict:
    """
    Real isolation path using Docker:
      - no network
      - read-only root
      - bind mount only sandbox workspace
      - no-new-privileges + dropped caps
    """
    image = settings.container_image
    cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "-v",
        f"{cwd}:/workspace:rw",
        "-w",
        "/workspace",
        image,
        *argv,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(1, timeout_sec),
        )
    except FileNotFoundError:
        return {"ok": False, "error": "docker binary not found; falling back"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "container exec timeout; falling back"}
    except OSError as e:
        return {"ok": False, "error": f"container exec error: {e}"}
    return {
        "ok": True,
        "payload": {
            "executed": True,
            "engine": "docker_isolated_container",
            "returncode": proc.returncode,
            "stdout": proc.stdout[:12000],
            "stderr": proc.stderr[:8000],
        },
    }


async def _run_playwright(
    *, target_url: str, steps: list[dict], timeout_sec: int
) -> dict:
    """
    Real browser control hook via Playwright.
    Optional dependency: playwright + browser binaries.
    """
    started = time.time()
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except Exception:
        return {
            "ok": False,
            "error": "playwright not installed. run: pip install playwright && playwright install chromium",
        }

    events: list[str] = []
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
            events.append(f"goto:{target_url}")
            for step in steps:
                t = str(step.get("type", "")).lower()
                selector = step.get("selector")
                if t == "click" and selector:
                    await page.click(str(selector), timeout=timeout_sec * 1000)
                    events.append(f"click:{selector}")
                elif t == "fill" and selector:
                    await page.fill(str(selector), str(step.get("value", "")), timeout=timeout_sec * 1000)
                    events.append(f"fill:{selector}")
                elif t == "press" and selector:
                    await page.press(str(selector), str(step.get("key", "Enter")), timeout=timeout_sec * 1000)
                    events.append(f"press:{selector}")
                elif t == "wait":
                    ms = int(step.get("ms", 300))
                    await page.wait_for_timeout(max(0, ms))
                    events.append(f"wait:{ms}")
            title = await page.title()
            final_url = page.url
            await browser.close()
    except Exception as e:
        return {"ok": False, "error": str(e), "events": events}

    return {
        "ok": True,
        "title": title,
        "final_url": final_url,
        "events": events,
        "elapsed_ms": int((time.time() - started) * 1000),
    }
