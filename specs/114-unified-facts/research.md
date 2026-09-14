# Research

Research delegated to finance_read_audit under speckit-plan and reviewed against callers.

Decision: display all recorded observations. Fact has no valid_from/to, active or superseded fields. Latest observed time does not prove present authority; conflict detection elsewhere must not be replaced in the register. The current typed predicate catalog is small, so only general search and actual held subject-type choices are introduced.

Decision: replace existing inline facts list queries with a scoped metadata read model. Current timestamp-only ordering is unstable for ties, page is not clamped, and source/rule ORM loads include payload/configuration for metadata. Explicit projected columns preserve response metadata while fixing these issues. Search includes stored values and implemented source metadata only, not invented subject names.

Decision: shared Inspector uses exact source/subject links in an added context section, leaving technical rows compatible. There is no interpretation_rule Inspector: render its name/version as metadata only. No-source does not imply manual/internal origin. Original value strings require localization exclusion markers because the application also translates DOM text.

Alternatives rejected: current-fact status, predicate-specific workflows, editing and conflict resolution broaden unproven scope. All unknowns resolved.
