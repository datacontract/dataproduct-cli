# Data Product CLI

The `dataproduct` CLI is an open-source command-line tool for working with
**data products** defined with the
[Open Data Product Standard (ODPS)](https://bitol-io.github.io/open-data-product-standard/v1.1.0/).

It is the data-product sibling of
[`datacontract-cli`](https://github.com/datacontract/datacontract-cli) (which
targets the Open Data **Contract** Standard) and mirrors its technology and
release mechanism. The tool is written in Python and can be used standalone, in
CI/CD, or as a Python library.

> The behavior of each command is specified in [`specs/`](specs/).

## Install

```bash
uv tool install --python python3.11 dataproduct-cli
# or
pip install dataproduct-cli
```

## Commands

### `init` — create a data product

```bash
dataproduct init                       # writes ./dataproduct.odps.yaml
dataproduct init my.odps.yaml          # custom path
dataproduct init --overwrite           # replace an existing file
dataproduct init --template <url|path> # seed from a template or existing product
```

### `lint` — validate against the ODPS standard

```bash
dataproduct lint                                   # lints ./dataproduct.odps.yaml
dataproduct lint my.odps.yaml
dataproduct lint --all-errors                      # report every schema violation
dataproduct lint --output-format junit --output TEST-dataproduct.xml
dataproduct lint --json-schema ./odps.schema.json  # validate against a custom schema
```

The data product is checked against the bundled ODPS JSON Schema matching its
`apiVersion` (`v1.1.0`, `v1.0.0`, or `v0.9.0`; unknown versions are validated
against the latest). Exit code is `0` when valid, `1` otherwise.

`lint` also resolves the data contracts linked via `inputPorts[].contractId` /
`outputPorts[].contractId`: through Entropy Data when an API key is set,
otherwise by searching `*.odcs.yaml` files (`kind: DataContract`, matching `id`)
under the current directory. `--local-references` searches the local files even
when an API key is set. If [`datacontract`](https://github.com/datacontract/datacontract-cli)
is on your PATH, each resolved contract is linted with it too; if it is missing or
cannot be run, `lint` says so in a warning. Unresolved or invalid contracts are
reported as warnings; `--no-resolve-references` turns this off.

### `publish` — publish to Entropy Data

```bash
export ENTROPY_DATA_API_KEY=...        # from Entropy Data → Settings → API Keys
dataproduct publish my.odps.yaml
```

`publish` sends `PUT {host}/api/dataproducts/{id}` with an `x-api-key` header.
The host defaults to `https://api.entropy-data.com` and can be overridden with
`ENTROPY_DATA_HOST`. The referenced `team` must already exist in your org.

## Configuration

| Purpose | Variable (with fallbacks) |
|---|---|
| API host | `ENTROPY_DATA_HOST` → `DATAMESH_MANAGER_HOST` → `DATACONTRACT_MANAGER_HOST` → `https://api.entropy-data.com` |
| API key | `ENTROPY_DATA_API_KEY` → `DATAMESH_MANAGER_API_KEY` → `DATACONTRACT_MANAGER_API_KEY` |

`.env` files are loaded automatically.

## Use as a library

```python
from dataproduct.data_product import DataProduct

run = DataProduct(data_product_file="dataproduct.odps.yaml").lint()
assert run.result == "passed"

DataProduct(data_product_file="dataproduct.odps.yaml").publish()
```

## Development

See [AGENTS.md](AGENTS.md).

## License

MIT
