"""Result model for a CLI run (lint, publish, …).

Mirrors datacontract-cli's ``Run``/``Check`` shape closely so the two tools feel
like siblings and share output tooling. The ``warning`` result level exists for
parity and forward-compat; 0.1 emits only ``passed`` / ``error``.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ResultEnum(str, Enum):
    passed = "passed"
    warning = "warning"
    error = "error"
    failed = "failed"


class Check(BaseModel):
    type: str = "lint"
    result: ResultEnum
    name: str
    reason: Optional[str] = None
    engine: str = "dataproduct"
    field: Optional[str] = None


class Run(BaseModel):
    result: ResultEnum = ResultEnum.passed
    checks: List[Check] = Field(default_factory=list)
    dataProductId: Optional[str] = None
    dataProductVersion: Optional[str] = None
    timestampStart: Optional[datetime] = None
    timestampEnd: Optional[datetime] = None
    logs: List[str] = Field(default_factory=list)

    @classmethod
    def create_run(cls) -> "Run":
        return cls(timestampStart=datetime.now(timezone.utc))

    def log_info(self, message: str) -> None:
        logging.info(message)
        self.logs.append(f"INFO {message}")

    def log_warn(self, message: str) -> None:
        logging.warning(message)
        self.logs.append(f"WARN {message}")

    def log_error(self, message: str) -> None:
        logging.error(message)
        self.logs.append(f"ERROR {message}")

    def has_passed(self) -> bool:
        return self.result == ResultEnum.passed

    def finish(self) -> None:
        """Compute the overall result and stamp the end time.

        Any ``error`` check fails the run; ``warning`` checks do not.
        """
        self.timestampEnd = datetime.now(timezone.utc)
        if any(c.result == ResultEnum.error for c in self.checks):
            self.result = ResultEnum.failed
        else:
            self.result = ResultEnum.passed
