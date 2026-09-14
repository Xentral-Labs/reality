# Acceptance: compact shell and persistent chat

Open http://localhost:5177/app. Header is 56px and remains at the top while scrolling.
Desktop navigation is 200px wide with 36px rows. Analytics is directly before Settings
in primary navigation, with Reports beneath Analytics. Migration support links remain
separate until final retirement.

The right chat is open by default on desktop. Use the header chat control or panel close
to hide it; reopening and changing workspace keep the draft/conversation. Switching
company remounts chat. On mobile use the header icon to open the full-width panel below
the header. Delivery discussion uses that same panel and current delivery context.

## Verification — 2026-09-08
- Test-first failure: missing data-global-chat panel before implementation.
- New test:shell-chat-browser passes sticky header geometry, compact rows, navigation
  order, hide/reopen and workspace draft retention, company isolation and one composer;
  48 open/closed layouts across 390/1440/1920px, four languages and two themes.
- Existing test:unified-browser (application and complete delivery/chat/action matrix)
  and test:activity-browser (16 layouts and history behavior) pass unchanged.
- 131 frontend contracts, 100 localization tests, 1872 keys per language with no
  missing/invalid entries, production build, format check, lint/spec/diff gates pass.
- Screenshots: /private/tmp/reality-135-browser. Logs: /private/tmp/reality-135-shell.log,
  /private/tmp/reality-135-existing.log, /private/tmp/reality-135-activity.log.
- No domain/service/tool/schema changes or shared business mutations. Previous complete
  backend baseline (Spec 134: 1750 passed, 7 skips) is retained; not rerun for this
  presentation-only increment. No API restart or deployment required.

Final review: selected tenant keys prevent cross-company draft retention; existing chat
mutation review and uncertain-send semantics are reused. Unique composer IDs avoid label
collisions for any remaining standalone reuse. Ordinary and practice admission remain
unchanged. Functional closure packages are still open; the owner explicitly requested
this bounded UI work earlier than the original sequence.

Navigation correction: browser first failed on the missing Analytics section. After the correction, the 48-layout shell browser matrix passes, including literal Analytics headings in all four languages, a single Reports link and section order above Company. Build, i18n audit, changed-file formatting, spec policy and diff checks pass. German desktop screenshot reviewed. No backend changes.

Company selector refinement (FR-006): shell/browser matrix passes with menu viewport bounds, selected state, Escape focus return, outside dismissal, tenant switch and draft isolation. Company-access and settings browser suites pass (including duplicate names, permissions and 48 localized settings layouts). Added the existing copilot response to older fixtures to support the global chat introduced in Spec 135. All 131 frontend contracts, production build, 1889-key localization audit, changed-file formatting, spec policy and diff checks pass. German desktop and narrow mobile popover screenshots visually reviewed. Existing browser company-select interactions now use the visible switcher buttons; no hidden compatibility select. No backend changes.

FR-007: daily-work sidebar has exactly Home, Your work, Exceptions and Decisions. Header toggle and existing copilot deep-link handling remain. Shell browser (48 layouts), unified app and full delivery/chat-action browser matrix, build, formatting, spec and diff checks pass.

FR-008: all twelve audited legacy exit sites removed. Unsupported proposals remain visible in Decisions, chat stays in the unified app, unknown-role party receipts enter Inspector record search, and sandbox company selection presents a read-only explanation with non-sandbox switch buttons. Verified by 133 frontend contracts, 1933-key/four-language audit, production build, changed-file formatting, spec/diff checks, shell browser (48 localized layouts, absent migration links and sandbox-to-live recovery), and full unified application/delivery browser including review and uncertain-outcome recovery. No actual business data changed. Existing legacy routes remain directly reachable; application/data retirement is not claimed.
