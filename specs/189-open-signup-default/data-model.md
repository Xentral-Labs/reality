# Data Model

No schema change. AppUser transitions unverified → active after valid verification
in unlimited or available finite mode; otherwise pending_approval. Existing
AccessApplication receives approved/pending and the existing review timestamp.
AccessAdmissionCounter.used_slots records successful automatic admissions in both
open and finite modes. Tenant membership and invitation relationships are unchanged.
