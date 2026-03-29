"""Load C policy helpers (realpath, sandbox prefix, FNV-1a digest) with safe Python fallbacks."""

from __future__ import annotations

import ctypes
import os
from ctypes import (
    POINTER,
    byref,
    c_char_p,
    c_int,
    c_size_t,
    c_uint,
    c_uint64,
    c_uint8,
    create_string_buffer,
)
from pathlib import Path
from typing import Any

_LIB: ctypes.CDLL | None = None


def _lib_candidates() -> list[Path]:
    root = Path(__file__).resolve().parent.parent.parent / "native"
    return [root / "libsentinel.dylib", root / "libsentinel.so"]


def _load() -> ctypes.CDLL | None:
    global _LIB
    if _LIB is not None:
        return _LIB
    for p in _lib_candidates():
        if p.exists():
            try:
                _LIB = ctypes.CDLL(str(p))
                _LIB.sentinel_realpath.argtypes = [c_char_p, c_char_p, c_size_t]
                _LIB.sentinel_realpath.restype = c_int
                _LIB.sentinel_within_root.argtypes = [c_char_p, c_char_p]
                _LIB.sentinel_within_root.restype = c_int
                _LIB.sentinel_hash64.argtypes = [POINTER(c_uint8), c_size_t]
                _LIB.sentinel_hash64.restype = c_uint64
                _LIB.sentinel_lstat_info.argtypes = [
                    c_char_p,
                    POINTER(c_uint),
                    POINTER(c_int),
                ]
                _LIB.sentinel_lstat_info.restype = c_int
                _LIB.sentinel_sandbox_exec.argtypes = [
                    c_char_p,
                    POINTER(c_char_p),
                    c_char_p,
                    c_size_t,
                    c_char_p,
                    c_size_t,
                    POINTER(c_int),
                    c_uint,
                ]
                _LIB.sentinel_sandbox_exec.restype = c_int
                return _LIB
            except OSError:
                continue
    return None


def fnv1a64_py(data: bytes) -> int:
    h = 14695981039346656037
    prime = 1099511628211
    for b in data:
        h ^= b
        h = (h * prime) & 0xFFFFFFFFFFFFFFFF
    return h


def policy_digest(parts: list[str]) -> str:
    blob = "\n".join(parts).encode("utf-8")
    lib = _load()
    if lib:
        buf = (c_uint8 * len(blob))(*blob)
        h = int(lib.sentinel_hash64(buf, len(blob)))
    else:
        h = fnv1a64_py(blob)
    return f"{h:016x}"


def canonicalize_path(path: str) -> tuple[bool, str]:
    lib = _load()
    if lib:
        out = create_string_buffer(8192)
        rc = lib.sentinel_realpath(path.encode("utf-8"), out, 8192)
        if rc == 0:
            return True, out.value.decode("utf-8", errors="replace")
        return False, os.path.realpath(path) if os.path.exists(path) else ""
    try:
        return True, os.path.realpath(path)
    except Exception:
        return False, ""


def within_sandbox(canon_path: str, root: str) -> bool:
    lib = _load()
    cr = os.path.realpath(root)
    if lib:
        return bool(
            lib.sentinel_within_root(
                canon_path.encode("utf-8"),
                cr.encode("utf-8"),
            )
        )
    if canon_path == cr:
        return True
    return canon_path.startswith(cr + os.sep)


def lstat_info(path: str) -> tuple[bool, int, bool]:
    """Return (ok, st_mode, is_symlink). Fallback uses Python os.stat."""
    lib = _load()
    if lib:
        mode = c_uint(0)
        islnk = c_int(0)
        rc = lib.sentinel_lstat_info(path.encode("utf-8"), byref(mode), byref(islnk))
        if rc == 0:
            return True, int(mode.value), bool(islnk.value)
    try:
        import stat as statmod

        st = os.lstat(path)
        return True, st.st_mode, bool(statmod.S_ISLNK(st.st_mode))
    except OSError:
        return False, 0, False


def sandbox_exec(
    argv: list[str],
    cwd: str,
    *,
    timeout_sec: int = 8,
    stdout_cap: int = 65536,
    stderr_cap: int = 16384,
) -> tuple[bool, int, str, str, str | None]:
    """
    Run via C (fork/pipe/execve). Returns:
      ok, exit_code, stdout, stderr, error_message_if_any
    """
    lib = _load()
    if not lib or not argv:
        return False, -1, "", "", "native library or argv missing"
    n = len(argv)
    argv_c = (c_char_p * (n + 1))()
    for i, a in enumerate(argv):
        argv_c[i] = a.encode("utf-8")
    argv_c[n] = None
    out_buf = create_string_buffer(stdout_cap)
    err_buf = create_string_buffer(stderr_cap)
    code = c_int(-1)
    rc = lib.sentinel_sandbox_exec(
        cwd.encode("utf-8"),
        argv_c,
        out_buf,
        c_size_t(stdout_cap),
        err_buf,
        c_size_t(stderr_cap),
        byref(code),
        c_uint(max(1, timeout_sec)),
    )
    if rc != 0:
        return False, -1, "", "", f"sentinel_sandbox_exec failed (errno={ctypes_get_errno()})"
    return True, int(code.value), out_buf.value.decode("utf-8", errors="replace"), err_buf.value.decode(
        "utf-8", errors="replace"
    ), None


def ctypes_get_errno() -> int:
    try:
        return ctypes.get_errno()
    except Exception:
        return -1


def native_status() -> dict[str, Any]:
    lib = _load()
    return {
        "c_library_loaded": lib is not None,
        "library_path": next((str(p) for p in _lib_candidates() if p.exists()), None),
        "c_components": [
            "sentinel_policy.c: realpath, prefix check, FNV-1a",
            "sentinel_fs.c: lstat symlink/mode",
            "sentinel_exec.c: fork, pipe, poll, execve, setrlimit(RLIMIT_CPU)",
        ],
    }
