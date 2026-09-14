# Retirement dependency review

- Decision: remove presentation, preserve backend history contracts. Existing audit records active/archived runs and unresolved outcomes; erasing services or migrations is not necessary to remove the UI.
- Decision: move the exception catalog into unified/. Both AttentionPage and RealityInspectorPage import it; deleting it would break retained pages.
- Decision: sole entry plus explicit compatibility map. Leaving the migration flag or old fallback retains two products; blindly mapping every path to Home conceals invalid bookmarks.
- Decision: retain shared Tailwind/auth styles and remove legacy-only CSS. The current shell owns its UI styling independently.
- Alternatives rejected: deleting tables, converting sandbox tenants to production, recreating all legacy workflows, or embedding the old Playground in the new shell.
