"""Logging with secret redaction. Human-readable progress goes to stderr (so that
`--json` output on stdout stays machine-readable) and to the run log file."""
from __future__ import annotations

import logging
import sys

from .secrets import redact

log = logging.getLogger("automatio")


class _Redact(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = ()
        return True


def setup(verbose: bool = False, quiet: bool = False) -> None:
    if getattr(setup, "_done", False):
        return
    log.setLevel(logging.DEBUG)
    h = logging.StreamHandler(sys.stderr)
    h.setLevel(logging.WARNING if quiet else (logging.DEBUG if verbose else logging.INFO))
    h.setFormatter(logging.Formatter("%(message)s"))
    h.addFilter(_Redact())
    log.addHandler(h)
    log.propagate = False
    setup._done = True


def add_file(path) -> logging.Handler:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = logging.FileHandler(path, encoding="utf-8")
    h.setLevel(logging.DEBUG)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    h.addFilter(_Redact())
    log.addHandler(h)
    return h


def remove(handler: logging.Handler) -> None:
    log.removeHandler(handler)
    handler.close()
