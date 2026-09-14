# Workbench contract

Reuse api.realityGapSourceExamples (read), addRealityGapEntry, recommendRealityGap,
decideRealityGap, prepareRealityGap, simulateRealityGapRule, activateRealityGapRule,
disableRealityGapRule and replayRealityGapRule. Every write routes through the existing
review/confirm lock. expected_revision is captured from current detail where supported.
No automatic replay loop. Cursor/result state belongs to tenant + gap + rule identity.
Simulation failure does not unlock activation; editing a new draft never changes active version.
