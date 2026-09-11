from typing import Any, Dict, List, Optional

import yaml
from jsonschema.validators import validator_for

from dataproduct.model.exceptions import DataProductException
from dataproduct.model.run import Check, ResultEnum


def parse_yaml(content: str) -> Dict[str, Any]:
    """Parse a data product YAML string into a mapping.

    Raises :class:`DataProductException` (single ``error``, no traceback) on
    malformed YAML or a non-mapping document.
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise DataProductException(
            type="lint",
            name="Parsing data product YAML",
            reason=f"The data product is not valid YAML: {e}",
            result=ResultEnum.error,
        )
    if not isinstance(data, dict):
        raise DataProductException(
            type="lint",
            name="Parsing data product YAML",
            reason="The data product must be a YAML mapping (object).",
            result=ResultEnum.error,
        )
    return data


def validate_against_schema(
    data: Dict[str, Any], schema: Dict[str, Any], all_errors: bool = False, schema_version: Optional[str] = None
) -> List[Check]:
    """Validate ``data`` against the ODPS JSON Schema.

    Returns a list of ``error`` checks — empty when the document is valid. With
    ``all_errors=False`` (default) only the first violation is reported. Check
    names state the bundled ``schema_version`` that ran; ``None`` means a custom
    schema was supplied and no version is named.
    """
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)

    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not all_errors:
        errors = errors[:1]

    name = (
        "Check that data product YAML is valid"
        if schema_version is None
        else f"Check that data product is valid against ODPS v{schema_version}"
    )
    checks: List[Check] = []
    for error in errors:
        path = "/".join(str(p) for p in error.absolute_path)
        checks.append(
            Check(
                type="lint",
                result=ResultEnum.error,
                name=name,
                reason=f"{path}: {error.message}" if path else error.message,
                field=path or "(root)",
            )
        )
    return checks
