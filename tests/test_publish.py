from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dataproduct.data_product import DataProduct
from dataproduct.integration.entropy_data import DataProductPublishError

FIXTURE = Path(__file__).parent / "fixtures" / "publish" / "dataproduct.odps.yaml"


def _response(status_code=200, headers=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = text
    return resp


def test_publish_success(monkeypatch, capsys):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")
    monkeypatch.setenv("ENTROPY_DATA_HOST", "https://api.example.com")

    with patch("dataproduct.integration.entropy_data.requests.put", return_value=_response(200)) as put:
        DataProduct(data_product_file=str(FIXTURE)).publish()

    put.assert_called_once()
    _, kwargs = put.call_args
    assert kwargs["url"] == "https://api.example.com/api/dataproducts/my-published-product"
    assert kwargs["headers"]["x-api-key"] == "secret-key"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["json"]["id"] == "my-published-product"
    assert "Published data product successfully" in capsys.readouterr().out


def test_publish_default_host(monkeypatch):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")

    with patch("dataproduct.integration.entropy_data.requests.put", return_value=_response(200)) as put:
        DataProduct(data_product_file=str(FIXTURE)).publish()

    _, kwargs = put.call_args
    assert kwargs["url"].startswith("https://api.entropy-data.com/api/dataproducts/")


def test_publish_missing_api_key(monkeypatch):
    with patch("dataproduct.integration.entropy_data.requests.put") as put:
        with pytest.raises(DataProductPublishError, match="ENTROPY_DATA_API_KEY"):
            DataProduct(data_product_file=str(FIXTURE)).publish()
    put.assert_not_called()


def test_publish_http_error(monkeypatch):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")
    monkeypatch.setenv("ENTROPY_DATA_HOST", "https://api.example.com")

    with patch(
        "dataproduct.integration.entropy_data.requests.put",
        return_value=_response(422, text="team 'my-team' does not exist"),
    ):
        with pytest.raises(DataProductPublishError, match="team 'my-team' does not exist"):
            DataProduct(data_product_file=str(FIXTURE)).publish()


def test_publish_no_ssl_verification(monkeypatch):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")

    with patch("dataproduct.integration.entropy_data.requests.put", return_value=_response(200)) as put:
        DataProduct(data_product_file=str(FIXTURE)).publish(ssl_verification=False)

    _, kwargs = put.call_args
    assert kwargs["verify"] is False


def test_publish_location_html_header(monkeypatch, capsys):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")

    headers = {"location-html": "https://app.entropy-data.com/dataproducts/my-published-product"}
    with patch(
        "dataproduct.integration.entropy_data.requests.put",
        return_value=_response(200, headers=headers),
    ):
        DataProduct(data_product_file=str(FIXTURE)).publish()

    assert "🚀 Open https://app.entropy-data.com/dataproducts/my-published-product" in capsys.readouterr().out
