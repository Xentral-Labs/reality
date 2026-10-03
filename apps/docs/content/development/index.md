# Build with Reality

Reality gives you an operational business model and shared application services to extend. You can
add a business rule, interpret data from your ERP or expose a capability to agents and applications.
The same rule then serves Web, Chat, MCP, API and CLI through their existing boundaries.

## Three things you can build

| Your goal             | A concrete example                                                                                          | Start here                                         |
| --------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Extend business logic | Add a tenant-scoped operation that checks a business condition and records its approved effect.             | [Develop business logic](./commands)               |
| Connect an ERP        | Receive an original order payload, retain it losslessly and interpret its order lines and delivery promise. | [Connect ERP and data sources](./connectors)       |
| Add an interface      | Let an agent or application read stock or prepare a reservation through the existing service.               | [Agent and API interfaces](./application-surfaces) |

## Start with a working example

Follow [your first extension](./first-extension): add a read-only Agent Tool that returns the same
inventory rows as an existing capability. You will register its input schema, reuse the shared
application tool and verify its result with the repository's PostgreSQL fixtures.

The exercise is deliberately small. It shows the complete extension path without asking you to
invent new business rules or a new database table.

## Where business logic belongs

```text
Web / Chat / MCP / API / CLI
             ↓
Shared Application Tool and service
             ↓
Tenant-scoped Reality records
```

A service owns the business rule. Its interfaces translate inputs and expose results; they do not
reimplement that rule. For example, a reservation checks the delivery commitment and available stock
in the shared service, regardless of whether a person or agent requested it.

ERP intake follows **Source → Evidence → Reality**: preserve the received payload, interpret its
business evidence and create the operational records it supports. A connector transports data; an
interpreter gives it business meaning. See
[From source data to Reality](/integrations/connector-contract).

## Choose your next step

- [Business logic](./commands): service, application operation, catalog and tests.
- [ERP integration](./connectors): source identity, lossless intake and interpretation.
- [Agent tools](./agent-tools): discovery, schemas, shared readers and governed proposals.
- [API and CLI](./api-cli): thin adapters around an existing capability.

Changes follow the repository's specification and test workflow. Mutating agent calls prepare a
proposal and require human confirmation. Every read and write stays scoped to its company.

The
[repository development handbook](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/README.md)
contains deeper guides for views, projections, exception derivations and implementation checks.
