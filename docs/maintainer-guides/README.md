# Maintainer guides

Public product documentation is for getting started, using Reality, understanding business records,
connecting agents and a curated developer entry. Installation, deployment, runtime configuration
and deeper implementation guides live here for repository maintainers and integration developers.

- Spec impact: none
- Reason when none: This documentation-only change relocates technical guides, simplifies public
  navigation, introduces three starting recipes and expands the glossary. It changes no business
  services, schemas, authorization, confirmation or source interpretation.

The demo handover assigns responsibility and a schedule within each short mission. It distinguishes
seeded purchasing/return cases from continuous sales and customer payment intake. Recurring
purchasing and finance checks describe existing tools; expanding the synthetic source lifecycle
remains separate implementation work. The final mission checks existing routines rather than
creating a second daily plan.

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
