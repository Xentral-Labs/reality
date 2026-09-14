# Autoplay refresh review

Requirement review: user requests continuous autoplay, already required by FR-013. No unresolved clarification.

Pre-implementation analysis: each completed player action emits `reality:delivery-settled`; `useRead` preserves its answer while refreshing, but TrialEntry replaces its children whenever loading is true. This unmounts Player and resets its local presentation state. Restrict the loading replacement to the initial unanswered read. Existing error and admission behavior remains. No critical findings.

Verification: the regression failed before the fix while waiting for the next chapter. With the fix, one activation prepares, confirms and advances through the Home-entry path despite delayed entry refreshes. Full Storyline browser suite including pause/error behavior and 16 localized layouts passed; production build, 156 contract tests, four-language audit, formatting and spec policy passed. Initial loader and failed reads remain guarded.
