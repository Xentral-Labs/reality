# Research: Prominent Open-Source Entry

## Persistent discovery

**Decision**: Add GitHub as a labelled utility link in the existing shared navigation and keep the three entries that represent Site pages.

**Rationale**: The repository is reachable from every entry page without pretending it is a fourth local page. The existing mobile disclosure carries the same content.

**Alternatives considered**: Footer-only placement remains too easy to miss. A separate local page adds maintenance without improving direct code access.

## Editorial placement

**Decision**: Place one open-source band immediately before the final account CTA.

**Rationale**: Visitors first understand the product, then receive proof they can inspect, then choose whether to start.

**Alternatives considered**: A hero GitHub button competes with the primary CTA. Repeating the band distracts from each page's purpose.

## External dependency behavior

**Decision**: Render static canonical links and fetch no GitHub data.

**Rationale**: Repository availability cannot affect rendering, no rate limits or loading states arise, and claims remain reviewable.

**Alternatives considered**: Stars, releases, and contributor counts add runtime dependency and volatile marketing claims.
