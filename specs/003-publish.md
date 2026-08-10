# Spec 003 — `dataproduct publish`

## Goal

Publish a local data product definition to **Entropy Data** so it appears in the
catalog / manager UI. Parallels `datacontract publish`, which PUTs an ODCS data
contract to `{host}/api/datacontracts/{id}`.

## CLI contract

```
dataproduct publish [LOCATION] [OPTIONS]
```

| Arg / Option | Type | Default | Description |
|---|---|---|---|
| `LOCATION` | positional | `dataproduct.odps.yaml` | url or local path of the data product yaml. |
| `--json-schema` | option (str) | none | Alternate ODPS JSON Schema (passed through to the pre-publish lint). |
| `--ssl-verification` / `--no-ssl-verification` | flag | `true` | Toggle TLS verification for the request. |
| `--debug` | flag | `false` | Enable debug logging. |

Example: `dataproduct publish dataproduct.odps.yaml`

## Behavior

1. Resolve the document at `LOCATION` into a Python dict (read file / fetch URL,
   parse YAML).
2. **No client-side lint in 0.1** — parity with datacontract-cli's `publish`,
   which reads → PUTs and lets the server validate. The pre-publish lint gate
   (+ `--skip-lint`) is **backlogged** ([backlog.md](backlog.md)). The server
   validates and returns a message on rejection, which we surface verbatim.
3. Resolve host + API key from config/env:
   - Host: `ENTROPY_DATA_HOST` (default `https://api.entropy-data.com`), with
     `DATAMESH_MANAGER_HOST` / `DATACONTRACT_MANAGER_HOST` fallbacks.
   - API key: `ENTROPY_DATA_API_KEY`, falling back to
     `DATAMESH_MANAGER_API_KEY` / `DATACONTRACT_MANAGER_API_KEY`.
   - Missing API key → error:
     `Cannot publish, as neither ENTROPY_DATA_API_KEY, DATAMESH_MANAGER_API_KEY, nor DATACONTRACT_MANAGER_API_KEY is set`.
4. `PUT {host}/api/dataproducts/{id}` with:
   - headers `Content-Type: application/json`, `x-api-key: <key>`
   - body = the JSON of the data product dict
   - `verify=<ssl_verification>`
5. On HTTP `200`: print `✅ Published data product successfully`; if the
   response carries a `location-html` header, print `🚀 Open <url>`.
6. On non-`200`: print `Error publishing data product to <hostname>: <body>`
   and exit `1`.
7. Network / unexpected errors: print `Failed publishing data product. Error: <e>`.

### Confirmed Entropy Data API contract (verified 2026-08-10)

Confirmed against the official docs ([entropy-data.com](https://docs.entropy-data.com/concepts/dataproducts),
[datamesh-manager.com](https://docs.datamesh-manager.com/dataproducts),
[auth](https://docs.entropy-data.com/authentication)). The public
OpenAPI/Swagger UI is at `https://api.entropy-data.com/swagger/index.html`
(the `openapi.json` itself is auth-gated).

- **Method + path:** `PUT /api/dataproducts/{id}` — idempotent create-or-replace.
- **Headers:** `x-api-key: <ENTROPY_DATA_API_KEY>`, `content-type: application/json`.
- **Body:** JSON of the data product following ODPS. The server
  **auto-detects `specificationType`** and supports both ODPS and the (legacy)
  Data Product Specification, migrating accordingly.
- **Success:** `200 OK`.
- **Base URL:** `https://api.entropy-data.com`.
- **Server-required fields** (beyond raw ODPS schema): `id`, `name`,
  `apiVersion`, `kind`, at least one `outputPort`, and a **`team`** whose
  `name`/id **references an already-existing team** in the org. ⇒ Publishing a
  product that references a non-existent team will be rejected by the server;
  surface that error message clearly rather than masking it.

This matches datacontract-cli's `publish` exactly (same verb, `x-api-key`,
`200`), so `integration/entropy_data.py` can be a near-copy with the path
changed from `datacontracts` to `dataproducts`.

## Config / auth

Reuse `dataproduct/integration/entropy_data.py`, structurally identical to
datacontract-cli's, with `_get_host` / `_get_api_key` helpers and the same
env-var precedence. `.env` is auto-loaded.

## Library API

```python
from dataproduct.data_product import DataProduct

DataProduct(data_product_file="dataproduct.odps.yaml").publish()
```

## Acceptance criteria

- [ ] With a valid file and a valid API key, `publish` PUTs to
      `{host}/api/dataproducts/{id}` and prints the success message on `200`.
- [ ] Missing API key → clear error, exit `1`, **no** HTTP request made.
- [ ] Non-200 response → error message including the server body, exit `1`.
- [ ] `--no-ssl-verification` disables TLS verification on the request.
- [ ] A `location-html` response header is surfaced as `🚀 Open <url>`.

## Test cases (pytest, HTTP mocked)

1. `test_publish_success` — mock `200`; assert URL, method `PUT`, `x-api-key`
   header, and success message.
2. `test_publish_missing_api_key` — unset env; assert error + no request.
3. `test_publish_http_error` — mock `422`; assert error message + exit 1.
4. `test_publish_no_ssl_verification` — assert `verify=False` passed.
5. `test_publish_location_html_header` — assert `🚀 Open` printed.

## Open questions

1. ~~**Endpoint path & method — CONFIRM with Entropy Data API.**~~ ✅ **Resolved
   2026-08-10** — confirmed `PUT /api/dataproducts/{id}`, JSON body of ODPS,
   `x-api-key` + `content-type: application/json`, `200 OK`. See "Confirmed
   Entropy Data API contract" above. New sub-question: should `publish`
   pre-check that the referenced `team` exists (an extra API call), or just let
   the server reject and surface its message? Recommendation: surface the
   server message (no extra call in v1).
2. ~~**Pre-publish lint gate.**~~ ✅ **Resolved** — no client-side lint in 0.1
   (parity). Hard gate + `--skip-lint` is backlogged ([backlog.md](backlog.md)).
3. **`id` requirement:** publish requires a top-level `id`; if absent, fail
   before making a request (schema-required anyway).
```