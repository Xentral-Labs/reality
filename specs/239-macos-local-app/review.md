# Review Record: macOS Local App

## Authorization and scope

The owner accepted the concept for planning and subsequently instructed continuation
with implementation after the next packaging milestone was described. The isolated
packaging/port spike is within that authorization. Custom reviewer-owned checklist
markers remain unchanged; later security/schema and release reviews remain open.
No account schema or production authorization change is implemented by this spike.

## Pre-spike consistency review

Spec, plan, tasks and contracts map all 17 FR and four DR requirements to tests and
implementation/design tasks. The spike is infrastructure-only and introduces no
business authority, alternate service path or tenant query. The six port-state tests
and native-process tests cover FR-017 without assuming that loopback means authentication.
No critical design finding blocks this isolated proof. Full identity/schema approval
and production implementation review are not inferred from self-review.

## Result

Port proof passes. The existing Python candidate fails relocatability preflight;
T003/T004 remain incomplete. Do not proceed to product integration or publish an app
until those package/signing/clean-machine gates pass. Refer to verification.md for
actual checks; unexecuted future tests remain pending.

## Runtime build follow-up

The runtime build and real database smoke now pass; see verification.md. Review kept
all database writes inside disposable test storage, ensured existing output rejection,
checked path/hash failure cases and preserved the offline assembly boundary. No
identity/schema/security approval is inferred from this build work. The product
Tauri/window and release qualification gates remain open.

## FR-018 bounded preview review

Owner explicitly requests repeatable fresh tests and agent-operated cleanup. Reviewed
against FR-014: disposable copies must not invoke production uninstall/data erasure.
No clarification required for the stateless preview. Plan consistency analysis: no
critical findings for this bounded helper; future persistent-data/Keychain isolation
is a prerequisite before extending its fresh-state claim to the full product.

## Owner-directed onboarding implementation (2026-09-19)

After viewing the native proof, the owner explicitly requested continuing toward
opening the app and proceeding through setup. Local development integration is now
in scope; the earlier blanket post-spike stop is superseded for development by that
instruction. Developer ID / notarization / clean-machine results still gate release,
not development of the requested onboarding. No security checklist is marked reviewed
on the owner's behalf. Schema rationale remains the repeated account-policy uses in
data-model.md; tests must prove hosted rejection and exact installation binding before
wiring a desktop HTTP adapter. This is engineering review, not an independent audit.

## Interactive milestone review after explicit session approval

The owner approved the shared session boundary change. Review confirms that native
code receives a real session token over its private pipe, both transports call the
same issuer/revoker, and the desktop HTTP wrapper retains shared product membership
checks. Existing hosted cookie attributes are unchanged. No auth-disabled mode,
fake verified email, direct adapter business write or automatic company creation.

The packaged development runtime is deliberately disposable, visibly labeled and
limited to empty-company setup. The real browser journey and two native fresh-install
cycles pass, including removal of the test cluster after use. Persistent installation
state, replay across app restarts, demo/live workers, Keychain and signed release gates
remain open. Do not mark the encompassing product/security tasks complete based on this
bounded milestone. Full-suite verification results are recorded in verification.md.

### First-use refinement pre-implementation review

Owner screenshots establish compact startup and settings landing as the issues.
FR-019/020, the plan and T034 agree on desktop size, Home after creation, and preserved
restoration behavior. Existing Home routing and responsive sidebar are reused.
No unresolved clarification or critical consistency finding blocks this change.

### First-use refinement implementation review

Changes are presentation/navigation only. Creation opts into Home explicitly; the
shared open-company default and restoration call remain unchanged. Native startup
uses work-area overflow prevention without locking resize behavior. Real browser
acceptance, native cookie proof, navigation checks and artifact signature pass.
This is a bounded development milestone; demo/live remains T035 and release gates
remain open.

### Demo/live and optional Anthropic pre-implementation review

FR-021/022 and T035/T036 preserve the canonical company setup, Demo Data, scheduler,
worker and AI settings services. The desktop layer only supervises processes and
advertises an onboarding capability. Identity crosses process boundaries on private
stdin and remains bound to the exact installation owner; request data cannot set it.
The API key follows the existing tenant-secret path and is never returned. The test
artifact's encryption key, database and artifacts share its disposable root.

Cross-artifact analysis found no schema expansion, alternative business rule or
hosted-onboarding change. Required acceptance covers a real queued initialization,
running live connection, existing payment records, configured-key metadata and child
cleanup. AI setup is explicitly confirmed by the same Create action described beside
the optional field. No unresolved clarification or critical finding blocks T035/T036.

### Native icon pre-implementation review

The source of truth is the existing `LogoMark` SVG path and `#635bff` web brand tile.
The desktop generator only rasterizes that geometry at native resolutions. The plan,
FR-023 and T037 agree on ICNS packaging and macOS metadata. No behavioral, security,
schema or tenant-isolation concern is introduced, and no clarification remains.

### Native icon implementation review

The generated mark matches the web component's three paths and brand color. Packaging
copies one declared ICNS resource; no runtime loading, network access or new authority
is involved. Multi-resolution extraction, bundle metadata, signing and native launch
passed. T037 and FR-023 are satisfied for the development artifact.

### Demo default and missing-AI implementation review

The setup default lives only in the shared confirmation form; the API remains explicit
and compatible. Chat readiness derives from tenant-scoped AI settings plus the managed
deployment key and returns no secret material. Deterministic no-LLM reads and confirmed
proposals retain their existing order before the new guidance fallback. Focused tests,
lint, frontend build and the real disposable demo acceptance pass. T038/T039 satisfy
FR-024/025 for the development artifact; full release gates remain open as recorded.

### No-scroll first-use implementation review

The change is responsive presentation plus accounting for the development notice's
known height. Smaller viewports retain normal document scrolling, labels and controls.
The 1440 by 960 assertion and full real demo acceptance pass. No service, schema,
tenant, confirmation or persistent-release behavior changed. T040 satisfies FR-026.

### Demo default and missing-AI pre-implementation review

FR-024/025, the plan and T038/T039 agree on one shared setup behavior and one shared
Copilot readiness signal. The API retains its false default, so existing clients do not
gain implicit side effects. The browser owns the visible default before confirmation.
The readiness payload discloses no credential, and Chat continues to call shared
services. No schema, tenant boundary, confirmation rule or alternative demo scheduler
is introduced. Cross-artifact analysis found no critical gap or unresolved decision.
