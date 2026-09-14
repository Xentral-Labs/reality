# Research
Decision: one tenant per sandbox, reuse its name and add a lifecycle discriminator.
Current active-owner uniqueness prevents persistence; change it only for practice
companies. UI-only naming cannot protect lifecycle; production tenant sharing violates
isolation; JSON metadata for a repeated lifecycle predicate loses a useful constraint.
No new technology or unknown requiring external research.
