# ADR 0003: Shortest true relationship
Status: accepted.

Store the shortest semantically correct FK and traverse for provenance. Example Reservation → Commitment → DocumentLine → Document → SourceRecord. Avoid redundant FKs that can disagree.
