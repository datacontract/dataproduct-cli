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
   the bundled ODPS JSON Schema (`dataproduct/schemas/odps-1.0.0.schema.json`),
   or the `--json-schema` override. Each violation is an `error` (path +
   message). With `--all-errors`, collect every violation; otherwise stop at
   the first.
   - This enforces the strictly-required fields (`apiVersion`, `kind`, `id`,
     `status`), the `kind: DataProduct` / `apiVersion` enums (both `v0.9.0` and
     `v1.0.0` are accepted, silently — no version special-casing), and the
     required subfields of ports/support/etc.

**0.1 is schema-only** — parity with datacontract-cli's `lint`, which validates
against the JSON Schema and nothing more. Best-practice warnings (≥1 outputPort,
`id` is a UUID, recommended `status` values, `v0.9.0` deprecation) are
**backlogged** for a coordinated pass across both CLIs — see
[backlog.md](backlog.md).

## Output & exit codes

- Produce a `Run` result object (parallel to datacontract-cli's `Run`) with a
  list of checks, each `{result: passed|warning|error, name, message, ...}`.
  The `warning` level exists in the model for parity/forward-compat, but 0.1
  emits only `passed` / `error`.
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

## Bundled schema

- `dataproduct/schemas/odps-1.0.0.schema.json`, vendored from
  `https://raw.githubusercontent.com/bitol-io/open-data-product-standard/main/schema/odps-json-schema-v1.0.0.json`.
- A small maintenance script (`update_schema.py`, parallel to datacontract-cli's
  update scripts) can refresh the vendored copy.

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

## Decisions

1. **Warnings model:** ✅ **Schema-only for 0.1** — full parity with
   datacontract-cli. Best-practice warnings backlogged ([backlog.md](backlog.md)).
2. **Reference resolution:** ✅ **Deferred** — no inlining of
   `authoritativeDefinitions` in 0.1 ([backlog.md](backlog.md)).
3. **`apiVersion v0.9.0`:** ✅ **Accept both silently** (schema default; no
   special-casing). A deprecation warning is backlogged.
```