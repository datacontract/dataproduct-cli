# Backlog — post-0.1 improvements

Items deliberately deferred to ship a useful **0.1 this week**. Where noted,
these are **cross-CLI**: to keep `dataproduct-cli` and `datacontract-cli` true
siblings, implement them in **both** together (or file a matching issue in the
other repo when doing one).

## 0.1 scope (for reference)

`init` (static-id template), `lint` (schema-only), `publish` (read → PUT, no
client-side lint). Everything below is out of scope for 0.1.

## Deferred items

### 1. Auto-generated UUID `id` on `init` (cross-CLI)
0.1 ships a static placeholder `id: my-data-product-id` (parity with
datacontract-cli). Improvement: generate a UUID v4 on `init`. If adopted,
resolve the `--overwrite` identity question then (reuse existing id vs fresh —
see 001-init.md history). Do this in both CLIs.
- Source: [001-init.md](001-init.md)

### 2. Best-practice `lint` warnings (cross-CLI)
Non-blocking `warning`-level checks on top of JSON-Schema validation:
- No / empty `outputPorts` → "should expose at least one output port".
- `id` is not a UUID.
- `status` not in `proposed|draft|active|deprecated|retired`.
- Missing `name` / `version` / `description`.
The `Run`/`Check` model already carries a `warning` level, so this is additive.
Do this in both CLIs (datacontract-cli is also schema-only today).
- Source: [002-lint.md](002-lint.md)

### 3. `apiVersion v0.9.0` deprecation warning (cross-CLI)
`v0.9.0`, `v1.0.0`, and `v1.1.0` are accepted silently. Improvement: warn
(non-blocking) when `v0.9.0` is used, nudging toward `v1.1.0`. Pairs with item 2.
- Source: [002-lint.md](002-lint.md)

### 4. Pre-publish lint gate + `--skip-lint` (cross-CLI)
0.1 `publish` does no client-side validation (parity). Improvement: lint before
publishing and refuse on `error` (exit 1), with `--skip-lint` to bypass. Gives
a friendly `status is required` instead of a raw server error. Do this in both
CLIs (datacontract-cli's `publish` is also un-gated today).
- Source: [003-publish.md](003-publish.md)

### 5. `authoritativeDefinitions` reference resolution (this CLI)
Optionally resolve/inline external references during `lint` (as datacontract-cli
does behind `--inline-references`). Deferred until a concrete need.
(Port `contractId` resolution shipped separately — see 002-lint.md check 4.)
- Source: [002-lint.md](002-lint.md)

### 6. Publish-time `team` existence pre-check (this CLI)
The Entropy Data API requires the referenced `team` to already exist. 0.1 lets
the server reject and surfaces its message. Improvement: optionally pre-check
the team via the API and give a clearer local error. Low priority.
- Source: [003-publish.md](003-publish.md)

## Later features (never in 0.1 scope)
`export`, `import`, `changelog`, `catalog`, `edit`, `test`, `api` — mirror
datacontract-cli's surface as demand appears.
