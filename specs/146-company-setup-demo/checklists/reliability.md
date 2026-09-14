# Requirements Quality Review: Company Setup and Demo Data

Purpose: reviewer-owned design checklist; unchecked markers are not missing implementation tests. Scope and defaults are defined in spec/plan/contracts. No marker is owner-approved by generating this file.

- [ ] CHK001 Are application metadata, first/later creation and existing membership/invitation precedence unambiguous? [Clarity, FR-001/002]
- [ ] CHK002 Are all content/environment/admission combinations and exact pending destinations defined without broadening production access? [Consistency, FR-003/004/005]
- [ ] CHK003 Is same-request replay specified across both persistence paths, including changed content/name and lost responses? [Completeness, FR-006]
- [ ] CHK004 Are empty, partial, failed, ready and cancelled setup consequences precise? [Coverage, FR-006/007]
- [ ] CHK005 Does the canonical profile identify counts, case expectations, source provenance, windows and capability gaps without false financial authority? [Measurability, FR-008–011, DR-001–003]
- [ ] CHK006 Is execution fixture creation separate from actual action approval and destructive reset? [Safety, FR-012, DR-004]
- [ ] CHK007 Are the proposed two tables and supporting uniqueness justified field by field, with explicit schema approval pending? [Schema proof, data-model.md]
- [ ] CHK008 Are initialization and continuous-intake permissions narrowly scoped and distinct from general Sandbox/business rights? [Authorization, FR-005/020]
- [ ] CHK009 Are stopped-by-default, prerequisite preview, three rates and Start/pause/resume/stop/reconnect semantics fully specified? [Completeness, FR-014–017]
- [ ] CHK010 Is queued cancellation distinguished from spec 147 ordinary pause and in-flight/unknown work? [Consistency, FR-017]
- [ ] CHK011 Are import success, generator success, failure/backpressure, timestamps, identity and pagination independently defined? [Clarity, FR-018/019]
- [ ] CHK012 Are all four languages, themes, viewports and keyboard/recovery states covered at both UI entries? [Coverage, FR-013]
- [ ] CHK013 Do tasks map every FR/DR and success criterion to executable proof and implementation paths? [Traceability, tasks.md]
