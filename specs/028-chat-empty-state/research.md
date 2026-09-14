# Research: Focused Chat Empty State

Use loaded zero-session state as the sole condition for the session rail, always omit the redundant conversation header, and retain lazy session creation on first send. This distinguishes confirmed emptiness from loading and preserves the canonical API/service path. Creating a placeholder session on page load was rejected because merely viewing Ask Reality must not mutate tenant state.
