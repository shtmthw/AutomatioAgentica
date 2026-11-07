"""Resumable execution state for one production (build/<slug>/state.json).

Each stage (and each per-language part, e.g. "render:hi") records its status and
the fingerprint of the inputs it was produced from. A stage is skipped when it is
`done` with the same fingerprint, so an interrupted or repeated run continues where
it stopped and never redoes successful (or paid) work. Heavy artefacts live in a
content-addressed cache (cache/), so even invalidated stages reuse unchanged parts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import Locked
from .util import atomic_write_json, now_iso, read_json

SCHEMA = 1


class State:
    def __init__(self, build_dir: Path):
        self.dir = Path(build_dir)
        self.path = self.dir / "state.json"
        self.data = read_json(self.path) or {"schema": SCHEMA, "stages": {}, "approval": None,
                                              "spent": {}, "created_at": now_iso()}

    # ------------------------------------------------------------ stages
    def stage(self, sid: str) -> dict:
        return self.data["stages"].get(sid, {})

    def fresh(self, sid: str, fp: str) -> bool:
        s = self.stage(sid)
        return s.get("status") == "done" and s.get("fingerprint") == fp

    def mark(self, sid: str, status: str, fp: str | None = None, **info) -> None:
        cur = self.data["stages"].setdefault(sid, {})
        if status == "running":
            for k in ("error", "task", "approval"):
                cur.pop(k, None)
            cur["started_at"] = now_iso()
            cur["pid"] = os.getpid()
        else:
            cur.pop("pid", None)
            cur["finished_at"] = now_iso()
        cur["status"] = status
        if fp is not None:
            cur["fingerprint"] = fp
        cur.update(info)
        self.save()

    def invalidate(self, prefix: str) -> list[str]:
        hit = [k for k in self.data["stages"] if k == prefix or k.startswith(prefix + ":")]
        for k in hit:
            self.data["stages"][k]["status"] = "stale"
        self.save()
        return hit

    # ------------------------------------------------------------ approval / spend
    @property
    def approval(self) -> dict | None:
        return self.data.get("approval")

    def set_approval(self, rec: dict) -> None:
        self.data["approval"] = rec
        self.save()

    def spent(self, provider: str) -> float:
        return float(self.data.get("spent", {}).get(provider, 0.0))

    def add_spent(self, provider: str, amount: float) -> None:
        sp = self.data.setdefault("spent", {})
        sp[provider] = float(sp.get(provider, 0.0)) + float(amount)
        self.save()

    def save(self) -> None:
        self.data["updated_at"] = now_iso()
        atomic_write_json(self.path, self.data)

    # ------------------------------------------------------------ events / progress
    def event(self, kind: str, **data) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.dir / "events.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"t": now_iso(), "event": kind, **data}, ensure_ascii=False, default=str) + "\n")

    def progress(self, stage: str, done: int, total: int, detail: str = "") -> None:
        atomic_write_json(self.dir / "progress.json", {"stage": stage, "done": done, "total": total,
                                                         "detail": detail, "updated_at": now_iso(),
                                                         "pid": os.getpid()})

    def read_progress(self) -> dict | None:
        return read_json(self.dir / "progress.json")


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class RunLock:
    """One `run` per production at a time. A lock left by a dead process is stale and
    is taken over (that is how an interrupted run resumes)."""

    def __init__(self, build_dir: Path, command: str):
        self.path = Path(build_dir) / "run.lock"
        self.command = command

    def holder(self) -> dict | None:
        d = read_json(self.path)
        if d and pid_alive(int(d.get("pid", -1))):
            return d
        return None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        h = self.holder()
        if h and h.get("pid") != os.getpid():
            raise Locked(f"another run of this production is in progress (pid {h['pid']}, since {h.get('since')})",
                         remedy="Wait for it to finish (`status` shows progress) or stop that process.",
                         details=h)
        stale = read_json(self.path)
        atomic_write_json(self.path, {"pid": os.getpid(), "since": now_iso(), "command": self.command,
                                      "took_over": stale if stale else None})
        return self

    def __exit__(self, *exc):
        d = read_json(self.path)
        if d and d.get("pid") == os.getpid():
            self.path.unlink(missing_ok=True)
        return False

