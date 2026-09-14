# What Can Be Adapted?

This page is for ERP consultants and integration developers. Start with the business outcome, then
choose the smallest extension that produces it.

If you first want to understand Reality with data from a system you already know, follow
[Try Reality alongside your ERP](./parallel-test). It starts read-only with respect to the ERP and
shows when configuration is enough and when a small adapter or interpreter is still needed.

| Business requirement                          | What you change                           | Usually requires                     |
| --------------------------------------------- | ----------------------------------------- | ------------------------------------ |
| Import orders from another ERP                | connector transport and order interpreter | integration code                     |
| Map different CSV column names                | file mapping                              | configuration or a small code change |
| Accept another ERP object type                | Source Capability and interpreter         | integration code                     |
| Call an existing Reality operation            | HTTP API or MCP tool                      | integration configuration            |
| Place an existing action in another workspace | workspace catalog                         | configuration                        |
| Calculate a genuinely new business position   | Projection                                | Reality Core development             |
| Detect a new operational risk                 | Exception derivation                      | Reality Core development             |
| Introduce a new governed business operation   | service and Command                       | Reality Core development             |

## What can normally stay unchanged

An ERP connection should not require a second order, inventory or finance model. The connector keeps
the original payload; the interpreter translates understood meaning into the existing Evidence and
Reality records. Unknown fields remain available in the `SourceRecord.payload`.

Before writing code, inspect the generated
[business commands and agent tools](../tool-usage/commands) and the
[views, projections and actions](../tool-usage/views). Often the required capability already exists
and only the ERP transport or interpretation is missing.

## Choose the next chapter

- To bring records into Reality, continue with [Connect another ERP](../development/connectors).
- To understand the full path, read the [ERP order example](./order-example).
- For authentication, versioning, retries and errors, read the
  [Connector contract](./connector-contract).
- To call existing capabilities, use [API and agent interfaces](../api-tools/).
- Only when the required business behaviour does not exist, continue with
  [Reality Core Development](../development/).

## Add supported observations without a new connector

Owners can configure bounded Fact rules for retained sources and existing subjects. Start with
[missing-information guidance](/concepts/business-reality-guide/06-facts-and-open-questions#missing-information):
simulate before activation, then replay older sources separately. This can extract an observation or
produce a reviewed classification. It is not a general field editor, a transport connection, an
arbitrary formula engine or a custom Exception builder.
