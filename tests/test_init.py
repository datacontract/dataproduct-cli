from typer.testing import CliRunner

from dataproduct.cli import app
from dataproduct.data_product import DataProduct

runner = CliRunner()


def test_init_default_creates_valid_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    created = tmp_path / "dataproduct.odps.yaml"
    assert created.exists()

    # The generated file must pass lint with zero errors.
    run = DataProduct(data_product_file=str(created)).lint()
    assert run.result == "passed", run.checks


def test_init_refuses_existing_without_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "dataproduct.odps.yaml"
    target.write_text("original: content\n")

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "already exists" in result.output
    assert target.read_text() == "original: content\n"


def test_init_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "dataproduct.odps.yaml"
    target.write_text("original: content\n")

    result = runner.invoke(app, ["init", "--overwrite"])
    assert result.exit_code == 0, result.output
    assert target.read_text() != "original: content\n"
    assert "kind: DataProduct" in target.read_text()


def test_init_custom_location(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my.odps.yaml"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "my.odps.yaml").exists()


def test_init_template_from_local_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    template = tmp_path / "template.yaml"
    template.write_text("apiVersion: v1.0.0\nkind: DataProduct\nid: seeded\nstatus: draft\n")

    result = runner.invoke(app, ["init", "seeded.odps.yaml", "--template", str(template)])
    assert result.exit_code == 0, result.output
    assert "id: seeded" in (tmp_path / "seeded.odps.yaml").read_text()
