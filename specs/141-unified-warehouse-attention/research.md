# Research decisions

- Reuse `inventory_page` for physical/reserved/available stock. Its incoming/projected fields are not needed for this slice and are not displayed as shipment readiness. No duplicated calculation.
- Existing reservation/movement read models already paginate and resolve labels. Add exact item filters rather than treating a search string as an identity constraint. Reference search remains explicitly ID-based in these registers.
- Reuse `_movement_correction_relation_for_member` for movement roles. A corrected replacement must keep canonical role precedence. Avoid recomputing stock from the loaded movement page.
- The exception service already exposes class, cause, severity, impact, subject and source trace. Preserve it. Filter before slicing; acknowledge full-company derivation instead of claiming SQL-first exception aggregation.
- `/app/attention` preserves the legacy `/app/exceptions` path used for unsupported action reviews. Product label stays Exceptions; no Old/New toggle is introduced.
- No unresolved clarification or new infrastructure requirement remains. The owner authorized continued implementation of the established new-design direction.
