# Research: Repeating Form Groups

- **Decision**: Extend the existing action form metadata with a recursive repeating-group kind.
- **Rationale**: It covers typed business arrays while preserving current controls and explicit action endpoints.
- **Rejected**: Raw JSON is not usable business UI; JSON Schema is broader than the proven use case; specialized order-only state would not be reusable.
