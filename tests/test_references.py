import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dataproduct.cli import app
from dataproduct.data_product import DataProduct

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures" / "references"
DATA_PRODUCT = FIXTURES / "dataproduct.odps.yaml"
LOCAL_CONTRACT = FIXTURES / "contracts" / "nested" / "orders.odcs.yaml"


def _reference_checks(run):
    return {c.field: c for c in run.checks if c.name.startswith("Data contract") and "resolvable" in c.name}


def _response(status_code):
    resp = MagicMock()
    resp.status_code = status_code
    return resp


def test_resolves_linked_contracts_locally():
    run = DataProduct(data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES).lint()

    checks = _reference_checks(run)
    assert set(checks) == {"inputPorts/0/contractId", "outputPorts/0/contractId", "outputPorts/1/contractId"}
    assert checks["outputPorts/0/contractId"].result == "passed"
    assert checks["outputPorts/0/contractId"].reason.endswith("contracts/nested/orders.odcs.yaml")
    # Wrong kind, wrong suffix, and node_modules don't count as a match.
    assert checks["inputPorts/0/contractId"].result == "warning"
    assert "missing-contract" in checks["inputPorts/0/contractId"].reason
    # Unresolved contracts warn but don't fail the run.
    assert run.result == "passed", run.checks


def test_local_search_defaults_to_cwd(monkeypatch):
    monkeypatch.chdir(FIXTURES)
    run = DataProduct(data_product_file=str(DATA_PRODUCT)).lint()
    assert _reference_checks(run)["outputPorts/0/contractId"].result == "passed"


def test_resolves_via_entropy_data_when_api_key_set(monkeypatch):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")
    monkeypatch.setenv("ENTROPY_DATA_HOST", "https://api.example.com")

    def get(url, **kwargs):
        return _response(200 if url.endswith("/orders-contract") else 404)

    with patch("dataproduct.integration.entropy_data.requests.get", side_effect=get) as mock_get:
        run = DataProduct(data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES).lint()

    checks = _reference_checks(run)
    assert checks["outputPorts/0/contractId"].result == "passed"
    assert (
        checks["outputPorts/0/contractId"].reason
        == "Found at https://api.example.com/api/datacontracts/orders-contract"
    )
    assert checks["inputPorts/0/contractId"].result == "warning"
    assert "api.example.com" in checks["inputPorts/0/contractId"].reason
    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["x-api-key"] == "secret-key"
    assert kwargs["allow_redirects"] is False


def test_entropy_data_lookup_failure_is_a_warning(monkeypatch):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")
    with patch("dataproduct.integration.entropy_data.requests.get", return_value=_response(403)):
        run = DataProduct(data_product_file=str(DATA_PRODUCT)).lint()

    check = _reference_checks(run)["outputPorts/0/contractId"]
    assert check.result == "warning"
    assert "HTTP 403" in check.reason
    assert run.result == "passed"


def test_empty_api_key_resolves_locally(monkeypatch):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "")
    monkeypatch.setenv("DATACONTRACT_MANAGER_API_KEY", " ")
    with patch("dataproduct.integration.entropy_data.requests.get") as mock_get:
        run = DataProduct(data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES).lint()

    mock_get.assert_not_called()
    assert _reference_checks(run)["outputPorts/0/contractId"].result == "passed"


def test_local_references_ignore_api_key(monkeypatch):
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")
    with patch("dataproduct.integration.entropy_data.requests.get") as mock_get:
        run = DataProduct(
            data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES, local_references=True
        ).lint()

    mock_get.assert_not_called()
    check = _reference_checks(run)["outputPorts/0/contractId"]
    assert check.result == "passed"
    assert check.reason.endswith("contracts/nested/orders.odcs.yaml")


def test_resolution_can_be_disabled():
    run = DataProduct(data_product_file=str(DATA_PRODUCT), resolve_references=False).lint()
    assert _reference_checks(run) == {}


def test_lints_each_resolved_contract_once_with_datacontract_cli():
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("dataproduct.lint.contract_lint.subprocess.run", return_value=completed) as run_mock:
        run = DataProduct(
            data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES, datacontract_cli="/bin/datacontract"
        ).lint()

    assert [c.args[0][:2] for c in run_mock.call_args_list] == [
        ["/bin/datacontract", "--version"],
        ["/bin/datacontract", "lint"],
    ]
    assert Path(run_mock.call_args.args[0][2]).resolve() == LOCAL_CONTRACT.resolve()
    lint_checks = [c for c in run.checks if "passes datacontract lint" in c.name]
    assert [c.result for c in lint_checks] == ["passed"]


def test_failing_contract_lint_is_a_warning():
    version = subprocess.CompletedProcess(args=[], returncode=0, stdout="0.11.0", stderr="")
    completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="status is invalid", stderr="")
    with patch("dataproduct.lint.contract_lint.subprocess.run", side_effect=[version, completed]):
        run = DataProduct(
            data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES, datacontract_cli="/bin/datacontract"
        ).lint()

    check = next(c for c in run.checks if "passes datacontract lint" in c.name)
    assert check.result == "warning"
    assert "status is invalid" in check.reason
    assert run.result == "passed"


def _lint_with(side_effect):
    with patch("dataproduct.lint.contract_lint.subprocess.run", side_effect=side_effect) as run_mock:
        run = DataProduct(
            data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES, datacontract_cli="/bin/datacontract"
        ).lint()
    return run, run_mock


