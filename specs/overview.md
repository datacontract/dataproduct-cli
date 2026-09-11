# dataproduct-cli — Overview Spec

## Purpose

`dataproduct-cli` is an open-source command-line tool for working with **data
products** defined with the [Open Data Product Standard (ODPS) v1.1.0](https://bitol-io.github.io/open-data-product-standard/v1.1.0/).
It is the data-product counterpart to
[`datacontract-cli`](https://github.com/datacontract/datacontract-cli) (which
targets the Open Data **Contract** Standard, ODCS), and deliberately mirrors its
technology, project layout, pipelines, and release mechanism.

The CLI can be used standalone, in CI/CD, or as a Python library.

## Scope of the first iteration

Three commands only:

1. **`init`** — create a valid `dataproduct.odps.yaml`. See [001-init.md](001-init.md).
2. **`lint`** — validate a local data product definition against the standard. See [002-lint.md](002-lint.md).
3. **`publish`** — put the local definition on Entropy Data. See [003-publish.md](003-publish.md).

Out of scope for now (candidates for later): `export`, `import`, `changelog`,
`catalog`, `edit`, `test`, `api`.

## The artifact: `dataproduct.odps.yaml`

The default filename is `dataproduct.odps.yaml`. The document is an ODPS
`DataProduct`.

### Top-level fields (ODPS v1.1.0)

| Field | Req. | Notes |
|---|---|---|
| `apiVersion` | ✅ | `v1.1.0` (schema also allows `v1.0.0`, `v0.9.0`) |
| `kind` | ✅ | must be `DataProduct` |
| `id` | ✅ | unique identifier, UUID recommended |
| `status` | — | e.g. `proposed`, `draft`, `active`, `deprecated`, `retired` (required in v1.0.0, optional since v1.1.0) |
| `name` | — | human-readable name |
| `version` | — | product version (e.g. `v1.0.0`) |
| `type` | — | architectural type, e.g. `sourceAligned`, `aggregate`, `consumerAligned` (v1.1.0) |
| `deprecated` | — | boolean, default `false` (v1.1.0; also on ports) |
| `domain` | — | business domain |
| `tenant` | — | organization identifier |
| `description` | — | object: `purpose`, `usage`, `limitations`, … |
| `tags` | — | list of strings |
| `synonyms` | — | list of `{synonym, locale?, source?, …}` (v1.1.0; also on output ports) |
| `context` | — | AI/semantic context: `instructions`, `verifiedStatements`, `constraints` (v1.1.0; also on output ports) |
| `inputPorts` | — | items require `name` (`version`, `contractId` also required in v1.0.0) |
| `outputPorts` | — | items require `name` (`version` also required in v1.0.0); best practice ≥ 1 |
| `managementPorts` | — | management/observability endpoints |
| `support` | — | items require `channel`, `url` |
| `team` | — | object with `members` |
| `customProperties` | — | list of `{property, value, vendor?}` |
| `authoritativeDefinitions` | — | list of `{type, url}` |
| `productCreatedTs` | — | ISO 8601 UTC timestamp |

> **Required-field note.** The official v1.1.0 JSON Schema strictly requires
> only `apiVersion`, `kind`, `id` (v1.0.0 also requires `status`). The prose standard additionally
> recommends at least one `outputPort`. `lint` treats the JSON Schema as
> authoritative for pass/fail. In 0.1 that's the whole story (schema-only,
> parity with datacontract-cli); best-practice warnings like "≥1 outputPort"
> are backlogged (see 002-lint.md and backlog.md).

### Minimal valid example (from the ODPS repo)

```yaml
apiVersion: v1.1.0
kind: DataProduct
id: 064c4630-8aad-4dc0-ba95-0f69940e6b18
status: active
name: Simple Data Product
version: v1.0.0
description:
  purpose: Simple test data product
  limitations: None
  usage: Testing purposes only
tags: ['test', 'simple']
inputPorts:
  - name: source-data
    version: 1.0.0
    contractId: 12345678-1234-1234-1234-123456789abc
outputPorts:
  - name: processed-data
    description: "Processed output data"
    type: tables
    version: 1.0.0
    contractId: 87654321-4321-4321-4321-cba987654321
```

## Technology (mirrors datacontract-cli)

