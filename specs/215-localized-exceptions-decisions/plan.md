# Plan
Edit existing de/nl/es catalog values in place; do not change keys or callers. Remove just Exception(s) and Decision(s) from the invariant allowlist. Update model-terminology tests to retain every other canonical noun and assert the localized subset and its related labels. Review effective catalog values after overrides and inspect usages.

Constitution Check: PASS for all eight principles. Presentation-only; no schema, source, tenancy, service or business-rule impact. User explicitly approves the limited spec208 change. No new dependencies or unresolved research questions.

Test-first: update existing vocabulary expectations and observe red before implementation. Run all frontend tests, language audit, formatting and build, plus spec policy. Review runtime catalogs and changed values for grammar and English leakage. No backend tests needed for catalog-only edits. Rollback: revert translations/allowlist/tests together.
