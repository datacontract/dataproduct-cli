# Data Product CLI

Sister project of [`datacontract-cli`](https://github.com/datacontract/datacontract-cli).
When a design question comes up, prefer parity with datacontract-cli and
backlog shared improvements for **both** CLIs (see `specs/backlog.md`).

## Development Environment Setup

Using uv (recommended):

```bash
uv python pin 3.11
uv sync --all-extras --dev
uv run pre-commit install
```

## Common Commands

### Testing

```bash
uv run pytest            # all tests
uv run pytest -n 8       # parallel
uv run pytest tests/test_lint.py::test_lint_valid
```

### Linting and Formatting

```bash
uv run ruff check
uv run ruff check --fix
uv run ruff format
uv run pre-commit run --all-files
```

### CLI Usage

```bash
uv run dataproduct init
uv run dataproduct lint dataproduct.odps.yaml
uv run dataproduct publish dataproduct.odps.yaml
```

## Project Architecture

Spec-driven: each command's behavior is defined in `specs/` (`overview.md`,
`001-init.md`, `002-lint.md`, `003-publish.md`, `backlog.md`). Read the spec
before changing a command.

- **`dataproduct/cli.py`** — Typer entry point, global options, command ordering.
- **`dataproduct/command_*.py`** — thin Typer commands (`init`, `lint`, `publish`).
- **`dataproduct/data_product.py`** — `DataProduct` core class (library entry point).
- **`dataproduct/lint/`** — file reading, schema fetch, JSON-Schema validation.
- **`dataproduct/integration/entropy_data.py`** — publish to Entropy Data.
- **`dataproduct/model/`** — `Run`/`Check` result model and exceptions.
- **`dataproduct/output/`** — console / json / junit result writers.
- **`dataproduct/schemas/`** — bundled ODPS JSON Schema + init template.

## Code Conventions

- Python 3.10+ syntax and features.
- Pydantic v2 for the result model; JSON-Schema validation via `jsonschema`.
- Type hints throughout; ruff with a 120-character line length.
- `CHANGELOG.md` entries are one line each: what changed (user-facing).
- Tests describe expected behavior. If a test fails, fix the code under test,
  not the test (unless the test is wrong).

## Refreshing the bundled ODPS schema

The ODPS JSON Schemas are vendored at `dataproduct/schemas/odps-<version>.schema.json`;
`dataproduct/schemas/download` refreshes them (parallel to datacontract-cli's
`datacontract/schemas/download`). `lint` picks the bundled schema by the
document's `apiVersion` (`ODPS_SCHEMA_VERSIONS` in `dataproduct/lint/schema.py`).
A new ODPS release means: add it to `download` and run it, register it in
`ODPS_SCHEMA_VERSIONS`, bump `DEFAULT_ODPS_SCHEMA_VERSION`, and move the init
template to the new version.

## Release

Bump `project.version` in `pyproject.toml`, update `CHANGELOG.md`, commit, then
run `./release` to tag `v<version>` and push. The tag triggers
`.github/workflows/release.yaml` (PyPI trusted publishing + signed GitHub
release). The tag must equal `project.version`.
