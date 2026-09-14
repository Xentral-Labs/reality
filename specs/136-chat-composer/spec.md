# Reference-style chat experience
**Language**: English
## Context and Intent
The owner requests the right chat to match the supplied screenshot: one compact header, flat messages, a single composer with attachment, microphone and send arrow, without extra cards.
### Non-Goals
No new model/provider, fabricated learning claim, automatic sending, binary document interpretation, source import or business mutation rule changes.
## User Scenarios & Testing
US1: Read plain assistant text and tables; switch history or start a conversation from header icons.
US2: Type, attach a supported text file or dictate into one draft, then explicitly send. Failure retains the draft. Hiding chat or switching company stops dictation.
## Requirements
- **FR-001**: Dock owns one header with current conversation title (New chat when empty), history toggle and new-chat icon. History selection is hidden by default. Use existing sessions API.
- **FR-002**: Dock messages and empty state have no individual card borders/background boxes. Markdown tables use readable row dividers and bounded horizontal scrolling. Messages/proposals scroll above a fixed composer; show actual pending status without invented progress. A sent question appears at once as the person's message, the field empties and the list scrolls to it; a failed send returns the draft to the field and withdraws the unsent message.
- **FR-003**: Single rounded composer contains borderless textarea, left paperclip, right microphone and upward send arrow. Preserve accessible labels, explicit submission, existing failure recovery, tenant isolation and confirmation flow. Enter sends; Shift+Enter inserts a newline; IME composition must not submit.
- **FR-004**: Paperclip accepts UTF-8 text, Markdown, CSV and JSON up to 64 KiB, reads locally and appends labeled original content to the editable draft. Reject unsupported/binary/oversized files visibly. Preserve the existing 4,000-character API message limit: refuse an attachment that would exceed it without truncation, and block oversize typed/dictated drafts with an explanatory message. No upload or source-import claim. Voice uses browser speech recognition only after user click and browser permission, appends final transcript without sending, exposes listening/stop/errors and stops on hide/company/unmount/send. Unsupported browsers give an honest explanation.
- **FR-005**: Four languages, both themes and mobile/desktop; brief accuracy footer, no unsubstantiated learning or data-retention promise.
## Requirement Traceability
FR-001..005: isolated browser fixture for flat messages/table, header/history/new chat, text file and rejection, mocked browser speech lifecycle, keyboard, immediate echo and send recovery, responsive screenshots; existing shell/delivery/activity browser and frontend gates.
## Assumptions and Dependencies
Repository content is English. Browser recognition availability varies; no separate transcription service exists. File content is user-provided chat text, not an imported business source. Existing core services and APIs are unchanged.
## Success Criteria
One visible dock composer/header, no message-card frames; controls have real bounded behavior and all required tests pass.
