# Validation

1. Run `PYTHONPATH=packages/reality-core/src .venv/bin/python -m unittest discover -s apps/docs/scripts -p 'test_data_model_reference.py'`.
2. Run `make docs-generate`, then `cd apps/docs && npm test && npm run build`.
3. Open `/de/tool-usage/#model:commitment`; inspect original date, revisions, actions, fields and relationships. Search `due_at`, follow revision and use Back. Repeat in English and at 375px.
4. Run `make spec-check` and scoped formatting/lint; confirm deterministic catalog generation.
5. Build the docs Docker image and verify port 8083 serves the new assets.

## Browser acceptance

With Playwright available, serve the built docs or point `DOCS_TEST_URL` to the local docs container, then run `node apps/docs/scripts/model-browser-check.mjs`. `PLAYWRIGHT_MODULE` may name an existing Playwright module path and `CHROMIUM_PATH` may select an installed test browser. The check covers DE/EN at 375/1280px, fields, search, relationships, action navigation, Back, reload, unknown model keys and horizontal overflow. Screenshots are written to `/tmp/model-<locale>-<width>.png`.

`make docs-build` and the docs CI job both run Python schema parity; the normal Node docs tests verify catalog semantics and links. Browser acceptance uses a locally available browser and adds no production dependency.

The ERP expansion adds Party, Item and Shipment direct-link checks, group selection, all 35 records, and global `tracking_number` search from master data into ShipmentPackage. Follow Shipment and Back to verify cross-group context.
