# Validation

Run `make spec-check`, `make docs-generate`, the documentation Python reference tests, and `npm test`, `npm run format:check`, `npm run build` in `apps/docs`.

Open Tool Usage in English and German, select Technical, read the category guide, follow all reservation links, and inspect a mapped command/tool/action and an unmapped read tool. Check mobile wrapping and both themes. Generation must be deterministic; `make docs-catalog-check` compares output with Git HEAD, so a working diff is expected until the generated output is committed. Compare a second generation with the first without staging user files.

No migration or business execution is required. Backend and application frontend changes are out of scope; existing executable schema/reference proofs and final diff review protect compatibility.
