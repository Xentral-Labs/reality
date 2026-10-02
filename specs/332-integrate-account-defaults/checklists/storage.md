# Storage Requirements Checklist: Integrate account defaults

Purpose: reviewer-owned requirements-quality assessment, not implementation completion.
Created: 2026-10-02. Feature: [spec.md](../spec.md).
Ownership: mark x only after reviewer evaluation. Implementation does not edit markers.

- [x] CHK001 Are the exact selection/account identity boundaries specified? [FR-002, FR-006]
- [x] CHK002 Is one-default-per-tenant/role behavior explicit for concurrency? [FR-002, FR-004]
- [x] CHK003 Are unchanged account revisions and historical postings specified? [FR-005]
- [x] CHK004 Are legacy SELECT compatibility and all write refusals explicit? [FR-007]
- [x] CHK005 Does incompatible legacy role state have a lossless abort requirement? [FR-006]
- [x] CHK006 Are blocked, missing and cross-tenant selections distinguished? [US1, US2, FR-008]

Notes: owner has authorized the concrete scope and implementation; this checklist
assesses wording quality independently of that authorization and release acceptance.

Reviewer: projection_research (independent requirements and architecture review).
Review date: 2026-10-02. Decision: PASS for CHK001-CHK006. The specification distinguishes
selection identity from account identity, states tenant/role concurrency invariants,
preserves revisions and financial provenance, explicitly refuses legacy relation writes,
requires lossless abort for incompatible role mappings, and separates missing, blocked
and cross-tenant cases. The plan preserves service mutation semantics through account
markers and keeps the legacy relation read-only. This decision approves requirements
quality and architecture, not implementation completion or release acceptance.
