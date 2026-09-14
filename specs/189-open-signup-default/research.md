# Research

Decision: absent or blank limit means unlimited; use None/null, not a huge number
or negative sentinel. This distinguishes unlimited from manual review and preserves
positive capacity. Invalid/negative explicit values retain manual review.

Decision: extract the existing counter operation into one shared service used by
auth and platform reporting. An extra setting or schema would duplicate policy.

Decision: increment the existing counter even in unlimited mode so switching to a
finite cap remains cumulative. Keep explicitly restricted profiles and existing
pending/rejected accounts unchanged. No unknown technology or external research needed.
