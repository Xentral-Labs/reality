# UI contract

Desktop: full-height navigation; content-only 48px header; optional full-height side
chat with 48px header. Rail is 60px and expanded navigation is 200px.
Mobile: 48px content header with Navigation and Chat controls, labeled drawer,
viewport-bounded menus and existing overlay chat.
All controls keep localized accessible names. Native popovers close on Escape and
restore focus. Company changes dismiss company-scoped overlays. Existing permissions,
source links, action confirmations and API requests stay authoritative.

Inspector history is labeled Activities (German: Aktivitäten). Its history URL is
stable. The bottom utility area contains Actions and Profile, without an Activity
trigger or shell-owned activity overlay. Home retains its shared history drawer.

FR-009 supersedes the bottom Actions placement: Search actions plus a platform
shortcut hint lives in the company area and opens a centered palette. The lower
utility area contains Profile only. The existing catalog and execution contract stay.

FR-012 supersedes the title-plus-tabs arrangement: multiple tabs occupy the header
in place of its visible title, with an adjacent selected-register count. Page actions
and the labeled chat icon remain separate from the horizontal tab scroller. Pages
without multiple tabs retain title/count and all pages retain their information button.

FR-013 groups the three daily queues under Inbox. The shared primary tabs are now
Commitments / Exceptions / Decisions; direction and exception rules use local controls.
The Inbox sidebar entry has no aggregate badge and old queue URLs remain valid.
