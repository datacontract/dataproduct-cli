import os
from pathlib import Path

import requests

from dataproduct.config import Config
from dataproduct.model.exceptions import DataProductException
from dataproduct.model.run import ResultEnum


def read_resource(location: str, config: Config | None = None) -> str:
    """Read the raw text of a data product from a URL or local path.

    Raises :class:`DataProductException` (an ``error`` result, no traceback) if a
    local file is missing or a URL cannot be fetched.
    """
    location_str = str(location)
    if location_str.startswith("http://") or location_str.startswith("https://"):
        try:
            response = requests.get(location_str)
            response.raise_for_status()
        except requests.RequestException as e:
            raise DataProductException(
                type="lint",
                name=f"Reading data product from {location_str}",
                reason=f"Failed to fetch '{location_str}': {e}",
                result=ResultEnum.error,
            )
        return response.text

    if not os.path.exists(location_str):
        raise DataProductException(
            type="lint",
            name=f"Reading data product from {location_str}",
            reason=f"The file '{location_str}' does not exist.",
            result=ResultEnum.error,
        )
    return Path(location_str).read_text(encoding="utf-8")
