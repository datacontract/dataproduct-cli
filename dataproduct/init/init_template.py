import importlib.resources as resources
import logging

import requests

DEFAULT_DATA_PRODUCT_INIT_TEMPLATE = "odps-1.1.0.init.yaml"


def get_init_template(location: str = None) -> str:
    """Return the contents of an init template.

    - ``None`` -> the bundled default template.
    - an ``http(s)://`` URL -> the fetched body.
    - anything else -> read as a local file path.
    """
    if location is None:
        logging.info("Use default bundled template " + DEFAULT_DATA_PRODUCT_INIT_TEMPLATE)
        schemas = resources.files("dataproduct")
        template = schemas.joinpath("schemas", DEFAULT_DATA_PRODUCT_INIT_TEMPLATE)
        with template.open("r") as file:
            return file.read()
    elif location.startswith("http://") or location.startswith("https://"):
        return requests.get(location).text
    else:
        with open(location, "r") as file:
            return file.read()
