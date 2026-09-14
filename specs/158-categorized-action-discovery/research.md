# Research

- Decision: one validated core catalog, surfaced through application-reference.
  Rationale: current launcher, workspace catalog and page literals disagree.
  Alternative rejected: a frontend-only taxonomy duplicates classification ownership.
- Decision: business categories contain both Action and Command entries with badges.
  Rationale: preserves semantic distinction without two long lists.
- Decision: native disclosures, controlled branch expansion and pure search helper.
  Alternative rejected: dependency-heavy tree widget; this is browsing, not file editing.
- Decision: retain explicit typed forms and management navigation destinations.
  Alternative rejected: execute arbitrary command inputs from catalog metadata.
- No unresolved research questions. Existing repository tools suffice.
- Decision: store discovery metadata as JSON, loaded by the existing core YAML parser.
  Rationale: JSON is also directly readable by Node-only web CI. The portable catalog
  fixture carries command/action source data; classification remains in production metadata.
