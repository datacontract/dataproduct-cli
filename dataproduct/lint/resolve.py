from typing import Any, Dict

from dataproduct.config import Config
from dataproduct.lint.files import read_resource
from dataproduct.lint.validate import parse_yaml


def resolve_data_product_dict(location: str, config: "Config | None" = None) -> Dict[str, Any]:
    """Read and parse the data product at ``location`` into a plain dict."""
    content = read_resource(location, config)
    return parse_yaml(content)
