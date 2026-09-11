from pathlib import Path

from typer.testing import CliRunner

from dataproduct.cli import app
from dataproduct.data_product import DataProduct
from dataproduct.lint.schema import fetch_schema, schema_version_for

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures" / "lint"
REPO_ROOT = Path(__file__).parent.parent
BUNDLED_SCHEMA = REPO_ROOT / "dataproduct" / "schemas" / "odps-1.0.0.schema.json"


def _lint(name: str, **kwargs) -> "object":
    return DataProduct(data_product_file=str(FIXTURES / name), **kwargs).lint()


def test_lint_valid():
    run = _lint("valid-dataproduct.odps.yaml")
    assert run.result == "passed", run.checks
    assert run.dataProductId == "064c4630-8aad-4dc0-ba95-0f69940e6b18"


def test_lint_valid_v1_1_0():
    run = _lint("valid-dataproduct-v1.1.0.odps.yaml", all_errors=True)
    assert run.result == "passed", run.checks
    assert run.checks[0].name == "Data product is valid against ODPS v1.1.0"


def test_lint_names_the_schema_that_ran():
    run = _lint("valid-dataproduct.odps.yaml")
    assert run.result == "passed", run.checks
    assert run.checks[0].name == "Data product is valid against ODPS v1.0.0"


def test_lint_names_no_version_for_custom_schema():
    run = DataProduct(
        data_product_file=str(FIXTURES / "valid-dataproduct.odps.yaml"),
        schema_location=str(BUNDLED_SCHEMA),
    ).lint()
    assert run.checks[0].name == "Data product is syntactically valid"


def test_lint_v1_1_0_status_is_optional():
    run = _lint("missing-status-v1.1.0.odps.yaml")
    assert run.result == "passed", run.checks


def test_lint_v1_1_0_fields_rejected_under_v1_0_0():
    run = _lint("v1.1.0-fields-in-v1.0.0.odps.yaml")
    assert run.result == "failed"
    assert run.checks[0].name == "Check that data product is valid against ODPS v1.0.0"
    assert "type" in (run.checks[0].reason or "")


def test_lint_unknown_api_version_reported():
    run = _lint("multiple-errors.odps.yaml", all_errors=True)
    assert run.result == "failed"
    assert all(c.name == "Check that data product is valid against ODPS v1.1.0" for c in run.checks)
    assert "apiVersion" in [c.field for c in run.checks]


def test_schema_version_selected_by_api_version():
    assert schema_version_for("v1.1.0") == "1.1.0"
    assert schema_version_for("v1.0.0") == "1.0.0"
    assert schema_version_for("v0.9.0") == "1.0.0"
    assert schema_version_for(None) == "1.1.0"
    assert schema_version_for("v9.9.9") == "1.1.0"
    assert schema_version_for(["not", "a", "string"]) == "1.1.0"


def test_fetch_bundled_schema_per_version():
    assert "status" in fetch_schema(schema_version="1.0.0")["required"]
    assert "status" not in fetch_schema(schema_version="1.1.0")["required"]
    assert fetch_schema()["properties"]["apiVersion"]["default"] == "v1.1.0"


def test_lint_valid_cli_exit_zero():
    result = runner.invoke(app, ["lint", str(FIXTURES / "valid-dataproduct.odps.yaml")])
    assert result.exit_code == 0, result.output


def test_lint_missing_required_field():
    run = _lint("missing-status.odps.yaml")
    assert run.result == "failed"
    reasons = " ".join(c.reason or "" for c in run.checks)
    assert "status" in reasons


def test_lint_wrong_kind():
    run = _lint("wrong-kind.odps.yaml")
    assert run.result == "failed"


def test_lint_invalid_yaml():
    run = _lint("invalid.yaml")
    assert run.result == "failed"
    error_checks = [c for c in run.checks if c.result == "error"]
    assert len(error_checks) == 1
    assert "YAML" in (error_checks[0].reason or "") or "YAML" in error_checks[0].name


def test_lint_no_output_ports_passes():
    run = _lint("no-output-ports.odps.yaml")
    assert run.result == "passed", run.checks


def test_lint_all_errors_reports_multiple():
    run = _lint("multiple-errors.odps.yaml", all_errors=True)
    error_checks = [c for c in run.checks if c.result == "error"]
    assert len(error_checks) >= 2


def test_lint_first_error_only_by_default():
    run = _lint("multiple-errors.odps.yaml")
    error_checks = [c for c in run.checks if c.result == "error"]
    assert len(error_checks) == 1


def test_lint_junit_output(tmp_path):
    out = tmp_path / "TEST-dataproduct.xml"
    result = runner.invoke(
        app,
        ["lint", str(FIXTURES / "valid-dataproduct.odps.yaml"), "--output", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    import xml.etree.ElementTree as ET

    tree = ET.parse(out)
    assert tree.getroot().tag == "testsuite"


def test_lint_custom_json_schema():
    run = DataProduct(
        data_product_file=str(FIXTURES / "valid-dataproduct.odps.yaml"),
        schema_location=str(BUNDLED_SCHEMA),
    ).lint()
    assert run.result == "passed", run.checks


def test_lint_missing_file():
    run = DataProduct(data_product_file="does-not-exist.odps.yaml").lint()
    assert run.result == "failed"
    reasons = " ".join(c.reason or "" for c in run.checks)
    assert "does not exist" in reasons


def test_lint_missing_file_cli_exit_one():
    result = runner.invoke(app, ["lint", "does-not-exist.odps.yaml"])
    assert result.exit_code == 1
