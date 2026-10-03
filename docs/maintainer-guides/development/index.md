# Extending Reality

## What you will learn

Learn which building blocks Reality uses and how to adapt an existing template for your own
extension. You will be able to add a read surface, application operation or interface and verify its
result.

You need basic Python knowledge and a repository checkout. Web surfaces also require
TypeScript/React. You do not need to memorize business rules: the chapters share one story,
**reserve stock and understand fulfillment blockers**.

## How the building blocks connect

A **View** presents data. A **Projection** supplies a derived read model when needed. A **Command**
defines a shared application operation; **Agent Tools** and **Web Actions** expose it through
different entrypoints. An exception describes a current condition requiring attention.

```text
Read:    View or Agent Tool → shared reader → Reality or Projection
Act:     Web Action or Agent Tool → Command/service → Reality
Import:  Connector → SourceRecord → interpreter → Evidence → Reality
```

Mutating Agent Tools prepare proposals; execution follows explicit approval. A View does not
automatically need a Projection. Technical category names remain English in every language.

## Building blocks at a glance

| Building block          | Purpose                   | Example              | Guide                        |
| ----------------------- | ------------------------- | -------------------- | ---------------------------- |
| View                    | Present data              | Fulfillment blockers | [Views](./views.md)             |
| Projection              | Derive a read model       | Fulfillment queue    | [Projections](./projections.md) |
| Command                 | Execute an operation      | Reserve stock        | [Commands](./commands.md)       |
| Exception               | Identify attention needed | At-risk commitment   | [Exceptions](./exceptions.md)   |
| Agent Tool              | Offer agent access        | Propose reservation  | [Agent Tools](./agent-tools.md) |
| Web Action              | Offer a human workflow    | Reservation form     | [Web Actions](./web-actions.md) |
| Connector / interpreter | Receive source data       | ERP order            | [Data sources](./connectors.md) |

API and CLI are further entrypoints to the same services; the [adapter guide](./api-cli.md) covers
their implementation.

## How to read this handbook

1. Start with [configuration or development?](../integrations/customization.md). Not every adaptation
   needs code.
2. Follow the [first extension](./first-extension.md): a small read agent interface with no new
   business rules.
3. Choose your chapter. Each explains purpose, prerequisites, a worked example, changes,
   verification and an exercise.
4. Use the [shared development reference](./reference.md) for repository locations, Spec Kit workflow
   and checks.

If you already know what you need, go directly to that building block. Chapters explicitly state
which parts must already exist.
