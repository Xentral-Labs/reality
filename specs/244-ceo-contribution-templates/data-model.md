# Data Model: CEO Contribution Analytics Templates

No persistent entity or schema change is introduced.

## Contribution analytics template

- Stable key
- English and German label and explanation
- Context-free graph question
- Optional relative period metadata
- Declared nodes, properties, measures, and ordering only

## Runtime contribution question

The adopted template becomes executable only after it carries exactly one eligible existing context: confirmed contribution review action, captured contribution generation, or verified company contribution generation. Currency and base unit remain required grouping axes. Final DB1/DB2 and rates retain canonical completeness behavior.

## Lifecycle

Declared → validated at load → listed → adopted context-free → context selected → tenant-scoped execution → optionally saved as an ordinary graph report.
