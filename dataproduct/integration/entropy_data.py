"""Publish a data product to Entropy Data.

Confirmed API contract (see specs/003-publish.md):
``PUT {host}/api/dataproducts/{id}`` with ``x-api-key`` +
``content-type: application/json`` and a JSON ODPS body; ``200 OK`` on success.
Structurally identical to datacontract-cli's data-contract publish, with the
path changed from ``datacontracts`` to ``dataproducts``.
"""

from urllib.parse import quote, urlparse

import requests

from dataproduct.config import Config

# Response header carrying the HTML location of the published data product.
RESPONSE_HEADER_LOCATION_HTML = "location-html"


def publish_data_product_to_entropy_data(
    data_product_dict: dict, ssl_verification: bool, config: Config | None = None
) -> None:
    config = Config.resolve(config)
    api_key = _get_api_key(config)
    host = get_host(config)
    headers = {"Content-Type": "application/json", "x-api-key": api_key}

    id = data_product_dict.get("id")
    if not id:
        raise DataProductPublishError("The data product has no top-level 'id'; cannot publish.")

    url = f"{host}/api/dataproducts/{id}"
    response = requests.put(
        url=url,
        json=data_product_dict,
        headers=headers,
        verify=ssl_verification,
    )
    if response.status_code != 200:
        display_host = _extract_hostname(host)
        raise DataProductPublishError(f"Error publishing data product to {display_host}: {response.text}")

    print("✅ Published data product successfully")

    location_html = response.headers.get(RESPONSE_HEADER_LOCATION_HTML)
    if location_html:
        print(f"🚀 Open {location_html}")


class DataProductPublishError(Exception):
    """Raised when a publish attempt fails (missing key, bad id, non-200)."""


class DataContractLookupError(Exception):
    """Raised when Entropy Data cannot answer whether a data contract exists."""


def data_contract_url(contract_id: str, config: Config | None = None) -> str:
    return f"{get_host(Config.resolve(config))}/api/datacontracts/{quote(contract_id, safe='')}"


def fetch_data_contract_exists(contract_id: str, config: Config | None = None) -> bool:
    """``GET {host}/api/datacontracts/{id}``: ``True`` on 200, ``False`` on 404.

    Any other outcome raises :class:`DataContractLookupError`. Redirects are not
    followed, so the API key never travels to another host.
    """
    config = Config.resolve(config)
    url = data_contract_url(contract_id, config)
    headers = {"Accept": "application/json", "x-api-key": _get_api_key(config)}
    display_host = _extract_hostname(get_host(config))
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
    except requests.RequestException as e:
        raise DataContractLookupError(f"Could not reach {display_host} to look up data contract '{contract_id}': {e}")
    if response.status_code == 200:
        return True
    if response.status_code == 404:
        return False
    raise DataContractLookupError(
        f"Could not look up data contract '{contract_id}' on {display_host}: HTTP {response.status_code}"
    )


def get_api_key_or_none(config: Config | None = None) -> str | None:
    """Same lookup as :func:`_get_api_key`, but ``None`` when no key is set (empty or blank counts as unset)."""
    config = Config.resolve(config)
    for api_key in (
        config.get_entropy_data_api_key(),
        config.get_datamesh_manager_api_key(),
        config.get_datacontract_manager_api_key(),
    ):
        if api_key and api_key.strip():
            return api_key
    return None


def _get_api_key(config: Config) -> str:
    """API key with fallback priority:

    1. ``ENTROPY_DATA_API_KEY``
    2. ``DATAMESH_MANAGER_API_KEY``
    3. ``DATACONTRACT_MANAGER_API_KEY``
    """
    api_key = get_api_key_or_none(config)
    if api_key is None:
        raise DataProductPublishError(
            "Cannot publish, as neither ENTROPY_DATA_API_KEY, DATAMESH_MANAGER_API_KEY, "
            "nor DATACONTRACT_MANAGER_API_KEY is set"
        )
    return api_key


def get_host(config: Config) -> str:
    """Host with fallback priority: ENTROPY_DATA_HOST, DATAMESH_MANAGER_HOST,
    DATACONTRACT_MANAGER_HOST, then the default ``https://api.entropy-data.com``."""
    return (
        config.get_entropy_data_host()
        or config.get_datamesh_manager_host()
        or config.get_datacontract_manager_host()
        or "https://api.entropy-data.com"
    )


def _extract_hostname(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.split(":")[0] if parsed.netloc else url
