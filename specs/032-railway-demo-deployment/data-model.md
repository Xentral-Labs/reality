# Data Model: Temporary Hosted Product Demo

No Business Reality schema changes are introduced. The following are deployment resources, not domain entities and not database tables.

## Demo Environment

- **Identity:** provider project ID plus environment ID.
- **State:** empty → provisioning → deploying → healthy → disabled → deleted.
- **Contains:** Product Web service, Web/API service, managed PostgreSQL, environment variables, and one public Product Web domain.
- **Invariant:** only Product Web has a public domain.

## Demo Account

- **Identity:** existing opaque application user ID.
- **Owner account:** dedicated bootstrap platform administrator, retained only by the owner.
- **Evaluator account:** active non-admin user with explicit membership in the prepared tenant.
- **Invariant:** evaluator access never relies on platform-admin bypass.

## Deployment Credential

- **Identity:** provider-managed project token identity; the secret value is never persisted in repository artifacts.
- **Scope:** one project environment.
- **State:** active → revoked.
- **Invariant:** removal of the demo includes revocation and removal from the ignored local environment file.

## Managed Data Store

- **Identity:** provider service ID and private connection reference.
- **Owns:** existing PostgreSQL Business Reality records and schema version.
- **State:** provisioning → migrated → available → deleted.
- **Invariant:** it has no public domain or TCP proxy.

## Public Domain

- **Identity:** provider-generated HTTPS hostname.
- **Routes to:** Product Web port 80 only.
- **State:** provisioning → available → removed.
- **Invariant:** its exact HTTPS origin is the API's configured application URL.