- **Language:** Python 3.10+ (CI matrix 3.10–3.14).
- **CLI framework:** [Typer](https://typer.typiface.io/) on Click, `rich` for output.
- **Models/validation:** Pydantic v2; JSON Schema validation via `jsonschema` / `fastjsonschema`.
- **YAML:** `ruamel.yaml` / `pyyaml`.
- **HTTP:** `requests` (for `publish` and remote references).
- **Packaging/deps:** [`uv`](https://docs.astral.sh/uv/); build backend `setuptools`.
- **Lint/format:** `ruff` (line length 120; rule set pinned as in datacontract-cli).
- **Tests:** `pytest` (+ `pytest-xdist`), fixtures under `tests/fixtures/`.
- **Pre-commit:** `ruff check` + `ruff format`.

## Repository layout

```
dataproduct-cli/
├── pyproject.toml               # package "dataproduct-cli", script "dataproduct"
├── uv.lock
├── README.md
├── AGENTS.md                    # dev setup + conventions (mirrors datacontract-cli)
├── CHANGELOG.md                 # one line per user-facing change
├── Dockerfile
├── release                      # tag-based release helper script
├── .pre-commit-config.yaml
├── .github/workflows/
│   ├── ci.yaml                  # lint + test matrix + docker snapshot
│   └── release.yaml             # tag -> PyPI (trusted publishing) + GitHub release + Docker
├── specs/                       # ← these documents (spec-driven)
├── dataproduct/
│   ├── __init__.py
│   ├── cli.py                   # Typer app, global options, command ordering
│   ├── command_init.py
│   ├── command_lint.py
│   ├── command_publish.py
│   ├── data_product.py          # DataProduct core class (library entry point)
│   ├── config/                  # Config: hosts + API keys from env
│   ├── init/                    # init template loader
│   ├── lint/                    # schema fetch + validation + reference resolve
│   ├── integration/
│   │   └── entropy_data.py      # publish to Entropy Data
│   ├── model/                   # Pydantic models + Run/result types + exceptions
│   ├── output/                  # result writers (console, json, junit)
│   └── schemas/                 # bundled odps-<version>.schema.json (one per supported apiVersion) + *.init.yaml
└── tests/
    ├── fixtures/
    └── test_*.py
```

## Config & environment variables

Reuse datacontract-cli's Entropy Data conventions:

- **Host:** `ENTROPY_DATA_HOST` (default `https://api.entropy-data.com`), with
  `DATAMESH_MANAGER_HOST` / `DATACONTRACT_MANAGER_HOST` as fallbacks.
- **API key:** `ENTROPY_DATA_API_KEY`, falling back to
  `DATAMESH_MANAGER_API_KEY` / `DATACONTRACT_MANAGER_API_KEY`.
- All connection options are also settable programmatically via a `Config`
  object / dict passed to `DataProduct(config=...)`.
- `.env` files are auto-loaded (via `python-dotenv`).

## Library entry point (parallel to `DataContract`)

```python
from dataproduct.data_product import DataProduct

run = DataProduct(data_product_file="dataproduct.odps.yaml").lint()
DataProduct(data_product_file="dataproduct.odps.yaml").publish()
```

## Pipelines & release (mirror datacontract-cli)

- **CI** (`ci.yaml`): ruff check + format check; lint bundled examples; pytest
  across Python 3.10–3.14; build wheel and smoke-test `dataproduct --help`,
  `--version`, `init`, `lint`; build Docker snapshot on `main`.
- **Release** (`release.yaml`): triggered by `v*` tag → verify tag ==
  `pyproject` version → build → publish to PyPI via **trusted publishing** →
  TestPyPI → signed GitHub Release with notes extracted from `CHANGELOG.md` →
  multi-arch Docker image.
- **`release` script:** bump version in `pyproject.toml`, update `CHANGELOG.md`
  header, commit, then `./release` tags `v<version>` and pushes the tag.
- **Versioning:** SemVer; tag `v<version>` must equal `project.version`.

## Non-goals / principles

- The ODPS JSON Schema is the single source of truth for validity.
- Commands stay thin; logic lives in the `DataProduct` core class and helpers,
  so the tool is equally usable as a library.
- Keep parity with datacontract-cli conventions wherever reasonable so the two
  tools feel like siblings.
```