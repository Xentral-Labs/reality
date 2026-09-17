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
