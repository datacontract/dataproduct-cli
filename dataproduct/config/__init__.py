"""Programmatic configuration for hosts and API keys.

Every value the CLI reads from ``ENTROPY_DATA_*`` (and the legacy
``DATAMESH_MANAGER_*`` / ``DATACONTRACT_MANAGER_*``) environment variables can
also be provided programmatically via :class:`Config` (or a plain dict keyed by
the env var names). Reads fall back to the process environment.
"""

import os
from typing import Optional, Union


class Config:
    def __init__(self, values: Optional[dict] = None):
        self._values = dict(values or {})

    def getenv(self, key: str) -> Optional[str]:
        value = self._values.get(key)
        if value is not None:
            return value
        return os.environ.get(key)

    @classmethod
    def resolve(cls, config: "Optional[Union[Config, dict]]" = None) -> "Config":
        if config is None:
            return cls()
        if isinstance(config, Config):
            return config
        if isinstance(config, dict):
            return cls(config)
        raise TypeError(f"Unsupported config type: {type(config)!r}")

    # Hosts
    def get_entropy_data_host(self) -> Optional[str]:
        return self.getenv("ENTROPY_DATA_HOST")

    def get_datamesh_manager_host(self) -> Optional[str]:
        return self.getenv("DATAMESH_MANAGER_HOST")

    def get_datacontract_manager_host(self) -> Optional[str]:
        return self.getenv("DATACONTRACT_MANAGER_HOST")

    # API keys
    def get_entropy_data_api_key(self) -> Optional[str]:
        return self.getenv("ENTROPY_DATA_API_KEY")

    def get_datamesh_manager_api_key(self) -> Optional[str]:
        return self.getenv("DATAMESH_MANAGER_API_KEY")

    def get_datacontract_manager_api_key(self) -> Optional[str]:
        return self.getenv("DATACONTRACT_MANAGER_API_KEY")


# Simple process-wide "current" config set from the CLI entry point.
_cli_config = Config()


def set_cli_config(config: Config) -> None:
    global _cli_config
    _cli_config = config


def cli_config() -> Config:
    return _cli_config


__all__ = ["Config", "cli_config", "set_cli_config"]
