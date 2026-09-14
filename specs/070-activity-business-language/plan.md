# Implementation Plan: Business-readable Activity

## Summary

Keep Activity catalog membership as the cross-functional Company Overview read surface, but render its one navigation entry in the primary block and exclude it from contextual View lists. Enrich the existing tenant-scoped timeline response with display labels assembled from BusinessEvent payloads and batched shortest-link Party and Item reads. Render exact technical fields behind a disclosure.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Existing source, document, and Reality identifiers remain available. | PASS |
| Reality authority | BusinessEvents and related authoritative records remain the only inputs. | PASS |
| Proven schema | No fields or migration are added. | PASS |
| Tenant/service boundaries | Enrichment occurs in the tenant-scoped timeline service using tenant-filtered batch reads. | PASS |
| Test evidence | Service/API and frontend contracts precede implementation. | PASS |
| Explainable Web | Business language leads while technical traceability remains on demand. | PASS |
| Smallest design | Existing endpoint, page, navigation component, and localization system are reused. | PASS |

## Technical Approach

- Filter `activity` from the catalog-derived contextual navigation set and render one fixed `timeline` button after Exceptions.
- Derive group and event display fields in `timeline_activity`; batch-resolve referenced Party and Item names within the tenant.
- Extend the existing typed timeline response and render business copy first.
- Put exact event type and identifiers inside a nested `Technical details` disclosure.
- Update the durable Web contract and localization strings.

No schema, migration, new endpoint, or new dependency is required. Rollback restores the former navigation placement and removes additive display fields.

## Test Strategy

Add a service/API story for a sourced sales order and frontend structural contracts for fixed placement, workspace exclusion, business display fields, and technical disclosure. Run focused backend tests, Node contracts, formatting, localization audit, Web build, spec check, and diff review.

