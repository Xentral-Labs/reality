# Plan
## Constitution Check
PASS all principles: frontend composition only, existing chat services/tenant boundary and confirmations, no schema or derived authority. Attachments are explicitly editable chat text; no fabricated SourceRecords. Dictation never executes or sends automatically.
## Implementation
Add ChatComposer.tsx for draft input, local text reading and browser dictation with teardown. Pass active visibility into ChatPage. Move dock header/history into ChatPage; remove redundant Shell header. Retain non-dock compatibility. Scroll messages and proposal controls together. Add scoped CSS for flat dock messages/tables and composer, with theme tokens.
## Tests first
Observe failing browser proof for new controls before implementation. Mock native speech recognition deterministically; no real microphone or shared business writes. Verify file limits/unsupported files, Enter/Shift+Enter, hide-stop and company isolation; existing frontend/browser regressions. No core changes: previous full backend baseline remains applicable.
## Rollback
Revert presentation components/styles; no API restart or migration.
