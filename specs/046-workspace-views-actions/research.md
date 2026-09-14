# Research: Workspace Views and Actions

## Decision: Use one workspace presentation catalog

**Rationale**: A View is broader than a Projection and may point to an authoritative register. A separate workspace catalog can reference canonical routes and registered Projection/Command keys without overloading technical catalogs with route ordering. One validated composer still prevents drift.

**Alternatives considered**: Independent workspace fields in Projection and Command catalogs leave authoritative registers without an owner and duplicate ordering. A React-only map cannot be validated or consumed by other adapters. Tenant-configurable database navigation has no proven use case.

## Decision: Product labels are Views and Actions

**Rationale**: `View` truthfully covers authoritative registers and rebuildable read models. `Action` describes operator intent while preserving `Command` as technical application vocabulary.

**Alternatives considered**: `Projections and Commands` exposes implementation language and misclassifies registers. `Manual interventions` makes normal daily work sound exceptional.

## Decision: Reuse existing action endpoints and services

**Rationale**: Reservations, movements, corrections, holds, handling units, lots, and serial units already have tenant-scoped API routes over shared services. The missing layer is discovery, typed clients, forms, confirmation, and result routing.

**Alternatives considered**: A generic command endpoint weakens explicit typing and review. Executing through MCP or Copilot would add an unnecessary transport hop.

## Decision: Use two confirmation strengths

**Rationale**: Every mutation receives distinct human confirmation. Snapshot-sensitive correction uses its server preview fingerprint. Atomic create/hold/reserve/movement commands confirm an exact input summary and leave invariant evaluation to the server.

**Alternatives considered**: New server previews for every atomic create command add unproven service surface. Immediate form submission violates the mutation-safety contract.

## Decision: Preserve current frontend edits in place

**Rationale**: The worktree already improves the area picker and related styling. Focused patches will extend that version rather than reverting or regenerating it.

**Alternatives considered**: Restoring committed files would destroy user work. A full shell refactor is unrelated to proving this feature.
# Searchable Action Launcher Amendment

- **Decision**: In every actionable workspace, show its first two ordered actions in the sidebar and search the complete validated workspace action array in a shared modal launcher.
- **Rationale**: This preserves a compact operational surface, avoids workspace-specific UI logic or duplicate promotion metadata, and makes every eligible action discoverable without adding a generic executor.
- **Alternatives considered**: Showing every action inline creates an unbounded sidebar; exposing every command-catalog entry would advertise commands without a safe Web boundary.
- **Eligibility finding**: Order Operations has four directly Web-backed action families: reservation, commitment hold/release, document commitment hold/release, and party delivery hold/release. Manual order creation remains outside the launcher because its canonical command is not Web-eligible.
