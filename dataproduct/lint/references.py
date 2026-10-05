"""Resolve the data contracts a data product links via its ports.

Only ``inputPorts[].contractId`` and ``outputPorts[].contractId`` are resolved.
With an Entropy Data API key configured, each id is looked up on the platform
(``GET {host}/api/datacontracts/{id}``); otherwise the current directory and its
subdirectories are searched for ``*.odcs.yaml`` files with ``kind: DataContract``
and a matching ``id``. An unresolved contract is a ``warning``, not an ``error``:
the contract may legitimately live somewhere this lint run cannot see.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import yaml

from dataproduct.config import Config
from dataproduct.integration.entropy_data import (
    DataContractLookupError,
    data_contract_url,
    fetch_data_contract_exists,
    get_api_key_or_none,
    get_host,
)
from dataproduct.model.run import Check, ResultEnum

PORT_KINDS = ("inputPorts", "outputPorts")
LOCAL_CONTRACT_GLOBS = ("*.odcs.yaml", "*.odcs.yml")
# Directories never worth descending into when searching for contracts.
SKIPPED_DIRS = {"node_modules", "__pycache__", "venv", "site-packages"}


@dataclass
class ContractReference:
    contract_id: str
    field: str  # e.g. "outputPorts/0/contractId"
    port: str  # human-readable port label, e.g. "outputPorts[orders]"


@dataclass
class ResolvedContract:
    contract_id: str
    location: str  # local path or Entropy Data API URL
    source: str  # "local" or "entropy-data"


def collect_contract_references(data: Dict[str, Any]) -> List[ContractReference]:
    """All ``contractId``s on input and output ports, in document order."""
    references: List[ContractReference] = []
    for kind in PORT_KINDS:
        ports = data.get(kind)
        if not isinstance(ports, list):
            continue
        for index, port in enumerate(ports):
            if not isinstance(port, dict):
                continue
            contract_id = port.get("contractId")
            if not isinstance(contract_id, str) or not contract_id.strip():
                continue
            label = port.get("name") or port.get("id") or index
            references.append(
                ContractReference(
                    contract_id=contract_id,
                    field=f"{kind}/{index}/contractId",
                    port=f"{kind}[{label}]",
                )
            )
    return references


def resolve_contract_references(
    data: Dict[str, Any], config: Config, search_dir: Optional[Path] = None
) -> tuple[List[Check], List[ResolvedContract]]:
    """Resolve every port ``contractId``; return one check per reference plus the resolved contracts."""
    references = collect_contract_references(data)
    if not references:
        return [], []

    if get_api_key_or_none(config) is not None:
        resolver = _EntropyDataResolver(config)
    else:
        resolver = _LocalResolver(search_dir or Path.cwd())

    checks: List[Check] = []
    resolved: Dict[str, ResolvedContract] = {}
    for ref in references:
        name = f"Data contract '{ref.contract_id}' linked by {ref.port} is resolvable"
        try:
            contract = resolver.resolve(ref.contract_id)
        except DataContractLookupError as e:
            checks.append(Check(type="lint", result=ResultEnum.warning, name=name, reason=str(e), field=ref.field))
            continue
        if contract is None:
            checks.append(
                Check(
                    type="lint",
                    result=ResultEnum.warning,
                    name=name,
                    reason=resolver.not_found(ref.contract_id),
                    field=ref.field,
                )
            )
            continue
        resolved.setdefault(contract.contract_id, contract)
        checks.append(
            Check(
                type="lint",
                result=ResultEnum.passed,
                name=name,
                reason=f"Found at {contract.location}",
                field=ref.field,
            )
        )
    return checks, list(resolved.values())


class _EntropyDataResolver:
    def __init__(self, config: Config):
        self._config = config
        self._host = get_host(config)

    def resolve(self, contract_id: str) -> Optional[ResolvedContract]:
        if not fetch_data_contract_exists(contract_id, self._config):
            return None
        return ResolvedContract(contract_id, data_contract_url(contract_id, self._config), "entropy-data")

    def not_found(self, contract_id: str) -> str:
        return f"No data contract with id '{contract_id}' exists on {self._host}."


class _LocalResolver:
    def __init__(self, search_dir: Path):
        self._search_dir = search_dir
        self._index: Optional[Dict[str, Path]] = None

    def resolve(self, contract_id: str) -> Optional[ResolvedContract]:
        path = self._contracts().get(contract_id)
        if path is None:
            return None
        return ResolvedContract(contract_id, _display_path(path), "local")

    def not_found(self, contract_id: str) -> str:
        return (
            f"No local data contract (*.odcs.yaml, kind: DataContract) with id '{contract_id}' found under "
            f"{self._search_dir}. Set ENTROPY_DATA_API_KEY to resolve contracts via Entropy Data."
        )

    def _contracts(self) -> Dict[str, Path]:
        if self._index is None:
            self._index = {}
            for path in _find_contract_files(self._search_dir):
                contract_id = _data_contract_id(path)
                if contract_id is not None:
                    self._index.setdefault(contract_id, path)
        return self._index


def _display_path(path: Path) -> str:
    """``path`` relative to the cwd when it lies below it, else as is."""
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _find_contract_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIPPED_DIRS)
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if any(path.match(pattern) for pattern in LOCAL_CONTRACT_GLOBS):
                yield path


def _data_contract_id(path: Path) -> Optional[str]:
    """The ``id`` of the ODCS document at ``path``, or ``None`` if it isn't a parseable data contract."""
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as e:
        logging.debug(f"Skipping {path}: {e}")
        return None
    if not isinstance(data, dict) or data.get("kind") != "DataContract":
        return None
    contract_id = data.get("id")
    return contract_id if isinstance(contract_id, str) else None
