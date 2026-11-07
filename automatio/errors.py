"""Typed errors. Every error carries a stable `code`, a human message, an optional
`remedy` (what the user or harness should do) and maps to a CLI exit code, so a
harness can react without parsing prose.

Exit codes (also used for `run` / `next` outcomes):
    0  done                 everything requested is complete
    1  failed               a stage failed (see error.code / message)
    2  usage                bad command line
    10 needs_agent          an agent task is waiting for the harness (see task)
    11 needs_approval       the user must approve the configuration / budget
    12 blocked              missing credential, permission, tool or capability
    13 locked               another run of this production is in progress
"""
from __future__ import annotations

EXIT = {"done": 0, "failed": 1, "usage": 2, "needs_agent": 10, "needs_approval": 11,
        "blocked": 12, "locked": 13}


class AAError(Exception):
    code = "error"
    outcome = "failed"

    def __init__(self, message: str, *, remedy: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.remedy = remedy
        self.details = details or {}

    @property
    def exit_code(self) -> int:
        return EXIT[self.outcome]

    def to_dict(self) -> dict:
        from .secrets import redact
        d = {"code": self.code, "message": redact(self.message)}
        if self.remedy:
            d["remedy"] = redact(self.remedy)
        if self.details:
            d["details"] = self.details
        return d


class UsageError(AAError):
    code = "usage"
    outcome = "usage"


class ConfigError(AAError):
    code = "config_invalid"


class InputError(AAError):
    code = "input_invalid"


class ValidationFailed(AAError):
    code = "validation_failed"


class StageFailed(AAError):
    code = "stage_failed"


class MissingCredential(AAError):
    code = "missing_credential"
    outcome = "blocked"


class InvalidCredential(AAError):
    code = "invalid_credential"
    outcome = "blocked"


class MissingCapability(AAError):
    code = "missing_capability"
    outcome = "blocked"


class ProviderError(AAError):
    """A provider (TTS API) failed. `retryable` errors are retried with backoff
    before they surface; non-retryable ones stop the stage immediately."""
    code = "provider_error"

    def __init__(self, message: str, *, status: int | None = None, retryable: bool = False,
                 retry_after: float | None = None, **kw):
        super().__init__(message, **kw)
        self.status = status
        self.retryable = retryable
        self.retry_after = retry_after


class ProviderBlocked(ProviderError):
    """The provider refuses this account/key (permissions, plan) - a human must act."""
    code = "provider_blocked"
    outcome = "blocked"


class QuotaExceeded(ProviderError):
    code = "quota_exceeded"
    outcome = "blocked"


class BudgetExceeded(AAError):
    code = "budget_exceeded"
    outcome = "needs_approval"


class Locked(AAError):
    code = "locked"
    outcome = "locked"
