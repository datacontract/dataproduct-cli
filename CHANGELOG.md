# Changelog

All notable changes to this project are documented here. Each entry is one line:
what changed (user-facing).

## [Unreleased]

- `lint` resolves data contracts linked via port `contractId` (Entropy Data when an API key is set, else local `*.odcs.yaml` files under the current directory) and warns on unresolved ones; `--no-resolve-references` disables it
- `lint` runs `datacontract lint` on each linked data contract when datacontract-cli is on the PATH

## [0.2.0]

- Support ODPS v1.1.0: `lint` validates against the bundled v1.1.0 JSON Schema (`type`, `context`, `synonyms`, `deprecated`, `customProperties[].vendor`, element `id`s, optional port `version`/`contractId`)
- `lint` validates against the bundled JSON Schema for the `apiVersion` the document declares (`v1.1.0` → v1.1.0 schema; `v1.0.0`/`v0.9.0` → v1.0.0 schema; unknown → newest), and check names state which schema ran
- `init` template now uses `apiVersion: v1.1.0`

## [0.1.0]

- `init` command: create a valid `dataproduct.odps.yaml` from a bundled ODPS v1.0.0 template
- `lint` command: validate a data product against the ODPS v1.0.0 JSON Schema (json/junit output)
- `publish` command: publish a data product to Entropy Data (`PUT /api/dataproducts/{id}`)

## [0.0.1]

- Test release to validate the PyPI publishing pipeline
