# Spec 002 — `dataproduct lint`

## Goal

Validate that a local (or remote) data product definition is well-formed and
conforms to the Open Data Product Standard. This is the core correctness gate,
usable locally and in CI.

## CLI contract

```
dataproduct lint [LOCATION] [OPTIONS]
```

| Arg / Option | Type | Default | Description |
|---|---|---|---|
| `LOCATION` | positional | `dataproduct.odps.yaml` | url or local path of the data product yaml. |
| `--json-schema` | option (str) | none | Location (url or path) of an alternate ODPS JSON Schema to validate against. |
| `--output` | option (path) | none | Write test results to this file (e.g. `TEST-dataproduct.xml`); default is stdout. |
| `--output-format` | option (enum) | none | `json` or `junit`. |
| `--all-errors` | flag | `false` | Report all JSON Schema violations instead of stopping at the first. |
| `--resolve-references / --no-resolve-references` | flag | `true` | Resolve (and, with datacontract-cli on the PATH, lint) the data contracts linked via port `contractId`. |
| `--local-references` | flag | `false` | Resolve linked data contracts among local `*.odcs.yaml` files even when an API key is set. |
| `--debug` | flag | `false` | Enable debug logging. |

Example: `dataproduct lint dataproduct.odps.yaml`

(Mirrors `datacontract lint`. `--inline-references` from datacontract-cli is
**deferred** until the standard's `authoritativeDefinitions` resolution is
needed; see Open questions.)

## Validation performed

Run as an ordered set of checks, each producing a result entry:

1. **File is readable** — LOCATION exists / URL fetches; else `error`.
2. **Valid YAML** — parses to a mapping; else `error`.
3. **Schema validation (authoritative)** — validate the parsed document against
   the bundled ODPS JSON Schema matching the document's `apiVersion`
   (`v1.1.0` → `odps-1.1.0.schema.json`; `v1.0.0` and `v0.9.0` →
   `odps-1.0.0.schema.json`; unknown/missing → latest, which then reports the
   bad `apiVersion`), or the `--json-schema` override. Each violation is an `error` (path +
   message). With `--all-errors`, collect every violation; otherwise stop at
   the first.
   - This enforces the strictly-required fields (`apiVersion`, `kind`, `id`;
     plus `status` for v1.0.0 documents), the `kind: DataProduct` /
     `apiVersion` enums (`v0.9.0`, `v1.0.0`, `v1.1.0` are all accepted, silently),
     and the required subfields of ports/support/etc.
   - Picking the schema by `apiVersion` is deliberate: v1.1.0 both relaxed
     required fields (`status`, port `version`/`contractId`) and added new
     ones (`type`, `context`, `synonyms`, `deprecated`, `vendor`), so a v1.0.0
     document must not silently pass with v1.1.0 fields or without `status`.

4. **Linked data contracts resolve** (since 0.3) — for every
   `inputPorts[].contractId` and `outputPorts[].contractId` (nothing else is
   followed), one check per reference:
   - **API key set** (`ENTROPY_DATA_API_KEY` or its fallbacks; empty or blank
     counts as unset) and no `--local-references`: `GET
     {host}/api/datacontracts/{id}` with `x-api-key`, redirects not followed.
     `200` → `passed`; `404` → `warning` (not found on host); anything else
     (network, `401/403`, `5xx`) → `warning` (could not verify). No local
     fallback.
   - **No API key, or `--local-references`**: search the current working directory and its
     subdirectories (skipping hidden dirs, `node_modules`, `venv`, …) for
     `*.odcs.yaml` / `*.odcs.yml`, parse each, and match `kind: DataContract`
     + `id`. Found → `passed` (reason names the path); else `warning`.
   - Unresolved references are **warnings**, never errors: the contract may
     live somewhere this run can't see, and `lint` stays a non-breaking gate
     for existing users.
5. **Linked data contracts lint** — only from the `dataproduct lint` command
   (never the library API by default). Without a `datacontract` executable on
   the PATH, a single `warning` "datacontract-cli is runnable" says so (only
   when at least one contract resolved). Otherwise each *resolved* contract (deduplicated) is run
   through `datacontract lint <path-or-api-url>` (the env, including the API
   key, is inherited). Exit `0` → `passed`; otherwise `warning` carrying
   datacontract-cli's output (ANSI codes stripped, truncated). First,
   `datacontract --version` must succeed; if it can't be started, times out,
   or exits non-zero (e.g. a broken launcher on Windows), a single `warning`
   "datacontract-cli is runnable" replaces the per-contract lints. The child
   runs with UTF-8 I/O (`PYTHONIOENCODING`, `PYTHONUTF8`) and `NO_COLOR`;
   timeouts or any error starting it are `warning`s, never crashes.
   All files are read and written as UTF-8, independent of the OS locale.

**Schema validation itself is schema-only** — parity with datacontract-cli's `lint`, which validates
against the JSON Schema and nothing more. Best-practice warnings (≥1 outputPort,
`id` is a UUID, recommended `status` values, `v0.9.0` deprecation) are
**backlogged** for a coordinated pass across both CLIs — see
[backlog.md](backlog.md).

## Output & exit codes

