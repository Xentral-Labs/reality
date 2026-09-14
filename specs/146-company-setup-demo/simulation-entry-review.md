# Simulation entry review

Owner approved the proposal: existing compatible Sandboxes use the shared controls; Storyline Sandboxes offer a separate demo. No unresolved clarification. FR-032 maps to the company-card entry and fallback browser checks; existing demo-live controls and setup-recovery tests retain confirmation and identity coverage. No critical findings, schema expansion or new service rules. The backend retains final eligibility authority.

Local verification passed: production build; 156 Web contract tests; four-language audit; formatting/spec policy; 8 new card/eligibility/setup browser cases; 8 saved-request recovery cases; 16 simulation lifecycle/layout cases. The current Sidebar includes Storyline between Companies and Demo Data, so the prior immediate-sibling assertion was corrected to relative ordering. No eligibility services, creation request identity or business effects were changed. Deployment remains pending green CI and merge.

Visual follow-up review: screenshot confirms legacy panel classes leave content flush against its border and heading without hierarchy. Scope is shared styling only; no unresolved product decisions or critical findings.

Final scope follows the owner correction: no inline creation, no historical-data suggestion and no change to existing backend compatibility restrictions. The unavailable card has explicit copy, a Companies link and shared spacing/heading/button tokens. Supported existing Sandboxes retain current connect/start controls. Removed obsolete initial-demo choice props. Local build, 156 contract tests, language audit, spec policy and eight localized desktop/mobile browser cases pass. No deployment before green CI and merge.
