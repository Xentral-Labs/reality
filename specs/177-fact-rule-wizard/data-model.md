# Data Model

No persisted model changes. RealityGap owns goal, purpose, destination and revision;
entries retain evidence, recommendation and draft proposal; InterpretationRule owns
immutable versions and their status. Fact keeps its existing subject, source and rule
links. All records remain tenant scoped. Wizard stage, unsaved input, review snapshot
and exact-version simulation are ephemeral presentation state and reset on close or
tenant change. Resume uses authoritative detail, never a stored wizard completion flag.