- Produce a `Run` result object (parallel to datacontract-cli's `Run`) with a
  list of checks, each `{result: passed|warning|error, name, message, ...}`.
  `warning` is used by the linked-contract checks (4, 5).
- Overall result: `passed` if no `error` checks (warnings allowed), else
  `failed`.
- **Exit code:** `0` when overall `passed`, `1` when `failed`.
- Console output uses `rich` (green ✅ / yellow ⚠️ / red ❌ summary).
- `--output` + `--output-format` writes machine-readable `json` or JUnit `xml`
  for CI, matching datacontract-cli's `write_test_result`.

## Library API

```python
from dataproduct.data_product import DataProduct

run = DataProduct(data_product_file="dataproduct.odps.yaml").lint()
assert run.result == "passed"
```

## Bundled schemas

- `dataproduct/schemas/odps-1.1.0.schema.json` (default) and
  `dataproduct/schemas/odps-1.0.0.schema.json`, vendored from
  `https://raw.githubusercontent.com/bitol-io/open-data-product-standard/main/schema/odps-json-schema-v<version>.json`.
- Selection lives in `ODPS_SCHEMA_VERSIONS` (`dataproduct/lint/schema.py`);
  `dataproduct/schemas/download` refreshes the vendored copies.
- Check names state the schema that ran (`Data product is valid against ODPS
  v1.1.0` / `Check that data product is valid against ODPS v1.0.0`); with a
  custom `--json-schema` no version is named.


## Acceptance criteria

- [ ] Linting the `init` output returns `passed`, exit `0`.
- [ ] A file missing `status` (a required field) returns `failed`, exit `1`,
      with a message naming the missing field.
- [ ] `kind: SomethingElse` fails schema validation.
- [ ] Malformed YAML returns a single `error` (not a stack trace).
- [ ] A file with no `outputPorts` still `passes` (the JSON Schema doesn't
      require it; the "≥1 outputPort" recommendation is backlogged).
- [ ] `--all-errors` reports multiple violations at once.
- [ ] `--output-format junit --output TEST.xml` writes valid JUnit XML.
- [ ] `--json-schema <path>` validates against the supplied schema instead of
      the bundled one.
- [ ] A missing file yields a clean `error` result (no traceback), exit `1`.
- [ ] A `v1.1.0` document using `type`, `context`, `synonyms`, `deprecated`,
      `vendor`, and ports without `version`/`contractId` returns `passed`.
- [ ] A `v1.1.0` document without `status` returns `passed`; a `v1.0.0` one fails.
- [ ] A `v1.0.0` document using a v1.1.0-only field (e.g. `type`) fails.

- [ ] A port `contractId` matching a local `*.odcs.yaml` with `kind: DataContract`
      passes; one with no match warns; the run still `passes`.
- [ ] With an API key, contracts resolve via Entropy Data only.
- [ ] An empty or blank API key resolves locally.
- [ ] `--local-references` resolves locally even with an API key.
- [ ] `dataproduct lint` runs `datacontract lint` once per resolved contract
      when it is on the PATH, and warns once when it isn't; the library API doesn't.

## Test cases (pytest)

1. `test_lint_valid` — `tests/fixtures/lint/valid-dataproduct.odps.yaml` → passed.
2. `test_lint_missing_required_field` — remove `status` → failed.
3. `test_lint_wrong_kind` → failed.
4. `test_lint_invalid_yaml` → single error.
5. `test_lint_no_output_ports_passes` → passed (schema-only; no warning in 0.1).
6. `test_lint_all_errors_reports_multiple`.
7. `test_lint_junit_output` → well-formed XML written to file.
8. `test_lint_custom_json_schema`.
9. `test_lint_missing_file` → error, exit 1.
10. `test_lint_valid_v1_1_0`, `test_lint_v1_1_0_status_is_optional`,
    `test_lint_v1_1_0_fields_rejected_under_v1_0_0`,
    `test_lint_names_the_schema_that_ran`, `test_schema_version_selected_by_api_version`.
11. `tests/test_references.py` — local / Entropy Data resolution, warnings,
    datacontract-cli invocation, `--no-resolve-references`, `--local-references`.

## Decisions

1. **Warnings model:** ✅ **Schema-only for 0.1** — full parity with
   datacontract-cli. Best-practice warnings backlogged ([backlog.md](backlog.md)).
2. **Reference resolution:** ✅ **Deferred** — no inlining of
   `authoritativeDefinitions` in 0.1 ([backlog.md](backlog.md)).
   Port `contractId`s are resolved since 0.3 (check 4), as warnings.
3. **`apiVersion v0.9.0`:** ✅ **Accept silently** (validated with the v1.0.0
   schema, which has no dedicated v0.9.0 rules). A deprecation warning is backlogged.
4. **ODPS v1.1.0 (2026-09):** ✅ **Schema chosen per `apiVersion`**, mirroring
   datacontract-cli #1606 (`lint` validates against the declared ODCS
   `apiVersion`; older versions without their own schema share the nearest
   one, unknown versions fall back to the newest). Needed here because v1.1.0
   loosened required fields, so a v1.0.0 document must not pass without
   `status` or with v1.1.0-only fields.
```