def test_unrunnable_datacontract_cli_is_one_warning_and_skips_lint():
    run, run_mock = _lint_with(FileNotFoundError(2, "No such file or directory"))

    run_mock.assert_called_once()
    checks = [c for c in run.checks if "datacontract" in c.name]
    assert [(c.name, c.result) for c in checks] == [("datacontract-cli is runnable", "warning")]
    assert "Could not run '/bin/datacontract'" in checks[0].reason
    assert run.result == "passed"


def test_failing_datacontract_version_is_one_warning_and_skips_lint():
    broken = subprocess.CompletedProcess(args=[], returncode=101, stdout="", stderr="Fatal error in launcher")
    run, run_mock = _lint_with([broken])

    run_mock.assert_called_once()
    check = next(c for c in run.checks if c.name == "datacontract-cli is runnable")
    assert check.result == "warning"
    assert "exited with 101" in check.reason
    assert "Fatal error in launcher" in check.reason


def test_datacontract_lint_timeout_is_a_warning():
    version = subprocess.CompletedProcess(args=[], returncode=0, stdout="0.11.0", stderr="")
    run, _ = _lint_with([version, subprocess.TimeoutExpired(cmd="datacontract", timeout=120)])

    check = next(c for c in run.checks if "passes datacontract lint" in c.name)
    assert check.result == "warning"
    assert "did not finish within 120s" in check.reason


def test_unexpected_error_running_datacontract_lint_is_a_warning():
    version = subprocess.CompletedProcess(args=[], returncode=0, stdout="0.11.0", stderr="")
    run, _ = _lint_with([version, UnicodeDecodeError("cp1252", b"\x81", 0, 1, "undefined")])

    check = next(c for c in run.checks if "passes datacontract lint" in c.name)
    assert check.result == "warning"
    assert run.result == "passed"


def test_datacontract_lint_runs_with_utf8_and_strips_ansi():
    version = subprocess.CompletedProcess(args=[], returncode=0, stdout="0.11.0", stderr="")
    failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="\x1b[31m❌ status is invalid\x1b[0m", stderr="")
    run, run_mock = _lint_with([version, failed])

    kwargs = run_mock.call_args.kwargs
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["env"]["PYTHONIOENCODING"] == "utf-8"
    assert kwargs["stdin"] == subprocess.DEVNULL
    check = next(c for c in run.checks if "passes datacontract lint" in c.name)
    assert check.reason.endswith("❌ status is invalid")


def test_library_does_not_run_datacontract_cli_by_default():
    with patch("dataproduct.lint.contract_lint.subprocess.run") as run_mock:
        DataProduct(data_product_file=str(DATA_PRODUCT), reference_search_dir=FIXTURES).lint()
    run_mock.assert_not_called()


def test_cli_lints_contracts_when_datacontract_cli_on_path(monkeypatch):
    monkeypatch.chdir(FIXTURES)
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with (
        patch("dataproduct.command_lint.datacontract_cli_path", return_value="/bin/datacontract"),
        patch("dataproduct.lint.contract_lint.subprocess.run", return_value=completed) as run_mock,
    ):
        result = runner.invoke(app, ["lint", str(DATA_PRODUCT)])

    assert result.exit_code == 0, result.output
    assert run_mock.call_count == 2  # --version, then lint
    assert "passes datacontract lint" in result.output


def test_cli_warns_and_skips_contract_lint_without_datacontract_cli(monkeypatch):
    monkeypatch.chdir(FIXTURES)
    with (
        patch("dataproduct.lint.contract_lint.shutil.which", return_value=None),
        patch("dataproduct.lint.contract_lint.subprocess.run") as run_mock,
    ):
        result = runner.invoke(app, ["lint", str(DATA_PRODUCT)])

    assert result.exit_code == 0, result.output
    run_mock.assert_not_called()
    output = " ".join(result.output.split())
    assert "datacontract-cli is runnable" in output
    assert "'datacontract' was not found on the PATH" in output


def test_cli_no_resolve_references(monkeypatch):
    monkeypatch.chdir(FIXTURES)
    with patch("dataproduct.lint.contract_lint.subprocess.run") as run_mock:
        result = runner.invoke(app, ["lint", str(DATA_PRODUCT), "--no-resolve-references"])
    assert result.exit_code == 0, result.output
    assert "resolvable" not in result.output
    run_mock.assert_not_called()


def test_cli_local_references(monkeypatch):
    monkeypatch.chdir(FIXTURES)
    monkeypatch.setenv("ENTROPY_DATA_API_KEY", "secret-key")
    with (
        patch("dataproduct.lint.contract_lint.shutil.which", return_value=None),
        patch("dataproduct.integration.entropy_data.requests.get") as mock_get,
    ):
        result = runner.invoke(app, ["lint", str(DATA_PRODUCT), "--local-references"])

    assert result.exit_code == 0, result.output
    mock_get.assert_not_called()
    assert "Found at contracts/nested/orders.odcs.yaml" in " ".join(result.output.split())


def test_cli_prints_port_label_and_relative_path(monkeypatch):
    monkeypatch.chdir(FIXTURES)
    with patch("dataproduct.lint.contract_lint.shutil.which", return_value=None):
        result = runner.invoke(app, ["lint", str(DATA_PRODUCT)])
    output = " ".join(result.output.split())
    assert "linked by inputPorts[raw-orders]" in output
    assert "Found at contracts/nested/orders.odcs.yaml" in output
