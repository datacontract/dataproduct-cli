"""Lint linked data contracts with datacontract-cli, when it is installed.

Only used by the ``dataproduct lint`` command (not the library API): it shells
out to whatever ``datacontract`` is on the PATH. A contract that fails its own
lint is reported as a ``warning`` on the data product run.

If ``datacontract`` is not on the PATH, a single ``warning`` says so. Before
linting, ``datacontract --version`` must also succeed; otherwise a single
``warning`` explains why the contracts were not linted (e.g. a broken install
or launcher on Windows) instead of one cryptic failure per contract.
"""

import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional

from dataproduct.lint.references import ResolvedContract
from dataproduct.model.run import Check, ResultEnum

DATACONTRACT_EXECUTABLE = "datacontract"
TIMEOUT_SECONDS = 120
VERSION_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 2000
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def datacontract_cli_path() -> Optional[str]:
    return shutil.which(DATACONTRACT_EXECUTABLE)


def lint_contracts_with_datacontract_cli(contracts: List[ResolvedContract], executable: str) -> List[Check]:
    """Lint each contract with ``executable``; a bare name (e.g. ``datacontract``) is looked up on the PATH."""
    if not contracts:
        return []
    problem = _check_runnable(executable)
    if problem is not None:
        return [
            Check(
                type="lint",
                result=ResultEnum.warning,
                name="datacontract-cli is runnable",
                reason=f"Skipped linting {len(contracts)} linked data contract(s): {problem}",
            )
        ]
    return [_lint_contract(contract, executable) for contract in contracts]


def _check_runnable(executable: str) -> Optional[str]:
    """``None`` if ``datacontract --version`` succeeds, else a description of what went wrong."""
    if not os.path.dirname(executable) and shutil.which(executable) is None:
        return (
            f"'{executable}' was not found on the PATH. Install datacontract-cli (pip install datacontract-cli) "
            "to lint them, or pass --no-resolve-references."
        )
    try:
        completed = _run([executable, "--version"], VERSION_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return f"'{executable} --version' did not finish within {VERSION_TIMEOUT_SECONDS}s."
    except Exception as e:
        return f"Could not run '{executable}': {e}"
    if completed.returncode != 0:
        return f"'{executable} --version' exited with {completed.returncode}:\n{_output(completed)}"
    return None


def _lint_contract(contract: ResolvedContract, executable: str) -> Check:
    name = f"Data contract '{contract.contract_id}' passes datacontract lint"
    try:
        # The environment is inherited, so datacontract-cli sends ENTROPY_DATA_API_KEY to the platform URL itself.
        completed = _run([executable, "lint", contract.location], TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return Check(
            type="lint",
            result=ResultEnum.warning,
            name=name,
            reason=f"datacontract lint {contract.location} did not finish within {TIMEOUT_SECONDS}s.",
        )
    except Exception as e:
        return Check(type="lint", result=ResultEnum.warning, name=name, reason=f"Could not run datacontract lint: {e}")

    if completed.returncode == 0:
        return Check(type="lint", result=ResultEnum.passed, name=name, reason=contract.location)
    return Check(
        type="lint",
        result=ResultEnum.warning,
        name=name,
        reason=f"datacontract lint {contract.location} exited with {completed.returncode}:\n{_output(completed)}",
    )


def _run(args: List[str], timeout: int) -> subprocess.CompletedProcess:
    # Decode as UTF-8 regardless of the locale (cp1252 on Windows), and never block on stdin.
    return subprocess.run(
        args,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=_child_env(),
    )


def _child_env() -> Dict[str, str]:
    """The inherited environment, with datacontract-cli (Python + rich) told to write plain UTF-8."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NO_COLOR"] = "1"
    env.setdefault("COLUMNS", "200")
    return env


def _output(completed: subprocess.CompletedProcess) -> str:
    output = _ANSI_ESCAPE.sub("", (completed.stdout or "") + (completed.stderr or "")).strip()
    if not output:
        return "(no output)"
    if len(output) > MAX_OUTPUT_CHARS:
        output = "…" + output[-MAX_OUTPUT_CHARS:]
    return output
