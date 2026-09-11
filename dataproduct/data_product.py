"""Core library entry point, parallel to datacontract-cli's ``DataContract``.

from dataproduct.data_product import DataProduct

run = DataProduct(data_product_file="dataproduct.odps.yaml").lint()
DataProduct(data_product_file="dataproduct.odps.yaml").publish()
"""

from typing import Optional, Union

from dataproduct.config import Config
from dataproduct.integration.entropy_data import publish_data_product_to_entropy_data
from dataproduct.lint.files import read_resource
from dataproduct.lint.schema import fetch_schema, schema_version_for
from dataproduct.lint.validate import parse_yaml, validate_against_schema
from dataproduct.model.exceptions import DataProductException
from dataproduct.model.run import Check, ResultEnum, Run


class DataProduct:
    def __init__(
        self,
        data_product_file: Optional[str] = None,
        data_product_str: Optional[str] = None,
        schema_location: Optional[str] = None,
        all_errors: bool = False,
        config: "Optional[Union[Config, dict]]" = None,
    ):
        self._data_product_file = data_product_file
        self._data_product_str = data_product_str
        self._schema_location = schema_location
        self._all_errors = all_errors
        self._config = Config.resolve(config)

    def _load_dict(self) -> dict:
        if self._data_product_file is not None:
            content = read_resource(self._data_product_file, self._config)
        elif self._data_product_str is not None:
            content = self._data_product_str
        else:
            raise DataProductException(
                type="lint",
                name="Load data product",
                reason="No data product provided (file or string).",
            )
        return parse_yaml(content)

    def lint(self) -> Run:
        """Validate the data product against the ODPS JSON Schema matching its ``apiVersion`` (schema-only)."""
        run = Run.create_run()
        run.log_info("Linting data product")
        try:
            data = self._load_dict()
            run.dataProductId = data.get("id")
            run.dataProductVersion = data.get("version")
            schema_version = None if self._schema_location else schema_version_for(data.get("apiVersion"))
            schema = fetch_schema(self._schema_location, schema_version)
            checks = validate_against_schema(data, schema, self._all_errors, schema_version)
            if checks:
                run.checks.extend(checks)
                for check in checks:
                    run.log_error(str(check.reason))
            else:
                run.checks.append(
                    Check(
                        type="lint",
                        result=ResultEnum.passed,
                        name="Data product is syntactically valid"
                        if schema_version is None
                        else f"Data product is valid against ODPS v{schema_version}",
                    )
                )
        except DataProductException as e:
            run.checks.append(Check(type=e.type, result=e.result, name=e.name, reason=e.reason, engine=e.engine))
            run.log_error(str(e))
        except Exception as e:
            run.checks.append(
                Check(
                    type="general",
                    result=ResultEnum.error,
                    name="Check Data Product",
                    reason=str(e),
                )
            )
            run.log_error(str(e))
        run.finish()
        return run

    def publish(self, ssl_verification: bool = True) -> None:
        """Publish the data product to Entropy Data (no client-side lint in 0.1)."""
        data = self._load_dict()
        publish_data_product_to_entropy_data(
            data_product_dict=data,
            ssl_verification=ssl_verification,
            config=self._config,
        )
