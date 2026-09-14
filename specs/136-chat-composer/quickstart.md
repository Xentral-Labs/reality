# Reference-style chat acceptance

Open http://localhost:5177/app. The right dock has one conversation header with history
and new-chat icons, unboxed messages/tables and one rounded composer. Its paperclip
opens a local text-file picker; the microphone starts browser dictation where available;
the arrow or Enter sends, while Shift+Enter adds a line. Hiding the dock stops dictation
and preserves the draft. File reading and speech never send automatically.

Attachments support UTF-8 .txt/.md/.csv/.json up to 64 KiB and must fit the existing
4,000-character message limit including the current draft and filename. No truncation,
binary upload or PDF/image interpretation. The native browser speech service may be
unavailable or need permission; failures remain visible and typing stays available.

## Verified — 2026-09-08
- New browser proof first failed on the missing Conversation history control.
- test:chat-composer-browser passes flat Markdown/table rendering, history/new conversation,
  literal file inclusion, unsupported/oversized/combined-message-limit rejection, simulated
  speech final-result append, hide teardown, unsupported-browser fallback, Shift+Enter,
  explicit Enter and retained draft after provider failure. Four table/error screenshots.
- test:shell-chat-browser passes 48 localized open/closed layouts and existing draft/tenant
  continuity; test:unified-browser passes existing application and full delivery/action/chat
  journeys; test:activity-browser passes history/focus behavior and 16 localized layouts.
- 131 frontend contracts, 100 localization tests, 1890 audited keys per language with no
  missing/invalid keys, production build, full format check, lint/spec/diff gates pass.
- No live microphone/provider call or shared business mutation is used as acceptance proof.
  Dictation is verified with both browser recognition constructors replaced by a test double;
  physical microphone/device/network quality is not claimed tested.
- No core, service, tool, schema or API changes; prior complete backend baseline remains
  Spec 134 (1750 passed, 7 skips), not rerun for this presentation increment.
- Logs use /private/tmp/reality-136-*.log; screenshots are in /private/tmp/reality-136-browser/
  and the refreshed /private/tmp/reality-135-browser/ layout matrix.

Final review: one header/composer; original content is editable chat input, never a new
source authority. Browser recognition aborts when its component/session is torn down,
when hidden, or when sending. Existing proposal review remains explicit. Unknown sends
retain the established reconciliation behavior. Functional closure and retirement remain
separate work; no deployment or API restart required for the local Vite app.
