# Generated API Client

This directory holds the generated OpenAPI client produced by
[`@hey-api/openapi-ts`](https://heyapi.dev/).

Generate / refresh:

```bash
# from repo root, with backend running:
bash ./scripts/generate-client.sh
# or manually from mobile/:
bun run generate-client
```

The generator reads `../openapi.json` (download from
`http://localhost:8000/api/v1/openapi.json`) and writes:

- `core/` runtime helpers
- `schemas.gen.ts`
- `sdk.gen.ts`
- `types.gen.ts`
- `index.ts`

Screens under `src/app/` currently use `axios` directly via
`@/lib/auth`. Swap to the generated SDK services as the app grows
(same pattern as `frontend/`).
