"""Small helpers shared by the stages: hashing, atomic files, links, ffprobe, subprocesses."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

from . import ROOT
from .errors import MissingCapability, StageFailed
from .secrets import redact, scrubbed_env


# ------------------------------------------------------------------ hashing
def stable_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def fingerprint(*objs, n: int = 20) -> str:
    return hashlib.sha1(stable_json(list(objs)).encode("utf-8")).hexdigest()[:n]


_file_fp_cache: dict[tuple, str] = {}


def file_fp(path: Path, n: int = 20) -> str:
    """sha1 of a file's bytes (memoised per (path, size, mtime) within this process)."""
    p = Path(path)
    st = p.stat()
    key = (str(p.resolve()), st.st_size, st.st_mtime_ns)
    if key not in _file_fp_cache:
        h = hashlib.sha1()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        _file_fp_cache[key] = h.hexdigest()
    return _file_fp_cache[key][:n]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_fp(paths) -> str:
    """Fingerprint of several files (order-independent, content-based)."""
    items = sorted((rel(p), file_fp(p)) for p in paths)
    return fingerprint(items)


# ------------------------------------------------------------------ files
def atomic_write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, obj, indent: int | None = 1) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=indent, default=str) + "\n")


def read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def tmp_path(path: Path) -> Path:
    """A sibling temp path that keeps the extension (ffmpeg/manim infer formats from it)."""
    path = Path(path)
    return path.with_name(f".{path.stem}.partial{path.suffix}")


def link_or_copy(src: Path, dst: Path) -> None:
    """Hard-link src to dst (no extra disk space), falling back to a copy. Replaces dst atomically."""
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.link")
    tmp.unlink(missing_ok=True)
    try:
        os.link(src, tmp)
    except OSError:
        shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def rel(path) -> str:
    p = Path(path).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def resolve(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else (ROOT / p)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def fmt_time(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


# ------------------------------------------------------------------ processes
def which(name: str) -> str | None:
    return shutil.which(name)


def need_tool(name: str) -> str:
    p = which(name)
    if not p:
        raise MissingCapability(f"`{name}` is not installed or not on PATH.",
                                remedy=f"Install {name} (e.g. `pacman -S ffmpeg` / `apt install ffmpeg`).")
    return p


_CHILDREN: set = set()
_CHILDREN_LOCK = threading.Lock()
STOPPING = threading.Event()     # set on SIGINT/SIGTERM: no new subprocess may start


def terminate_children(grace: float = 5.0) -> int:
    """Stop every subprocess started through run() (called on SIGINT/SIGTERM), so an
    interrupted run leaves no orphaned manim/ffmpeg processes behind. From now on no
    new subprocess starts (worker threads holding queued renders fail fast instead)."""
    import time as _time
    STOPPING.set()
    with _CHILDREN_LOCK:
        procs = list(_CHILDREN)
    for p in procs:
        try:
            p.terminate()
        except OSError:
            pass
    deadline = _time.time() + grace
    for p in procs:
        try:
            p.wait(max(0.05, deadline - _time.time()))
        except subprocess.TimeoutExpired:
            p.kill()
    return len(procs)


def _spawn(cmd, *, cwd, env, stdout, stderr, text, timeout, essential=False):
    with _CHILDREN_LOCK:
        if STOPPING.is_set() and not essential:
            raise StageFailed("interrupted: not starting new work")
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=stdout, stderr=stderr, text=text)
        _CHILDREN.add(p)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        raise
    finally:
        with _CHILDREN_LOCK:
            _CHILDREN.discard(p)
    return subprocess.CompletedProcess(cmd, p.returncode, out, err)


def run(cmd: list, *, log_file: Path | None = None, cwd: Path | None = None, env: dict | None = None,
        capture: bool = False, timeout: float | None = None, what: str | None = None,
        essential: bool = False) -> subprocess.CompletedProcess:
    """Run a subprocess with a credential-free environment. Raises StageFailed with
    the tail of the output on failure. `essential` commands (quick probes that finish
    recording work already paid for) still run while an interrupt is in progress."""
    env = scrubbed_env(env)
    cmd = [str(c) for c in cmd]
    try:
        if log_file is not None:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "w", encoding="utf-8") as fh:
                cp = _spawn(cmd, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT, text=False, timeout=timeout,
                            essential=essential)
            if cp.returncode != 0:
                tail = Path(log_file).read_text(encoding="utf-8", errors="replace").splitlines()[-25:]
                raise StageFailed(f"{what or cmd[0]} failed (exit {cp.returncode}); see {rel(log_file)}",
                                  details={"log": rel(log_file), "tail": [redact(t) for t in tail]})
            return cp
        cp = _spawn(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout,
                    essential=essential)
    except subprocess.TimeoutExpired as e:
        raise StageFailed(f"{what or cmd[0]} timed out after {timeout}s") from e
    if cp.returncode != 0:
        tail = (cp.stderr or cp.stdout or "").splitlines()[-25:]
        raise StageFailed(f"{what or cmd[0]} failed (exit {cp.returncode}): {redact(' | '.join(tail[-3:]))}",
                          details={"tail": [redact(t) for t in tail]})
    return cp


def ffprobe(path: Path) -> dict:
    cp = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
             capture=True, what="ffprobe", essential=True)
    return json.loads(cp.stdout)


def probe_duration(path: Path) -> float:
    cp = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
             capture=True, what="ffprobe", essential=True)
    return float(cp.stdout.strip())
