# UI Contract: Home Activity Live Action

- `HomePulse` keeps ownership of the optional `watchLive` callback.
- The activity range control contains only 24 hours, 7 days and 30 days.
- When `watchLive` is available, `HomePulse` supplies a localized, keyboard-accessible action to `ActivityGraph`.
- `ActivityGraph` renders that action inline after its Live status and before the independent right-aligned range control.
- The action has link-like emphasis, retains a visible focus treatment and invokes `watchLive` once when activated.
- Without `watchLive`, the Live status remains unchanged and no empty action container is rendered.

