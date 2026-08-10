import importlib.resources as resources
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Union

import requests

from dataproduct.model.exceptions import DataProductException
from dataproduct.model.run import ResultEnum

DEFAULT_DATA_PRODUCT_SCHEMA = "odps-1.0.0.schema.json"


def fetch_schema(location: Union[str, Path] = None) -> Dict[str, Any]:
    """Fetch the ODPS JSON Schema to validate against.

    ``None`` uses the bundled ODPS v1.0.0 schema; otherwise ``location`` is a URL
    or local path.
    """
    if location is None:
        logging.info("Use default bundled schema " + DEFAULT_DATA_PRODUCT_SCHEMA)
        schemas = resources.files("dataproduct")
        schema_file = schemas.joinpath("schemas", DEFAULT_DATA_PRODUCT_SCHEMA)
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
