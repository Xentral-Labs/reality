# Research: Interpretation Coverage

## Decisions

- Add an immutable outcome per terminal attempt; extending mutable ImportJob would lose retry history.
- Store produced identities as child rows; JSON would create an unvalidated relationship format and polymorphic FKs cannot express all target tables.
- Report old sources as `not_recorded`; do not infer or fabricate evidence.
- Keep coverage computed; persisting it would duplicate source/job/outcome state.

