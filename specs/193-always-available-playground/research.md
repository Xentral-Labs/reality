# Research

Decision: remove the gate from all four shared services, including explicit false.
Rationale: the owner requested removal, and inconsistent defaults caused production
Storyline failures. Alternatives rejected: changing only the default would leave a
hidden operator switch; enabling it only in AWS would retain the product defect.

Decision: keep availability response booleans as true for compatibility; retain
separate account eligibility. No unknown technology choices require research agents.
