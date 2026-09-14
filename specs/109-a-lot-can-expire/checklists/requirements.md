# Specification Quality Checklist: A Lot Can Expire

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-08
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] Every functional requirement has an acceptance scenario or a named edge case
- [x] Every domain requirement states what may not be computed or invented
- [x] The report deliberately not built is named, argued, and given an unblocking condition
- [x] The schema exception is justified with the alternatives that were rejected
- [x] What the feature cannot prevent, only report, is stated

## Author Notes

Shelf life is the largest business gap left in the model, and the feature is smaller than the gap:
**one nullable date**. `Lot` carries an item, a number, where it came from and when it was
recorded, and nothing anywhere in the schema can hold a best-before — the three `expires_at`
columns belong to invitations and chat sessions. For a company trading food, pharmaceuticals,
cosmetics or chemicals, that is not a missing report. It is a missing sentence, and the
consequence is the worst kind: **expired stock looks exactly like good stock.**

Two things a reviewer should weigh, and the first is what is *not* here.

**There is no "expiring soon" class**, which is the more useful report and the one a reader will
look for. It needs a horizon, and no horizon exists on stated ground: nothing on an item says a
shelf life, no term says a minimum remaining life. The one mechanism that could produce a number
is Spec 080's learned rule — which already governs **ten of the thirty-four classes** on figures
nobody has checked against a real business, the largest standing risk in this queue. Adding an
eleventh to buy a threshold nobody could defend is the wrong trade. Reporting what has *actually*
expired needs nothing invented at all, and the specification names exactly what would unblock the
other: a customer's stated minimum remaining life, or a measured turnover from a real tenant.

**This reduces surprise rather than preventing loss.** Nothing is blocked: a picker can still ship
expired stock, and the entry reports it afterwards. Refusing the movement would stop a company
recording something that already happened — the customer has the goods either way — and choosing
which lot ships is an allocation policy this product has never had and this does not start.

One smaller decision worth flagging: a **stated date cannot be corrected**. Re-stating a different
one is refused, because a best-before read off the goods is a received value and two dates for one
lot means one is wrong in a way the product cannot adjudicate. A typo is therefore stuck until
somebody builds the append-only restatement Spec 093 built for promises. Silently overwriting a
received value would be worse; refusing at least makes the typo visible.
