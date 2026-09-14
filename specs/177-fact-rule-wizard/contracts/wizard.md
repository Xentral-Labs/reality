# Wizard Contract

New or never-activated setup opens five stages: goal, evidence, configuration, test,
activation. Existing active/disabled rules retain version management. Use current
`api.createRealityGap`, `addRealityGapEntry`, `recommendRealityGap`, `decideRealityGap`,
`prepareRealityGap`, `simulateRealityGapRule`, `activateRealityGapRule` without schema
changes. Search/simulation are reads; every other call requires explicit review.

Every review captures its input and blocks editing until canceled or confirmed.
Question creation retains one idempotency key for a review/retry. An uncertain write
locks all writes. Known failures retain the review for correction/retry. Late results
are ignored after unmount. New saved versions invalidate old simulations. Evidence
samples are not simulation filters. Activation and historical replay remain separate.
