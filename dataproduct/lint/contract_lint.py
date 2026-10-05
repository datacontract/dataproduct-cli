"""Lint linked data contracts with datacontract-cli, when it is installed.

Only used by the ``dataproduct lint`` command (not the library API): it shells
out to whatever ``datacontract`` is on the PATH. A contract that fails its own
lint is reported as a ``warning`` on the data product run.
"""

import shutil
import subprocess
from typing import List, Optional

from dataproduct.lint.references import ResolvedContract
from dataproduct.model.run import Check, ResultEnum

DATACONTRACT_EXECUTABLE = "datacontract"
TIMEOUT_SECONDS = 120


def datacontract_cli_path() -> Optional[str]:
    return shutil.which(DATACONTRACT_EXECUTABLE)


def lint_contracts_with_datacontract_cli(contracts: List[ResolvedContract], executable: str) -> List[Check]:
    return [_lint_contract(contract, executable) for contract in contracts]


def _lint_contract(contract: ResolvedContract, executable: str) -> Check:
    name = f"Data contract '{contract.contract_id}' passes datacontract lint"
    try:
        # The environment is inherited, so datacontract-cli sends ENTROPY_DATA_API_KEY to the platform URL itself.
        completed = subprocess.run(
            [executable, "lint", contract.location],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return Check(type="lint", result=ResultEnum.warning, name=name, reason=f"Could not run datacontract lint: {e}")

    if completed.returncode == 0:
        return Check(type="lint", result=ResultEnum.passed, name=name, reason=contract.location)
    output = (completed.stdout + completed.stderr).strip()
    return Check(
        type="lint",
        result=ResultEnum.warning,
        name=name,
        reason=f"datacontract lint {contract.location} exited with {completed.returncode}:\n{output}",
    )
