# Data Model: Reality Product Advisor

The first release adds no database tables. These are immutable generated or request-scoped domain models, not business authority.

## EvidenceSource

- Opaque stable identity, source kind, public title, visibility and authority class
- Governed logical location and optional public link
- Deterministic content fingerprint and freshness information

A source must originate in a canonical catalog or explicit allowlist. Draft plans, tasks and ideas cannot establish current capability.

## EvidenceUnit

- Opaque identity and shortest link to its EvidenceSource
- Subject, bounded search text and source-owned claim text
- Support meaning: proven, limited, unavailable, explanatory or vocabulary-only
- Limitations, validated references, canonical language and fingerprint

Units retain source meaning and cannot upgrade it. Tool vocabulary proves a tool's existence and mode, not an end-to-end outcome.

## AdvisoryQuestion

- Bounded latest question and conversation history
- Detected language, optional surface-language hint and evidence scope
- Intent, no more than six subquestions and explicit interpretation when needed

User/history text is context, never evidence. Public questions contain no tenant selector.

## AdvisoryClaim

- Request-scoped identity, requested subject and material statement
- Support: proven, limited, unavailable or not established
- Exact EvidenceUnit references and mandatory limitations
- Workflow role: native, agent proposal, confirmed execution, manual, workaround or gap
- Exact governed tool names and validation result/reason codes

Every accepted material statement has eligible evidence or is explicitly not established. Support cannot exceed the most restrictive applicable evidence.

## AdvisoryAnswer

- Question, detected language, intent and backward-compatible aggregate status
- Direct summary, validated claims, workflow, tools and limitations
- Public sources, Journey citations, optional clarification and knowledge version
- Outcome: researched, deterministic, clarification or unavailable

Composition cannot add a material statement absent from accepted claims. Public output omits internal traces. The answer is not persisted as operational authority.

## BuyerEvaluationCase

- Stable identity and equivalent questions in representative languages
- Expected intent and support range
- Required claims and limitations
- Forbidden claims and allowed source classes
- Maximum clarification count

The runner checks structured claims first and prose safety second; exact prose is not fixed.

## KnowledgeVersion

- Deterministic artifact fingerprint and schema version
- Complete sorted source/unit fingerprints
- Informational generation time excluded from identity

Equivalent public questions on the same version share evidence and support ceilings.
