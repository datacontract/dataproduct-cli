import importlib.resources as resources
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

from dataproduct.model.exceptions import DataProductException
from dataproduct.model.run import ResultEnum

# ODPS v1.1.0 relaxed several required fields (e.g. `status`, port `version`/`contractId`)
# and added new ones, so older documents must be validated against their own schema.
# v0.9.0 has no dedicated bundled schema; the v1.0.0 schema accepts it.
ODPS_SCHEMA_VERSIONS = {
    "v1.1.0": "1.1.0",
    "v1.0.0": "1.0.0",
    "v0.9.0": "1.0.0",
}
DEFAULT_ODPS_SCHEMA_VERSION = "1.1.0"


def schema_version_for(api_version: Any = None) -> str:
    """Return the bundled ODPS schema version for a document's ``apiVersion``.

    Unknown or missing versions fall back to the newest bundled schema, which
    then reports the invalid ``apiVersion`` as a schema violation.
    """
    if isinstance(api_version, str):
        return ODPS_SCHEMA_VERSIONS.get(api_version, DEFAULT_ODPS_SCHEMA_VERSION)
    return DEFAULT_ODPS_SCHEMA_VERSION


def fetch_schema(location: Union[str, Path] = None, schema_version: Optional[str] = None) -> Dict[str, Any]:
    """Fetch the ODPS JSON Schema to validate against.

    ``None`` uses the bundled schema for ``schema_version`` (newest when
    omitted); otherwise ``location`` is a URL or local path.
    """
    if location is None:
        schema_name = f"odps-{schema_version or DEFAULT_ODPS_SCHEMA_VERSION}.schema.json"
        logging.info("Use default bundled schema " + schema_name)
        schemas = resources.files("dataproduct")
        schema_file = schemas.joinpath("schemas", schema_name)
        with schema_file.open("r") as file:
            return json.load(file)

    location_str = str(location)
    if location_str.startswith("http://") or location_str.startswith("https://"):
        logging.debug(f"Downloading schema from {location_str}")
        response = requests.get(location_str)
        return response.json()

    if not os.path.exists(location_str):
        raise DataProductException(
            type="lint",
            name=f"Reading schema from {location_str}",
            reason=f"The file '{location_str}' does not exist.",
            result=ResultEnum.error,
        )
    logging.debug(f"Loading JSON schema locally at {location_str}")
    with open(location_str, "r") as file:
        return json.load(file)
