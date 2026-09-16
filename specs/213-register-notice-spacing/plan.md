# Plan
Use `.register-surface > [data-projection-freshness] { margin-inline: 16px; }` in the shared stylesheet. Direct-child scope avoids double padding in InspectorCatalog and leaves standalone/dialog/form contexts unchanged. No JavaScript or backend logic changes.

Constitution Check: PASS for all eight principles; presentation-only, source/tenant/service/schema boundaries unchanged.

Verification: add geometry assertions to the existing finance browser fixture and observe failure before CSS; check desktop/mobile and all freshness states. Use the same DOM element in a temporary padded wrapper and standalone container to verify selector scope, restoring it afterwards. Run format, frontend tests, language audits, build and spec policy. No backend tests required for CSS-only correction. Rollback: remove the single CSS rule.

Review: two requirements fully covered by three tasks; no critical findings, conflicts or ambiguities. Existing wrapper structure inspected, no research or new dependency needed.
