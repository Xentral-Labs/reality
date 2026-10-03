# Maintainer guides

Public product documentation is for getting started, using Reality, understanding business records
connecting agents and a curated developer entry. Installation, deployment, runtime configuration and deeper implementation guides
live here for repository maintainers and integration developers.

Spec impact: none. This documentation-only change relocates existing technical guides, simplifies
public navigation, offers three starting recipes including a guided demo-agent handover and recurring-run setup, expands the public glossary with existing product and developer concepts, and removes deployment choices from product onboarding. It does not alter
installation, business services, authorization, confirmation or source interpretation.

The demo handover distinguishes seeded purchasing/return cases from continuous sales and customer
payment intake. Recurring purchasing and finance checks describe existing tools; expanding the
synthetic source lifecycle remains separate implementation work.

## Install and operate

- [Installation options](operations/index.md)
- [One-line installer](operations/installation.md)
- [Docker Compose](operations/docker-compose.md)
- [Kubernetes and Helm](operations/kubernetes.md)
- [Railway](operations/railway.md)
- [Deployment and operation](operations/deployment.md)
- [Environment variables](reference/environment.md)
- [Docs URL configuration](reference/docs-url-configuration.md)

## Develop and integrate

- [Extension handbook](development/index.md)
- [Configuration or development](integrations/customization.md)
- [First extension](development/first-extension.md)
- [Source interpretation and integration contract](integrations/connector-contract.md)
- [Example ERP integration](integrations/example-erp.md)
- [Technical order-import example](integrations/order-example.md)
- [Complete integration guides](development/connectors.md)
- [Technical pilot checklist](integrations/parallel-test.md)
- [Table responsibilities](reference/table-map.md)

Existing German editions are retained in `de/` for reference. New repository decisions and technical
changes are recorded in English.
