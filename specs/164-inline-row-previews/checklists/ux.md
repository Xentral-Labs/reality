# UX Requirements Checklist: Inline Row Previews

**Purpose**: Validate UX, interaction, and accessibility requirement quality before implementation
**Created**: 2026-09-10
**Feature**: [spec.md](../spec.md)

This is a reviewer-owned requirements-quality checklist. `[x]` means a reviewer approves the requirement quality, not that implementation is complete.

## Completeness

- [ ] CHK001 Are all eight in-scope surfaces named and are their applicable row types bounded? [Completeness, Spec §Scope, FR-001]
- [ ] CHK002 Are preview, navigation, related filtering, editing, and operational action all defined as distinct meanings? [Completeness, Spec §FR-005]
- [ ] CHK003 Are loading, loaded, error, retry, close, and switch-preview requirements documented? [Completeness, Spec §US1, Edge Cases]
- [ ] CHK004 Are both list and dense-table disclosure structures specified? [Completeness, Spec §FR-008–009]
- [ ] CHK005 Is the deeper Source → Evidence → Reality path required wherever supporting data exists? [Completeness, Spec §FR-014, DR-001]

## Clarity and Consistency

- [ ] CHK006 Is “read-only preview” clearly separated from full Inspector depth and all mutating workflows? [Clarity, Spec §Non-Goals, FR-004]
- [ ] CHK007 Is the chevron vocabulary unambiguous across collapsed and expanded states? [Clarity, Spec §FR-007]
- [ ] CHK008 Are icon and visible-label rules consistent between compact work lists and dense tables? [Consistency, Spec §US2, FR-006]
- [ ] CHK009 Do Master Data requirements preserve a clear distinction between preview and edit despite replacing passive side detail? [Consistency, Spec §US3 scenario 3]
- [ ] CHK010 Do the scope and non-goals consistently exclude Data Sources, Facts, Analytics, Activity, Playground, and technical catalogs? [Consistency, Spec §Scope, Non-Goals]

## Accessibility and Responsive Coverage

- [ ] CHK011 Are pointer, Enter, Space, focus restoration, expanded state, and controlled-region relationships all specified? [Coverage, Spec §FR-003, FR-012]
- [ ] CHK012 Are accessible-name and tooltip requirements sufficient for any permitted icon-only control? [Coverage, Spec §US2 scenario 3, FR-006]
- [ ] CHK013 Is narrow-screen reflow distinguished from acceptable horizontal scrolling for genuinely tabular content? [Clarity, Spec §FR-015]
- [ ] CHK014 Are long identifiers, translated labels, money, quantity, and external values addressed as layout edge cases? [Coverage, Spec §Edge Cases]

## State and Safety Coverage

- [ ] CHK015 Are all context changes that invalidate an open preview enumerated? [Completeness, Spec §FR-010]
- [ ] CHK016 Is opaque identity explicitly required so duplicate human numbers cannot collide? [Coverage, Spec §DR-004, Edge Cases]
- [ ] CHK017 Are nested controls and selectable-row interactions defined so one gesture has one outcome? [Coverage, Spec §Edge Cases]
- [ ] CHK018 Is non-mutation specified for opening, closing, loading, retrying, and failing previews? [Safety, Spec §FR-011]
- [ ] CHK019 Are confirmation requirements preserved for every operational action reachable from a preview? [Safety, Spec §FR-017]

## Measurability and Dependencies

- [ ] CHK020 Can overlay removal and immediate-below-row placement be measured across every included surface? [Measurability, Spec §SC-001]
- [ ] CHK021 Can semantic icon-and-label compliance be inventoried objectively? [Measurability, Spec §SC-002]
- [ ] CHK022 Are keyboard and responsive success criteria expressed as observable outcomes? [Measurability, Spec §SC-003–004]
- [ ] CHK023 Is the assumption that current read models are sufficient paired with an explicit scope response if a gap is found? [Dependency, Spec §Assumptions]

## Review

- **Specification reviewer**: Product owner, 2026-09-10
- **Domain/architecture reviewer**: N/A — presentation-only plan; Constitution Check passed
- **Decision**: Approved

## Notes

- `$speckit-implement` reads this checklist but does not change reviewer-owned markers.

