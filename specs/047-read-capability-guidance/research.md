# Research: Read Capability Guidance

- **Decision**: One discriminated guidance catalog. **Why**: one lookup remains simple
  while read fields cannot masquerade as mutation events/confirmation.
- **Decision**: Validate application and public identities separately. **Why**: names
  such as `commitments_list` intentionally map to `commitments`.
- **Decision**: Controlled data-basis references. **Why**: free prose cannot catch
  drift; requiring physical foreign keys or new schema would be false precision.
- **Rejected**: private prompt prose, because it drifts and cannot be tested.

