# Spec 001 — `dataproduct init`

## Goal

Create a new, **valid** ODPS `dataproduct.odps.yaml` on disk so a user can start
authoring a data product immediately. The generated file must pass
`dataproduct lint` with no errors.

## CLI contract

```
dataproduct init [LOCATION] [OPTIONS]
```

| Arg / Option | Type | Default | Description |
|---|---|---|---|
| `LOCATION` | positional | `dataproduct.odps.yaml` | Path of the file to create. |
| `--template` | option (str) | none | URL or local path of a template / existing data product to seed from. |
| `--overwrite` | flag | `false` | Overwrite an existing file at `LOCATION`. |
| `--debug` | flag | `false` | Enable debug logging. |

Example: `dataproduct init dataproduct.odps.yaml`

## Behavior

1. If `LOCATION` exists and `--overwrite` is not set → print
   `File already exists, use --overwrite to overwrite` and exit code `1`.
2. Resolve the template contents:
   - No `--template` → use the **bundled** default template
     (`dataproduct/schemas/odps-1.0.0.init.yaml`).
   - `--template` is an `http(s)://` URL → fetch its body.
   - `--template` is a local path → read it.
3. Write the template string to `LOCATION`.
4. Print `📄 data product written to <LOCATION>` and exit `0`.

(Directly parallels `datacontract init`: same overwrite guard, same
`get_init_template` resolution order, same success message shape.)

## Bundled default template

- Lives at `dataproduct/schemas/odps-1.0.0.init.yaml`.
- Uses `apiVersion: v1.0.0`, `kind: DataProduct`.
- Contains a **static** `id` placeholder (`my-data-product-id`) — see decision
  below.
- Includes at least one `outputPort` so the result satisfies the best-practice
  recommendation, and commented-out stubs for optional sections.

Proposed content:

```yaml
apiVersion: v1.0.0
kind: DataProduct
id: my-data-product-id
name: My Data Product
version: v1.0.0
status: draft

description:
  purpose: Purpose of the data product.
  usage: Intended usage of the data product.
  limitations: Limitations of the data product.

# tags: ['example']

# inputPorts:
#   - name: source-data
#     version: 1.0.0
#     contractId: 00000000-0000-0000-0000-000000000000

outputPorts:
  - name: my-output-port
    description: The data this product exposes.
    type: tables
    version: 1.0.0
    # contractId: 00000000-0000-0000-0000-000000000000

# support:
#   - channel: My Team Slack
#     url: https://example.slack.com/archives/C0000000000
#     tool: slack

# team:
#   name: My Team
#   members:
#     - username: jane.doe@example.com
#       name: Jane Doe
#       role: owner
```

## Acceptance criteria

- [ ] `dataproduct init` with no args writes `dataproduct.odps.yaml`.
- [ ] The generated file passes `dataproduct lint` with **zero errors**.
- [ ] Running `init` again without `--overwrite` fails with exit code `1` and
      the "File already exists" message; the existing file is left untouched.
- [ ] `--overwrite` replaces the file.
- [ ] `dataproduct init custom/path.odps.yaml` honors the custom path.
- [ ] `--template <url>` seeds from a remote file; `--template <path>` seeds
      from a local file.
- [ ] Success prints `📄 data product written to <LOCATION>`.

## Test cases (pytest)

1. `test_init_default_creates_valid_file` — invoke `init` in a tmp dir; assert
   file exists and `lint` of it returns result `passed`.
2. `test_init_refuses_existing_without_overwrite` — pre-create the file; assert
   exit code 1 and content unchanged.
3. `test_init_overwrite` — pre-create; run with `--overwrite`; assert replaced.
4. `test_init_custom_location`.
5. `test_init_template_from_local_path`.
6. (optional/mocked) `test_init_template_from_url`.

## Decisions

1. **`id` in the default template:** ✅ **Static placeholder**
   (`my-data-product-id`), matching datacontract-cli. `init` stays a pure
   generator that never reads the existing file, so `--overwrite` simply stamps
   the template down again (no id to preserve). Auto-generated UUIDs were
   considered but deferred to keep sister-project parity; revisit in **both**
   CLIs together later.
2. **File extension in default:** ✅ `dataproduct.odps.yaml`.
```