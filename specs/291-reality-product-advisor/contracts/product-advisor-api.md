# Contract: Product Advisor Question API

The existing public route remains backward compatible:

`POST /api/journey-guide/questions`

## Request

```json
{
  "question": "Wie würden wir B2B-Vertrieb mit Reality abbilden?",
  "locale": "en",
  "history": []
}
```

`locale` becomes a surface-language hint for ambiguous or very short input. The latest substantive question determines the answer language. Existing anonymous, read-only and bounded-history rules remain.

## Additive response

```json
{
  "question": "Wie würden wir B2B-Vertrieb mit Reality abbilden?",
  "detected_language": "de",
  "intent": "solution_advice",
  "status": "partial",
  "text": "Reality deckt den üblichen Ablauf ...",
  "citations": ["A01", "C07", "E02"],
  "matches": [],
  "outcome": "researched",
  "knowledge_version": "advisor-v1:sha256:...",
  "clarification": null,
  "claims": [
    {
      "id": "claim_...",
      "statement": "Mehrere Lieferungen können in einer Monatsrechnung zusammengefasst werden.",
      "support": "proven",
      "workflow_role": "native",
      "source_ids": ["journey:E02"],
      "limitations": [],
      "tools": []
    }
  ],
  "sources": [
    {
      "id": "journey:E02",
      "kind": "journey",
      "title": "Monthly collective invoice over several shipments",
      "url": "https://docs.example/getting-started/business-journeys#E02"
    }
  ]
}
```

## Compatibility and safety

- Existing clients may continue to render `text`, `status`, `citations`, `matches` and `outcome`.
- `citations` remains Journey IDs; other references appear in `sources`.
- New fields are optional to clients and clients never recalculate status.
- Provider failure returns validated deterministic evidence, one clarification or not established.
- Failed claim validation never passes raw provider prose through.
- The canonical read tool returns the same public structure. Authorized internal and tenant context is additive through existing scoped paths.
