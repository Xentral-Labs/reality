# Implementation Plan: Playground Companion

## Technical Context
Python/FastAPI/SQLAlchemy and React/TypeScript reuse the managed Anthropic tool loop.
No schema change or new dependency. Conversation is bounded browser state.

## Constitution Check
All principles PASS: shared read tools preserve Source → Evidence → Reality;
no operational derivations, schema, received-value recalculation or business writes.
Owner-scoped run validation supplies the tenant. Tool schemas and dispatch both use
read-only access within a transaction/session-bound companion authority. Existing
normal Copilot behavior is unchanged. Tests precede implementation.

## Design
- services/tenant_policy.py: narrow owner/run/session scope authorizes managed provider
  only and makes the existing tool loop read-only, including on practice companies.
- services/playground_chat.py: validates active/archived run, bounded question/history,
  uses the existing managed provider, reports failure honestly; stores no chat records.
- agent/mcp_chat.py: shared loop reads the scope and restricts schemas and dispatch.
- web/playground.py: owner-scoped POST /runs/{run_id}/chat, strict bounded body.
- apps/web/src/playground/PlaygroundChat.tsx: session-local conversation, contextual
  questions from loaded shared Reality presence, view shortcuts and fixed composer.
- PlaygroundWorkspace.tsx/css: attention remains right; chat is an alternative central
  tab and remains mounted but hidden across tab changes; run key resets history.
  Standard theme and translations. This supersedes the initial right-column layout.

## Tests and review
FR-006 speaker refinement: replace visible speaker headings with article aria-labels;
preserve role-specific alignment, pending/error states and Markdown. User approved;
Constitution PASS and no critical findings. Regression contract, build and web gates.
FR-005 navigation refinement: remove only the companion's duplicate register links
and unused onView prop. Existing tabs and attention-detail links remain unchanged.
Owner approved; Constitution PASS; no critical analysis findings. Regression contract
checks absence of duplicate links and presence of both tabs; verify contracts/build.
FR-008/009 owner-approved refinement: remove the redundant chat header and focus
state. Keep completed history separate from a pending/failed user turn. Inline retry
resubmits that turn with unchanged completed history. Render accessible spinner and
respect reduced motion. Attention groups retain server order and use existing
inspector reads for context and RecordRelations for center exploration; no new
endpoint, schema or business rule. Missing context has an explicit fallback.
Test pending/success/failure/retry and known/unknown attention classes before adapters.
Analysis: requirements map to T009 and tests; no unresolved clarification or critical
finding. Constitution PASS. Rollback is frontend-only. Earlier focus tests are
superseded; collapsed timeline tests remain required.
FR-007: bound the collapsed recorder to 44px; reset on sandbox changes. Initial
focus-mode experiment was superseded by FR-008/009: remove focus state and controls,
retain central conversation state. Constitution PASS; no data or service impact.
FR-006 presentation refinement: reuse installed remark-gfm with ReactMarkdown's
element allowlist, scoped typography and a bounded table wrapper. Regression contract
and synthetic browser answer cover a heading, paragraph, list and wide table.
Constitution PASS; no service, prompt, schema or permission changes. No clarifications
or critical findings; rollback only the renderer/CSS. Tests precede implementation.
FR-001/002/005: frontend contracts, build, localization and desktop/mobile review.
FR-003/004: tests/test_playground_chat.py covers owner isolation, policy scope,
provider failure, read-only dispatch, unavailable key and unchanged normal Copilot.
Rollback removes the panel/endpoint/scope; no persisted data changes.
Highest risk: granting provider access must never grant a mutation capability.
