# Contract: `capability_catalog`

**Access**: read · **Group**: Discovery · **Confirmation**: none · **Side effects**: none

Answers what this Reality can do, and what the calling credential may use of it. Describes
capabilities only; it reads no tenant business record.

## Arguments

| Name | Type | Required | Meaning |
|---|---|---|---|
| `topic` | string | no | A topic key. Omitted, the answer is the topic index. |

An unknown `topic` is refused by naming the topics that exist.

## Step 1 — the topic index (no arguments)

```json
{
  "credential": {"kind": "interactive", "limits_tools": true},
  "topics": [
    {"topic": "payments", "label": "Invoices and payments", "capabilities": 32, "tools": 33},
    {"topic": "accounting", "label": "Accounting and allocation", "capabilities": 22, "tools": 27}
  ]
}
```

`credential.kind` is `manual`, `interactive` or `none`. `limits_tools` is false when no MCP
credential is in context, in which case every tool is reported callable.

## Step 2 — one topic

```json
{
  "topic": "payments",
  "label": "Invoices and payments",
  "capabilities": [
    {
      "capability": "Record dunning notice",
      "label_de": "Mahnung erfassen",
      "purpose": "change",
      "description": "Records one explicitly reviewed manual reminder and optional exact stated fee without sending a message.",
      "tools": [
        {"name": "finance_dunning_record_propose", "access": "propose",
         "callable": false, "reason": "scope_excluded"}
      ]
    },
    {
      "capability": "Dunning notices",
      "label_de": null,
      "purpose": "read",
      "description": "List recorded manual dunning notices with fee and reversal trace.",
      "tools": [
        {"name": "finance_dunning_notices", "access": "read", "callable": true, "reason": null}
      ]
    }
  ]
}
```

`label_de` is null where the resource catalog holds no German label; the English `capability` is
then the only name.

## Grant state

| `reason` | Meaning |
|---|---|
| `null` | The credential may call the tool. A call will not be refused for permission reasons. |
| `not_in_token` | A manual token whose tool list does not name it. |
| `not_in_grant` | An interactive grant whose scopes cover the tool's access class, but whose tool list does not name it. |
| `scope_excluded` | An interactive grant whose scopes exclude the tool's whole access class. |

The two interactive reasons are actionable in different ways, which is why they are
separate. `not_in_grant` is fixed by selecting the tool at consent. `scope_excluded` is
not: `approve_interaction` refuses tools outside the requested scopes, so no tool of an
unrequested access class can be in any grant, and the client must ask for the scope
before the tool can be selected at all.

`scope_excluded` cannot occur for a manual token, which models no access-class scopes.

## Invariants

- Every name in the MCP catalog appears under at least one topic.
- A tool bound to several capabilities is listed under each, with the same grant state.
- The topic keys are the eleven of `config/tool_catalog.json`; this tool defines none of its own.
- `callable: true` and a subsequent refusal for permission reasons is a defect, not a race.
