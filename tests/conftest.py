from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture(autouse=True)
def clean_entropy_env(monkeypatch):
    """Ensure publish-related env vars don't leak in from the host environment."""
    for var in (
        "ENTROPY_DATA_API_KEY",
        "ENTROPY_DATA_HOST",
        "DATAMESH_MANAGER_API_KEY",
        "DATAMESH_MANAGER_HOST",
        "DATACONTRACT_MANAGER_API_KEY",
        "DATACONTRACT_MANAGER_HOST",
    ):
        monkeypatch.delenv(var, raising=False)
