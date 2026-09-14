# Feature Specification: Context Graph naming

**Language**: English

## Context and Intent
### Problem
The connected facts of a company appear under several names. The Reality Inspector
navigation calls the section Context, its page heading says Understand context, and the
public site speaks of a temporal plan-versus-actual graph, the full graph, a subgraph and a
context load. The same thing therefore has no name a reader can carry from the landing page
into the product.
### Scope
Name the connected facts the Context Graph everywhere: the Reality Inspector navigation
entry and the public site wherever it speaks of facts connected over time. The term is a
product term and reads the same in every language.
### Non-Goals
No change to routes, tabs, reads, layout, the Timeline recorder or the Record graph tab. No
change to the marketing claims themselves beyond the name; no rename of the domain terms
Fact, Evidence, Commitment, Reservation and Movement.

## User Scenarios & Testing
### US1 — From the landing page into the product
A reader sees on the public site that agents load the Context Graph, opens the app and finds
the Reality Inspector entry Context Graph with the Timeline and Record graph tabs.
Acceptance: the navigation entry reads Context Graph in all four languages; the public site
uses Context Graph where it explains connected facts and no longer says subgraph or full
graph; existing inspector_view URLs still open the section.

## Requirements
- **FR-001**: The first Reality Inspector navigation section is labelled Context Graph;
  its tabs and routes are unchanged.
- **FR-002**: The public site uses the term Context Graph wherever it describes facts
  connected over time (the Why Reality graph illustration and its footer, the agent context
  cut, the landing page comparison card, the illustrative timeline, the agent principle and
  the MCP door). The term is invariant across English, German, Dutch and Spanish.
- **FR-003**: The localization audits of the web app and the public site treat Context Graph
  as an invariant product term.

## Assumptions and Dependencies
Owner chose the name on 2026-09-10 after weighing Timeline, Fact Graph and Context Graph:
Fact is a typed record in Reality and must not be widened, and Context alone names a purpose
rather than a thing. Timeline stays the name of the recorder tab inside the Context Graph.
No unresolved clarifications.

## Success Criteria
- SC-001: Navigation contract, site contracts, both localization audits, both builds and the
  spec gate pass.
- SC-002: A repository search of the public site finds no "subgraph" and no "full graph".

## Requirement Traceability
FR-001 → US1, T001. FR-002 → US1, T001. FR-003 → T001. SC-001–002 → T002.
