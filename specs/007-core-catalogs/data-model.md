# Data Model: Canonical Core Catalogs

No PostgreSQL entity is added. These are immutable load-time definitions:

- **CommandDefinition**: unique name, services, mode, adapters, reads/writes, effect,
  confirmation, enriched input/return contracts.
- **BusinessEventDefinition**: unique exact type, producer, subject, affected Projections.
- **ProjectionDefinition**: unique display/materialized names, services, inputs,
  calculation, consumers, outputs, derived invalidating Events.
- **FactPredicateDefinition**: unique predicate, subject type, value contract, meaning,
  producer, consumers; the collection may be empty.
- **ApplicationReference**: version, principle, parameter descriptions, four arrays,
  and category counts.

Invalid configuration fails to load; valid configuration is read-only.

